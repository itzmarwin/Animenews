import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Example: "@yourchannelname"

# Multiple RSS sources
RSS_FEEDS = [
    "https://www.animenewsnetwork.com/all/rss.xml",
    "https://cr-news-api-service.prd.crunchyrollsvc.com/v1/en-US/rss",  # Crunchyroll
    "https://myanimelist.net/rss/news.xml",
    "https://animecorner.me/feed/"
]

# Directory to store last GUIDs per feed
LAST_GUID_DIR = "last_guids"
os.makedirs(LAST_GUID_DIR, exist_ok=True)
