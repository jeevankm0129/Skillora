from typing import Dict, List

import requests

from scrapers.base_scraper import BaseScraper


class NaukriScraper(BaseScraper):
    source_name = "Naukri"

    def fetch_jobs(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        jobs: List[Dict] = []

        query = " ".join(keywords)
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
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return jobs  # fail safely

        for item in data.get("jobDetails", []):
            jobs.append(
                {
                    "title": item.get("title", "").strip(),
                    "company": item.get("companyName", "").strip(),
                    "location": item.get("location", "").strip(),
                    "link": item.get("jdURL", "").strip(),
                    "source": self.source_name,
                }
            )

        return jobs
