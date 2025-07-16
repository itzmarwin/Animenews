import asyncio
import re
import html
import os
from telegram import Bot
from bot.config import BOT_TOKEN, CHANNEL_ID
from bot.fetcher import fetch_latest_post
from bot.anilist import get_anime_info
from bot.utils import download_trailer_youtube
from bs4 import BeautifulSoup  # For better HTML cleaning

bot = Bot(token=BOT_TOKEN)

def clean_summary(raw_html):
    """Remove all HTML tags except basic formatting and links."""
    # Use BeautifulSoup for better HTML parsing
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # Remove all links but keep their text
    for a in soup.find_all('a'):
        a.replace_with(a.get_text())
    
    # Remove any remaining HTML tags except formatting
    allowed_tags = ["b", "strong", "i", "u", "em"]
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()
    
    return str(soup)

def is_trailer_related(text: str) -> bool:
    """Detect trailer or teaser announcements with more keywords."""
    text = text.lower()
    keywords = ["trailer", "teaser", "key visual", "pv", "promo video", "opening", "ending", "mv"]
    return any(word in text for word in keywords)

async def post_news():
    """Fetch and post news (text, photo, or trailer)."""
    news = fetch_latest_post()
    if not news:
        print("No new news.")
        return

    # Combine title and content for better relevance checking
    combined = f"{news['title']} {news.get('raw_content', news['summary'])}".lower()

    # Prepare message content
    title = html.escape(news['title'])
    
    # Use raw content if available, otherwise summary
    content = news.get('raw_content', news['summary'])
    summary = clean_summary(content)
    
    # Remove any remaining URLs
    summary = re.sub(r'https?://\S+', '', summary)
    
    # Truncate to 300 characters
    if len(summary) > 300:
        summary = summary[:300] + "..."

    message = f"📰 <b>{title}</b>\n\n"
    message += f"{html.unescape(summary)}\n\n"
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
                if anime_info.get('release_date'):
                    caption += f"📅 Release: {anime_info['release_date']}\n"
                if anime_info.get('studio'):
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
                    
                    # Now post the news details separately
                    await bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=message,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    print(f"❌ Telegram send error: {e}")
                finally:
                    if os.path.exists(filename):
                        os.remove(filename)
                return

    # If not trailer or video failed, send news with image
    try:
        if news.get("image"):
            await bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=news["image"],
                caption=message,
                parse_mode="HTML",
                disable_notification=False
            )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True  # No link previews
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
        # Check every 10 minutes (600 seconds)
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(main_loop())
