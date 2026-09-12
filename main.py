import time
import re
import requests
import os

import json
import google.generativeai as genai
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

from dotenv import load_dotenv


from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from playwright.sync_api import sync_playwright

from database import SessionLocal
from models import Incident

load_dotenv()

CATEGORY_MAPPING = {
    "Грабіж": 1,
    "Розбійний напад": 2,
    "ДТП": 3,
    "Вбивство": 4,
    "Хуліганство": 5
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

CATEGORIES = {
    316: "Грабіж",
    320: "ДТП",
    321: "Вбивство",
    322: "Розбійний напад",
    326: "Хуліганство",
}

genai.configure(api_key="")  

model = genai.GenerativeModel('gemini-3.1-flash-lite')

geolocator = Nominatim(user_agent="kyiv_safety_map")


geolocator = Nominatim(user_agent="kyiv_safety_map_backend")

def analyze_incident_with_gemini(text):
    """Відправляє текст у Gemini для витягування геолокації та форматує у JSON."""
    
    
    prompt = f"""
    Ти — аналітик кримінальних новин. Прочитай текст і витягни геолокацію.
    Поверни ТІЛЬКИ валідний JSON.
    Формат JSON:
    {{
        "street": "тільки назва вулиці (наприклад: Василя Порика)",
        "district": "район (наприклад: Подільський)",
        "is_outdoor": true або false (true - якщо злочин стався на вулиці, у парку, false - якщо у квартирі чи будинку)
    }}
    Якщо вулицю неможливо визначити, поверни null для поля street.
    
    Текст для аналізу:
    {text}
    """

    try:
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        
        data = json.loads(response.text)
        
        street = data.get("street")
        is_outdoor = data.get("is_outdoor")
        
        
        if street and is_outdoor:
            location = geolocator.geocode(f"Київ, вулиця {street}", timeout=5)
            if location:
                return street, location.latitude, location.longitude
                
        
        return None, None, None

    except Exception as e:
        print(f"Помилка API Gemini: {e}")
        return None, None, None


def get_news_links_for_category(category_id, max_clicks=0):
    """Збирає посилання на новини для конкретної категорії."""
    url = f"https://kyiv.npu.gov.ua/timeline?&type=posts&category_id={category_id}"
    links = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        time.sleep(2)
        
        for _ in range(max_clicks):
            try:
                btn = page.locator("text=Завантажити ще")
                if btn.is_visible():
                    btn.click()
                    time.sleep(2)
                else:
                    break
            except Exception:
                break
                
        elements = page.query_selector_all("a")
        for el in elements:
            href = el.get_attribute("href")
            if href and "/news/" in href:
                full_url = f"https://kyiv.npu.gov.ua{href}" if href.startswith('/') else href
                links.add(full_url)
                
        browser.close()
    return list(links)


if __name__ == "__main__":
    all_crimes = []

    
    

    for cat_id, crime_type in CATEGORIES.items():
        print(f"\n--- Збираємо посилання для категорії: {crime_type} ---")
        links = get_news_links_for_category(cat_id, max_clicks=0) 
        print(f"Знайдено {len(links)} новин. Аналізуємо текст...")
        
        for link in links:

            response = requests.get(link, headers=HEADERS)
            
            if response.status_code != 200:
                print(f"[!] Помилка доступу до {link}: статус {response.status_code}")
                time.sleep(1)
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            text = " ".join([p.get_text() for p in soup.find_all('p')])
            
            if len(text) < 50:
                print(f"Текст занадто короткий або не знайдено тегів <p>.")
                continue

            street, lat, lon = analyze_incident_with_gemini(text)
            
            if street:
                if lat and lon:
                    crime_data = {
                        "type": crime_type,
                        "street": street,
                        "lat": lat,
                        "lon": lon,
                        "url": link,
                        "source": "web"
                    }
                    all_crimes.append(crime_data)
                    print(f"Успіх! {crime_type}: {street} ({lat}, {lon})")
                else:
                    print(f"Знайдено вулицю '{street}', але Geopy не зміг її знайти на мапі.")
            else:
                pass 
            

            time.sleep(2)
    
    db = SessionLocal()

    for crime in all_crimes:
        point_geom = f"SRID=4326;POINT({crime['lon']} {crime['lat']})"
        
        # 2. Отримуємо правильний ID зі словника за назвою категорії
        cat_id = CATEGORY_MAPPING.get(crime['type'])
        
        # Захист від помилок: якщо категорію не знайдено, пропускаємо запис
        if not cat_id:
            print(f"невідома категорія '{crime['type']}' для новини {crime['url']}")
            continue
        
        new_incident = Incident(
            category_id=cat_id,
            title=f"{crime['type']} на {crime['street']}", 
            address_text=crime['street'],
            geom=point_geom,
            source_url=crime['url'],
            source="web"
        )
        
        try:
            db.add(new_incident)
            db.commit()
            print(f"Збережено: {crime['street']}")
        except Exception as e:
            db.rollback() 
            print(f"Помилка при збереженні {crime['url']}:")
            print(f"Деталі помилки: {e}\n")

    db.close()
