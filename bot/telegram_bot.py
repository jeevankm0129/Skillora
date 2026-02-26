import json
import logging
import os
from asyncio import create_task
from typing import Optional, cast

from telegram import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram import User as TelegramUser
from telegram.ext import ContextTypes, ConversationHandler

import database.crud as crud
from database.db import SessionLocal
from services.ai_service import (
    extract_skills_from_resume,
    get_job_recommendations,
    tailor_resume,
)
from utils.resume_generator import generate_pdf_resume
from utils.resume_parser import parse_resume

logger = logging.getLogger(__name__)

# Conversation States
CHOOSING, RESUME_UPLOAD, JOB_DESC_UPLOAD = range(3)

SUPPORTED_RESUME_EXTENSIONS = ("pdf", "docx")


def _safe_filename_for_user(telegram_id: int, original_filename: str) -> str:
    """Create a predictable temp filename tied to the Telegram user."""
    return f"temp_{telegram_id}_{original_filename}"


def _get_user_and_message(update: Update) -> tuple[Optional[TelegramUser], Optional[Message]]:
    """Return strongly-typed user and message objects from update payload."""
    tg_user = cast(Optional[TelegramUser], update.effective_user)
    message = cast(Optional[Message], update.message)
    return tg_user, message


def _is_supported_resume(filename: str) -> bool:
    """Check whether uploaded file extension is supported by parser."""
    extension = filename.split(".")[-1].lower()
    return extension in SUPPORTED_RESUME_EXTENSIONS


def _build_job_results_message(jobs: list[dict]) -> str:
    """Build a markdown response containing top job matches."""
    response = "🚀 *Top Job Matches for You:*\n\n"
    for job in jobs[:3]:
        title = job.get("title", "Unknown")
        company = job.get("company", "Unknown")
        location = job.get("location", "Unknown")
        link = job.get("link", "")

        response += f"*{title}*\n{company} — {location}\n"
        response += f"[Apply Here]({link})\n\n" if link else "\n"

    return response


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Register user if needed and present primary actions."""
    tg_user, message = _get_user_and_message(update)
    if not tg_user or tg_user.id is None or not message:
        return ConversationHandler.END

    db = SessionLocal()
    try:
        db_user = crud.get_user_by_telegram_id(db, tg_user.id)
        if not db_user:
            crud.create_user(db, telegram_id=tg_user.id)
            logger.info("New user registered: %s", tg_user.id)
    finally:
        db.close()

    reply_keyboard = [["Job Recommendations", "Resume Building"]]
    await message.reply_text(
        f"Hi {tg_user.first_name}! 👋\n\nHow can I help you today?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
        ),
    )
    return CHOOSING


# =========================
# JOB RECOMMENDATION FLOW
# =========================
async def ask_for_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt user to upload resume for recommendations."""
    _, message = _get_user_and_message(update)
    if not message:
        return ConversationHandler.END

    await message.reply_text(
        "Please upload your resume (PDF or DOCX).",
        reply_markup=ReplyKeyboardRemove(),
    )
    return RESUME_UPLOAD


async def handle_resume_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate, parse, and persist uploaded resume before async job matching."""
    tg_user, message = _get_user_and_message(update)
    if not tg_user or tg_user.id is None or not message:
        return ConversationHandler.END

    document = message.document
    if not document:
        await message.reply_text("Please upload a valid document file.")
        return RESUME_UPLOAD

    file_name = document.file_name
    if not file_name:
        await message.reply_text("Uploaded file has no filename. Please try again.")
        return RESUME_UPLOAD

    if not _is_supported_resume(file_name):
        await message.reply_text("Only PDF and DOCX files are supported.")
        return RESUME_UPLOAD

    temp_filename = _safe_filename_for_user(tg_user.id, file_name)

    try:
        file = await context.bot.get_file(document.file_id)
        await file.download_to_drive(temp_filename)

        await message.reply_text("📄 Reading your resume…")

        resume_text = parse_resume(temp_filename)
        if not resume_text or len(resume_text) < 50:
            await message.reply_text(
                "I couldn't read enough text from this resume. Please upload a text-based file."
            )
            return RESUME_UPLOAD

        # Save resume immediately
        db = SessionLocal()
        try:
            db_user = crud.get_user_by_telegram_id(db, tg_user.id)
            if db_user:
                crud.save_resume(db, db_user.id, resume_text)
        finally:
            db.close()

        # Quick response
        await message.reply_text(
            "✅ Resume received!\n"
            "🔍 Finding the best job matches for you…\n"
            "⏳ This may take ~10–30 seconds."
        )

        # Run heavy work once in background
        create_task(
            process_resume_background(
                chat_id=message.chat_id,
                telegram_id=tg_user.id,
                resume_text=resume_text,
                context=context,
            )
        )

    except Exception as e:
        logger.exception("Error handling resume upload: %s", e)
        await message.reply_text("❌ An internal error occurred while reading your resume.")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    return ConversationHandler.END


# =========================
# BACKGROUND JOB PROCESSING
# =========================
async def process_resume_background(
    chat_id: int,
    telegram_id: int,
    resume_text: str,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Run heavier recommendation tasks without blocking the chat interaction."""
    try:
        # 1) Extract skills
        extracted = await extract_skills_from_resume(resume_text)
        skills = (extracted.get("skills") or [])[:10]

        # ---------------- DEBUG SKILL EXTRACTION ----------------
        print("\n================ EXTRACTED SKILLS ================")
        print(skills)
        print("=================================================\n")
        # --------------------------------------------------------

        if not skills:
            await context.bot.send_message(chat_id, "❌ Could not extract skills from your resume.")
            return

        # 2) Cache extracted JSON into DB (Resume.parsed_json) + link skills
        db = SessionLocal()
        try:
            db_user = crud.get_user_by_telegram_id(db, telegram_id)
            if db_user and db_user.resume:
                db_user.resume.parsed_json = json.dumps(extracted)
                db.commit()

                # optional but good: keep skills linked to user
                try:
                    crud.link_skills_to_user(db, db_user.id, skills)
                except Exception:
                    # Don't break the flow if skill linking fails
                    db.rollback()
        finally:
            db.close()

        # 3) Fetch + rank jobs
        jobs = await get_job_recommendations(skills, resume_text)

        if not jobs:
            await context.bot.send_message(chat_id, "No suitable jobs found right now.")
            return

        # 4) Send results
        msg = _build_job_results_message(jobs)

        await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

    except Exception as e:
        logger.exception("Background resume processing failed: %s", e)
        await context.bot.send_message(
            chat_id, "❌ Something went wrong while processing your resume."
        )


# =========================
# RESUME BUILDING FLOW (Tailor existing resume)
# =========================
async def ask_for_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt user for target job description to tailor existing resume."""
    _, message = _get_user_and_message(update)
    if not message:
        return ConversationHandler.END

    await message.reply_text(
        "Please paste the job description you are targeting.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return JOB_DESC_UPLOAD


async def handle_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate a tailored resume PDF from stored resume and supplied job description."""
    tg_user, message = _get_user_and_message(update)
    if not tg_user or tg_user.id is None or not message:
        return ConversationHandler.END

    job_desc = message.text
    if not job_desc or len(job_desc) < 10:
        await message.reply_text("Please paste a full job description.")
        return JOB_DESC_UPLOAD

    db = SessionLocal()
    try:
        db_user = crud.get_user_by_telegram_id(db, tg_user.id)
        if not db_user or not db_user.resume:
            await message.reply_text("Please upload your resume first (Job Recommendations).")
            return ConversationHandler.END

        base_resume = db_user.resume.text_content
    finally:
        db.close()

    new_resume = await tailor_resume(base_resume, job_desc)
    if not new_resume:
        await message.reply_text("Failed to generate tailored resume.")
        return ConversationHandler.END

    output_file = f"Tailored_Resume_{tg_user.id}.pdf"
    if generate_pdf_resume(new_resume, output_file):
        with open(output_file, "rb") as f:
            await message.reply_document(f)
        os.remove(output_file)
    else:
        await message.reply_text("PDF generation failed.")

    return ConversationHandler.END


# =========================
# CANCEL
# =========================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Abort active conversation flow and remove custom keyboard."""
    _, message = _get_user_and_message(update)
    if not message:
        return ConversationHandler.END

    await message.reply_text(
        "Operation cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
