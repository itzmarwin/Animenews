import os
import re
import feedparser
import requests
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
from .config import RSS_FEEDS, LAST_GUID_DIR

# Anime-relevant keywords
RELEVANT_KEYWORDS = [
    "anime adaptation", "anime announced", "anime project", "tv anime", "new anime",
    "trailer", "teaser", "key visual", "promo video", "pv", "mv",
    "delayed", "delay", "anime film", "movie", "postponed", "on break", "hiatus",
    "release date", "airing", "premiere", "starts airing", "final season", "season 2", "season 3",
    "manga adaptation", "break next week", "no episode this week", "returns next week", 
    "announcement", "new series", "new project", "voice cast", "staff", "theme song", "episode",
    "visual revealed", "official poster", "official site", "first look"
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

    for word in EXCLUDE_KEYWORDS:
        if word in content:
            print(f"⛔ Skipped (excluded word): {word}")
            return False

    for keyword in RELEVANT_KEYWORDS:
        if keyword in content:
            print(f"✅ Relevant (matched keyword): {keyword}")
            return True

    print("⛔ Not relevant: No matching keywords")
    return False

def extract_image(entry) -> str:
    """Extract image from entry using multiple methods with priority"""
    # Method 1: Direct media tags
    if "media_thumbnail" in entry and entry.media_thumbnail:
        return entry.media_thumbnail[0]['url']
    
    if "media_content" in entry and entry.media_content:
        for media in entry.media_content:
            if media.get('type', '').startswith('image'):
                return media['url']
    
    # Method 2: Enclosure links
    if "links" in entry:
        for link in entry.links:
            if link.get('type', '').startswith('image'):
                return link.href
    
    # Method 3: Content parsing (for feeds like Anime Corner)
    if "content" in entry:
        for content in entry.content:
            soup = BeautifulSoup(content.value, 'html.parser')
            img = soup.find('img')
            if img and img.get('src'):
                return img['src']
    
    # Method 4: Summary parsing
    if "summary" in entry:
        soup = BeautifulSoup(entry.summary, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            return img['src']
    
    # Method 5: Open Graph scraping (fallback)
    if "link" in entry:
        try:
            print(f"🔍 Scraping OG image from: {entry.link}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
            }
            response = requests.get(entry.link, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    return og_image['content']
                
                # Fallback to first content image
                content_img = soup.find('img')
                if content_img and content_img.get('src'):
                    return content_img['src']
        except Exception as e:
            print(f"⚠️ OG image scraping failed: {e}")
    
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

            last_guid = get_last_guid(feed_url)
            new_entries_found = False

            for entry in feed.entries:
                if last_guid and entry.id == last_guid:
                    print("🔁 Reached last processed GUID")
                    break
                    
                new_entries_found = True
                print(f"🔍 Processing new entry: {entry.get('title', 'Untitled')[:50]}...")
                
                if is_relevant(entry):
                    save_last_guid(feed_url, entry.id)
                    
                    title = translate_if_needed(entry.title)
                    summary = translate_if_needed(entry.get('summary', ''))
                    
                    # Extract raw content for better processing
                    raw_content = ""
                    if "content" in entry:
                        for content in entry.content:
                            raw_content += content.value
                    
                    return {
                        "title": title,
                        "link": entry.get("link", ""),
                        "summary": summary,
                        "published": entry.get("published", ""),
                        "image": extract_image(entry),
                        "raw_content": raw_content
                    }
                else:
                    # Save GUID even if not relevant to prevent reprocessing
                    save_last_guid(feed_url, entry.id)
                    
            if not new_entries_found:
                print("🔁 No new entries in feed")
                    
        except Exception as e:
            print(f"⚠️ Error processing feed {feed_url}: {e}")
            
    print("ℹ️ No relevant news found in any feed")
    return None
