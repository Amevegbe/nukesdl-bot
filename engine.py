import os
from yt_dlp import YoutubeDL

os.makedirs("downloads", exist_ok=True)

def download_video(url, platform="general", media="video"):
    if media == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"downloads/{platform}_%(title)s.%(ext)s",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
        }
    elif media == "picture":
        ydl_opts = {
            "format": "best",
            "outtmpl": f"downloads/{platform}_%(title)s.%(ext)s",
            "writethumbnail": True,
            "skip_download": True,
        }
    else:
        ydl_opts = {
            "format": "best/bestvideo+bestaudio/bestvideo/bestaudio",
            "outtmpl": f"downloads/{platform}_%(title)s.%(ext)s",
            "merge_output_format": "mp4",
        }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if media == "audio":
                file_path = os.path.splitext(file_path)[0] + ".mp3"
        return {"success": True, "file": file_path}
    except Exception as e:
        return {"success": False, "error": str(e)}
