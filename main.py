import os
import time
import logging
import schedule
from scrapers import scrape_crunchyroll, scrape_myanimelist
from telegram_utils import send_to_telegram
from config import POSTED_URLS_FILE, SOURCES, POST_INTERVAL

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_posted_urls():
    if not os.path.exists(POSTED_URLS_FILE):
        return set()
    try:
        with open(POSTED_URLS_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except Exception as e:
        logger.error(f"Error loading posted URLs: {str(e)}")
        return set()

def save_url(url):
    try:
        with open(POSTED_URLS_FILE, 'a') as f:
            f.write(url + '\n')
    except Exception as e:
        logger.error(f"Error saving URL: {str(e)}")

def scrape_and_post():
    posted_urls = load_posted_urls()
    logger.info(f"Loaded {len(posted_urls)} posted URLs")
    
    # Scrape all sources
    all_articles = []
    for source in SOURCES:
        try:
            scraper = globals().get(source['scraper'])
            if scraper:
                articles = scraper()
                logger.info(f"Found {len(articles)} articles from {source['name']}")
                all_articles.extend(articles)
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {str(e)}")
    
    # Process and send new articles
    new_count = 0
    for article in all_articles:
        if article['url'] not in posted_urls:
            logger.info(f"Processing new article: {article['title']}")
            if send_to_telegram(article):
                save_url(article['url'])
                new_count += 1
                # Avoid rate limits
                time.sleep(POST_INTERVAL)
    
    logger.info(f"Posted {new_count} new articles")

def main():
    logger.info("Starting Anime News Bot")
    # Run immediately on start
    scrape_and_post()
    
    # Schedule to run every 30 minutes
    schedule.every(30).minutes.do(scrape_and_post)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
