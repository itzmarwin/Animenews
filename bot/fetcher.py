import os
import feedparser
from deep_translator import GoogleTranslator
from .config import RSS_FEEDS, LAST_GUID_DIR

# Anime-relevant keywords
RELEVANT_KEYWORDS = [
    "anime adaptation", "anime announced", "anime project", "tv anime", "new anime",
    "trailer", "teaser", "key visual", "promo video", "pv", "mv",
    "delayed", "delay", "anime film", "movie", "postponed", "on break", "hiatus",
    "release date", "airing", "premiere", "starts airing", "final season", "season 2", "season 3"
]

# Excluded non-anime related terms
EXCLUDE_KEYWORDS = [
    "zelda", "live-action", "netflix film", "game franchise", "hollywood", "actor", "casts"
]

def guid_path(feed_url: str) -> str:
    filename = feed_url.replace("https://", "").replace("/", "_") + ".txt"
    return os.path.join(LAST_GUID_DIR, filename)

def get_last_guid(feed_url: str) -> str:
    path = guid_path(feed_url)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return f.read().strip()

def save_last_guid(feed_url: str, guid: str):
    with open(guid_path(feed_url), "w") as f:
        f.write(guid)

def is_relevant(entry) -> bool:
    title = entry.get("title", "").lower()
    summary = entry.get("summary", "").lower()
    content = f"{title} {summary}"

    for word in EXCLUDE_KEYWORDS:
        if word in content:
            print(f"⛔ Skipped (excluded word): {word}")
            return False

    for keyword in RELEVANT_KEYWORDS:
        if keyword in content:
            return True

    return False

def extract_image(entry) -> str:
    if "media_thumbnail" in entry:
        return entry.media_thumbnail[0]['url']
    elif "media_content" in entry:
        return entry.media_content[0]['url']
    return None

def translate_if_needed(text: str) -> str:
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        return translated
    except Exception as e:
        print(f"⚠️ Translation failed: {e}")
        return text

def fetch_latest_post():
    for feed_url in RSS_FEEDS:
        print(f"🌐 Checking feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            print("❌ No entries found in feed.")
            continue

        latest = feed.entries[0]
        last_guid = get_last_guid(feed_url)

        if latest.id == last_guid:
            print("🔁 No new post (GUID match).")
            continue

        if is_relevant(latest):
            save_last_guid(feed_url, latest.id)

            title = translate_if_needed(latest.title)
            summary = translate_if_needed(latest.summary)

            return {
                "title": title,
                "link": latest.link,
                "summary": summary,
                "published": latest.published,
                "image": extract_image(latest)
            }
        else:
            print("⛔ Skipped: Not relevant.")
    return None
