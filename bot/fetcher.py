import os
import feedparser
from .config import RSS_FEED_URL, LAST_GUID_FILE

# Include only relevant anime keywords
RELEVANT_KEYWORDS = [
    "anime adaptation", "movie", "anime announced", "anime project", "tv anime", "new anime",
    "trailer", "teaser", "key visual", "promo video", "pv", "mv",
    "delayed", "delay", "anime film", "movie", "postponed", "on break", "hiatus",
    "release date", "airing", "premiere", "starts airing", "final season", "season 2", "season 3"
]

# Words to skip if they appear in title/summary
EXCLUDE_KEYWORDS = [
    "zelda", "live-action", "netflix film", "game franchise", "hollywood", "actor", "casts"
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
    content = title + " " + summary

    # Debug: print title being checked
    print(f"🔍 Checking: {title}")

    for word in EXCLUDE_KEYWORDS:
        if word in content:
            print(f"⛔ Skipped (excluded word): {word}")
            return False

    for keyword in RELEVANT_KEYWORDS:
        if keyword in content:
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
