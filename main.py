import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import cast

import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Bot logic
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
    build_and_send_resume,
    cancel,
    handle_build_resume_choice,   # FIX: was handle_resume_choice (wrong handler)
    handle_contact,
    handle_education,
    handle_email_input,
    handle_exams,
    handle_experience,
    handle_internships,
    handle_job_rec_choice,        # FIX: new dedicated handler for Job Recommendations
    handle_name,
    handle_projects,
    handle_resume_file,
    handle_skills,
    start,
)
from bot.whatsapp_bot import whatsapp_router
from config import TELEGRAM_BOT_TOKEN
from database.db import Base, engine
from services.notification_service import schedule_job_checks

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

telegram_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app

    logger.info("Initialising Skillora Engine…")

    # Create all DB tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start background job scheduler
    schedule_job_checks(asyncio.get_running_loop())

    # Build Telegram application
    valid_token = cast(str, TELEGRAM_BOT_TOKEN)
    telegram_app = Application.builder().token(valid_token).build()

    # ------------------------------------------------------------------
    # ConversationHandler — fully wired routing
    # ------------------------------------------------------------------
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # Main menu — two distinct buttons, two distinct handlers
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^Job Recommendations$"),
                    handle_job_rec_choice,       # → RESUME_UPLOAD
                ),
                MessageHandler(
                    filters.Regex("^Build Resume$"),
                    handle_build_resume_choice,  # → ASK_NAME
                ),
            ],

            # Job recommendation path
            RESUME_UPLOAD: [
                MessageHandler(filters.Document.ALL, handle_resume_file),
            ],
            EMAIL_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email_input),
            ],

            # Resume builder path
            ASK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name),
            ],
            ASK_CONTACT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact),
            ],
            ASK_EDUCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_education),
            ],
            ASK_SKILLS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_skills),
            ],
            ASK_PROJECTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_projects),
            ],
            ASK_INTERNSHIPS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_internships),
            ],
            ASK_EXPERIENCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_experience),
            ],
            ASK_EXAMS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_exams),
            ],
            ASK_EXTRACURRICULAR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, build_and_send_resume),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        # Persist conversation state across bot restarts (optional but recommended)
        allow_reentry=True,
    )

    telegram_app.add_handler(conv_handler)

    await telegram_app.initialize()
    await telegram_app.start()
    if telegram_app.updater:
        await telegram_app.updater.start_polling(drop_pending_updates=True)

    yield  # Server runs here

    # Graceful shutdown
    if telegram_app:
        if telegram_app.updater and telegram_app.updater.running:
            await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()

    await engine.dispose()
    logger.info("Skillora Engine shut down cleanly.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Skillora Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (only mount if the directory exists to avoid startup errors)
if os.path.exists("frontend"):
    app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
    if os.path.exists("frontend/assets"):
        app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# Routers
app.include_router(whatsapp_router, prefix="/whatsapp", tags=["WhatsApp"])


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/recommend-jobs")
async def recommend_jobs(resume: UploadFile = File(...)):
    """Web-facing endpoint — placeholder for future web UI integration."""
    logger.info(f"Web resume upload received: {resume.filename}")
    return {"status": "success", "message": "File received", "jobs": []}


@app.get("/health")
async def health_check():
    return {"status": "Skillora Engine is running."}


# ---------------------------------------------------------------------------
# Dev entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
