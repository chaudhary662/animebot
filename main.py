import os
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Environment variables (for security)
TOKEN = os.getenv("BOT_TOKEN")  # Set this in Render environment settings
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Your Telegram channel ID (@YourChannel)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Hello! Upload a MKV video file, and I will check, compress (if needed), and upload it to your channel."
    )

def check_file_size(file_path):
    """Check if file size exceeds 2GB."""
    file_size = os.path.getsize(file_path)
    if file_size > 2 * 1024 * 1024 * 1024:  # 2GB limit
        return False, "❌ File size exceeds the 2GB limit. Please compress the file."
    return True, "✔ File size is within the allowed limit."

def check_codec_compatibility(file_path):
    """Check codec compatibility using ffmpeg."""
    try:
        result = subprocess.run(["ffmpeg", "-i", file_path], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output = result.stderr.decode('utf-8')
        if "Unsupported codec" in output:
            return False, "❌ The video contains unsupported codecs. Please re-encode the video."
        return True, "✔ Video codecs are compatible."
    except Exception as e:
        return False, f"❌ Error checking codecs: {str(e)}"

def compress_video(input_file, output_file):
    """Compress MKV file without losing audio tracks or subtitles."""
    try:
        command = [
            "ffmpeg", "-i", input_file,
            "-vcodec", "libx264", "-crf", "23",
            "-acodec", "copy", "-scodec", "copy", output_file
        ]
        subprocess.run(command, check=True)
        return True, "✔ Video successfully compressed."
    except Exception as e:
        return False, f"❌ Error during compression: {str(e)}"

def upload_video(update: Update, context: CallbackContext):
    if update.message.video:
        video_file = context.bot.get_file(update.message.video.file_id)
        file_path = "input_video.mkv"
        video_file.download(file_path)

        # Step 1: Check file size
        size_ok, size_message = check_file_size(file_path)
        if not size_ok:
            update.message.reply_text(size_message)
            os.remove(file_path)
            return

        # Step 2: Check codec compatibility
        codec_ok, codec_message = check_codec_compatibility(file_path)
        if not codec_ok:
            update.message.reply_text(codec_message)
            os.remove(file_path)
            return

        # Step 3: Compress video if needed
        compressed_path = "compressed_video.mkv"
        compress_ok, compress_message = compress_video(file_path, compressed_path)
        update.message.reply_text(compress_message)

        # Select file to upload
        video_to_upload = compressed_path if compress_ok else file_path

        # Step 4: Upload video to channel
        try:
            with open(video_to_upload, 'rb') as video:
                context.bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=video,
                    caption="🎬 Video uploaded successfully!"
                )
            update.message.reply_text("✔ Video uploaded successfully!")
        except Exception as e:
            update.message.reply_text(f"❌ Error uploading video: {str(e)}")
        finally:
            # Clean up files
            os.remove(file_path)
            if os.path.exists(compressed_path):
                os.remove(compressed_path)
    else:
        update.message.reply_text("❌ Please upload a valid MKV video file.")

def main():
    # Set up bot
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.video, upload_video))

    # Start the bot
    updater.start_polling()
    print("Bot is running...")
    updater.idle()

if _name_ == "_main_":
    main()
