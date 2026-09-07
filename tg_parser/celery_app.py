from parser import parse_page

from config import TG_CHANNEL_NAMES, HEADERS

for channel_name in TG_CHANNEL_NAMES:
    parse_page(channel_name=channel_name, pages_to_scrape=1, headers=HEADERS)
