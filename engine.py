import os
from yt_dlp import YoutubeDL

os.makedirs("downloads", exist_ok=True)


def download_video(url, platform="general"):
    ydl_opts = {
        "format": "best[ext=mp4]/best[ext=webm]/best",  # single file, no merging needed
        "outtmpl": f"downloads/{platform}_%(title)s.%(ext)s",
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        return {"success": True, "file": file_path}

    except Exception as e:
        return {"success": False, "error": str(e)}
