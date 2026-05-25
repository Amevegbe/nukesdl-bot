import os
from yt_dlp import YoutubeDL

os.makedirs("downloads", exist_ok=True)


def get_thumbnail(info, platform):
    """Helper to download thumbnail/image from a pin."""
    fallback_opts = {
        "outtmpl": f"downloads/{platform}_%(title)s.%(ext)s",
        "writethumbnail": True,
        "skip_download": True,
    }
    return fallback_opts


def find_image_file(base_path):
    """Find the actual saved image file by checking common extensions."""
    for ext in [".webp", ".jpg", ".jpeg", ".png"]:
        path = os.path.splitext(base_path)[0] + ext
        if os.path.exists(path):
            return path
    return None


def download_video(url, platform="general", media="video"):
    if media == "picture":
        ydl_opts = {
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

            if media == "picture":
                image_path = find_image_file(file_path)
                if image_path:
                    file_path = image_path

        return {"success": True, "file": file_path, "type": media}

    except Exception as e:
        error_msg = str(e)

        # User selected video but pin is actually an image — auto fallback
        if "No video formats found" in error_msg:
            try:
                fallback_opts = {
                    "outtmpl": f"downloads/{platform}_%(title)s.%(ext)s",
                    "writethumbnail": True,
                    "skip_download": True,
                }
                with YoutubeDL(fallback_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    file_path = ydl.prepare_filename(info)
                    image_path = find_image_file(file_path)
                    if image_path:
                        file_path = image_path

                return {"success": True, "file": file_path, "type": "picture"}

            except Exception as img_error:
                return {"success": False, "error": str(img_error)}

        return {"success": False, "error": error_msg}
