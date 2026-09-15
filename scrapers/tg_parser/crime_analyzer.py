import os
import json
import time
import math
from sqlalchemy.orm import Session

from scrapers.tg_parser.crime_evaluation import analyze_crime_message
from scrapers.tg_parser.tg_parser import parse_page
from core.config import RAW_DATA_FILE, BATCH_SIZE
from core.database import SessionLocal
from core.crud import get_incident_by_url, create_incident


def scrape_and_save():
    """Йде в Телеграм, збирає тексти і зберігає в JSON."""
    print("🚀 Починаємо парсинг...")

    data = parse_page(channel_name="KyivOperativ", pages_to_scrape=1)

    os.makedirs(os.path.dirname(RAW_DATA_FILE), exist_ok=True)

    with open(RAW_DATA_FILE, "w", encoding="utf-8") as f:
        # ensure_ascii=False зберігає кирилицю нормально, а не як \u043a
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"✅ Збережено {len(data)} повідомлень у {RAW_DATA_FILE}")


def analyze_and_save(db: Session):
    """Бере сирі тексти з JSON, пропускає через ШІ і зберігає готовий результат."""
    print("🧠 Починаємо аналіз ШІ...")

    with open(RAW_DATA_FILE, "r", encoding="utf-8") as f:
        raw_messages = json.load(f)

    total_batches = math.ceil(len(raw_messages) / BATCH_SIZE)

    for i in range(0, len(raw_messages), BATCH_SIZE):
        batch = raw_messages[i : i + BATCH_SIZE]
        batch_texts = [item["raw_text"] for item in batch]

        current_batch_num = (i // BATCH_SIZE) + 1
        print(f"📦 Обробка пачки {current_batch_num} з {total_batches} (повідомлення {i} - {i + len(batch) - 1})...")

        ai_results = analyze_crime_message(batch_texts)

        for idx, ai_data in enumerate(ai_results):
            if ai_data:
                original_item = batch[idx]
                existing_incident = get_incident_by_url(db=db, url=original_item["source_url"])
                if existing_incident:
                    print(f"⚠️ Пропущено (вже є в БД): {ai_data['title']}")
                    continue

                lat = ai_data.get("lat")
                lon = ai_data.get("lon")

                if lat is not None and lon is not None:
                    geom_value = f"POINT({lon} {lat})"  # PostGIS формат: POINT(довгота широта)
                else:
                    geom_value = None

                incident_data = {
                    "category_id": ai_data["category_id"],
                    "title": ai_data["title"],
                    "address_text": ai_data["street"],
                    "geom": geom_value,
                    "incident_date": original_item["incident_date"],
                    "source_url": original_item["source_url"],
                    "source": original_item["source_type"],
                }

                new_incident = create_incident(db, incident_data)
                print(f"➕ Додано подію: {new_incident.title}.")

        time.sleep(5)  # Max Requests Per Minute (RPM) = 15, 60 seconds / 5 = 12 RPM


if __name__ == "__main__":
    scrape_and_save()

    db = SessionLocal()
    try:
        analyze_and_save(db=db)
    except Exception as e:
        print(f"❌ Сталася помилка під час аналізу/запису: {e}")
        db.rollback()
    finally:
        db.close()
        print("🔒 З'єднання з БД закрито.")
