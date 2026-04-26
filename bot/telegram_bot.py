import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler

from database import crud
from database.db import get_db_context
from services.ai_service import get_job_recommendations
from utils.llm_helper import (
    extract_skills_locally,
    extract_text_from_pdf,
    polish_project_description,
)
from utils.resume_generator import generate_ats_resume_pdf

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conversation States
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start handler.
    - Deep-link /start build_resume  → jumps into the builder flow.
    - Default                         → shows the main menu keyboard.
    """
    if not update.message or context.user_data is None:
        return ConversationHandler.END

    async with get_db_context() as db:
        await crud.get_or_create_user_by_platform_id(
            db, telegram_id=update.message.chat_id
        )

    args = context.args or []
    if args and args[0] == "build_resume":
        await update.message.reply_text(
            "Let's build your professional ATS resume.\n\nWhat is your *Full Name*?",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ASK_NAME

    reply_keyboard = [["Job Recommendations", "Build Resume"]]
    await update.message.reply_text(
        "Welcome to *Skillora*! What would you like to do?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return CHOOSING


# ---------------------------------------------------------------------------
# CHOOSING state handlers
# ---------------------------------------------------------------------------

async def handle_job_rec_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User selected 'Job Recommendations' — prompt for resume upload."""
    if not update.message or context.user_data is None:
        return ConversationHandler.END

    await update.message.reply_text(
        "Please upload your *resume as a PDF* and I'll find the best jobs for you. 📄",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return RESUME_UPLOAD


async def handle_build_resume_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User selected 'Build Resume' — kick off the guided builder."""
    if not update.message or context.user_data is None:
        return ConversationHandler.END

    await update.message.reply_text(
        "Let's build your professional ATS resume.\n\nWhat is your *Full Name*?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_NAME


# ---------------------------------------------------------------------------
# Resume Builder Flow
# ---------------------------------------------------------------------------

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["name"] = (update.message.text or "").strip() or "User"
    await update.message.reply_text(
        "Please provide your *Contact Details* (email, phone, and any profile links):",
        parse_mode="Markdown",
    )
    return ASK_CONTACT


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["contact"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "What is your *Educational Background*? (Degree, College, Year)",
        parse_mode="Markdown",
    )
    return ASK_EDUCATION


async def handle_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["education"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "List your *Technical Skills* (comma-separated):",
        parse_mode="Markdown",
    )
    return ASK_SKILLS


async def handle_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["skills"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "Describe your *Projects*.\n\nFocus on the problem you solved and the impact/result:",
        parse_mode="Markdown",
    )
    return ASK_PROJECTS


async def handle_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    raw = (update.message.text or "").strip()
    context.user_data["projects"] = polish_project_description(raw)
    await update.message.reply_text(
        "Any *Internships*? Describe them, or reply *None* to skip:",
        parse_mode="Markdown",
    )
    return ASK_INTERNSHIPS


async def handle_internships(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["internships"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "Any *Full-Time Work Experience*? Or reply *None* to skip:",
        parse_mode="Markdown",
    )
    return ASK_EXPERIENCE


async def handle_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["experience"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "Any *Competitive Exams* (JEE, GATE, GRE…)? Or reply *None* to skip:",
        parse_mode="Markdown",
    )
    return ASK_EXAMS


async def handle_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END
    context.user_data["exams"] = (update.message.text or "").strip()
    await update.message.reply_text(
        "List your *Achievements & Extracurricular Activities*:",
        parse_mode="Markdown",
    )
    return ASK_EXTRACURRICULAR


async def build_and_send_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or context.user_data is None:
        return ConversationHandler.END

    context.user_data["extracurricular"] = (update.message.text or "").strip()
    await update.message.reply_text("Generating your professional ATS resume… ⏳")

    pdf_buffer = generate_ats_resume_pdf(context.user_data)

    if pdf_buffer:
        safe_name = (
            context.user_data.get("name", "User")
            .replace(" ", "_")
            .replace("/", "_")
        )
        filename = f"{safe_name}_Resume.pdf"
        await update.message.reply_document(document=pdf_buffer, filename=filename)
        await update.message.reply_text(
            "✅ Your resume is ready! Type /start to use Skillora again."
        )
    else:
        await update.message.reply_text(
            "❌ Something went wrong generating the PDF. Please try again with /start."
        )

    context.user_data.clear()
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Job Recommendation Flow
# ---------------------------------------------------------------------------

async def handle_resume_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives the uploaded PDF, extracts text, asks for email."""
    if not update.message or context.user_data is None:
        return ConversationHandler.END

    document = update.message.document
    if not document:
        await update.message.reply_text(
            "⚠️ I didn't receive a file. Please upload your resume as a PDF."
        )
        return RESUME_UPLOAD

    mime = document.mime_type or ""
    if mime not in ("application/pdf", "application/octet-stream") and not (
        document.file_name or ""
    ).lower().endswith(".pdf"):
        await update.message.reply_text(
            "⚠️ Please upload a *PDF* file only.", parse_mode="Markdown"
        )
        return RESUME_UPLOAD

    await update.message.reply_text("📄 Reading your resume… please wait.")

    try:
        telegram_file = await context.bot.get_file(document.file_id)
        pdf_bytes = await telegram_file.download_as_bytearray()
    except Exception as e:
        logger.error(f"Failed to download Telegram file: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Failed to download your file. Please try again."
        )
        return RESUME_UPLOAD

    parsed_text = await extract_text_from_pdf(pdf_bytes)

    if not parsed_text or not parsed_text.strip():
        await update.message.reply_text(
            "⚠️ I couldn't extract text from that PDF. "
            "It may be image-based (scanned). Please try a text-based PDF."
        )
        return RESUME_UPLOAD

    context.user_data["parsed_text"] = parsed_text

    await update.message.reply_text(
        "✅ Resume received!\n\n"
        "To enable background job tracking and email alerts, "
        "please reply with your *Email Address*:",
        parse_mode="Markdown",
    )
    return EMAIL_INPUT


async def handle_email_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Saves email + resume + activates tracking in ONE atomic DB transaction,
    then extracts skills and fetches job recommendations.
    """
    if not update.message or context.user_data is None:
        return ConversationHandler.END

    email = (update.message.text or "").strip()
    telegram_id = update.message.chat_id
    parsed_text = str(context.user_data.get("parsed_text", ""))

    if not email or "@" not in email:
        await update.message.reply_text(
            "⚠️ That doesn't look like a valid email. Please try again:"
        )
        return EMAIL_INPUT

    try:
        async with get_db_context() as db:
            await crud.save_user_resume_and_activate(
                db,
                email=email,
                resume_text=parsed_text,
                telegram_id=telegram_id,
            )
    except Exception as e:
        logger.error(f"DB error saving user data: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ A database error occurred. Please try again with /start."
        )
        context.user_data.clear()
        return ConversationHandler.END

    await update.message.reply_text("📧 Email saved! Analysing your skills now… 🔍")

    skills = await extract_skills_locally(parsed_text)

    if not skills:
        await update.message.reply_text(
            "⚠️ I couldn't extract specific tech skills from your resume. "
            "Please ensure your resume clearly lists technologies you know."
        )
        context.user_data.clear()
        return ConversationHandler.END

    await update.message.reply_text(
        f"🎯 *Skills found:* {', '.join(skills)}\n\nFetching live jobs… ⏳",
        parse_mode="Markdown",
    )

    raw_jobs = await get_job_recommendations(skills=skills, resume_text=parsed_text)

    if not raw_jobs:
        await update.message.reply_text(
            "😕 No live jobs matched your skills right now. "
            "I'll keep checking every 2 hours and email you when something turns up!"
        )
    else:
        job_message = "🎯 *Top Job Matches For You:*\n\n"
        for idx, job in enumerate(raw_jobs[:3], 1):
            job_message += (
                f"*{idx}. {job.get('title', 'Unknown Role')}*\n"
                f"🏢 *Company:* {job.get('company', 'N/A')}\n"
                f"📍 *Location:* {job.get('location', 'N/A')}\n"
                f"💡 *Why:* {job.get('reasoning', 'Matches your profile')}\n"
                f"🔗 [Apply Here]({job.get('link', '')})\n\n"
            )
        await update.message.reply_text(
            job_message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )

    await update.message.reply_text(
        "✅ Done! I'll email you whenever new matching jobs appear. Type /start to run again."
    )

    context.user_data.clear()
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return ConversationHandler.END
    await update.message.reply_text(
        "Operation cancelled. Type /start to begin again.",
        reply_markup=ReplyKeyboardRemove(),
    )
    if context.user_data:
        context.user_data.clear()
    return ConversationHandler.END
