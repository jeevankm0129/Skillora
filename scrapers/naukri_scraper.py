from typing import Dict, List

import httpx

from scrapers.base_scraper import BaseScraper


class NaukriScraper(BaseScraper):
    source_name = "Naukri"

    async def fetch_jobs(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        jobs: List[Dict] = []

        query = " ".join(keywords).strip()
        if not query:
            return jobs

        url = "https://www.naukri.com/jobapi/v3/search"
        params = {
            "keyword": query,
            "noOfResults": limit,
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return jobs  # fail safely

        for item in data.get("jobDetails", []) or []:
            jobs.append(
                {
                    "title": (item.get("title") or "").strip(),
                    "company": (item.get("companyName") or "").strip(),
                    "location": (item.get("location") or "").strip(),
                    "link": (item.get("jdURL") or "").strip(),
                    "source": self.source_name,
                }
            )

        return jobs
