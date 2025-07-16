import asyncio
import re
import html
import os
import logging
import tempfile
import requests
from telegram import Bot, InputMediaPhoto
from bot.config import BOT_TOKEN, CHANNEL_ID
from bot.fetcher import fetch_latest_post
from bot.anilist import get_anime_info
from bot.utils import download_trailer_youtube
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)

def clean_summary(raw_html):
    """Remove all HTML tags except basic formatting and links."""
    # Use BeautifulSoup for better HTML parsing
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # Remove all links but keep their text
    for a in soup.find_all('a'):
        a.replace_with(a.get_text())
    
    # Remove any remaining HTML tags except formatting
    allowed_tags = ["b", "strong", "i", "u", "em"]
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()
    
    return str(soup)

def clean_crunchyroll_content(raw_html):
    """Special cleaning for Crunchyroll content that preserves paragraphs"""
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # Remove unwanted elements
    for element in soup.find_all(['script', 'style', 'iframe']):
        element.decompose()
    
    # Convert headings to bold
    for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        h.name = 'strong'
    
    # Preserve paragraphs and line breaks
    for p in soup.find_all('p'):
        p.insert_after(soup.new_tag('br'))
        p.insert_after(soup.new_tag('br'))
    
    # Remove all links but keep their text
    for a in soup.find_all('a'):
        a.replace_with(a.get_text())
    
    # Remove any remaining HTML tags except formatting
    allowed_tags = ["b", "strong", "i", "u", "em", "br"]
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()
    
    return str(soup)

def is_trailer_related(text: str) -> bool:
    """Detect trailer or teaser announcements with more keywords."""
    text = text.lower()
    keywords = ["trailer", "teaser", "key visual", "pv", "promo video", "opening", "ending", "mv"]
    return any(word in text for word in keywords)

async def post_news():
    """Fetch and post news (text, photo, or trailer)."""
    news = fetch_latest_post()
    if not news:
        logger.info("No new news found.")
        return

    # Special handling for Crunchyroll news
    if "crunchyrollsvc.com" in news.get("link", "") or "crunchyroll.com" in news.get("link", ""):
        logger.info("🎬 Processing Crunchyroll news")
        # Prepare Crunchyroll-specific message
        title = html.escape(news['title'])
        content = news.get('raw_content', news['summary'])
        
        # Clean but preserve paragraphs
        summary = clean_crunchyroll_content(content)
        
        # Remove any remaining URLs
        summary = re.sub(r'https?://\S+', '', summary)
        
        # Don't truncate Crunchyroll content
        message = f"📰 <b>CRUNCHYROLL: {title}</b>\n\n"
        message += f"{html.unescape(summary)}\n\n"
        message += f"<i>Published: {news['published']}</i>"
        
        # Always try to include image
        await send_news_with_image(news, message)
        return
    
    # For other news sources
    # Combine title and content for relevance checking
    combined = f"{news['title']} {news.get('raw_content', news['summary'])}".lower()

    # Prepare message content
    title = html.escape(news['title'])
    
    # Use raw content if available, otherwise summary
    content = news.get('raw_content', news['summary'])
    summary = clean_summary(content)
    
    # Remove any remaining URLs
    summary = re.sub(r'https?://\S+', '', summary)
    
    # Truncate to 300 characters
    if len(summary) > 300:
        summary = summary[:300] + "..."

    message = f"📰 <b>{title}</b>\n\n"
    message += f"{html.unescape(summary)}\n\n"
    message += f"<i>Published: {news['published']}</i>"

    # Detect trailer-related posts
    if is_trailer_related(combined):
        logger.info("🎬 Detected trailer-related news. Fetching from AniList...")
        anime_info = get_anime_info(news['title'])

        if anime_info and anime_info.get('trailer'):
            trailer_url = anime_info['trailer']
            filename = download_trailer_youtube(trailer_url)

            if filename:
                # Caption for trailer
                caption = f"🎬 <b>{anime_info['title']}</b>\n\n"
                caption += "Official Trailer Released!\n"
                if anime_info.get('release_date'):
                    caption += f"📅 Release: {anime_info['release_date']}\n"
                if anime_info.get('studio'):
                    caption += f"🏢 Studio: {anime_info['studio']}\n"

                try:
                    # Send trailer video
                    await bot.send_video(
                        chat_id=CHANNEL_ID,
                        video=open(filename, "rb"),
                        caption=caption,
                        parse_mode="HTML",
                        supports_streaming=True
                    )
                    logger.info("✅ Trailer posted as video!")
                    
                    # Now post the news details with image
                    await send_news_with_image(news, message)
                except Exception as e:
                    logger.error(f"❌ Telegram send error: {e}")
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)
                return
        else:
            logger.info("ℹ️ No AniList trailer found, posting as regular news")
    
    # For regular news posts
    await send_news_with_image(news, message)

async def download_image(image_url: str):
    """Download image from URL and return temporary file path"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()
        
        # Create temporary file
        file_ext = os.path.splitext(image_url)[1][:4] or '.jpg'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
            return f.name
    except Exception as e:
        logger.error(f"❌ Image download failed: {e}")
        return None

async def send_news_with_image(news, message):
    """Send news with image if available, otherwise send as text."""
    try:
        image_url = news.get("image")
        
        # Special handling for Crunchyroll image URLs
        if image_url and ("crunchyrollsvc.com" in image_url or "crunchyroll.com" in image_url):
            # Crunchyroll images need parameter modification for better quality
            if 'width=' in image_url:
                image_url = re.sub(r'width=\d+', 'width=800', image_url)
            if 'height=' in image_url:
                image_url = re.sub(r'height=\d+', 'height=600', image_url)
        
        if image_url:
            logger.info(f"🖼️ Found image: {image_url}")
            
            # First try: Send using URL
            try:
                await bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image_url,
                    caption=message,
                    parse_mode="HTML",
                    disable_notification=False
                )
                logger.info("✅ News posted with image (URL).")
                return
            except Exception as e:
                logger.warning(f"⚠️ Photo send by URL failed: {e}. Trying download method...")
                
            # Second try: Download and send as file
            try:
                image_path = await download_image(image_url)
                if image_path:
                    with open(image_path, 'rb') as photo_file:
                        await bot.send_photo(
                            chat_id=CHANNEL_ID,
                            photo=photo_file,
                            caption=message,
                            parse_mode="HTML"
                        )
                    logger.info("✅ News posted with image (downloaded).")
                    os.remove(image_path)
                    return
            except Exception as e:
                logger.error(f"⚠️ Downloaded image send failed: {e}")
        
        # If all image methods fail or no image, send as text
        logger.info("ℹ️ No image available, sending as text")
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        logger.info("✅ News posted as text.")
        
    except Exception as e:
        logger.error(f"❌ Telegram send error: {e}")

async def main_loop():
    """Run the bot loop every 10 minutes."""
    while True:
        try:
            logger.info("🔍 Checking for new news...")
            await post_news()
        except Exception as e:
            logger.error(f"⚠️ Error in main loop: {e}")
        # Check every 10 minutes (600 seconds)
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main_loop())
