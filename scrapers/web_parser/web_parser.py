
import requests
import time
import dateparser

from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from core.database import SessionLocal
from core.models import Incident
from scrapers.web_parser.func_parser import get_news_links_for_category, extract_location_from_text
from core.config import CATEGORIES_WEB, CATEGORIES, HEADERS
from core.crud import get_incident_by_url, create_incident




db = SessionLocal()

for cat_id, crime_type in CATEGORIES_WEB.items():
    print(f"\n--- Збираємо посилання для категорії: {crime_type} ---")

    links = get_news_links_for_category(cat_id, max_clicks=0) 

    print(f"Знайдено {len(links)} новин. Аналізуємо...")

        
    for link in links:
        if get_incident_by_url(db, link):
            print(f"Пропущено (вже є в базі): {link}")
            continue 

        response = requests.get(link, headers=HEADERS)
        if response.status_code != 200:
            print(f"Помилка доступу до {link}")
            continue
                
        soup = BeautifulSoup(response.text, 'html.parser')
        article_text = soup.find("article", class_="editor-content")
            
        if article_text:
            text = " ".join([p.get_text() for p in article_text.find_all('p')])
        else:
            text = " ".join([p.get_text() for p in soup.find_all('p')])
            
        if len(text) < 50:
            continue

            
        date_block = soup.find('div', class_='page_title-desc')
        if date_block:
            raw_text = date_block.get_text(strip=True)
            clean_text = raw_text.replace("Опубліковано", "").replace("року", "").replace(" о ", " ").strip()
            parsed_date = dateparser.parse(clean_text, languages=['uk'])
            final_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S") if parsed_date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")            

        else:
            final_date = datetime.now().strftime("%Y-%m-%d")

            street, lat, lon = extract_location_from_text(text)
            
            if street and lat and lon:
                cat_db_id = CATEGORIES.get(crime_type)
                if not cat_db_id:
                    continue

                incident_data = {
                    "category_id": cat_db_id,
                    "title": f"{crime_type} на {street}",
                    "address_text": street,
                    "geom": f"SRID=4326;POINT({lon} {lat})",
                    "incident_date": final_date,
                    "source_url": link,
                    "source": "web"
                }

                try:
                    create_incident(db, incident_data)
                    print(f"Успіх! Збережено: {crime_type} на {street} ({final_date})")
                except Exception as e:
                    db.rollback()
                    print(f"Помилка бази при збереженні {link}: {e}")
            
        time.sleep(2) 
    
db.close()
print("Готово!")