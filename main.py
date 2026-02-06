import logging

from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Bot Handlers
from bot.telegram_bot import handle_resume_file  # ✅ FIXED NAME
from bot.telegram_bot import (
    CHOOSING,
    JOB_DESC_UPLOAD,
    RESUME_UPLOAD,
    ask_for_job_description,
    ask_for_resume,
    cancel,
    handle_job_description,
    start,
)

# Config
from config import ENABLE_BACKGROUND_JOB_MATCHING, TELEGRAM_BOT_TOKEN

# Database
from database.db import Base, engine  # ✅ FIXED IMPORT

# Services
from services.notification_service import schedule_job_checks

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    """Application Entry Point."""

    # 1. Initialize Database
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready.")

    # 2. Start Background Scheduler (if enabled)
    if ENABLE_BACKGROUND_JOB_MATCHING:
        logger.info("Starting background job scheduler...")
        schedule_job_checks()
    else:
        logger.info("Background job scheduler disabled by config.")

    # 3. Start Telegram Bot
    if not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN is missing. Exiting.")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 4. Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [
                MessageHandler(filters.Regex("^(Job Recommendations)$"), ask_for_resume),
                MessageHandler(filters.Regex("^(Resume Building)$"), ask_for_job_description),
            ],
            RESUME_UPLOAD: [MessageHandler(filters.Document.ALL, handle_resume_file)],
            JOB_DESC_UPLOAD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_job_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # 5. Run
    logger.info("Telegram bot started. Polling...")
    application.run_polling()


if __name__ == "__main__":
    main()
