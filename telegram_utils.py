import os
import requests
import tempfile
import youtube_dl
import logging
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from telegram.error import TelegramError
from config import TOKEN, CHANNEL_ID, HEADERS

logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)

def download_file(url, extension=''):
    """Download any file and return its path"""
    try:
        response = requests.get(url, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        # Create temporary file
        suffix = extension or url.split('.')[-1].split('?')[0]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{suffix}') as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp_file.write(chunk)
            return tmp_file.name
            
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return None

def download_youtube_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(tempfile.gettempdir(), '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        logger.error(f"YouTube download error: {str(e)}")
        return None

def send_to_telegram(article):
    try:
        # Prepare caption
        caption = f"<b>{article['title']}</b>\n\n"
        content = article['content']
        if content:
            # Truncate content to fit in Telegram caption
            max_length = 1000 - len(caption) - 100  # Leave space for footer
            if len(content) > max_length:
                content = content[:max_length] + '...'
            caption += content
        caption += f"\n\nSource: {article['source']}\n{article['url']}"
        
        # Handle YouTube videos first
        if article.get('youtube'):
            for yt_url in article['youtube']:
                try:
                    video_path = download_youtube_video(yt_url)
                    if video_path and os.path.exists(video_path):
                        with open(video_path, 'rb') as video_file:
                            bot.send_video(
                                chat_id=CHANNEL_ID,
                                video=video_file,
                                caption=caption,
                                parse_mode='HTML'
                            )
                        os.unlink(video_path)
                        return True
                except Exception as e:
                    logger.error(f"YouTube video error: {str(e)}")
        
        # Handle regular videos
        if article.get('videos'):
            for video_url in article['videos']:
                try:
                    video_path = download_file(video_url, 'mp4')
                    if video_path:
                        with open(video_path, 'rb') as video_file:
                            bot.send_video(
                                chat_id=CHANNEL_ID,
                                video=video_file,
                                caption=caption,
                                parse_mode='HTML',
                                supports_streaming=True
                            )
                        os.unlink(video_path)
                        return True
                except Exception as e:
                    logger.error(f"Video processing error: {str(e)}")
        
        # Handle images
        if article.get('images'):
            images = article['images']
            # For single image
            if len(images) == 1:
                try:
                    bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=images[0],
                        caption=caption,
                        parse_mode='HTML'
                    )
                    return True
                except Exception as e:
                    logger.error(f"Error sending photo: {str(e)}")
            
            # For multiple images
            try:
                media_group = []
                for i, img_url in enumerate(images[:10]):  # Telegram limit
                    if i == 0:
                        media_group.append(InputMediaPhoto(
                            media=img_url,
                            caption=caption,
                            parse_mode='HTML'
                        ))
                    else:
                        media_group.append(InputMediaPhoto(
                            media=img_url
                        ))
                bot.send_media_group(
                    chat_id=CHANNEL_ID,
                    media=media_group
                )
                return True
            except Exception as e:
                logger.error(f"Media group error: {str(e)}")
                # Fallback to single image
                if images:
                    try:
                        bot.send_photo(
                            chat_id=CHANNEL_ID,
                            photo=images[0],
                            caption=caption,
                            parse_mode='HTML'
                        )
                        return True
                    except Exception as e:
                        logger.error(f"Fallback photo error: {str(e)}")
        
        # Text-only fallback
        try:
            bot.send_message(
                chat_id=CHANNEL_ID,
                text=caption,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error(f"Text message error: {str(e)}")
            
        return False
        
    except TelegramError as e:
        logger.error(f"Telegram API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error sending to Telegram: {str(e)}")
    return False
