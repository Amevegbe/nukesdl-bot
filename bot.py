import os
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters, ConversationHandler
)
from engine import download_video, MAX_FILESIZE_MB

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

if not TOKEN:
    raise SystemExit("BOT_TOKEN environment variable is not set.")

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


def _admin_id_int():
    if not ADMIN_ID:
        return None
    try:
        return int(ADMIN_ID)
    except ValueError:
        logger.warning("ADMIN_ID is set but not a valid integer: %r", ADMIN_ID)
        return None


async def send_error_to_admin(context: ContextTypes.DEFAULT_TYPE, error: str, url: str = None):
    admin_id = _admin_id_int()
    if admin_id is None:
        return
    try:
        message = f"⚠️ Bot Error\n\nURL: {url or 'N/A'}\n\nError:\n{error}"
        await context.bot.send_message(chat_id=admin_id, text=message[:4000])
    except Exception as e:
        logger.warning("Failed to notify admin: %s", e)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Error: %s", context.error)
    admin_id = _admin_id_int()
    if admin_id is None:
        return
    try:
        await context.bot.send_message(chat_id=admin_id, text=f"⚠️ Bot Error\n\n{context.error}"[:4000])
    except Exception:
        pass


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

    # Prevent one user from queuing multiple concurrent downloads, which
    # would otherwise spike disk/CPU usage unpredictably since downloads
    # run in a thread executor (see below) and are not otherwise rate-limited.
    if context.user_data.get("downloading"):
        await update.message.reply_text("⏳ You already have a download in progress. Please wait for it to finish.")
        return URL

    platform = detect_platform(url)
    await update.message.reply_text(f"Downloading from {platform}... ⏳")

    context.user_data["downloading"] = True
    try:
        # download_video() is a blocking, synchronous call (network I/O +
        # ffmpeg muxing). Running it directly here would block the entire
        # bot's event loop for every other user. Offload it to a thread.
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, download_video, url, platform)
    finally:
        context.user_data["downloading"] = False

    if not result["success"]:
        await send_error_to_admin(context, result["error"], url)
        await update.message.reply_text(f"❌ Download failed\n\n{result['error']}")
        return URL

    file_path = result["file"]

    try:
        # Check size before attempting upload — avoids wasting time/bandwidth
        # on an upload that Telegram will reject anyway.
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > MAX_FILESIZE_MB:
            await update.message.reply_text(
                f"❌ File too large to send ({size_mb:.1f}MB).\n\n"
                f"Telegram only allows files up to {MAX_FILESIZE_MB}MB.\n"
                "Try a shorter video or lower quality URL."
            )
            return URL

        await update.message.reply_text("Uploading... 📤")
        with open(file_path, "rb") as f:
            if file_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                await update.message.reply_photo(photo=f)
            else:
                await update.message.reply_video(video=f)
        await update.message.reply_text("Done ✅ Send another URL to download more.")
        await update.message.reply_text(
            "📢 Join our channel for updates and more!\n"
            "👉 https://t.me/NukesUpdates"
        )

    except Exception as e:
        error_msg = str(e)
        await send_error_to_admin(context, error_msg, url)

        if "Request Entity Too Large" in error_msg:
            await update.message.reply_text(
                "❌ File too large to send.\n\n"
                f"Telegram only allows files up to {MAX_FILESIZE_MB}MB.\n"
                "Try a shorter video or lower quality URL."
            )
        else:
            await update.message.reply_text(f"❌ Upload failed\n\n{error_msg}")

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
    app = ApplicationBuilder()\
        .token(TOKEN)\
        .read_timeout(60)\
        .write_timeout(60)\
        .connect_timeout(60)\
        .build()

    app.add_error_handler(error_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling(drop_pending_updates=True)
