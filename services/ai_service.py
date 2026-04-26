import json
import logging
import os
import re
from typing import Any, Dict, List

from services.job_fetcher import fetch_jobs_from_sources
from utils.llm_helper import extract_skills_locally

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock job fallback
# ---------------------------------------------------------------------------

def _load_mock_jobs() -> List[Dict[str, Any]]:
    """
    Loads mock_jobs.json as a fallback when the live API returns nothing.
    Resolves the path relative to this file so it works regardless of cwd.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mock_path = os.path.join(base_dir, "data", "mock_jobs.json")
    try:
        with open(mock_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"mock_jobs.json not found at {mock_path}. No fallback available.")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse mock_jobs.json: {e}")
        return []


# ---------------------------------------------------------------------------
# Semantic scorer
# ---------------------------------------------------------------------------

def _score_job_semantically(job: Dict[str, Any], user_skills: List[str]) -> int:
    """
    Token-based scoring using word boundaries to prevent false matches
    (e.g. 'Java' matching 'JavaScript').

    Scoring weights:
      +3  skill appears in job title
      +2  skill appears in job description
      +1  skill appears in company name or location
    """
    title       = (job.get("title")       or "").lower()
    description = (job.get("description") or "").lower()
    company     = (job.get("company")     or "").lower()
    location    = (job.get("location")    or "").lower()

    score = 0
    matched_skills: list[str] = []

    for skill in user_skills:
        sk_lower = skill.lower()
        pattern = r"\b" + re.escape(sk_lower) + r"\b"

        if re.search(pattern, title):
            score += 3
            matched_skills.append(skill)
        elif re.search(pattern, description):
            score += 2
            matched_skills.append(skill)
        elif re.search(pattern, company) or re.search(pattern, location):
            score += 1
            matched_skills.append(skill)

    job["matched_skills"] = list(set(matched_skills))
    return score


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def extract_skills_from_resume(resume_text: str) -> Dict[str, Any]:
    """Wrapper that keeps the dict structure expected by the rest of the app."""
    skills = await extract_skills_locally(resume_text)
    return {"skills": skills, "roles": [], "seniority": "mid-level"}


async def get_job_recommendations(
    skills: List[str], resume_text: str
) -> List[Dict[str, Any]]:
    """
    Full pipeline:
      1. Extract skills if not provided.
      2. Fetch live jobs from Remotive.
      3. Fall back to mock_jobs.json if the API returns nothing.
      4. Score + filter + sort.
    """
    # 1. Skill extraction
    if not skills:
        extracted = await extract_skills_from_resume(resume_text)
        skills = extracted.get("skills", [])

    if not skills:
        logger.warning("No skills found — cannot fetch or score jobs.")
        return []

    search_keywords = skills[:8]

    # 2. Live fetch
    raw_jobs = await fetch_jobs_from_sources(search_keywords, limit=20)

    # 3. Fallback
    if not raw_jobs:
        logger.info("Live API returned no results — using mock jobs as fallback.")
        raw_jobs = _load_mock_jobs()

    if not raw_jobs:
        return []

    # 4. Score, filter (score > 0), sort
    ranked_jobs: List[Dict[str, Any]] = []
    for job in raw_jobs:
        score = _score_job_semantically(job, skills)
        if score > 0:
            job["score"] = score
            matched = job.get("matched_skills", [])
            job["reasoning"] = (
                f"Matches your skills: {', '.join(matched)}"
                if matched
                else "Matches your profile"
            )
            ranked_jobs.append(job)

    ranked_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)
    logger.info(f"Returning {len(ranked_jobs)} ranked job(s) to caller.")
    return ranked_jobs
