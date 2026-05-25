import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters, ConversationHandler
)
from engine import download_video

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

UNSUPPORTED = ["spotify.com", "apple.com/music", "deezer.com", "tidal.com"]

URL = 0

WELCOME = """
👋 Welcome to NukesDL Bot!

I can download videos from:
- YouTube
- TikTok
- Instagram
- Facebook
- Pinterest
- Snapchat
- Twitter/X
- And more!

Just send me a URL to get started 🔗
"""


async def send_error_to_admin(context: ContextTypes.DEFAULT_TYPE, error: str, url: str = None):
    if ADMIN_ID:
        message = f"⚠️ Bot Error\n\nURL: {url or 'N/A'}\n\nError:\n{error}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)
    return URL


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "." not in url or " " in url:
        await update.message.reply_text("That doesn't look like a valid URL. Please try again.")
        return URL

    if not url.startswith("http"):
        url = "https://" + url

    if any(platform in url for platform in UNSUPPORTED):
        await update.message.reply_text(
            "❌ This platform is not supported.\n\n"
            "Try YouTube, TikTok, Instagram, Facebook, Pinterest, Twitter/X instead."
        )
        return URL

    platform = detect_platform(url)
    await update.message.reply_text(f"Downloading from {platform}... ⏳")

    result = download_video(url, platform)

    if not result["success"]:
        await send_error_to_admin(context, result["error"], url)
        await update.message.reply_text(f"❌ Download failed\n\n{result['error']}")
        return URL

    file_path = result["file"]

    try:
        await update.message.reply_text("Uploading... 📤")
        with open(file_path, "rb") as f:
            await update.message.reply_video(video=f)
        await update.message.reply_text("Done ✅ Send another URL to download more.")

    except Exception as e:
        await send_error_to_admin(context, str(e), url)
        await update.message.reply_text(f"❌ Upload failed\n\n{str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return URL


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bye! Send /start to use me again. 👋")
    return ConversationHandler.END


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
        return "pinterest"
    elif "snapchat.com" in url:
        return "snapchat"
    elif "twitter.com" in url or "x.com" in url:
        return "twitter"
    return "general"


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
