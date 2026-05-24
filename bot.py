import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from engine import download_video

TOKEN = os.environ.get("BOT_TOKEN")

URL_PATTERN = re.compile(r'https?://[^\s]+')

WELCOME = """
Welcome! Send me a video URL and I'll download it.

Supported platforms:
- YouTube
- TikTok
- Instagram
- Facebook
- Pinterest
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not URL_PATTERN.match(url):
        await update.message.reply_text("Please send a valid URL.")
        return

    await update.message.reply_text("Downloading... ⏳")

    platform = detect_platform(url)
    result = download_video(url, platform)

    if not result["success"]:
        await update.message.reply_text(f"Failed ❌\n{result['error']}")
        return

    file_path = result["file"]

    try:
        await update.message.reply_text("Uploading... 📤")
        with open(file_path, "rb") as video_file:
            await update.message.reply_video(video=video_file)
        await update.message.reply_text("Done ✅")

    except Exception as e:
        await update.message.reply_text(f"Upload failed ❌\n{str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def detect_platform(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "tiktok.com" in url:
        return "tiktok"
    elif "instagram.com" in url:
        return "instagram"
    elif "facebook.com" in url or "fb.watch" in url:
        return "facebook"
    elif "pinterest.com" in url or "pin.it" in url:
        return "pinterest_video"
    return "general"


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()