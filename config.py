import os
import sys

# Telegram configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
    print("Please set it using: export TELEGRAM_BOT_TOKEN='your_token_here'")
    sys.exit(1)

CHANNEL_ID = '-1002332375459'  # Your channel ID

# Scraping configuration
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
HEADERS = {'User-Agent': USER_AGENT}
POSTED_URLS_FILE = 'posted_urls.txt'

# Time between article posts (in seconds)
POST_INTERVAL = 20

# Websites to scrape
SOURCES = [
    {
        'name': 'Crunchyroll',
        'url': 'https://www.crunchyroll.com/news',
        'scraper': 'scrape_crunchyroll'
    },
    {
        'name': 'MyAnimeList',
        'url': 'https://myanimelist.net/news',
        'scraper': 'scrape_myanimelist'
    }
]
