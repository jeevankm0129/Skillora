from typing import Dict, List

from scrapers.naukri_scraper import NaukriScraper


def fetch_jobs_from_sources(keywords: List[str], limit: int = 20) -> List[Dict]:
    """
    Fetch raw jobs from all enabled scrapers.
    """
    scrapers = [
        NaukriScraper(),
    ]

    all_jobs: List[Dict] = []

    for scraper in scrapers:
        try:
            jobs = scraper.fetch_jobs(keywords, limit)
            all_jobs.extend(jobs)
        except Exception:
            continue  # isolate scraper failures

    return deduplicate_jobs(all_jobs)


def deduplicate_jobs(jobs: List[Dict]) -> List[Dict]:
    seen = set()
    unique = []

    for job in jobs:
        key = (job.get("title"), job.get("company"), job.get("link"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)

    return unique
