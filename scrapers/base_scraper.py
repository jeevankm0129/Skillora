from abc import ABC, abstractmethod
from typing import Dict, List


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""

    source_name: str = "unknown"

    @abstractmethod
    def fetch_jobs(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """
        Fetch jobs for given keywords.

        MUST return a list of dicts with keys:
        - title (str)
        - company (str)
        - location (str)
        - link (str)
        - source (str)
        """
        raise NotImplementedError
