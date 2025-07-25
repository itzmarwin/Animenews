import time
import json
import os
import schedule
import logging
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from config import TOKEN, CHANNEL_ID, STORAGE_FILE, SOURCES, CHECK_INTERVAL
from scrapers import scrape_anime_corner, scrape_ann
from media_handler import download_image, download_youtube_video

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)

# Load posted links
if os.path.exists(STORAGE_FILE):
    try:
        with open(STORAGE_FILE, "r") as f:
            posted_links = set(json.load(f))
        logger.info(f"Loaded {len(posted_links)} posted URLs")
    except:
        posted_links = set()
        logger.warning("Failed to load posted URLs, starting fresh")
else:
    posted_links = set()
    logger.info("No storage file found, starting fresh")

def save_posted_links():
    try:
        with open(STORAGE_FILE, "w") as f:
            json.dump(list(posted_links), f)
        logger.info("Saved posted URLs")
    except Exception as e:
        logger.error(f"Error saving posted URLs: {str(e)}")

def send_news_item(item):
    try:
        # Prepare caption
        caption = f"<b>{item['source']}</b>\n<b>{item['title']}</b>"
        if item.get('content'):
            # Truncate content to fit in Telegram caption
            max_length = 1000 - len(caption) - 100
            content = item['content']
            if len(content) > max_length:
                content = content[:max_length] + '...'
            caption += f"\n\n{content}"
        caption += f"\n\n<a href='{item['url']}'>Read more</a>"
        
        # Handle YouTube videos first
        if item.get('youtube'):
            for yt_url in item['youtube']:
                try:
                    video_path = download_youtube_video(yt_url)
                    if video_path and os.path.exists(video_path):
                        with open(video_path, 'rb') as video_file:
                            bot.send_video(
                                chat_id=CHANNEL_ID,
                                video=video_file,
                                caption=caption,
                                parse_mode="HTML"
                            )
                        os.unlink(video_path)
                        return True
                except Exception as e:
                    logger.error(f"YouTube video error: {str(e)}")
        
        # Handle images
        if item.get('images'):
            images = [img for img in item['images'] if img]  # Filter out None
            
            # For single image
            if len(images) == 1:
                try:
                    image_path = download_image(images[0])
                    if image_path:
                        with open(image_path, 'rb') as img_file:
                            bot.send_photo(
                                chat_id=CHANNEL_ID,
                                photo=img_file,
                                caption=caption,
                                parse_mode="HTML"
                            )
                        os.unlink(image_path)
                        return True
                except Exception as e:
                    logger.error(f"Image sending error: {str(e)}")
            
            # For multiple images
            elif len(images) > 1:
                try:
                    media_group = []
                    for i, img_url in enumerate(images[:10]):  # Telegram limit
                        if i == 0:
                            media_group.append(InputMediaPhoto(
                                media=img_url,
                                caption=caption,
                                parse_mode="HTML"
                            ))
                        else:
                            media_group.append(InputMediaPhoto(
                                media=img_url
                            ))
                    bot.send_media_group(
                        chat_id=CHANNEL_ID,
                        media=media_group
                    )
                    return True
                except Exception as e:
                    logger.error(f"Media group error: {str(e)}")
                    # Fallback to single image
                    if images:
                        try:
                            image_path = download_image(images[0])
                            if image_path:
                                with open(image_path, 'rb') as img_file:
                                    bot.send_photo(
                                        chat_id=CHANNEL_ID,
                                        photo=img_file,
                                        caption=caption,
                                        parse_mode="HTML"
                                    )
                                os.unlink(image_path)
                                return True
                        except Exception as e:
                            logger.error(f"Fallback photo error: {str(e)}")
        
        # Text-only fallback
        bot.send_message(
            chat_id=CHANNEL_ID,
            text=caption,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return True
        
    except Exception as e:
        logger.error(f"Error sending news item: {str(e)}")
        return False

def check_and_post():
    logger.info("Checking for new articles...")
    all_news = []
    
    # Scrape all sources
    for source in SOURCES:
        try:
            scraper = globals().get(source['scraper'])
            if scraper:
                articles = scraper()
                logger.info(f"Found {len(articles)} articles from {source['name']}")
                all_news.extend(articles)
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {str(e)}")
    
    # Process and send new articles
    new_count = 0
    for article in all_news:
        if article['url'] not in posted_links:
            logger.info(f"Processing new article: {article['title']}")
            if send_news_item(article):
                posted_links.add(article['url'])
                new_count += 1
                # Avoid rate limits
                time.sleep(5)
    
    if new_count > 0:
        save_posted_links()
    logger.info(f"Posted {new_count} new articles")

def safe_check_and_post():
    try:
        check_and_post()
    except Exception as e:
        logger.error(f"Error in scheduled job: {str(e)}")

def main():
    logger.info("Starting Anime News Bot")
    # Run immediately on start
    safe_check_and_post()
    
    # Schedule to run every 5 minutes
    schedule.every(CHECK_INTERVAL).minutes.do(safe_check_and_post)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
