FROM python:3.12-slim

WORKDIR /app
COPY . /app

# Встановлюємо залежності та системні браузери для Playwright
RUN pip install -r requirements.txt
RUN playwright install chromium
RUN playwright install-deps

# Команда за замовчуванням (запуск воркера Celery)
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]