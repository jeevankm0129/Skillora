import json
import logging
import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler

import database.crud as crud
from database.db import SessionLocal
from database.models import User
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


# =========================
# START COMMAND (FIXED)
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and registers the user."""
    user = update.effective_user

    db = SessionLocal()
    try:
        db_user = crud.get_user_by_telegram_id(db, user.id)
        if not db_user:
            crud.create_user(db, telegram_id=user.id)
            logger.info(f"New user registered: {user.id}")
    except Exception as e:
        logger.error(f"DB Error in start: {e}")
    finally:
        db.close()

    reply_keyboard = [["Job Recommendations", "Resume Building"]]
    await update.message.reply_text(
        f"Hi {user.first_name}! I am your AI Career Assistant.\n\nHow can I help you today?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return CHOOSING


# =========================
# JOB RECOMMENDATION FLOW
# =========================
async def ask_for_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Please upload your current resume (PDF or DOCX).",
        reply_markup=ReplyKeyboardRemove(),
    )
    return RESUME_UPLOAD


async def handle_resume_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    document = update.message.document

    if not document:
        await update.message.reply_text("Please upload a valid document file.")
        return RESUME_UPLOAD

    file_ext = document.file_name.split(".")[-1].lower()
    if file_ext not in ["pdf", "docx"]:
        await update.message.reply_text("Only PDF and DOCX are supported.")
        return RESUME_UPLOAD

    temp_filename = f"temp_{user.id}_{document.file_name}"

    try:
        file = await context.bot.get_file(document.file_id)
        await file.download_to_drive(temp_filename)

        await update.message.reply_text("Reading resume... 🔍")

        resume_text = parse_resume(temp_filename)
        if not resume_text or len(resume_text) < 50:
            await update.message.reply_text(
                "I couldn't read enough text from this file. Please upload a text-based resume."
            )
            return RESUME_UPLOAD

        await update.message.reply_text("Analyzing skills... 🧠")
        extracted = await extract_skills_from_resume(resume_text)
        if not extracted:
            await update.message.reply_text("AI analysis failed. Please try again later.")
            return ConversationHandler.END

        skills = extracted["skills"]

        db = SessionLocal()
        try:
            db_user = crud.get_user_by_telegram_id(db, user.id)
            if db_user:
                crud.save_resume(
                    db,
                    db_user.id,
                    resume_text,
                    parsed_json=json.dumps(extracted),
                )
                crud.link_skills_to_user(db, db_user.id, skills)
        finally:
            db.close()

        await update.message.reply_text(
            f"Found skills: {', '.join(skills[:5])}...\nSearching for jobs... 🌍"
        )

        ranked_jobs = await get_job_recommendations(skills, resume_text)
        if not ranked_jobs:
            await update.message.reply_text("No jobs found right now.")
            return ConversationHandler.END

        for job in ranked_jobs[:3]:
            text = (
                f"🚀 *{job['title']}*\n"
                f"🏢 {job['company']}\n"
                f"📍 {job['location']}\n"
                f"💡 _{job.get('reasoning', '')}_\n"
                f"🔗 [Apply Here]({job['link']})"
            )
            await update.message.reply_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error handling resume: {e}")
        await update.message.reply_text("An internal error occurred.")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    return ConversationHandler.END


# =========================
# RESUME BUILDING FLOW
# =========================
async def ask_for_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Please paste the job description you are targeting.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return JOB_DESC_UPLOAD


async def handle_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    job_desc = update.message.text

    if not job_desc or len(job_desc) < 10:
        await update.message.reply_text("Please paste a full job description.")
        return JOB_DESC_UPLOAD

    db = SessionLocal()
    try:
        db_user = crud.get_user_by_telegram_id(db, user.id)
        if not db_user or not db_user.resume:
            await update.message.reply_text(
                "Please upload your resume first using Job Recommendations."
            )
            return ConversationHandler.END
        base_resume = db_user.resume.text_content
    finally:
        db.close()

    new_resume = await tailor_resume(base_resume, job_desc)
    if not new_resume:
        await update.message.reply_text("Failed to generate resume.")
        return ConversationHandler.END

    output_file = f"Tailored_Resume_{user.id}.pdf"
    if generate_pdf_resume(new_resume, output_file):
        with open(output_file, "rb") as f:
            await update.message.reply_document(f)
        os.remove(output_file)
    else:
        await update.message.reply_text("PDF generation failed.")

    return ConversationHandler.END


# =========================
# CANCEL
# =========================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
