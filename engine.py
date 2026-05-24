import os
from yt_dlp import YoutubeDL

os.makedirs("downloads", exist_ok=True)

def download_video(url, platform="general"):
    ydl_opts = {
        "format": "best",
        "outtmpl": f"downloads/{platform}_%(title)s.%(ext)s"
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        return {"success": True, "file": file_path}  # ← this is the fix
    except Exception as e:
        return {"success": False, "error": str(e)}   # ← and this
