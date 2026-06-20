import os
import re
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

os.makedirs("downloads", exist_ok=True)

COOKIES_FILE = "cookies.txt" if os.path.exists("cookies.txt") else None

# Telegram bot upload limit (standard Bot API). If you run a local Bot API
# server you can raise this to ~2000.
MAX_FILESIZE_MB = 50

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Referer is checked by some CDNs against the originating site. Setting the
# wrong one (e.g. always Pinterest) breaks extraction on every other platform.
PLATFORM_REFERERS = {
    "pinterest": "https://www.pinterest.com/",
    "tiktok": "https://www.tiktok.com/",
    "instagram": "https://www.instagram.com/",
    "facebook": "https://www.facebook.com/",
    "twitter": "https://twitter.com/",
    "snapchat": "https://www.snapchat.com/",
    "youtube": "https://www.youtube.com/",
}


def _safe_title_template(platform: str) -> str:
    # Force a fixed extension so yt-dlp never has to *infer* one from the
    # URL/CDN response. This is what avoids the
    # "extracted extension is unusual and will be skipped for safety reasons"
    # error, which happens on Snapchat/TikTok/Rumble/etc. when the source
    # exposes an opaque token where an extension is normally expected.
    return f"downloads/{platform}_%(title).100B_%(id)s.%(ext)s"


def _build_opts(platform: str, fmt: str, force_ext: str | None):
    headers = {
        "User-Agent": DEFAULT_UA,
        "Referer": PLATFORM_REFERERS.get(platform, "https://www.google.com/"),
    }

    outtmpl = _safe_title_template(platform)
    if force_ext:
        # Strip the %(ext)s placeholder and hardcode the extension instead,
        # which sidesteps yt-dlp's extension-inference safety check entirely.
        outtmpl = outtmpl.replace(".%(ext)s", f".{force_ext}")

    opts = {
        "format": fmt,
        "outtmpl": outtmpl,
        "restrictfilenames": True,
        "http_headers": headers,
        "merge_output_format": "mp4",
        "max_filesize": MAX_FILESIZE_MB * 1024 * 1024,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 3,
    }
    if COOKIES_FILE:
        opts["cookiefile"] = COOKIES_FILE
    return opts


def download_video(url: str, platform: str = "general") -> dict:
    """
    Synchronous, blocking. Callers running an asyncio event loop (e.g. a
    Telegram bot handler) MUST run this in an executor/thread pool:

        result = await loop.run_in_executor(None, download_video, url, platform)

    Returns: {"success": True, "file": path} or {"success": False, "error": str}
    """

    # Attempt order: try video containers, then fall back to forcing a fixed
    # extension (this is what fixes the "unusual extension" class of error),
    # then images, then a last-resort generic merge.
    format_attempts = [
        ("best[ext=mp4]", None),
        ("best[ext=webm]", None),
        ("best", "mp4"),          # force extension: fixes opaque-ext CDNs
        ("bestvideo+bestaudio/best", "mp4"),
        ("best[ext=jpg]", None),
        ("best[ext=jpeg]", None),
        ("best[ext=png]", None),
        ("best[ext=webp]", None),
        ("best", "jpg"),          # image fallback with forced extension
        ("worst", "mp4"),
    ]

    last_error = "Unknown error"

    for fmt, force_ext in format_attempts:
        ydl_opts = _build_opts(platform, fmt, force_ext)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)

            if not os.path.exists(file_path):
                # prepare_filename can mismatch the actual written file in
                # edge cases (e.g. merger renamed it); try to recover.
                base, _ = os.path.splitext(file_path)
                for ext in ("mp4", "webm", "mkv", "jpg", "jpeg", "png", "webp"):
                    candidate = f"{base}.{ext}"
                    if os.path.exists(candidate):
                        file_path = candidate
                        break
                else:
                    last_error = "Download reported success but file was not found on disk."
                    continue

            return {"success": True, "file": file_path}

        except DownloadError as e:
            error_msg = str(e)
            last_error = error_msg
            recoverable_markers = (
                "Requested format is not available",
                "ffmpeg is not installed",
                "unusual and will be skipped for safety reasons",
                "No video formats found",
                "Unsupported URL",
            )
            if any(marker in error_msg for marker in recoverable_markers):
                continue
            # File-too-large is not recoverable by trying another format.
            if "max-filesize" in error_msg.lower() or "File is larger than max-filesize" in error_msg:
                return {"success": False, "error": "File exceeds the size limit and cannot be downloaded."}
            return {"success": False, "error": error_msg}

        except Exception as e:
            last_error = str(e)
            continue

    return {"success": False, "error": f"No compatible format found for this URL. Last error: {last_error}"}
