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
# LLM / AI (OLLAMA OR OPENAI SAFE)
# =========================================
# These are optional when using Ollama,
# but defined so imports NEVER fail.

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

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
# These are OPTIONAL unless email notifications are enabled.
# Defaults prevent ImportError.

SMTP_SERVER = os.getenv("SMTP_SERVER", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# =========================================
# VALIDATION (ONLY WHEN ENABLED)
# =========================================
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
