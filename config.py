# =========================================
# ENV LOADING (MUST BE FIRST)
# =========================================
from dotenv import load_dotenv

load_dotenv()

import os

# =========================================
# ENV / APP
# =========================================
ENV = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# =========================================
# DATABASE
# =========================================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required but not set.")

# =========================================
# TELEGRAM
# =========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is required but not set.")

# =========================================
# FEATURE FLAGS
# =========================================
ENABLE_BACKGROUND_JOB_MATCHING = (
    os.getenv("ENABLE_BACKGROUND_JOB_MATCHING", "true").lower() == "true"
)

ENABLE_EMAIL_NOTIFICATIONS = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "false").lower() == "true"

# =========================================
# EMAIL / SMTP
# =========================================
SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

if ENABLE_EMAIL_NOTIFICATIONS:
    missing = []
    if not SMTP_SERVER:
        missing.append("SMTP_SERVER")
    if not SMTP_EMAIL:
        missing.append("SMTP_EMAIL")
    if not SMTP_PASSWORD:
        missing.append("SMTP_PASSWORD")
    if missing:
        raise RuntimeError(f"Email notifications enabled but missing config: {', '.join(missing)}")

# =========================================
# OCR SETTINGS (optional)
# =========================================
# If tesseract isn’t on PATH (Windows), set this in .env:
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
#TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
#OCR_LANG = os.getenv("OCR_LANG", "eng")

# =========================================
# Skill dictionary path
# =========================================
SKILLS_FILE_PATH = os.getenv("SKILLS_FILE_PATH", "data/skills.txt")
