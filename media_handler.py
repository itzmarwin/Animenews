import requests
import tempfile
import youtube_dl
import os
import logging
from config import HEADERS

logger = logging.getLogger(__name__)

def download_image(url):
    try:
        response = requests.get(url, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        # Create temporary file
        suffix = url.split('.')[-1].split('?')[0]
        if suffix.lower() not in ['jpg', 'jpeg', 'png', 'gif']:
            suffix = 'jpg'
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{suffix}') as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp_file.write(chunk)
            return tmp_file.name
            
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
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
