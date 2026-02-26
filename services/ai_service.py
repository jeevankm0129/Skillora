from __future__ import annotations

from typing import Any, Dict, List

from services.job_fetcher import fetch_jobs_from_sources
from utils.skill_extractor import extract_skills_rule_based


def _normalize_skill_inputs(skills: List[str]) -> List[str]:
    """Normalize incoming skill list and drop empty values."""
    return [skill.strip() for skill in skills if isinstance(skill, str) and skill.strip()]


async def extract_skills_from_resume(resume_text: str) -> Dict[str, Any]:
    """Extract resume signals using the current rule-based extractor."""
    skills = extract_skills_rule_based(resume_text)
    return {"skills": skills, "roles": [], "seniority": "junior"}


def _score_job(job: Dict[str, Any], skills: List[str]) -> int:
    """
    Simple rule-based scoring:
    +2 if skill appears in title
    +1 if skill appears in company/location
    """
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    location = (job.get("location") or "").lower()

    score = 0
    for sk in skills:
        s = sk.lower()
        if not s:
            continue
        if s in title:
            score += 2
        elif s in company or s in location:
            score += 1

    return score


async def get_job_recommendations(skills: List[str], resume_text: str) -> List[Dict[str, Any]]:
    """Fetch and rank jobs against user skills while preserving existing behavior."""
    # 1) Extract skills if not provided
    if not skills:
        data = await extract_skills_from_resume(resume_text)
        skills = data.get("skills", []) if isinstance(data, dict) else []

    skills = _normalize_skill_inputs(skills)

    # keep query small for better Naukri relevance
    skills = skills[:5]

    if not skills:
        return []

    # 2) Fetch jobs (ASYNC)
    raw_jobs = await fetch_jobs_from_sources(skills, limit=10)
    if not raw_jobs:
        return []

    # 3) Score + sort
    ranked_jobs: List[Dict[str, Any]] = []
    for job in raw_jobs:
        score = _score_job(job, skills)
        ranked_job = dict(job)
        ranked_job["score"] = score
        ranked_job["reasoning"] = (
            f"Matched skills: {', '.join([s for s in skills if s.lower() in (job.get('title','').lower())])}"
        )
        ranked_jobs.append(ranked_job)

    ranked_jobs.sort(key=lambda item: item.get("score", 0), reverse=True)
    return ranked_jobs


async def tailor_resume(resume_text: str, job_description: str) -> str:
    """
    No-AI placeholder: returns original resume text.
    (You can add formatting improvements later.)
    """
    return resume_text.strip()


async def rank_jobs(resume_text: str, jobs: list) -> list:
    return await get_job_recommendations(skills=[], resume_text=resume_text)
