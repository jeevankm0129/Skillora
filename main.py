import logging

from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Bot Handlers
from bot.telegram_bot import (
    CHOOSING,
    JOB_DESC_UPLOAD,
    RESUME_UPLOAD,
    ask_for_job_description,
    ask_for_resume,
    cancel,
    handle_job_description,
    handle_resume_upload,
    start,
)

# Config & Database
from config import TELEGRAM_BOT_TOKEN
from database import Base, engine

# Services
from services.notification_service import schedule_job_checks

# Configure Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Application Entry Point."""

    # 1. Initialize Database
    logger.info("Initializing Database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")

    # 2. Start Background Scheduler (Job Notifications)
    schedule_job_checks()

    # 3. Build Telegram Bot
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("Bot token missing! Exiting.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 4. Setup Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^(Job Recommendations)$"), ask_for_resume),
                MessageHandler(filters.Regex("^(Resume Building)$"), ask_for_job_description),
            ],
            RESUME_UPLOAD: [MessageHandler(filters.Document.ALL, handle_resume_upload)],
            JOB_DESC_UPLOAD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_job_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # 5. Run
    logger.info("Bot is polling...")
    application.run_polling()


if __name__ == "__main__":
    main()
