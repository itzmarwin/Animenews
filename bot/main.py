import asyncio
import re
import html
from telegram import Bot
from bot.config import BOT_TOKEN, CHANNEL_ID
from bot.fetcher import fetch_latest_post

bot = Bot(token=BOT_TOKEN)

def clean_summary(raw_html):
    allowed_tags = ["b", "strong", "i", "u", "a"]
    cleaned = re.sub(r'</?(?!({})).*?>'.format("|".join(allowed_tags)), '', raw_html)
    return cleaned

async def post_news():
    """Fetch and post anime news if it's relevant."""
    news = fetch_latest_post()
    if news:
        summary = clean_summary(news['summary'])
        message = f"📰 <b>{html.escape(news['title'])}</b>\n\n"
        message += f"{html.unescape(summary[:300])}...\n\n"
        message += f"<a href='{news['link']}'>🔗 Read More</a>\n"
        message += f"<i>Published: {news['published']}</i>"

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
            print("✅ News posted!")
        except Exception as e:
            print(f"❌ Telegram send error: {e}")
    else:
        print("No new news.")

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
