import os
from yt_dlp import YoutubeDL

os.makedirs("downloads", exist_ok=True)

COOKIES_FILE = "cookies.txt" if os.path.exists("cookies.txt") else None


def download_video(url, platform="general"):
    format_attempts = [
        "best[ext=mp4]",
        "best[ext=webm]",
        "best[ext=jpg]",
        "best[ext=jpeg]",
        "best[ext=png]",
        "best[ext=webp]",
        "best[ext=mp4]/best[ext=webm]/best",
        "bestvideo+bestaudio/best",
        "worst",
    ]

    for fmt in format_attempts:
        ydl_opts = {
            "format": fmt,
            "outtmpl": f"downloads/{platform}_%(title)s.%(ext)s",
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.pinterest.com/",
            },
        }

        if COOKIES_FILE:
            ydl_opts["cookiefile"] = COOKIES_FILE

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            return {"success": True, "file": file_path}

        except Exception as e:
            error_msg = str(e)

            if "Requested format is not available" in error_msg or "ffmpeg is not installed" in error_msg:
                continue

            return {"success": False, "error": error_msg}

    return {"success": False, "error": "No compatible format found for this URL."}
