import json
import logging
import os
from asyncio import create_task
from typing import cast

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


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_user = cast(TelegramUser, update.effective_user)
    message = cast(Message, update.message)

    db = SessionLocal()
    try:
        db_user = crud.get_user_by_telegram_id(db, tg_user.id)
        if not db_user:
            crud.create_user(db, telegram_id=tg_user.id)
            logger.info(f"New user registered: {tg_user.id}")
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
    message = cast(Message, update.message)
    await message.reply_text(
        "Please upload your resume (PDF or DOCX).",
        reply_markup=ReplyKeyboardRemove(),
    )
    return RESUME_UPLOAD


async def handle_resume_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_user = cast(TelegramUser, update.effective_user)
    message = cast(Message, update.message)

    document = message.document
    if not document:
        await message.reply_text("Please upload a valid document file.")
        return RESUME_UPLOAD

    file_name = document.file_name
    if not file_name:
        await message.reply_text("Uploaded file has no filename. Please try again.")
        return RESUME_UPLOAD

    file_ext = file_name.split(".")[-1].lower()
    if file_ext not in ["pdf", "docx"]:
        await message.reply_text("Only PDF and DOCX files are supported.")
        return RESUME_UPLOAD

    temp_filename = f"temp_{tg_user.id}_{file_name}"

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

        # Store data for background task
        create_task(
            process_resume_background(
                chat_id=message.chat_id,
                resume_text=resume_text,
                context=context,
            )
        )

        # Instant reply (FAST-NOW)
        await message.reply_text(
            "✅ Resume received!\n"
            "🔍 Finding the best job matches for you…\n"
            "⏳ This may take ~15–20 seconds."
        )

        # Run heavy AI in background
        create_task(
            process_resume_background(
                chat_id=message.chat_id,
                resume_text=resume_text,
                context=context,
            )
        )

    except Exception as e:
        logger.error(f"Error handling resume upload: {e}")
        await message.reply_text("An internal error occurred.")
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    return ConversationHandler.END


# =========================
# BACKGROUND JOB PROCESSING
# =========================
async def process_resume_background(
    chat_id: int,
    resume_text: str,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        # 1. Extract skills (slow but safe)
        extracted = await extract_skills_from_resume(resume_text)
        skills = extracted.get("skills", [])[:5]

        if not skills:
            await context.bot.send_message(chat_id, "Could not extract skills from your resume.")
            return

        # 2. Fetch + rank jobs
        jobs = await get_job_recommendations(skills, resume_text)

        if not jobs:
            await context.bot.send_message(chat_id, "No suitable jobs found right now.")
            return

        # 3. Send results
        msg = "🚀 *Top Job Matches for You:*\n\n"
        for job in jobs[:3]:
            msg += (
                f"*{job['title']}*\n"
                f"{job['company']} — {job['location']}\n"
                f"[Apply Here]({job['link']})\n\n"
            )

        await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error(f"Background resume processing failed: {e}")
        await context.bot.send_message(
            chat_id, "❌ Something went wrong while processing your resume."
        )


# =========================
# RESUME BUILDING FLOW
# =========================
async def ask_for_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = cast(Message, update.message)
    await message.reply_text(
        "Please paste the job description you are targeting.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return JOB_DESC_UPLOAD


async def handle_job_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_user = cast(TelegramUser, update.effective_user)
    message = cast(Message, update.message)

    job_desc = message.text
    if not job_desc or len(job_desc) < 10:
        await message.reply_text("Please paste a full job description.")
        return JOB_DESC_UPLOAD

    db = SessionLocal()
    try:
        db_user = crud.get_user_by_telegram_id(db, tg_user.id)
        if not db_user or not db_user.resume:
            await message.reply_text("Please upload your resume first.")
            return ConversationHandler.END

        base_resume = db_user.resume.text_content
    finally:
        db.close()

    new_resume = await tailor_resume(base_resume, job_desc)
    if not new_resume:
        await message.reply_text("Failed to generate resume.")
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
    message = cast(Message, update.message)
    await message.reply_text(
        "Operation cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
