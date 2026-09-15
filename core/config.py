TG_CHANNEL_NAMES = [
    "KyivOperativ",
    "dtpkievua",
    "kievreal1",
    "trukhakyiv",
    "kievmap",
    "typical_kiev",
    "lossolomas_kyiv",
    "darnitsalive",
    "troeshchyna_kiev",
    "poznyaki_live",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

CATEGORIES = {
    1: "ДТП",
    2: "Пограбування / Крадіжка",
    3: "Напад / Бійка",
    4: "Шахрайство",
    5: "Інше / Підозріла активність",
}

RAW_DATA_FILE = "data/raw_messages.json"
PROCESSED_DATA_FILE = "data/processed_crimes.json"
BATCH_SIZE = 20
