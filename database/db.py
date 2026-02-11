from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

# ===============================
# VALIDATION (CRITICAL)
# ===============================
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. " "Please define DATABASE_URL in your .env file.")

# SQLite requires this flag for multithreading
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# ===============================
# ENGINE & SESSION
# ===============================
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()
