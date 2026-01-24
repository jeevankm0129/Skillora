"""
Telegram bot handler.

Minimal end-to-end working flow:
- /start
- Resume upload
- Job matching response

Compatible with python-telegram-bot v20+
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from sqlalchemy import update
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.ai.skill_extractor import SkillExtractor
from app.bot.bot_messages import WELCOME_MESSAGE
from app.config import Settings
from app.jobs.job_fetcher import JobFetcher
from app.jobs.job_matcher import JobMatcher
from app.jobs.job_ranker import JobRanker
from app.resume.resume_parser import ResumeParser
from app.utils.file_handler import save_file_securely
from app.utils.logger import get_logger

logger = get_logger(__name__)

UPLOAD_DIR = Path("uploads")


# ---------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.message is None:
        return

    await update.message.reply_text(WELCOME_MESSAGE)
    await update.message.reply_text("📄 Please upload your resume (PDF or DOCX).")


# ---------------------------------------------------------------------
# Resume upload handler
# ---------------------------------------------------------------------


async def resume_upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle resume file uploads."""
    if update.message is None or update.message.document is None:
        return

    try:
        await update.message.reply_text("⏳ Processing your resume, please wait...")

        document = update.message.document
        telegram_file = await document.get_file()

        file_bytes = await telegram_file.download_as_bytearray()
        file_stream = BytesIO(file_bytes)

        filename = document.file_name or "User_Resume"

        file_path = save_file_securely(
            file_obj=file_stream,
            filename=filename,
            destination_dir=UPLOAD_DIR,
        )

        # Parse resume
        parser = ResumeParser()
        parsed_resume = parser.parse(str(file_path))

        # Extract skills
        extractor = SkillExtractor()
        resume_text = parsed_resume.get("text", "")
        if not isinstance(resume_text, str):
            resume_text = ""

        skills = extractor.extract(resume_text)
        logger.info("Extracted skills: %s", skills)
        await update.message.reply_text(f"🧪 Extracted skills:\n{skills}")

        # Fetch jobs
        jobs = JobFetcher().fetch_jobs()

        # Match and rank jobs
        matcher = JobMatcher()
        matched_jobs = matcher.match_jobs(skills, jobs)
        ranked_jobs = JobRanker().rank_jobs(matched_jobs)

        if not ranked_jobs:
            await update.message.reply_text("❌ No suitable jobs found for your profile.")
            return

        response_lines = ["🔍 Top Job Matches:\n"]

        for idx, job in enumerate(ranked_jobs[:3], start=1):
            response_lines.append(
                f"{idx}. {job['title']} " f"({job['confidence']}) — {job['location']}"
            )

        await update.message.reply_text("\n".join(response_lines))

    except Exception:
        logger.exception("Resume processing failed")
        await update.message.reply_text("❌ Something went wrong. Please try again.")


# ---------------------------------------------------------------------
# Application bootstrap
# ---------------------------------------------------------------------


def start_bot() -> None:
    """Start Telegram bot application."""
    settings = Settings()

    if not settings.TELE_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    application = Application.builder().token(settings.TELE_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.Document.ALL, resume_upload_handler))

    logger.info("Telegram bot started")
    application.run_polling()
