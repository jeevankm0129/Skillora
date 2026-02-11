import json
from typing import Dict, List

from services.job_fetcher import fetch_jobs_from_sources
from utils.llm_helper import call_llm


# ---------------------------
# SKILL EXTRACTION
# ---------------------------
async def extract_skills_from_resume(resume_text: str) -> Dict:
    prompt = f"""
You are an expert resume analyzer.

Extract:
- core technical skills
- roles
- seniority

Return STRICT JSON:
{{
  "skills": [string],
  "roles": [string],
  "seniority": "junior | mid | senior"
}}

Resume:
{resume_text}
"""

    response = await call_llm(prompt, expect_json=True)
    return response


# ---------------------------
# JOB RECOMMENDATION (REAL AI)
# ---------------------------
async def get_job_recommendations(skills: list, resume_text: str):
    """
    FAST + BALANCED job recommendations using local LLM.
    """

    # 1. If skills not provided, extract ONCE
    if not skills:
        data = await extract_skills_from_resume(resume_text)
        skills = data.get("skills", [])[:5]  # cap skills

    if not skills:
        return []

    # 2. Fetch FEW jobs only
    raw_jobs = fetch_jobs_from_sources(skills, limit=6)
    if not raw_jobs:
        return []

    # 3. VERY SHORT ranking prompt
    prompt = f"""
Rank these jobs for a candidate with skills: {', '.join(skills)}.

Return JSON ONLY:
[
  {{
    "title": str,
    "company": str,
    "location": str,
    "link": str,
    "source": str,
    "score": int
  }}
]

Jobs:
{raw_jobs}
"""

    ranked = await call_llm(prompt, expect_json=True)

    return sorted(ranked, key=lambda x: x.get("score", 0), reverse=True)


# ---------------------------
# RESUME TAILORING
# ---------------------------
async def tailor_resume(resume_text: str, job_description: str) -> str:
    prompt = f"""
You are an expert resume writer.

Rewrite the resume to strongly match the job description.
Do NOT add fake experience.

Resume:
{resume_text}

Job Description:
{job_description}
"""

    return await call_llm(prompt)


async def rank_jobs(resume_text: str, jobs: list) -> list:
    """
    Backward compatibility wrapper for notification_service.
    """
    # Reuse existing AI ranking logic
    skills_data = await extract_skills_from_resume(resume_text)
    skills = skills_data.get("skills", [])

    ranked_jobs = await get_job_recommendations(skills, resume_text)
    return ranked_jobs
