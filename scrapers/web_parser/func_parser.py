import time
import geopy
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from scrapers.promts.crime_analysis_prompt import get_crime_analysis_prompt_web
from geopy.geocoders import Nominatim


load_dotenv()

geolocator = Nominatim(user_agent="kyiv_safety_map_backend")


API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite') 


def get_news_links_for_category(category_id, max_clicks=0):
    """Збирає посилання на новини через Playwright."""
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


def extract_location_from_text(text):
    """Виконує запит до ШІ та шукає координати."""
    # 1. Отримуємо готовий текст промпту
    prompt = get_crime_analysis_prompt_web(text)
    
    # 2. Відправляємо його в Gemini
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
        
        # 3. Шукаємо координати
        if street and is_outdoor:
            location = geolocator.geocode(f"Київ, {street}", timeout=10)
            if location:
                return street, location.latitude, location.longitude
                
        return None, None, None
    except Exception as e:
        print(f"Помилка аналізу: {e}")
        return None, None, None
