import os
import feedparser
from .config import RSS_FEED_URL, LAST_GUID_FILE

# Keywords to detect important news
RELEVANT_KEYWORDS = [
    "anime adaptation",
    "anime announced",
    "anime project",
    "tv anime",
    "trailer",
    "teaser",
    "key visual",
    "delay",
    "postponed",
    "on break",
    "broadcast",
    "manga hiatus",
    "release date",
    "new anime"
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
    """Check if the entry is relevant based on keywords."""
    title = entry.title.lower()
    summary = entry.summary.lower()

    for keyword in RELEVANT_KEYWORDS:
        if keyword in title or keyword in summary:
            return True
    return False

def fetch_latest_post():
    feed = feedparser.parse(RSS_FEED_URL)
    if not feed.entries:
        return None

    latest_entry = feed.entries[0]
    last_guid = get_last_guid()

    # Skip if already posted
    if latest_entry.id == last_guid:
        return None

    # Save GUID only if post is relevant
    if is_relevant(latest_entry):
        save_last_guid(latest_entry.id)
        return {
            "title": latest_entry.title,
            "link": latest_entry.link,
            "summary": latest_entry.summary,
            "published": latest_entry.published,
            "image": latest_entry.media_thumbnail[0]['url'] if "media_thumbnail" in latest_entry else None
        }
    else:
        return None
