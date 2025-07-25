import os

# Telegram configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Set in environment variables
CHANNEL_ID = '@your_channel_username'   # Replace with your channel username

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
