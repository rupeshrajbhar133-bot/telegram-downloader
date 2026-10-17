import os
import time
import telebot
import yt_dlp

# ==========================================
# BOT TOKEN - Environment Variable Setup
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

# Initialize the Telegram Bot
bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

# Directory to temporarily save downloaded media files
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Developer Signature
SIGNATURE = "@RD3B4T"


# ==========================================
# START COMMAND HANDLER
# ==========================================
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "👋 <b>Добро пожаловать!</b>\n\n"
        "📥 Send me a public video URL.\n\n"
        f"🤖 {SIGNATURE}"
    )


# ==========================================
# MEDIA DOWNLOAD & UPLOAD HANDLER
# ==========================================
@bot.message_handler(func=lambda message: True)
def download_media(message):
    url = (message.text or "").strip()

    # Validate if input is a valid HTTP/HTTPS link
    if not url.startswith(("http://", "https://")):
        bot.reply_to(
            message,
            "❌ <b>Invalid URL</b>\n\n"
            "Please send a valid public video link.\n\n"
            f"🤖 {SIGNATURE}"
        )
        return

    # Send initial processing status message
    status = bot.reply_to(
        message,
        "⏳ <b>Downloading...</b>\n\n"
        f"🤖 {SIGNATURE}"
    )

    # Output template for yt-dlp
    output_template = os.path.join(
        DOWNLOAD_DIR,
        "%(id)s.%(ext)s"
    )

    # yt-dlp configuration options (No ffmpeg required)
    ydl_opts = {
        "outtmpl": output_template,
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 60,
        "quiet": True,
        "no_warnings": True,
    }

    filename = None

    try:
        # Download video using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # Fallback search in download dir for the video ID if filename is missing/different
            if not os.path.exists(filename):
                video_id = info.get("id")
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.startswith(video_id):
                        filename = os.path.join(DOWNLOAD_DIR, f)
                        break

        # Check if file was successfully downloaded
        if not filename or not os.path.exists(filename):
            bot.edit_message_text(
                "❌ <b>Download failed. File not found.</b>\n\n"
                f"🤖 {SIGNATURE}",
                message.chat.id,
                status.message_id
            )
            return

        # Update status message for uploading phase
        bot.edit_message_text(
            "📤 <b>Uploading...</b>\n\n"
            f"🤖 {SIGNATURE}",
            message.chat.id,
            status.message_id
        )

        # Send video file back to the user
        with open(filename, "rb") as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=(
                    "✅ <b>Download complete!</b>\n\n"
                    f"🤖 {SIGNATURE}"
                ),
                supports_streaming=True,
                timeout=120
            )

        # Cleanup local file after successful upload
        try:
            os.remove(filename)
        except Exception:
            pass

        # Remove the status message
        try:
            bot.delete_message(
                message.chat.id,
                status.message_id
            )
        except Exception:
            pass

    except Exception as e:
        print("DOWNLOAD ERROR:", e)

        # Cleanup file on error
        try:
            if filename and os.path.exists(filename):
                os.remove(filename)
        except Exception:
            pass

        # Notify user about failure
        try:
            bot.edit_message_text(
                "❌ <b>Download failed.</b>\n\n"
                "The URL may be private, unsupported, "
                "or temporarily unavailable.\n\n"
                f"🤖 {SIGNATURE}",
                message.chat.id,
                status.message_id
            )
        except Exception:
            pass


# ==========================================
# START BOT + AUTO RECONNECT LOOP
# ==========================================
print("🤖 @RD3B4T Downloader Bot is starting...")

while True:
    try:
        print("🔄 Connecting to Telegram...")
        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            skip_pending=True,
            allowed_updates=["message"]
        )
    except Exception as e:
        print("⚠️ Telegram connection error:")
        print(e)
        print("🔁 Retrying in 5 seconds...")
        time.sleep(5)
        
