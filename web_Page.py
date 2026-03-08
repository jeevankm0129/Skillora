import logging
import os

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from database import crud
from database.db import get_db_session
from services.ai_service import get_job_recommendations

# Import the exact same AI logic your Telegram bot uses
from utils.llm_helper import extract_skills_locally, extract_text_from_pdf

logger = logging.getLogger(__name__)

# Initialize the router for the web frontend
web_router = APIRouter(tags=["Web UI"])

# Point to the 'frontend' subfolder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# ==========================================
# 1. SERVE STATIC HTML, CSS, & JS
# ==========================================


@web_router.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@web_router.get("/{page}.html")
async def serve_pages(page: str):
    file_path = os.path.join(FRONTEND_DIR, f"{page}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "Page not found"}


@web_router.get("/style.css")
async def serve_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "style.css"))


@web_router.get("/script.js")
async def serve_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "script.js"))


# ==========================================
# 2. WEB API ENDPOINTS
# ==========================================


@web_router.post("/api/recommend-jobs")
async def web_recommend_jobs(resume: UploadFile = File(...)):
    filename = resume.filename or ""

    if not filename.lower().endswith(".pdf"):
        return {"status": "error", "message": "Only PDF files are accepted."}

    file_bytes = await resume.read()
    logger.info(f"🌐 Web UI processing resume: {filename}")

    try:
        # 1. Extract Text (Converting bytes to bytearray for bot compatibility)
        parsed_text = await extract_text_from_pdf(bytearray(file_bytes))
        if not parsed_text:
            return {"status": "error", "message": "Could not extract text from PDF."}

        # 2. Extract Skills
        skills = await extract_skills_locally(parsed_text)
        if not skills:
            return {"status": "error", "message": "No tech skills detected."}

        # 3. Get Job Recommendations
        raw_jobs = await get_job_recommendations(skills=skills, resume_text=parsed_text)

        # 4. Handle Empty Results (Fallback to Email UI)
        if not raw_jobs:
            return {
                "status": "needs_email",
                "message": "No immediate matches found. Enter your email to track live roles.",
            }

        # 5. Format for Web Frontend
        formatted_jobs = []
        for job in raw_jobs:
            formatted_jobs.append(
                {
                    "title": job.get("title", "Tech Role"),
                    "company": job.get("company", "Unknown"),
                    "location": job.get("location", "Remote"),
                    "salary": job.get("salary", "Competitive"),
                    "match": "Top Match",
                    "link": job.get("link", "#"),
                    "reasoning": job.get("reasoning", "Matches your profile."),
                }
            )

        return {"status": "success", "jobs": formatted_jobs}

    except Exception as e:
        logger.error(f"❌ Web API Error: {e}")
        return {"status": "error", "message": "Internal processing error."}


@web_router.post("/api/save-email-alert")
async def save_web_email_alert(email: str = Form(...)):
    """
    Saves the email for tracking using existing CRUD logic.
    """
    try:
        async for db in get_db_session():
            # Using your existing update_user_email logic
            # Since web users don't have a telegram_id, we use a negative ID to distinguish them
            web_user_id = -1
            await crud.get_or_create_user_by_platform_id(db, telegram_id=web_user_id)  #
            await crud.update_user_email(db, email=email, telegram_id=web_user_id)  #
            break

        return {"status": "success", "message": f"Alerts activated for {email}!"}
    except Exception as e:
        logger.error(f"❌ Failed to save web email: {e}")
        return {"status": "error", "message": "Could not save alert."}
