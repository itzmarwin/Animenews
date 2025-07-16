import os
import re
import feedparser
import requests
import time
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
from .config import RSS_FEEDS, LAST_GUID_DIR

# Anime-relevant keywords
RELEVANT_KEYWORDS = [
    "anime adaptation", "anime", "voice", "anime announced", "anime project", "tv anime", "new anime",
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
    """Generate safe filename for GUID storage"""
    filename = re.sub(r'[^a-zA-Z0-9]', '_', feed_url) + ".txt"
    return os.path.join(LAST_GUID_DIR, filename)

def get_last_guid(feed_url: str) -> str:
    path = guid_path(feed_url)
    if not os.path.exists(path):
        return ""
    with open(path, "r") as f:
        return f.read().strip()

def save_last_guid(feed_url: str, guid: str):
    os.makedirs(LAST_GUID_DIR, exist_ok=True)
    with open(guid_path(feed_url), "w") as f:
        f.write(guid)

def is_relevant(entry) -> bool:
    # ALWAYS include Crunchyroll news
    if "crunchyrollsvc.com" in entry.get("link", "") or "crunchyroll.com" in entry.get("link", ""):
        print("✅ Crunchyroll news - always relevant")
        return True
    
    # For other sources, apply keyword filtering
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

def extract_crunchyroll_image(entry) -> str:
    """Special image extraction for Crunchyroll API format"""
    try:
        # Method 1: Try media_content first
        if "media_content" in entry and entry.media_content:
            for media in entry.media_content:
                if media.get('type', '').startswith('image'):
                    return media['url']
        
        # Method 2: Check for images collection
        if "images" in entry and entry.images:
            # Find the highest quality image
            best_image = None
            max_width = 0
            
            for image in entry.images:
                try:
                    # Extract width from URL parameters
                    width_match = re.search(r'width=(\d+)', image.href)
                    if width_match:
                        width = int(width_match.group(1))
                        if width > max_width:
                            max_width = width
                            best_image = image.href
                except:
                    pass
            
            if best_image:
                return best_image
            return entry.images[0].href
    
    except Exception as e:
        print(f"⚠️ Crunchyroll image extraction failed: {e}")
    return None

def extract_image(entry) -> str:
    """Extract image from entry using multiple methods with priority"""
    # Special handling for Crunchyroll API
    if "crunchyrollsvc.com" in entry.get("link", ""):
        return extract_crunchyroll_image(entry)
    
    # Method 1: Direct media tags
    if "media_thumbnail" in entry and entry.media_thumbnail:
        print("ℹ️ Found image via media_thumbnail")
        return entry.media_thumbnail[0]['url']
    
    if "media_content" in entry and entry.media_content:
        for media in entry.media_content:
            if media.get('type', '').startswith('image'):
                print("ℹ️ Found image via media_content")
                return media['url']
    
    # Method 2: Enclosure links
    if "links" in entry:
        for link in entry.links:
            if link.get('type', '').startswith('image'):
                print("ℹ️ Found image via links")
                return link.href
    
    # Method 3: WordPress featured images
    if "wp_featured_image" in entry:
        print("ℹ️ Found WordPress featured image")
        return entry.wp_featured_image
    
    # Method 4: Content parsing
    if "content" in entry:
        for content in entry.content:
            soup = BeautifulSoup(content.value, 'html.parser')
            img = soup.find('img')
            if img and img.get('src'):
                src = img['src']
                # Fix relative URLs
                if src.startswith('//'):
                    src = f"https:{src}"
                elif src.startswith('/'):
                    base_url = '/'.join(entry.link.split('/')[:3])
                    src = f"{base_url}{src}"
                print("ℹ️ Found image via content parsing")
                return src
    
    # Method 5: Summary parsing
    if "summary" in entry:
        soup = BeautifulSoup(entry.summary, 'html.parser')
        img = soup.find('img')
        if img and img.get('src'):
            src = img['src']
            # Fix relative URLs
            if src.startswith('//'):
                return f"https:{src}"
            elif src.startswith('/'):
                base_url = '/'.join(entry.link.split('/')[:3])
                return f"{base_url}{src}"
            print("ℹ️ Found image via summary parsing")
            return src
    
    # Method 6: Open Graph scraping
    if "link" in entry:
        try:
            print(f"🔍 Scraping OG image from: {entry.link}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
            }
            response = requests.get(entry.link, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try Open Graph image
                og_image = soup.find('meta', property='og:image')
                if og_image and og_image.get('content'):
                    src = og_image['content']
                    print("ℹ️ Found image via OG tag")
                    return src
                
                # Try Twitter image
                twitter_image = soup.find('meta', property='twitter:image')
                if twitter_image and twitter_image.get('content'):
                    src = twitter_image['content']
                    print("ℹ️ Found image via Twitter card")
                    return src
                
                # Fallback to first large content image
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    if src:
                        # Fix relative URLs
                        if src.startswith('//'):
                            src = f"https:{src}"
                        elif src.startswith('/'):
                            base_url = '/'.join(entry.link.split('/')[:3])
                            src = f"{base_url}{src}"
                        
                        # Check for large images
                        if any(x in src for x in ['wp-content', 'uploads', 'media']):
                            print("ℹ️ Found image via content image")
                            return src
        except Exception as e:
            print(f"⚠️ OG image scraping failed: {e}")
    
    print("ℹ️ No image found for entry")
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
    """Fetch the latest relevant post from any feed"""
    for feed_url in RSS_FEEDS:
        print(f"🌐 Checking feed: {feed_url}")
        try:
            # Add cache busting to prevent 304 responses
            if "crunchyrollsvc.com" in feed_url:
                # Crunchyroll API needs special handling
                modified_url = f"{feed_url}?t={int(time.time())}"
            else:
                modified_url = f"{feed_url}?t={int(time.time())}"
                
            feed = feedparser.parse(modified_url)
            
            if not feed.entries:
                print("❌ No entries found in feed.")
                continue

            last_guid = get_last_guid(feed_url)
            print(f"ℹ️ Last GUID: {last_guid[:20]}...")

            # Process entries from oldest to newest to avoid missing updates
            for entry in reversed(feed.entries):
                entry_guid = entry.get('id', entry.get('link', ''))
                
                if not entry_guid:
                    print("⚠️ Entry has no GUID, skipping")
                    continue
                    
                if entry_guid == last_guid:
                    print("🔁 Already processed this GUID")
                    continue
                    
                print(f"🔍 Processing new entry: {entry.get('title', 'Untitled')[:50]}...")
                
                if is_relevant(entry):
                    print("✅ Found relevant entry")
                    save_last_guid(feed_url, entry_guid)
                    
                    title = translate_if_needed(entry.title)
                    summary = translate_if_needed(entry.get('summary', ''))
                    
                    # Extract raw content
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
                    print("⛔ Not relevant, skipping")
                    save_last_guid(feed_url, entry_guid)
                    
            print("ℹ️ No new relevant entries in this feed")
                    
        except Exception as e:
            print(f"⚠️ Error processing feed {feed_url}: {e}")
            
    print("ℹ️ No relevant news found in any feed")
    return None
