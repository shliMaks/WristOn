import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from geopy.geocoders import Nominatim

from core.custom_types import CrimeData
from scrapers.prompts.crime_analysis_prompt import get_crime_analysis_prompt
from core.config import CATEGORIES

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = get_crime_analysis_prompt()

client = genai.Client(api_key=GEMINI_API_KEY)
geolocator = Nominatim(user_agent="kyiv_safety_map_backend")


def analyze_crime_message(crimes: list[str]) -> list[CrimeData]:
    """
    Аналізує текст, визначає категорію, генерує заголовок і знаходить координати.
    Повертає словник, готовий до запису в БД, або None, якщо це не цільова новина.
    """
    if not crimes:
        return []

    numbered_crimes = "\n".join([f"[{i}] {text}" for i, text in enumerate(crimes)])

    try:
        chat = client.chats.create(
            model="gemini-3.1-flash-lite",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT, response_mime_type="application/json", temperature=0.1
            ),
        )

        response = chat.send_message(numbered_crimes)
        ai_results = json.loads(response.text.strip())

        processed_batch = [None] * len(crimes)

        for crime in ai_results:
            original_idx = crime.get("original_index")
            category_id = crime.get("category_id")
            if not category_id:
                continue

            title = crime.get("title", "Невідома подія")
            street = crime.get("street")
            is_outdoor = crime.get("is_outdoor")

            lat, lon = None, None

            if street and is_outdoor:
                location = geolocator.geocode(f"Київ, вулиця {street}", timeout=5)
                if location:
                    lat, lon = location.latitude, location.longitude

            if 0 <= original_idx <= len(crimes):
                processed_batch[original_idx] = {
                    "original_index": original_idx,
                    "category_id": category_id,
                    "title": title,
                    "street": street if street else "Локація невідома",
                    "lat": lat,
                    "lon": lon,
                }

        return processed_batch

    except Exception as e:
        print(f"Помилка пакетного аналізу API Gemini: {e}")
        return [None] * len(crimes)
