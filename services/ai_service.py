import logging
import re
from typing import Any, Dict, List

from services.job_fetcher import fetch_jobs_from_sources
from utils.llm_helper import extract_skills_locally

logger = logging.getLogger(__name__)


async def extract_skills_from_resume(resume_text: str) -> Dict[str, Any]:
    """Wrapper to maintain the dictionary structure for the rest of the app."""
    skills = await extract_skills_locally(resume_text)
    return {"skills": skills, "roles": [], "seniority": "mid-level"}


def _score_job_semantically(job: Dict[str, Any], user_skills: List[str]) -> int:
    """
    Advanced Token-based scoring.
    Prevents "Java" from matching "JavaScript" using word boundaries.
    """
    title = (job.get("title") or "").lower()
    location = (job.get("location") or "").lower()

    score = 0
    matched_skills = []

    for skill in user_skills:
        sk_lower = skill.lower()

        # \b means "Word Boundary". It ensures exact word matches.
        pattern = r"\b" + re.escape(sk_lower) + r"\b"

        if re.search(pattern, title):
            score += 3  # High value if skill is in the Job Title
            matched_skills.append(skill)
        elif re.search(pattern, location) or sk_lower in (job.get("company") or "").lower():
            score += 1  # Lower value for company/location matches
            matched_skills.append(skill)

    # Save the exact matched skills into the job dictionary for the UI reasoning
    job["matched_skills"] = list(set(matched_skills))
    return score


async def get_job_recommendations(skills: List[str], resume_text: str) -> List[Dict[str, Any]]:
    # 1. Extract skills if not provided
    if not skills:
        extracted = await extract_skills_from_resume(resume_text)
        skills = extracted.get("skills", [])

    if not skills:
        logger.warning("No skills found. Cannot fetch jobs.")
        return []

    # Take top 8 skills to broaden the search API query
    search_keywords = skills[:8]

    # 2. Fetch jobs concurrently from our unified aggregator
    raw_jobs = await fetch_jobs_from_sources(search_keywords, limit=15)

    if not raw_jobs:
        return []

    # 3. Score and Filter
    ranked_jobs = []
    for job in raw_jobs:
        score = _score_job_semantically(job, skills)

        if score > 0:  # Only keep jobs that actually have a semantic match
            job["score"] = score
            job["reasoning"] = f"Matches your skills: {', '.join(job['matched_skills'])}"
            ranked_jobs.append(job)

    # 4. Sort by highest score
    ranked_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)
    return ranked_jobs
