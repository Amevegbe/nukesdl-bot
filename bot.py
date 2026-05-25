import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters, ConversationHandler
)
from engine import download_video

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

UNSUPPORTED = ["spotify.com", "apple.com/music", "deezer.com", "tidal.com"]

MEDIA_TYPE, URL = range(2)

MEDIA_KEYBOARD = ReplyKeyboardMarkup(
    [["🎬 Video", "🖼️ Picture"]],
    one_time_keyboard=True,
    resize_keyboard=True
)

WELCOME = """
👋 Welcome to NukesDL Bot!

I can download from:
- YouTube
- TikTok
- Instagram
- Facebook
- Pinterest
- Snapchat
- Twitter/X
- And more!
"""


async def send_error_to_admin(context: ContextTypes.DEFAULT_TYPE, error: str, url: str = None):
    if ADMIN_ID:
        message = f"⚠️ Bot Error\n\nURL: {url or 'N/A'}\n\nError:\n{error}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=message)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)
    await update.message.reply_text(
        "What do you want to download?",
        reply_markup=MEDIA_KEYBOARD
    )
    return MEDIA_TYPE


async def media_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if "Video" in choice:
        context.user_data["media_type"] = "video"
    elif "Picture" in choice:
        context.user_data["media_type"] = "picture"
    else:
        await update.message.reply_text(
            "Please choose from the options below.",
            reply_markup=MEDIA_KEYBOARD
        )
        return MEDIA_TYPE

    await update.message.reply_text(
        "Now send me the URL 🔗",
        reply_markup=ReplyKeyboardRemove()
    )
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
        return await restart(update, context)

    media = context.user_data.get("media_type", "video")
    platform = detect_platform(url)

    await update.message.reply_text(f"Downloading {media} from {platform}... ⏳")

    result = download_video(url, platform, media)

    if not result["success"]:
        await send_error_to_admin(context, result["error"], url)
        await update.message.reply_text("❌ Something went wrong. Our team has been notified.")
        return await restart(update, context)

    file_path = result["file"]
    file_type = result.get("type", media)

    try:
        await update.message.reply_text("Uploading... 📤")
        with open(file_path, "rb") as f:
            if file_type == "picture":
                await update.message.reply_photo(photo=f)
            else:
                await update.message.reply_video(video=f)
        await update.message.reply_text("Done ✅")

    except Exception as e:
        await send_error_to_admin(context, str(e), url)
        await update.message.reply_text("❌ Upload failed. Our team has been notified.")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    return await restart(update, context)


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Want to download something else?",
        reply_markup=MEDIA_KEYBOARD
    )
    return MEDIA_TYPE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bye! Send /start to use me again. 👋", reply_markup=ReplyKeyboardRemove())
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
            MEDIA_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, media_type)],
            URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
