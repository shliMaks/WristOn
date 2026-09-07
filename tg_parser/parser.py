from bs4 import BeautifulSoup
import requests
import time

from config import HEADERS


def parse_page(
    channel_name: str,
    pages_to_scrape: int,
    headers: dict | None = HEADERS,
):
    url = f"https://t.me/s/{channel_name}"
    for _ in range(pages_to_scrape):
        response = requests.get(url, headers=headers if headers else {})

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            msgs_container = soup.find("section", class_="tgme_channel_history")

            if msgs_container:
                messages = msgs_container.find_all("div", class_="tgme_widget_message_wrap")
                print(f"Знайдено повідомлень: {len(messages)}")

                if messages:
                    for msg in messages:
                        text_div = msg.find("div", class_="tgme_widget_message_text")
                        if text_div:
                            print("Текст:", text_div.text[:100], "...")
                            print("-" * 30)

                    oldest_msg = messages[0].find("div", class_="tgme_widget_message")

                    if oldest_msg and oldest_msg.get("data-post"):
                        post_id = oldest_msg.get("data-post").split("/")[-1]
                        url = f"https://t.me/s/{channel_name}?before={post_id}"
                    else:
                        print("Не вдалося знайти ID для гортання далі.")
                        break

        else:
            print(f"Помилка доступу до каналу: {response.status_code}\n")
            break

        time.sleep(2)
