import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


async def fetch_jobs_from_sources(
    search_keywords: List[str], limit: int = 15
) -> List[Dict[str, Any]]:
    """Fetches live remote jobs using the open Remotive API."""
    if not search_keywords:
        return []

    # FIX: Remotive chokes on too many keywords. We only search the #1 top skill.
    query_string = search_keywords[0]
    url = "https://remotive.com/api/remote-jobs"
    querystring = {"search": query_string, "category": "software-dev"}

    jobs = []
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Querying Remotive for: '{query_string}'")
            response = await client.get(url, params=querystring, timeout=15.0)
            response.raise_for_status()

            data = response.json()
            api_results = data.get("jobs", [])

            for item in api_results[:limit]:
                job_data = {
                    "title": item.get("title", "Unknown Title"),
                    "company": item.get("company_name", "Unknown Company"),
                    "location": f"Remote ({item.get('candidate_required_location', 'Worldwide')})",
                    "link": item.get("url", ""),
                    "source": "Remotive API",
                }
                if job_data["link"]:
                    jobs.append(job_data)

        logger.info(f"Successfully fetched {len(jobs)} jobs from Remotive.")
        return jobs

    except Exception as e:
        logger.error(f"Failed to fetch jobs from Remotive: {e}")
        return []
