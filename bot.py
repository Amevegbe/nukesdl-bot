import os
import re
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters, ConversationHandler
)
from engine import download_video

TOKEN = os.environ.get("BOT_TOKEN")

# Conversation states
MEDIA_TYPE, URL = range(2)

MEDIA_KEYBOARD = ReplyKeyboardMarkup(
    [["🎬 Video", "🎵 Audio", "🖼️ Picture"]],
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
- Snapchat
- Twitter/X
NOTE:PINTEREST DOWNLOADS HAS NOT BEEN ADDED YET
"""


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
    elif "Audio" in choice:
        context.user_data["media_type"] = "audio"
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

    media = context.user_data.get("media_type", "video")
    platform = detect_platform(url)

    await update.message.reply_text(f"Downloading {media} from {platform}... ⏳")

    result = download_video(url, platform, media)

    if not result["success"]:
        await update.message.reply_text(f"Failed ❌\n{result['error']}")
        return await restart(update, context)

    file_path = result["file"]

    try:
        await update.message.reply_text("Uploading... 📤")

        with open(file_path, "rb") as f:
            if media == "video":
                await update.message.reply_video(video=f)
            elif media == "audio":
                await update.message.reply_audio(audio=f)
            elif media == "picture":
                await update.message.reply_photo(photo=f)

        await update.message.reply_text("Done ✅")

    except Exception as e:
        await update.message.reply_text(f"Upload failed ❌\n{str(e)}")

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
