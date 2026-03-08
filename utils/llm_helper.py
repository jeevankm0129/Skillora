import io
import logging
import os
import re
from typing import List

import pdfplumber
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

_cached_skills: List[str] = []


def _load_skills_from_file() -> List[str]:
    """Caches the skills.txt file in memory for instant access."""
    global _cached_skills
    if _cached_skills:
        return _cached_skills

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skills_file_path = os.path.join(base_dir, "data", "skills.txt")

    try:
        with open(skills_file_path, "r", encoding="utf-8") as f:
            _cached_skills = [line.strip().lower() for line in f if line.strip()]
        logger.info(f"Successfully loaded {len(_cached_skills)} skills from data/skills.txt")
    except FileNotFoundError:
        logger.error(f"CRITICAL: Could not find {skills_file_path}.")
        _cached_skills = ["python", "java", "javascript", "react", "sql"]

    return _cached_skills


async def extract_text_from_pdf(pdf_bytes: bytearray) -> str:
    """
    Physically rips the text out of the uploaded PDF file using pdfplumber.
    """
    text = ""
    try:
        # pdfplumber reads the raw byte stream directly from Telegram
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        logger.info("Successfully extracted text from actual PDF.")
        return text
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        return ""


def _llm_semantic_reasoning_placeholder(text: str):
    """
    PLACEHOLDER: The heavy Google LLM has been removed to maximize speed.
    This function remains as an architectural stub for future API integration.
    """
    pass


async def extract_skills_locally(resume_text: str) -> List[str]:
    """
    Lightning-fast rule-based and fuzzy extraction.
    """
    if not resume_text:
        return []

    skills_to_check = _load_skills_from_file()
    found_skills = set()
    text_lower = resume_text.lower()

    # 1. Lightning-Fast Exact Match (Handles 90% of cases perfectly)
    for skill in skills_to_check:
        # \b ensures we match exact words (e.g., 'java' won't trigger on 'javascript')
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.add(skill.title())

    # 2. RapidFuzz Pass (Catches typos like "pyhton" or "javascrip")
    # We extract all unique alphanumeric words from the resume to compare
    unique_resume_words = list(set(re.findall(r"\b[a-z0-9+#.-]+\b", text_lower)))

    for skill in skills_to_check:
        if skill.title() in found_skills:
            continue  # Skip if we already found it exactly

        # Only fuzzy match single words to keep it incredibly fast
        if " " not in skill:
            # WRatio is highly optimized for comparing strings of different lengths
            match = process.extractOne(
                skill, unique_resume_words, scorer=fuzz.WRatio, score_cutoff=88
            )
            if match:
                found_skills.add(skill.title())

    final_skills = list(found_skills)
    logger.info(f"RapidFuzz extracted skills: {final_skills}")
    return final_skills
