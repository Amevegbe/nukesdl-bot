import os
from yt_dlp import YoutubeDL

os.makedirs("downloads", exist_ok=True)


def download_video(url, platform="general"):
    # Try these format strategies one by one until one works
    format_attempts = [
        "best[ext=mp4]",
        "best[ext=webm]",
        "best[ext=mp4]/best[ext=webm]/best",
        "bestvideo+bestaudio/best",
        "worst",  # last resort — any format available
    ]

    for fmt in format_attempts:
        ydl_opts = {
            "format": fmt,
            "outtmpl": f"downloads/{platform}_%(title)s.%(ext)s",
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            return {"success": True, "file": file_path}

        except Exception as e:
            error_msg = str(e)

            # If format not available, try next one
            if "Requested format is not available" in error_msg or "ffmpeg is not installed" in error_msg:
                continue

            # Any other error, stop and return immediately
            return {"success": False, "error": error_msg}

    return {"success": False, "error": "No compatible format found for this URL."}
