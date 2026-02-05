import json
import logging
import re

from utils.llm_helper import call_gemini

logger = logging.getLogger(__name__)


def clean_json_response(response_text: str) -> str:
    """Helper to extract clean JSON string from LLM response."""
    if not response_text:
        return ""

    # Try to find JSON inside ```json ... ``` blocks
    match = re.search(r"```json\s*(\{.*?\})\s*```", response_text, re.DOTALL)
    if match:
        return match.group(1)

    # Try to find JSON inside plain ``` ... ``` blocks
    match = re.search(r"```\s*(\{.*?\})\s*```", response_text, re.DOTALL)
    if match:
        return match.group(1)

    # Fallback: Find first { and last }
    start = response_text.find("{")
    end = response_text.rfind("}")
    if start != -1 and end != -1:
        return response_text[start : end + 1]

    return response_text


async def extract_skills_from_resume(resume_text: str) -> dict | None:
    """
    Extracts structured data from resume text.
    Returns a dict with 'skills' (list) and 'search_keywords' (list of top 3-5 hard skills).
    """
    # Truncate to save tokens (Gemini 1.5 Flash has a large context, but safe limit is good)
    truncated_text = resume_text[:15000]

    prompt = f"""
    Analyze the following resume text.
    1. Extract a comprehensive list of all professional 'skills'.
    2. Identify the top 3-5 most critical technical 'search_keywords' for finding a relevant job (e.g., "Python", "React", "Data Analysis").

    Return ONLY a valid JSON object. Do not add markdown formatting.

    Structure:
    {{
        "skills": ["Skill1", "Skill2", ...],
        "search_keywords": ["Keyword1", "Keyword2", "Keyword3"]
    }}

    Resume Text:
    ---
    {truncated_text}
    ---
    """

    response_text = await call_gemini(prompt)
    if not response_text:
        return None

    try:
        json_str = clean_json_response(response_text)
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode skills JSON: {e}")
        return None


async def rank_jobs(jobs: list[dict], resume_text: str) -> list[dict]:
    """
    Uses AI to rank a list of jobs against the resume.
    Adds a 'reasoning' field to the relevant jobs.
    """
    if not jobs:
        return []

    # Optimize payload: Only send Title, Company, and ID to LLM
    job_summaries = [
        {"id": i, "title": j["title"], "company": j["company"], "location": j["location"]}
        for i, j in enumerate(jobs)
    ]

    prompt = f"""
    You are a career advisor. Rank the following jobs for a candidate.

    Candidate Resume Summary:
    {resume_text[:3000]}...

    Available Jobs:
    {json.dumps(job_summaries)}

    Task:
    1. Select the top 3 matches.
    2. Provide a short 1-sentence reasoning for each.

    Return ONLY JSON:
    {{
        "ranked_jobs": [
            {{ "id": 0, "reasoning": "..." }},
            {{ "id": 2, "reasoning": "..." }}
        ]
    }}
    """

    response_text = await call_gemini(prompt)
    if not response_text:
        return jobs[:3]  # Fallback: return top 3 unranked

    ranked_results = []
    try:
        json_str = clean_json_response(response_text)
        data = json.loads(json_str)
        ranked_items = data.get("ranked_jobs", [])

        for item in ranked_items:
            idx = item.get("id")
            if idx is not None and isinstance(idx, int) and 0 <= idx < len(jobs):
                job = jobs[idx]
                job["reasoning"] = item.get("reasoning", "AI Matched")
                ranked_results.append(job)

    except Exception as e:
        logger.error(f"Error ranking jobs: {e}")
        return jobs[:3]

    return ranked_results


async def tailor_resume(base_resume_text: str, job_description: str) -> str | None:
    """Rewrites a resume to match a specific job description."""
    prompt = f"""
    You are an expert Resume Writer.
    Rewrite the Base Resume to highlight skills relevant to the Target Job.

    - Keep factual history (dates, companies) unchanged.
    - Optimize the Summary and Bullet points.
    - Use Markdown formatting (**Bold** for headers).

    Base Resume:
    ---
    {base_resume_text[:5000]}
    ---

    Target Job:
    ---
    {job_description[:3000]}
    ---

    Return only the resume text.
    """
    return await call_gemini(prompt)
