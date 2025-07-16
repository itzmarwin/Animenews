import asyncio
import re
import html
import os
from telegram import Bot
from bot.config import BOT_TOKEN, CHANNEL_ID
from bot.fetcher import fetch_latest_post
from bot.anilist import get_anime_info
from bot.utils import download_trailer_youtube

bot = Bot(token=BOT_TOKEN)

def clean_summary(raw_html):
    allowed_tags = ["b", "strong", "i", "u", "a"]
    cleaned = re.sub(r'</?(?!({})).*?>'.format("|".join(allowed_tags)), '', raw_html)
    return cleaned

def is_trailer_related(text: str) -> bool:
    """Check if the title or summary suggests it's a trailer or teaser."""
    text = text.lower()
    keywords = ["trailer", "teaser", "key visual", "pv"]
    return any(word in text for word in keywords)

async def post_news():
    """Fetch and post news (text, photo, or trailer)."""
    news = fetch_latest_post()
    if not news:
        print("No new news.")
        return

    # Default message
    title = html.escape(news['title'])
    summary = clean_summary(news['summary'])
    message = f"📰 <b>{title}</b>\n\n"
    message += f"{html.unescape(summary[:300])}...\n\n"
    message += f"<i>Published: {news['published']}</i>"

    # Detect if it’s trailer-related
    if is_trailer_related(news['title'] + " " + news['summary']):
        print("🎬 Detected trailer-related news. Fetching from AniList...")
        anime_info = get_anime_info(news['title'])

        if anime_info and anime_info['trailer']:
            trailer_url = anime_info['trailer']
            filename = download_trailer_youtube(trailer_url)

            if filename:
                # Build caption
                caption = f"🎬 <b>{anime_info['title']}</b>\n\n"
                caption += "Official Trailer Released!\n"
                caption += f"📅 Release: {anime_info['release_date']}\n"
                caption += f"🏢 Studio: {anime_info['studio']}\n"

                try:
                    await bot.send_video(
                        chat_id=CHANNEL_ID,
                        video=open(filename, "rb"),
                        caption=caption,
                        parse_mode="HTML",
                        supports_streaming=True
                    )
                    print("✅ Trailer posted as video!")
                except Exception as e:
                    print(f"❌ Telegram send video error: {e}")
                finally:
                    # Clean up
                    os.remove(filename)
                return

    # If not trailer or video failed, fallback to image/text
    try:
        if news.get("image"):
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=news["image"],
                caption=message,
                parse_mode="HTML"
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )
        print("✅ News posted.")
    except Exception as e:
        print(f"❌ Telegram send error: {e}")

async def main_loop():
    """Run the bot loop every 10 minutes."""
    while True:
        try:
            await post_news()
        except Exception as e:
            print(f"⚠️ Error in loop: {e}")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main_loop())
