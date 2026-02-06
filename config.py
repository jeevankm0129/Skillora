import os

# ===============================
# ENVIRONMENT
# ===============================

ENV = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ===============================
# DATABASE
# ===============================

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required but not set.")


# ===============================
# LLM / AI CONFIG
# ===============================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # Optional (local/self-hosted)

AI_ENABLED = bool(OPENAI_API_KEY)

if not AI_ENABLED:
    raise RuntimeError("OPENAI_API_KEY is missing. AI features cannot start.")


# ===============================
# EMAIL
# ===============================

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

EMAIL_ENABLED = all([SMTP_SERVER, SMTP_EMAIL, SMTP_PASSWORD])


# ===============================
# TELEGRAM
# ===============================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# ===============================
# FEATURE FLAGS
# ===============================

ENABLE_EMAIL_NOTIFICATIONS = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() == "true"

ENABLE_BACKGROUND_JOB_MATCHING = (
    os.getenv("ENABLE_BACKGROUND_JOB_MATCHING", "true").lower() == "true"
)
