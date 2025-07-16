import asyncio
from telegram import Bot
from bot.config import BOT_TOKEN, CHANNEL_ID
from bot.fetcher import fetch_latest_post

bot = Bot(token=BOT_TOKEN)


async def post_news():
    """Check RSS and post new news to Telegram channel."""
    news = fetch_latest_post()
    if news:
        message = f"📰 <b>{news['title']}</b>\n\n"
        message += f"{news['summary'][:300]}...\n\n"  # short summary
        message += f"<a href='{news['link']}'>🔗 Read More</a>\n"
        message += f"<i>Published: {news['published']}</i>"

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )
        print("✅ News posted!")
    else:
        print("No new news.")


async def main_loop():
    """Run the bot loop every 10 minutes."""
    while True:
        try:
            await post_news()
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(600)  # 600s = 10 min


if __name__ == "__main__":
    asyncio.run(main_loop())
  
