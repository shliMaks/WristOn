from core.database import SessionLocal
from core.models import IncidentCategory
from core.config import CATEGORIES


def seed_categories():
    print("⏳ Заповнюємо таблицю категорій...")
    db = SessionLocal()

    try:
        added_count = 0
        for cat_id, cat_name in CATEGORIES.items():
            # Перевіряємо, чи немає вже такої категорії в базі
            existing_cat = db.query(IncidentCategory).filter(IncidentCategory.id == cat_id).first()

            if not existing_cat:
                new_category = IncidentCategory(id=cat_id, name=cat_name, danger_weight=1.0)  # Базова вага небезпеки
                db.add(new_category)
                added_count += 1

        db.commit()
        print(f"✅ Успішно додано категорій: {added_count}")

    except Exception as e:
        print(f"❌ Помилка: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_categories()
