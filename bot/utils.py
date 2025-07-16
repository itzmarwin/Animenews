import os
from yt_dlp import YoutubeDL

def download_trailer_youtube(url, filename="trailer.mp4"):
    """Download trailer video from YouTube."""
    ydl_opts = {
        'outtmpl': filename,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'merge_output_format': 'mp4',
        'quiet': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return filename if os.path.exists(filename) else None
    except Exception as e:
        print(f"❌ Failed to download video: {e}")
        return None
      
