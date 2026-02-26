from __future__ import annotations

from typing import Any, Dict, List

from services.job_fetcher import fetch_jobs_from_sources
from utils.skill_extractor import extract_skills_rule_based


async def extract_skills_from_resume(resume_text: str) -> Dict[str, Any]:
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
    # 1) Extract skills if not provided
    if not skills:
        data = await extract_skills_from_resume(resume_text)
        skills = data.get("skills", []) if isinstance(data, dict) else []

    skills = [s.strip() for s in skills if isinstance(s, str) and s.strip()]

    # keep query small for better Naukri relevance
    skills = skills[:5]

    if not skills:
        return []

    # 2) Fetch jobs (ASYNC)
    raw_jobs = await fetch_jobs_from_sources(skills, limit=10)
    if not raw_jobs:
        return []

    # 3) Score + sort
    ranked = []
    for job in raw_jobs:
        sc = _score_job(job, skills)
        job_out = dict(job)
        job_out["score"] = sc
        job_out["reasoning"] = (
            f"Matched skills: {', '.join([s for s in skills if s.lower() in (job.get('title','').lower())])}"
        )
        ranked.append(job_out)

    ranked.sort(key=lambda x: x.get("score", 0), reverse=True)
    return ranked


async def tailor_resume(resume_text: str, job_description: str) -> str:
    """
    No-AI placeholder: returns original resume text.
    (You can add formatting improvements later.)
    """
    return resume_text.strip()


async def rank_jobs(resume_text: str, jobs: list) -> list:
    return await get_job_recommendations(skills=[], resume_text=resume_text)
