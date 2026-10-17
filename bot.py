import os
import time
import telebot
import yt_dlp

# ==========================================
# BOT TOKEN - Environment Variable
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

SIGNATURE = "@RD3B4T"


# ==========================================
# START
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
# DOWNLOAD
# ==========================================
@bot.message_handler(func=lambda message: True)
def download_media(message):
    url = (message.text or "").strip()

    if not url.startswith(("http://", "https://")):
        bot.reply_to(
            message,
            "❌ <b>Invalid URL</b>\n\n"
            "Please send a valid public video link.\n\n"
            f"🤖 {SIGNATURE}"
        )
        return

    status = bot.reply_to(
        message,
        "⏳ <b>Downloading...</b>\n\n"
        f"🤖 {SIGNATURE}"
    )

    output_template = os.path.join(
        DOWNLOAD_DIR,
        "%(id)s.%(ext)s"
    )

    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 60,
        "quiet": True,
        "no_warnings": True,
    }

    filename = None

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # Ensure correct extension for merged formats
            base, _ = os.path.splitext(filename)
            mp4_file = base + ".mp4"
            
            if os.path.exists(mp4_file):
                filename = mp4_file
            elif not os.path.exists(filename):
                # Fallback search in download dir for the video ID
                video_id = info.get("id")
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.startswith(video_id):
                        filename = os.path.join(DOWNLOAD_DIR, f)
                        break

        if not filename or not os.path.exists(filename):
            bot.edit_message_text(
                "❌ <b>Download failed. File not found.</b>\n\n"
                f"🤖 {SIGNATURE}",
                message.chat.id,
                status.message_id
            )
            return

        bot.edit_message_text(
            "📤 <b>Uploading...</b>\n\n"
            f"🤖 {SIGNATURE}",
            message.chat.id,
            status.message_id
        )

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

        try:
            os.remove(filename)
        except Exception:
            pass

        try:
            bot.delete_message(
                message.chat.id,
                status.message_id
            )
        except Exception:
            pass

    except Exception as e:
        print("DOWNLOAD ERROR:", e)

        try:
            if filename and os.path.exists(filename):
                os.remove(filename)
        except Exception:
            pass

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
# START BOT + AUTO RECONNECT
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
