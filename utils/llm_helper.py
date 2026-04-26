"""
utils/llm_helper.py
-------------------
Utility functions for:
  - Extracting raw text from PDF bytes (async, non-blocking)
  - Matching skills from resume text using exact + fuzzy logic
  - Polishing project descriptions into ATS-friendly bullet points
"""

import io
import logging
import os
import re
from asyncio import to_thread
from pathlib import Path
from typing import List

import pdfplumber
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Resolves to  <project_root>/data/skills.txt  regardless of working directory
_SKILLS_FILE = Path(__file__).resolve().parent.parent / "data" / "skills.txt"

# Module-level cache — populated once on first call, read-only thereafter
_SKILLS_CACHE: List[str] = []

_FUZZY_SCORE_CUTOFF = 88  # RapidFuzz WRatio threshold for typo correction


# ---------------------------------------------------------------------------
# Skills loader
# ---------------------------------------------------------------------------

def _load_skills() -> List[str]:
    """
    Reads skills.txt into memory on first call; returns the cached list
    on every subsequent call.  Thread-safe for reads (list is immutable
    after population).
    """
    global _SKILLS_CACHE

    if _SKILLS_CACHE:
        return _SKILLS_CACHE

    try:
        with _SKILLS_FILE.open("r", encoding="utf-8") as fh:
            _SKILLS_CACHE = [line.strip().lower() for line in fh if line.strip()]
        logger.info(f"Loaded {len(_SKILLS_CACHE)} skills from {_SKILLS_FILE}")
    except FileNotFoundError:
        logger.error(f"skills.txt not found at {_SKILLS_FILE}. Using minimal fallback.")
        _SKILLS_CACHE = ["python", "java", "javascript", "react", "sql"]

    return _SKILLS_CACHE


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def _extract_text_sync(pdf_bytes: bytearray) -> str:
    """
    Synchronous pdfplumber extraction.
    Called via asyncio.to_thread — never runs on the event loop directly.
    """
    parts: List[str] = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
    except Exception as e:
        logger.error(f"pdfplumber failed to parse PDF: {e}", exc_info=True)
        return ""

    return "\n".join(parts)


async def extract_text_from_pdf(pdf_bytes: bytearray) -> str:
    """
    Async wrapper: offloads the blocking pdfplumber call to a thread pool
    so the Telegram event loop is never stalled during PDF parsing.
    """
    text = await to_thread(_extract_text_sync, pdf_bytes)
    if text:
        logger.info("Successfully extracted text from PDF.")
    else:
        logger.warning("PDF extraction returned empty text.")
    return text


# ---------------------------------------------------------------------------
# Skill extraction
# ---------------------------------------------------------------------------

async def extract_skills_locally(resume_text: str) -> List[str]:
    """
    Two-pass skill extraction:

    Pass 1 — Exact word-boundary match (fast, handles 90 %+ of cases).
              Uses \\b so 'java' never triggers on 'javascript'.

    Pass 2 — RapidFuzz fuzzy match on single-word skills only
              (catches typos like 'pyhton', 'javascrip').

    Returns a de-duplicated list of Title-cased skill names.
    """
    if not resume_text or not resume_text.strip():
        return []

    skills_master = _load_skills()
    text_lower = resume_text.lower()
    found: set[str] = set()

    # Pass 1: exact match with word boundaries
    for skill in skills_master:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.add(skill.title())

    # Pass 2: fuzzy match for single-word skills not already found
    resume_tokens = list(set(re.findall(r"\b[a-z0-9+#.\-]+\b", text_lower)))

    for skill in skills_master:
        if skill.title() in found:
            continue
        if " " in skill:
            # Multi-word skills are handled reliably by exact match only
            continue
        match = process.extractOne(
            skill,
            resume_tokens,
            scorer=fuzz.WRatio,
            score_cutoff=_FUZZY_SCORE_CUTOFF,
        )
        if match:
            found.add(skill.title())

    result = sorted(found)  # Sorted for deterministic output
    logger.info(f"Extracted {len(result)} skill(s): {result}")
    return result


# ---------------------------------------------------------------------------
# Project description polisher
# ---------------------------------------------------------------------------

def polish_project_description(raw_text: str) -> str:
    """
    Transforms raw user-typed project descriptions into ATS-friendly
    impact bullet points.

    Transformations applied per line:
      - Strips leading/trailing whitespace
      - Replaces weak verbs with stronger action verbs
      - Prepends a bullet character if not already present
    """
    if not raw_text or not raw_text.strip():
        return ""

    _VERB_MAP = {
        "built":  "Engineered",
        "made":   "Developed",
        "used":   "Leveraged",
        "worked": "Collaborated on",
        "helped": "Contributed to",
        "did":    "Executed",
        "wrote":  "Authored",
        "fixed":  "Resolved",
        "added":  "Implemented",
        "tested": "Validated",
    }

    polished_lines: List[str] = []

    for line in raw_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        # Apply verb substitutions (case-insensitive, whole-word only)
        for weak, strong in _VERB_MAP.items():
            stripped = re.sub(
                r"\b" + re.escape(weak) + r"\b",
                strong,
                stripped,
                flags=re.IGNORECASE,
            )

        # Add bullet if not already present
        if not stripped.startswith("•"):
            stripped = f"• {stripped}"

        polished_lines.append(stripped)

    return "\n".join(polished_lines)
