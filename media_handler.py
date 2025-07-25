# media_handler.py

import os
import requests
import yt_dlp
from urllib.parse import urlparse

MEDIA_FOLDER = "downloads"

# Folder banaye agar na ho
if not os.path.exists(MEDIA_FOLDER):
    os.makedirs(MEDIA_FOLDER)


def download_image(url):
    try:
        filename = os.path.join(MEDIA_FOLDER, os.path.basename(urlparse(url).path))
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(filename, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            return filename
        return None
    except Exception as e:
        print(f"❌ Image download error: {e}")
        return None


def download_youtube_video(url):
    try:
        filename = os.path.join(MEDIA_FOLDER, "video.mp4")
        ydl_opts = {
            "outtmpl": filename,
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "merge_output_format": "mp4",
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filename
    except Exception as e:
        print(f"❌ YouTube download error: {e}")
        return None
