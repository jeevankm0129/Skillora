import asyncio
from typing import Dict, List

from scrapers.naukri_scraper import NaukriScraper


async def fetch_jobs_from_sources(keywords: List[str], limit: int = 20) -> List[Dict]:
    scrapers = [
        NaukriScraper(),
    ]

    tasks = [scraper.fetch_jobs(keywords, limit) for scraper in scrapers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[Dict] = []
    for result in results:
        if isinstance(result, list):
            all_jobs.extend(result)

    return deduplicate_jobs(all_jobs)


def deduplicate_jobs(jobs: List[Dict]) -> List[Dict]:
    seen = set()
    unique: List[Dict] = []

    for job in jobs:
        key = (job.get("title"), job.get("company"), job.get("link"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)

    return unique
