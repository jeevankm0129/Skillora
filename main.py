import asyncio
import logging
from contextlib import asynccontextmanager
from typing import cast

import uvicorn
from fastapi import FastAPI
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Import Bot Logic
from bot.telegram_bot import (
    ASK_CONTACT,
    ASK_EDUCATION,
    ASK_EXAMS,
    ASK_EXPERIENCE,
    ASK_EXTRACURRICULAR,
    ASK_INTERNSHIPS,
    ASK_NAME,
    ASK_PROJECTS,
    ASK_SKILLS,
    CHOOSING,
    EMAIL_INPUT,
    RESUME_UPLOAD,
    ask_for_resume,
    build_and_send_resume,
    cancel,
    handle_contact,
    handle_education,
    handle_email_input,
    handle_exams,
    handle_experience,
    handle_internships,
    handle_name,
    handle_projects,
    handle_resume_file,
    handle_skills,
    start,
)
from bot.whatsapp_bot import whatsapp_router

# Import Infrastructure
from config import TELEGRAM_BOT_TOKEN
from database.db import Base, engine
from services.notification_service import schedule_job_checks

# IMPORT YOUR NEW WEB FRONTEND ROUTER
from web_Page import web_router

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Global variable to hold the Telegram app
telegram_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the startup and shutdown sequence of the entire Skillora system.
    """
    global telegram_app
    logger.info("Initializing Skillora Engine...")

    # 1. Initialize Async Database Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database ready.")

    # 2. Start Background Job Hunter (Runs every 2 hours)
    schedule_job_checks(asyncio.get_running_loop())

    # 3. Initialize Telegram Bot concurrently
    # Explicitly cast the token to a string to satisfy the type-checker
    valid_token = cast(str, TELEGRAM_BOT_TOKEN)
    telegram_app = Application.builder().token(valid_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # Branching state
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(Job Recommendations|Build Resume)$"), ask_for_resume
                )
            ],
            # Flow 1: Job Recommendations
            RESUME_UPLOAD: [MessageHandler(filters.Document.ALL, handle_resume_file)],
            EMAIL_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email_input)],
            # Flow 2: Resume Builder (Step-by-Step)
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            ASK_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact)],
            ASK_EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_education)],
            ASK_SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_skills)],
            ASK_PROJECTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_projects)],
            ASK_INTERNSHIPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_internships)],
            ASK_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_experience)],
            ASK_EXAMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_exams)],
            ASK_EXTRACURRICULAR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, build_and_send_resume)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    telegram_app.add_handler(conv_handler)

    # Start the bot natively inside the FastAPI event loop
    await telegram_app.initialize()
    await telegram_app.start()

    if telegram_app.updater:
        # drop_pending_updates ignores old messages sent while the bot was offline
        await telegram_app.updater.start_polling(drop_pending_updates=True)
        logger.info("Telegram Bot active and polling.")

    yield  # --- The Web Server runs here ---

    # 4. Graceful Shutdown with a Kill Switch
    logger.info("Shutting down Skillora Engine... (This may take up to 2 seconds)")
    if telegram_app:
        try:
            if telegram_app.updater:
                # Forcefully cut the long-polling network connection after 2 seconds
                await asyncio.wait_for(telegram_app.updater.stop(), timeout=2.0)

            await asyncio.wait_for(telegram_app.stop(), timeout=2.0)
            await telegram_app.shutdown()
        except asyncio.TimeoutError:
            logger.warning("Telegram shutdown timed out. Forcefully closed.")

    await engine.dispose()
    logger.info("Shutdown complete.")


# Create the FastAPI application
app = FastAPI(
    title="Skillora Backend",
    description="AI-Powered Resume Builder & Job Recommendation Bot",
    lifespan=lifespan,
)

# Mount the WhatsApp Router (Webhooks)
app.include_router(whatsapp_router, prefix="/whatsapp", tags=["WhatsApp"])

# MOUNT YOUR NEW WEB UI ROUTER
app.include_router(web_router)


# Changed this from "/" to "/health" so the Web UI can use "/" for the landing page
@app.get("/health")
async def health_check():
    return {"status": "Skillora Engine is running successfully."}


if __name__ == "__main__":
    # Run the server on port 8000 with hot reload for development
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
