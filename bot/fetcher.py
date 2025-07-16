import os
import feedparser
from .config import RSS_FEED_URL, LAST_GUID_FILE

# Keywords to detect important anime news
RELEVANT_KEYWORDS = [
    "anime adaptation", "anime announced", "anime project", "tv anime", "new anime",
    "trailer", "teaser", "key visual", "promo video", "pv", "mv",
    "delayed", "delay", "postponed", "on break", "hiatus",
    "release date", "airing", "premiere", "starts airing", "final season", "season 2", "season 3"
]

def get_last_guid():
    if not os.path.exists(LAST_GUID_FILE):
        return None
    with open(LAST_GUID_FILE, "r") as f:
        return f.read().strip()

def save_last_guid(guid):
    with open(LAST_GUID_FILE, "w") as f:
        f.write(guid)

def is_relevant(entry):
    """Check if the RSS entry is anime-news relevant."""
    title = entry.get("title", "").lower()
    summary = entry.get("summary", "").lower()

    for keyword in RELEVANT_KEYWORDS:
        if keyword in title or keyword in summary:
            return True
    return False

def extract_image(entry):
    """Try to extract thumbnail or media image if available."""
    if "media_thumbnail" in entry:
        return entry.media_thumbnail[0]['url']
    elif "media_content" in entry:
        return entry.media_content[0]['url']
    return None

def fetch_latest_post():
    feed = feedparser.parse(RSS_FEED_URL)
    if not feed.entries:
        print("❌ No entries in RSS feed.")
        return None

    latest_entry = feed.entries[0]
    last_guid = get_last_guid()

    # Already posted?
    if latest_entry.id == last_guid:
        print("🔁 No new post (GUID match).")
        return None

    if is_relevant(latest_entry):
        save_last_guid(latest_entry.id)
        return {
            "title": latest_entry.title,
            "link": latest_entry.link,
            "summary": latest_entry.summary,
            "published": latest_entry.published,
            "image": extract_image(latest_entry)
        }
    else:
        print("⛔ Skipped: Not relevant.")
        return None
