import logging
from typing import cast

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler

# UPGRADE: Corrected imports to match your actual file structure exactly
from database import crud
from database.db import get_db_session
from services.ai_service import get_job_recommendations

# Change your llm_helper import to this:
from utils.llm_helper import extract_skills_locally, extract_text_from_pdf

# Import for the resume builder flow
from utils.resume_generator import generate_ats_resume_pdf

logger = logging.getLogger(__name__)

# Define Conversation States
CHOOSING, RESUME_UPLOAD, EMAIL_INPUT = range(3)
(
    ASK_NAME,
    ASK_CONTACT,
    ASK_EDUCATION,
    ASK_SKILLS,
    ASK_PROJECTS,
    ASK_INTERNSHIPS,
    ASK_EXPERIENCE,
    ASK_EXAMS,
    ASK_EXTRACURRICULAR,
) = range(3, 12)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command and recognizes deep links from the website.
    """
    # Strict Guard Clause for the IDE type-checker
    if not update.message or context.user_data is None:
        return ConversationHandler.END

    # --- NEW: Check for Deep Link Argument from Website ---
    # This handles the 'https://t.me/YourBot?start=build_resume' link
    args = context.args
    if args and args[0] == "build_resume":
        await update.message.reply_text(
            "Hi! Welcome to Skillora. Let's start with building your resume! 🚀\n\n"
            "First, what is your **Full Name**?",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_NAME
    # ------------------------------------------------------

    reply_keyboard = [["Job Recommendations", "Build Resume"]]

    # UPGRADE: Using the correct get_db_session generator
    async for db in get_db_session():
        await crud.get_or_create_user_by_platform_id(db, telegram_id=update.message.chat_id)
        logger.info(f"Telegram user registered/verified: {update.message.chat_id}")
        break

    await update.message.reply_text(
        "Welcome to Skillora! 🚀\n\nWhat would you like to do today?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True
        ),
    )
    return CHOOSING


async def ask_for_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END

    choice = update.message.text or ""

    if choice == "Job Recommendations":
        await update.message.reply_text(
            "Great! Please upload your existing resume (PDF format).",
            reply_markup=ReplyKeyboardRemove(),
        )
        return RESUME_UPLOAD

    elif choice == "Build Resume":
        await update.message.reply_text(
            "Let's build a perfect ATS resume! I will ask you for your details step by step.\n\n"
            "First, what is your **Full Name**?",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_NAME


# ==========================================
# RESUME BUILDER FLOW
# ==========================================
async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["name"] = update.message.text or ""
    await update.message.reply_text(
        "Got it. Please provide your **Contact Details** (Email & Phone Number):",
        parse_mode="Markdown",
    )
    return ASK_CONTACT


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["contact"] = update.message.text or ""
    await update.message.reply_text(
        "What is your **Educational Background**? (e.g., B.Tech in CSE, 2026)",
        parse_mode="Markdown",
    )
    return ASK_EDUCATION


async def handle_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["education"] = update.message.text or ""
    await update.message.reply_text(
        "List your **Technical Skills** (comma-separated):", parse_mode="Markdown"
    )
    return ASK_SKILLS


async def handle_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["skills"] = update.message.text or ""
    await update.message.reply_text(
        "Describe your **Projects** (Keep it to 15-20 words per project):", parse_mode="Markdown"
    )
    return ASK_PROJECTS


async def handle_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["projects"] = update.message.text or ""
    await update.message.reply_text(
        "Do you have any **Internships**? (If none, just reply 'None')", parse_mode="Markdown"
    )
    return ASK_INTERNSHIPS


async def handle_internships(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["internships"] = update.message.text or ""
    await update.message.reply_text(
        "Any past **Full-Time Experience**? (If none, reply 'None')", parse_mode="Markdown"
    )
    return ASK_EXPERIENCE


async def handle_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["experience"] = update.message.text or ""
    await update.message.reply_text(
        "Any **Competitive Exams** cracked or scores? (If none, reply 'None')",
        parse_mode="Markdown",
    )
    return ASK_EXAMS


async def handle_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["exams"] = update.message.text or ""
    await update.message.reply_text(
        "Finally, list any **Extracurricular Activities** or soft skills:", parse_mode="Markdown"
    )
    return ASK_EXTRACURRICULAR


async def build_and_send_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["extracurricular"] = update.message.text or ""

    await update.message.reply_text(
        "Awesome! Generating your ATS-friendly text resume now... 📄 Please wait."
    )

    pdf_buffer = generate_ats_resume_pdf(context.user_data)

    if pdf_buffer:
        file_name = f"{context.user_data.get('name', 'User').replace(' ', '_')}_Resume.pdf"
        await update.message.reply_document(document=pdf_buffer, filename=file_name)
        await update.message.reply_text(
            "Here is your fresh ATS Resume! Type /start if you want to search for jobs now."
        )
    else:
        await update.message.reply_text("Sorry, something went wrong while formatting the PDF.")

    context.user_data.clear()
    return ConversationHandler.END


# ==========================================
# JOB RECOMMENDATION FLOW
# ==========================================
async def handle_resume_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END

    document = update.message.document
    if not document:
        await update.message.reply_text("Please upload a valid file.")
        return ConversationHandler.END

    await update.message.reply_text("📄 Downloading and reading your resume... Please wait.")

    telegram_file = await context.bot.get_file(document.file_id)
    pdf_bytes = await telegram_file.download_as_bytearray()

    parsed_text = await extract_text_from_pdf(pdf_bytes)

    if not parsed_text:
        await update.message.reply_text(
            "I couldn't read any text from that PDF. Is it an image-based scan?"
        )
        return ConversationHandler.END

    context.user_data["parsed_text"] = parsed_text

    await update.message.reply_text(
        "To enable background job tracking, please reply with your Email Address:"
    )
    return EMAIL_INPUT


async def handle_email_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END

    email = update.message.text or ""
    telegram_id = update.message.chat_id
    parsed_text = str(context.user_data.get("parsed_text", ""))

    async for db in get_db_session():
        await crud.update_user_email(db, email=email, telegram_id=telegram_id)
        await crud.save_resume_text(db, text_content=parsed_text, telegram_id=telegram_id)
        await crud.enable_background_tracking(db, telegram_id=telegram_id)
        break

    await update.message.reply_text("📧 Email saved! Analyzing your skills now...")

    skills = await extract_skills_locally(parsed_text)

    if not skills:
        await update.message.reply_text(
            "Sorry, I couldn't extract any specific tech skills from your resume."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"🎯 **Skills Found:** {', '.join(skills)}\n\nFetching live jobs...", parse_mode="Markdown"
    )

    raw_jobs = await get_job_recommendations(skills=skills, resume_text=parsed_text)

    if not raw_jobs:
        await update.message.reply_text(
            "I couldn't find any live jobs matching your skills right now. Try again later!"
        )
    else:
        job_message = "🎯 **Top Job Matches for You:**\n\n"
        for idx, job in enumerate(raw_jobs[:3], 1):
            job_message += f"*{idx}. {job['title']}*\n"
            job_message += f"🏢 **Company:** {job['company']}\n"
            job_message += f"📍 **Location:** {job['location']}\n"
            job_message += f"💡 **Why:** {job.get('reasoning', 'Matches your profile')}\n"
            job_message += f"🔗 [Apply Here]({job['link']})\n\n"

        await update.message.reply_text(
            job_message, parse_mode="Markdown", disable_web_page_preview=True
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    await update.message.reply_text(
        "Operation cancelled. Type /start to begin again.", reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END
