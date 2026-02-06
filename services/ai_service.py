import json
import logging
from typing import Dict, List, Optional

from services.job_fetcher import fetch_jobs
from utils.llm_helper import call_llm

logger = logging.getLogger(__name__)


# =========================
# Helpers
# =========================


def _safe_json_load(raw: Optional[str]) -> Optional[dict]:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error("LLM returned invalid JSON.")
        return None


# =========================
# 1. Skill Extraction
# =========================


async def extract_skills_from_resume(resume_text: str) -> Optional[Dict[str, List[str]]]:
    prompt = f"""
You are an expert technical recruiter.

From the resume text below:
1. Extract ALL professional skills.
2. Select the top 3–5 HARD SKILLS useful for job search.

Return ONLY valid JSON:
{{
  "skills": ["Skill1", "Skill2"],
  "search_keywords": ["Keyword1", "Keyword2"]
}}

Resume:
---
{resume_text[:12000]}
---
"""

    response = await call_llm(prompt)
    data = _safe_json_load(response)

    if not data:
        return None

    if not isinstance(data.get("skills"), list):
        return None

    if not isinstance(data.get("search_keywords"), list):
        return None

    return {
        "skills": list(dict.fromkeys(map(str, data["skills"]))),
        "search_keywords": list(dict.fromkeys(map(str, data["search_keywords"]))),
    }


# =========================
# 2. Job Ranking
# =========================


async def rank_jobs(jobs: List[dict], resume_text: str) -> List[dict]:
    if not jobs:
        return []

    job_payload = [
        {"id": i, "title": j["title"], "company": j["company"], "location": j["location"]}
        for i, j in enumerate(jobs)
    ]

    prompt = f"""
You are a senior career advisor.

Candidate resume:
{resume_text[:3000]}

Jobs:
{json.dumps(job_payload)}

Pick the BEST 3 jobs and explain why.

Return ONLY JSON:
{{
  "ranked_jobs": [
    {{ "id": 0, "reasoning": "..." }}
  ]
}}
"""

    response = await call_llm(prompt)
    data = _safe_json_load(response)

    if not data or "ranked_jobs" not in data:
        return []

    ranked = []
    for item in data["ranked_jobs"]:
        idx = item.get("id")
        if isinstance(idx, int) and 0 <= idx < len(jobs):
            job = jobs[idx]
            job["reasoning"] = str(item.get("reasoning", "AI matched"))
            ranked.append(job)

    return ranked


# =========================
# 3. ✅ MISSING FUNCTION (FIXED)
# =========================


async def get_job_recommendations(
    skills: List[str],
    resume_text: str,
) -> List[dict]:
    """
    FULL AI FLOW:
    1. Fetch jobs from scrapers
    2. Rank them using LLM reasoning
    """

    if not skills:
        logger.warning("No skills provided for job recommendations.")
        return []

    # 1. Fetch raw jobs
    jobs = await fetch_jobs(skills)
    if not jobs:
        return []

    # 2. Rank using AI
    ranked_jobs = await rank_jobs(jobs, resume_text)
    return ranked_jobs


# =========================
# 4. Resume Tailoring
# =========================


async def tailor_resume(base_resume_text: str, job_description: str) -> Optional[str]:
    prompt = f"""
You are a professional resume writer.

Rules:
- Do NOT invent experience
- Do NOT change dates or companies
- Emphasize relevance only
- Use Markdown headers

Base Resume:
---
{base_resume_text[:5000]}
---

Target Job:
---
{job_description[:3000]}
---

Return ONLY the rewritten resume.
"""

    response = await call_llm(prompt)
    return response.strip() if response else None
