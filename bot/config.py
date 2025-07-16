import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Example: "@yourchannelname"
RSS_FEED_URL = os.getenv("RSS_FEED_URL")  # Example: "https://www.animenewsnetwork.com/all/rss.xml"

# Local file to keep last posted GUID
LAST_GUID_FILE = "last_guid.txt"
