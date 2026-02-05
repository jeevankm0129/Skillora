import asyncio
import logging

from scrapers.naukri_scraper import search_naukri

# from scrapers.linkedin_scraper import search_linkedin # Future use

logger = logging.getLogger(__name__)


async def fetch_jobs(keywords: list[str]) -> list[dict]:
    """
    Fetches jobs from all connected sources concurrently.
    Deduplicates results based on Link.
    """
    if not keywords:
        logger.warning("Job fetch called with empty keywords.")
        return []

    logger.info(f"Fetching jobs for keywords: {keywords}")

    # Run scrapers in parallel
    results = await asyncio.gather(
        search_naukri(keywords),
        # search_linkedin(keywords),
        return_exceptions=True,
    )

    all_jobs = []
    seen_links = set()

    for res in results:
        if isinstance(res, list):
            for job in res:
                if job["link"] not in seen_links:
                    all_jobs.append(job)
                    seen_links.add(job["link"])
        else:
            logger.error(f"Scraper error: {res}")

    logger.info(f"Total unique jobs found: {len(all_jobs)}")
    return all_jobs
