import asyncio
import json
import logging
import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler

import database.crud as crud

# --- Absolute Imports ---
from database.database import SessionLocal
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> int:
    """Starts the conversation and registers the user."""
    user = update.effective_user

    db = SessionLocal()
    try:
        # Check/Create User
        db_user = crud.get_user_by_telegram_id(db, user.id)
        if not db_user:
            crud.create_user(db, telegram_id=user.id)
            logger.info(f"New user registered: {user.id}")
    except Exception as e:
        logger.error(f"DB Error in start: {e}")
    finally:
        db.close()

    # Show Menu
    reply_keyboard = [["Job Recommendations", "Resume Building"]]
    await update.message.reply_text(
        f"Hi {user.first_name}! I am your AI Career Assistant.\n\n" "How can I help you today?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return CHOOSING


async def ask_for_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Flow 1: Job Recommendations -> Ask for Resume."""
    await update.message.reply_text(
        "Please upload your current resume (PDF or DOCX).",
        reply_markup=ReplyKeyboardRemove(),
    )
    return RESUME_UPLOAD


async def handle_resume_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles resume upload.
    1. Saves file safely.
    2. Extracts skills.
    3. Searches for and ranks jobs.
    """
    user = update.effective_user
    document = update.message.document

    # Validation
    if not document:
        await update.message.reply_text("Please upload a valid document file.")
        return RESUME_UPLOAD

    file_ext = document.file_name.split(".")[-1].lower()
    if file_ext not in ["pdf", "docx"]:
        await update.message.reply_text("Invalid format. Only PDF and DOCX are supported.")
        return RESUME_UPLOAD

    # 1. Safe File Handling
    temp_filename = f"temp_{user.id}_{document.file_name}"

    try:
        file = await context.bot.get_file(document.file_id)
        await file.download_to_drive(temp_filename)

        await update.message.reply_text("Reading resume... 🔍")

        # 2. Parse Text
        resume_text = parse_resume(temp_filename)
        if not resume_text or len(resume_text) < 50:
            await update.message.reply_text(
                "I couldn't read enough text from this file. Is it an image scan? Please try a text-based PDF."
            )
            return RESUME_UPLOAD

        # 3. AI Extraction
        await update.message.reply_text("Analyzing skills... 🧠")
        skills = await extract_skills_from_resume(resume_text)

        if not skills:
            await update.message.reply_text("AI analysis failed. Please try again later.")
            return ConversationHandler.END

        # 4. Save to Database
        db = SessionLocal()
        try:
            db_user = crud.get_user_by_telegram_id(db, user.id)
            if db_user:
                # Save Resume (Serialize skills list to JSON string for storage)
                crud.save_resume(
                    db,
                    db_user.id,
                    resume_text,
                    parsed_json=json.dumps({"skills": skills}),
                )
                # Link Skills
                crud.link_skills_to_user(db, db_user.id, skills)
        finally:
            db.close()

        await update.message.reply_text(
            f"Found skills: {', '.join(skills[:5])}...\nSearching for jobs... 🌍"
        )

        # 5. Get Recommendations (Fetch + Rank)
        ranked_jobs = await get_job_recommendations(skills, resume_text)

        if not ranked_jobs:
            await update.message.reply_text(
                "No live jobs found right now. I have saved your profile and will notify you when new jobs appear! 🔔"
            )
            return ConversationHandler.END

        # 6. Display Results
        await update.message.reply_text(f"Found {len(ranked_jobs)} jobs. Here are the top matches:")

        for job in ranked_jobs[:3]:
            reason = job.get("reasoning", "Best match based on skills.")
            text = (
                f"🚀 *{job['title']}*\n"
                f"🏢 {job['company']}\n"
                f"📍 {job['location']}\n"
                f"💡 _{reason}_\n"
                f"🔗 [Apply Here]({job['link']})"
            )
            await update.message.reply_text(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in handle_resume_file: {e}")
        await update.message.reply_text("An internal error occurred. Please try again.")
    finally:
        # Cleanup
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    return ConversationHandler.END


async def ask_for_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Flow 2: Resume Building -> Ask for Target JD."""
    await update.message.reply_text(
        "To tailor your resume, please paste the **Job Description** you are targeting.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return JOB_DESC_UPLOAD


async def handle_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles Resume Building.
    1. Fetches base resume from DB.
    2. Rewrites it using AI.
    3. Generates PDF.
    """
    user = update.effective_user
    job_desc = update.message.text

    if not job_desc or len(job_desc) < 10:
        await update.message.reply_text(
            "That description looks too short. Please paste the full job details."
        )
        return JOB_DESC_UPLOAD

    await update.message.reply_text("Tailoring your resume... ✍️")

    db = SessionLocal()
    base_resume = ""
    try:
        db_user = crud.get_user_by_telegram_id(db, user.id)
        if not db_user or not db_user.resume:
            await update.message.reply_text(
                "I don't have your base resume yet! Please use 'Job Recommendations' first to upload one."
            )
            return ConversationHandler.END
        base_resume = db_user.resume.text_content
    finally:
        db.close()

    # 1. AI Generation
    new_resume_text = await tailor_resume(base_resume, job_desc)

    if not new_resume_text:
        await update.message.reply_text("Failed to generate resume. Please try again.")
        return ConversationHandler.END

    # 2. PDF Creation
    output_filename = f"Tailored_Resume_{user.id}.pdf"
    if generate_pdf_resume(new_resume_text, output_filename):
        with open(output_filename, "rb") as f:
            await update.message.reply_document(
                document=f, caption="Here is your tailored resume! Good luck. 🍀"
            )
        # Cleanup
        if os.path.exists(output_filename):
            os.remove(output_filename)
    else:
        await update.message.reply_text("Error generating the PDF file.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
