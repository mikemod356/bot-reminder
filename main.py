import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# The friendly reminder message
REMINDER_TEXT = "⏰ Hey! Just a gentle nudge to check your daily tasks. You've got this! 💪"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message and starts the 5-minute reminder loop."""
    chat_id = update.effective_chat.id

    # Check if a job already exists for this chat to avoid duplicates
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()

    # Schedule the repeating job: every 300 seconds (5 minutes)
    # first=10 waits 10 seconds before the first message so you see the confirmation first
    context.job_queue.run_repeating(
        send_reminder,
        interval=300,
        first=10,
        context=chat_id,
        name=str(chat_id)
    )

    await update.message.reply_text(
        "👋 Hi! I'll remind you about your tasks every 5 minutes.\n"
        "Send /stop if you want me to take a break."
    )

async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """The function that actually sends the reminder."""
    job = context.job
    await context.bot.send_message(chat_id=job.context, text=REMINDER_TEXT)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops the reminder loop for this chat."""
    chat_id = update.effective_chat.id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))

    if not current_jobs:
        await update.message.reply_text("I'm not currently reminding you. Send /start to begin.")
        return

    for job in current_jobs:
        job.schedule_removal()

    await update.message.reply_text("🛑 Okay, I've stopped the reminders. Send /start whenever you need me again.")

def main() -> None:
    """Start the bot."""
    # Railway will provide the token via environment variables
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN environment variable not set.")
        return

    application = Application.builder().token(token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))

    # Run the bot (long polling)
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
