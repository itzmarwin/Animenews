# bot.py

from telegram import Bot
import time, json, os, schedule
from config import BOT_TOKEN, CHAT_ID
from news_scraper import fetch_mal_news, fetch_crunchyroll_news
from media_handler import download_image, download_youtube_video

bot = Bot(token=BOT_TOKEN)
STORAGE_FILE = "posted.json"

# Load posted links
if os.path.exists(STORAGE_FILE):
    with open(STORAGE_FILE, "r") as f:
        posted_links = set(json.load(f))
else:
    posted_links = set()


def save_posted_links():
    with open(STORAGE_FILE, "w") as f:
        json.dump(list(posted_links), f)


def send_media_news(news_item):
    title = news_item["title"]
    link = news_item["link"]
    image_url = news_item["image"]
    video_url = news_item["video"]
    source = news_item["source"]

    caption = f"<b>{source}</b>\n<b>{title}</b>"

    # 🟨 Prefer YouTube video > Image > Text
    if video_url:
        video_file = download_youtube_video(video_url)
        if video_file:
            bot.send_video(chat_id=CHAT_ID, video=open(video_file, "rb"), caption=caption, parse_mode="HTML")
            print(f"🎞️ Posted video: {title}")
            return True

    elif image_url:
        image_file = download_image(image_url)
        if image_file:
            bot.send_photo(chat_id=CHAT_ID, photo=open(image_file, "rb"), caption=caption + f"\n{link}", parse_mode="HTML")
            print(f"🖼️ Posted image: {title}")
            return True

    else:
        # Fallback to text only
        text = f"{caption}\n{link}"
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")
        print(f"📝 Posted text: {title}")
        return True

    return False


def check_and_post():
    print("🔍 Checking for news updates...")
    all_news = fetch_mal_news() + fetch_crunchyroll_news()

    for news in all_news:
        if news["link"] not in posted_links:
            success = send_media_news(news)
            if success:
                posted_links.add(news["link"])
                save_posted_links()


# ⏰ Schedule every 5 minutes
schedule.every(5).minutes.do(check_and_post)

print("✅ Bot started and running...")

while True:
    schedule.run_pending()
    time.sleep(1)
