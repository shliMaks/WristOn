from bs4 import BeautifulSoup
import requests
import time

from core.config import HEADERS


def parse_page(
    channel_name: str,
    pages_to_scrape: int,
    headers: dict | None = HEADERS,
):
    url = f"https://t.me/s/{channel_name}"
    scraped_data = []

    for page_num in range(pages_to_scrape):
        current_page = page_num + 1

        if current_page == 1 or current_page % 5 == 0 or current_page == pages_to_scrape:
            pages_left = pages_to_scrape - current_page
            print(f"👉 [{channel_name}] Обробка сторінки {current_page} з {pages_to_scrape}. Залишилось: {pages_left}")

        response = requests.get(url, headers=headers if headers else {})

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            messages = soup.find_all("div", class_="tgme_widget_message_wrap")

            if messages:
                for msg in messages:
                    text_div = msg.find("div", class_="tgme_widget_message_text")
                    time_tag = msg.find("time")
                    msg_node = msg.find("div", class_="tgme_widget_message")

                    if text_div and time_tag and msg_node:
                        post_id_raw = msg_node.get("data-post")

                        scraped_data.append(
                            {
                                "raw_text": text_div.text,
                                "incident_date": time_tag.get("datetime"),
                                "source_url": f"https://t.me/{post_id_raw}",
                                "source_type": "telegram",
                            }
                        )

                oldest_msg = messages[0].find("div", class_="tgme_widget_message")

                if oldest_msg and oldest_msg.get("data-post"):
                    post_id = oldest_msg.get("data-post").split("/")[-1]
                    url = f"https://t.me/s/{channel_name}?before={post_id}"
                else:
                    print("Не вдалося знайти ID для гортання далі.")
                    break
            else:
                print("❌ На сторінці не знайдено блоків з повідомленнями.")
                break
        else:
            print(f"Помилка доступу до каналу: {response.status_code}\n")
            break

        time.sleep(2)

    return scraped_data
