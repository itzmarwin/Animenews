import os
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from pytube import YouTube
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHANNEL_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# Load posted links
if os.path.exists("posted.json"):
    with open("posted.json", "r") as f:
        posted_links = json.load(f)
else:
    posted_links = []

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                filename = "image.jpg"
                with open(filename, "wb") as f:
                    f.write(await resp.read())
                return filename
    return None

async def download_youtube_video(url):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        filename = "video.mp4"
        stream.download(filename=filename)
        return filename
    except Exception as e:
        print("❌ Error downloading YouTube video:", e)
        return None

async def send_to_telegram(link, title, image_file=None, video_file=None):
    caption = f"<b>{title}</b>\n{link}"
    try:
        if image_file:
            with open(image_file, "rb") as photo:
                await bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=caption, parse_mode="HTML")
                print("🖼️ Posted image:", title)
        elif video_file:
            with open(video_file, "rb") as video:
                await bot.send_video(chat_id=CHAT_ID, video=video, caption=caption, parse_mode="HTML")
                print("📽️ Posted video:", title)
        else:
            await bot.send_message(chat_id=CHAT_ID, text=caption, parse_mode="HTML")
            print("📝 Posted text:", title)

        posted_links.append(link)
        with open("posted.json", "w") as f:
            json.dump(posted_links, f, indent=2)

    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")

async def parse_crunchyroll():
    url = "https://www.crunchyroll.com/news"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as resp:
            soup = BeautifulSoup(await resp.text(), "html.parser")
            articles = soup.select("li.news-item a.news-link")
            for a in articles[:3]:
                link = "https://www.crunchyroll.com" + a["href"]
                if link in posted_links:
                    continue
                title = a.select_one(".text-wrapper h3").text.strip()
                img_tag = a.select_one("img")
                image_url = img_tag["src"] if img_tag else None
                image_file = await download_image(image_url) if image_url else None

                async with session.get(link, headers=HEADERS) as article_resp:
                    article_soup = BeautifulSoup(await article_resp.text(), "html.parser")
                    iframe = article_soup.find("iframe")
                    video_file = None
                    if iframe and "youtube.com" in iframe.get("src", ""):
                        youtube_url = iframe["src"].split("?")[0]
                        video_file = await download_youtube_video(youtube_url)

                await send_to_telegram(link, title, image_file, video_file)

async def parse_myanimelist():
    url = "https://myanimelist.net/news"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as resp:
            soup = BeautifulSoup(await resp.text(), "html.parser")
            items = soup.select("div.news-unit.clearfix")
            for item in items[:3]:
                a = item.select_one("a")
                link = a["href"]
                if link in posted_links:
                    continue
                title = a.text.strip()
                img_tag = item.select_one("img")
                image_url = img_tag["src"] if img_tag else None
                image_file = await download_image(image_url) if image_url else None

                async with session.get(link, headers=HEADERS) as article_resp:
                    article_soup = BeautifulSoup(await article_resp.text(), "html.parser")
                    iframe = article_soup.find("iframe")
                    video_file = None
                    if iframe and "youtube.com" in iframe.get("src", ""):
                        youtube_url = iframe["src"].split("?")[0]
                        video_file = await download_youtube_video(youtube_url)

                await send_to_telegram(link, title, image_file, video_file)

async def check_news():
    await parse_crunchyroll()
    await parse_myanimelist()

async def main():
    print("✅ Bot started and running...")
    while True:
        print("🔍 Checking for news updates...")
        await check_news()
        await asyncio.sleep(300)  # 5 minutes

if __name__ == "__main__":
    asyncio.run(main())
