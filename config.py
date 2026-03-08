import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ENV = os.getenv("ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# =========================================
# DATABASE
# =========================================
# We enforce aiosqlite for non-blocking database operations
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./skillora.db")
if not DATABASE_URL.startswith("sqlite+aiosqlite") and not DATABASE_URL.startswith(
    "postgresql+asyncpg"
):
    raise RuntimeError("DATABASE_URL must use an async driver (e.g., sqlite+aiosqlite:///...)")

# =========================================
# TELEGRAM & WHATSAPP
# =========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in the .env file")

# Placeholders for future Meta API integration
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "SKILLORA_SECRET_TOKEN_123")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")

# =========================================
# EMAIL / SMTP (For Background Alerts)
# =========================================
ENABLE_EMAIL_NOTIFICATIONS = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

if ENABLE_EMAIL_NOTIFICATIONS and not all([SMTP_SERVER, SMTP_EMAIL, SMTP_PASSWORD]):
    print("WARNING: Email notifications enabled but SMTP credentials are missing.")
