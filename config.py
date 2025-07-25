import os
import random

# Telegram configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
    print("Please set it using: export TELEGRAM_BOT_TOKEN='your_token_here'")
    exit(1)

CHANNEL_ID = '-1002332375459'  # Your channel ID

# Scraping configuration
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1'
    }

# Storage file for posted URLs
STORAGE_FILE = 'posted.json'

# Request timeout (in seconds)
REQUEST_TIMEOUT = 15

# Websites to scrape
SOURCES = [
    {
        'name': 'Anime Corner',
        'url': 'https://animecorner.me/category/news/anime-news/',
        'scraper': 'scrape_anime_corner'
    },
    {
        'name': 'Anime News Network',
        'url': 'https://www.animenewsnetwork.com/',
        'scraper': 'scrape_ann'
    }
]

# Time between checks (5 minutes)
CHECK_INTERVAL = 5
