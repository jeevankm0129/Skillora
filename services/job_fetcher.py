import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
REQUEST_TIMEOUT = 15.0


async def fetch_jobs_from_sources(
    search_keywords: List[str], limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Fetches remote jobs from the public Remotive API.

    Only the first (strongest) keyword is used as the search query because
    Remotive does not rank multi-keyword results reliably.

    Returns an empty list on any network or API failure so callers can
    fall back gracefully (e.g. to mock_jobs.json).
    """
    if not search_keywords:
        logger.warning("fetch_jobs_from_sources called with no keywords — skipping.")
        return []

    query = search_keywords[0]
    params = {"search": query, "category": "software-dev"}

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            logger.info(f"Querying Remotive API with keyword: '{query}'")
            response = await client.get(REMOTIVE_URL, params=params)
            response.raise_for_status()

        data = response.json()
        api_results: List[Dict[str, Any]] = data.get("jobs", [])

        jobs: List[Dict[str, Any]] = []
        for item in api_results[:limit]:
            link = item.get("url", "")
            if not link:
                continue  # Skip entries with no apply URL

            jobs.append(
                {
                    "title":       item.get("title", "Unknown Title"),
                    "company":     item.get("company_name", "Unknown Company"),
                    "location":    f"Remote ({item.get('candidate_required_location', 'Worldwide')})",
                    "link":        link,
                    "description": item.get("description", ""),  # FIX: expose for scoring
                    "source":      "Remotive API",
                }
            )

        logger.info(f"Fetched {len(jobs)} job(s) from Remotive.")
        return jobs

    except httpx.TimeoutException:
        logger.error("Remotive API request timed out.")
        return []
    except httpx.HTTPStatusError as e:
        logger.error(f"Remotive API returned HTTP {e.response.status_code}.")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching from Remotive: {e}", exc_info=True)
        return []
