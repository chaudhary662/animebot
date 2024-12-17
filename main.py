import os
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import logging

# Logging for debugging purposes
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(_name_)

# BOT_TOKEN is your Telegram bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Set as environment variable in Render


# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Upload your video file (MKV format only) and I'll process it."
    )


# Handle video files
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.document

    # Check if video is MKV
    if video.mime_type != "video/x-matroska":
        await update.message.reply_text("❌ Only MKV files are allowed!")
        return

    file_size_limit = 2 * 1024 * 1024 * 1024  # 2GB limit

    # Check file size
    if video.file_size > file_size_limit:
        await update.message.reply_text("❌ File size exceeds 2GB limit!")
        return

    # Download the file
    file_id = video.file_id
    file = await context.bot.get_file(file_id)
    file_path = f"{video.file_name}"

    await file.download_to_drive(file_path)
    await update.message.reply_text(f"✅ File '{video.file_name}' uploaded successfully!")


# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a video file in MKV format, and I'll process it for you.")


# Main function to run the bot
def main():
    # Initialize the application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Set bot commands
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Get help information")
    ]
    app.bot.set_my_commands(commands)

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_video))

    # Run the bot
    logger.info("Starting the bot...")
    app.run_polling()


if _name_ == "_main_":
    main()
