import asyncio
import logging
import urllib.parse

import aiohttp
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class NaukriScraper(BaseScraper):
    """Scraper for Naukri.com using Async I/O."""

    BASE_URL = "https://www.naukri.com/"

    async def search(self, keywords: list[str]) -> list[dict]:
        """Searches Naukri for jobs matching the keywords asynchronously."""
        if not keywords:
            return []

        search_query = "-".join([k.replace(" ", "-") for k in keywords])
        formatted_query = urllib.parse.quote(search_query)
        # Naukri URL structure for keyword search
        search_url = f"{self.BASE_URL}{formatted_query}-jobs"

        jobs = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        logger.warning(f"Naukri returned status {response.status}")
                        return []

                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Robust finding of job containers
                    job_listings = soup.find_all("div", class_="srp-jobtuple-wrapper")

                    for job in job_listings:
                        try:
                            title_elem = job.find("a", class_="title")
                            company_elem = job.find("a", class_="subTitle")
                            loc_elem = job.find("span", class_="locWdth")

                            # FIX: Check if title exists first
                            if not title_elem:
                                continue

                            title = title_elem.text.strip()
                            link = title_elem.get("href")

                            # Check if we actually got a link
                            if not link:
                                continue

                            company = company_elem.text.strip() if company_elem else "Unknown"
                            location = loc_elem.text.strip() if loc_elem else "Remote/Unknown"

                            jobs.append(
                                {
                                    "title": title,
                                    "company": company,
                                    "location": location,
                                    "link": link,
                                    "source": "Naukri",
                                }
                            )
                        except AttributeError:
                            continue

        except Exception as e:
            logger.error(f"Error scraping Naukri: {e}")

        return jobs


async def search_naukri(keywords: list[str]) -> list[dict]:
    """Helper function to run the scraper."""
    scraper = NaukriScraper()
    return await scraper.search(keywords)
