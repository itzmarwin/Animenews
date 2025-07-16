import os
import feedparser
from deep_translator import GoogleTranslator
from .config import RSS_FEEDS, LAST_GUID_DIR

# Expanded anime-relevant keywords
RELEVANT_KEYWORDS = [
    "anime adaptation", "anime announced", "anime project", "tv anime", "new anime",
    "trailer", "teaser", "key visual", "promo video", "pv", "mv", "opening", "ending",
    "delayed", "delay", "anime film", "movie", "postponed", "on break", "hiatus", "break next week",
    "release date", "airing", "premiere", "starts airing", "final season", "season 2", "season 3",
    "manga adaptation", "manga announced", "manga project", "manga break", "manga returns",
    "announcement", "new series", "new project", "voice cast", "staff", "theme song", "episode",
    "returns next week", "no episode", "break announcement", "final episode", "new visual",
    "anime corner", "crunchyroll", "netflix", "disney+", "hulu", "streaming"
]

# Refined excluded terms
EXCLUDE_KEYWORDS = [
    "zelda game", "live-action adaptation", "hollywood adaptation", 
    "game franchise", "actor interview", "real film", "documentary"
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
    os.makedirs(LAST_GUID_DIR, exist_ok=True)
    with open(guid_path(feed_url), "w") as f:
        f.write(guid)

def is_relevant(entry) -> bool:
    title = entry.get("title", "").lower()
    summary = entry.get("summary", "").lower()
    content = f"{title} {summary}"

    # Skip if any exclusion keyword matches
    for word in EXCLUDE_KEYWORDS:
        if word in content:
            print(f"⛔ Skipped (excluded word): {word}")
            return False

    # Check for at least one relevant keyword
    for keyword in RELEVANT_KEYWORDS:
        if keyword in content:
            print(f"✅ Relevant (matched keyword): {keyword}")
            return True

    print("⛔ Not relevant: No matching keywords")
    return False

def extract_image(entry) -> str:
    # Try different possible image locations
    if "media_thumbnail" in entry and entry.media_thumbnail:
        return entry.media_thumbnail[0]['url']
    elif "media_content" in entry and entry.media_content:
        for media in entry.media_content:
            if media.get('type', '').startswith('image'):
                return media['url']
    elif "links" in entry:
        for link in entry.links:
            if link.get('type', '').startswith('image'):
                return link.href
    return None

def translate_if_needed(text: str) -> str:
    try:
        # Only translate if not English
        if any(ord(char) > 127 for char in text):
            translated = GoogleTranslator(source="auto", target="en").translate(text)
            return translated
        return text
    except Exception as e:
        print(f"⚠️ Translation failed: {e}")
        return text

def fetch_latest_post():
    for feed_url in RSS_FEEDS:
        print(f"🌐 Checking feed: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                print("❌ No entries found in feed.")
                continue

            # Process all new entries, not just the latest
            for entry in feed.entries:
                last_guid = get_last_guid(feed_url)
                
                if entry.id == last_guid:
                    print("🔁 Reached last processed GUID")
                    break  # Stop processing this feed
                    
                if is_relevant(entry):
                    save_last_guid(feed_url, entry.id)
                    
                    title = translate_if_needed(entry.title)
                    summary = translate_if_needed(entry.summary)
                    
                    return {
                        "title": title,
                        "link": entry.link,
                        "summary": summary,
                        "published": entry.get("published", ""),
                        "image": extract_image(entry),
                        "raw_content": entry.get("content", [{}])[0].get("value", "") if "content" in entry else ""
                    }
                else:
                    # Save GUID even if not relevant to prevent reprocessing
                    save_last_guid(feed_url, entry.id)
                    
        except Exception as e:
            print(f"⚠️ Error processing feed {feed_url}: {e}")
            
    print("ℹ️ No relevant news found in any feed")
    return None
