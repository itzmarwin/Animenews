import os

# Telegram configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
    print("Please set it using: export TELEGRAM_BOT_TOKEN='your_token_here'")
    exit(1)

CHANNEL_ID = '-1002332375459'  # Your channel ID

# Scraping configuration
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
HEADERS = {'User-Agent': USER_AGENT}

# Storage file for posted URLs
STORAGE_FILE = 'posted.json'
