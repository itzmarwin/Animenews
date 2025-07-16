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

# ✅ Keywords to detect valid anime-related news
KEYWORDS = [
    "anime film", "anime movie", "anime film", "film", "movie adaptation", "film debut", "film release", "film opens",
    "tv anime", "new anime", "anime announced", "anime adaptation", "anime confirmed", "anime series",
    "anime premiere", "new season", "season 2", "season 3", "final season", "anime finale",
    "cast revealed", "full cast", "staff revealed", "theme song", "visual revealed", "key visual",
    "official poster", "official site", "first look", "trailer", "teaser", "pv", "mv",
    "release date", "air date", "debuts", "starts airing", "begins airing", "premiere date",
    "delayed", "delay", "break", "hiatus", "no episode this week", "episode postponed",
    "special episode", "prologue film", "preview screening", "advance screening",
    "final arc", "arc begins", "arc finale", "last episode", "ends with", "concludes with",
    "english dub", "netflix to stream", "crunchyroll to stream", "streaming on",
    "new visual", "promo video", "key art", "new cast member"
]

def is_relevant_news(text: str) -> bool:
    """Check if news title + summary contains anime-related keywords."""
    text = text.lower()
    return any(keyword in text for keyword in KEYWORDS)

def clean_summary(raw_html):
    """Allow only specific tags in summary."""
    allowed_tags = ["b", "strong", "i", "u", "a"]
    cleaned = re.sub(r'</?(?!({})).*?>'.format("|".join(allowed_tags)), '', raw_html)
    return cleaned

def is_trailer_related(text: str) -> bool:
    """Detect trailer or teaser announcements."""
    text = text.lower()
    keywords = ["trailer", "teaser", "key visual", "pv"]
    return any(word in text for word in keywords)

async def post_news():
    """Fetch and post news (text, photo, or trailer)."""
    news = fetch_latest_post()
    if not news:
        print("No new news.")
        return

    combined = (news['title'] + " " + news['summary']).lower()
    if not is_relevant_news(combined):
        print("⛔ Skipped: Not anime-relevant")
        return

    # Prepare default message
    title = html.escape(news['title'])
    summary = clean_summary(news['summary'])
    message = f"📰 <b>{title}</b>\n\n"
    message += f"{html.unescape(summary[:300])}...\n\n"
    message += f"<i>Published: {news['published']}</i>"

    # Detect trailer-related posts
    if is_trailer_related(combined):
        print("🎬 Detected trailer-related news. Fetching from AniList...")
        anime_info = get_anime_info(news['title'])

        if anime_info and anime_info['trailer']:
            trailer_url = anime_info['trailer']
            filename = download_trailer_youtube(trailer_url)

            if filename:
                # Caption for trailer
                caption = f"🎬 <b>{anime_info['title']}</b>\n\n"
                caption += "Official Trailer Released!\n"
                if anime_info['release_date']:
                    caption += f"📅 Release: {anime_info['release_date']}\n"
                if anime_info['studio']:
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
                    os.remove(filename)
                return

    # If not trailer or video failed, fallback to photo or message
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
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main_loop())
