import logging

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class LinkedinScraper(BaseScraper):
    """
    Scraper for LinkedIn.
    Currently a placeholder. LinkedIn scraping is complex and often requires
    Selenium or an official API to avoid immediate IP bans.
    """

    async def search(self, keywords: list[str]) -> list[dict]:
        """Placeholder for LinkedIn search."""
        logger.info("LinkedIn scraper called (Not implemented yet).")
        return []
