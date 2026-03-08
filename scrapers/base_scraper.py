from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseScraper(ABC):
    """
    Abstract Base Class for all job scrapers/APIs.
    Enforces a strict output schema to prevent the aggregator from crashing.
    """

    source_name: str = "unknown"

    @abstractmethod
    async def fetch_jobs(self, keywords: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Must return a list of dictionaries with the following keys:
        - title (str)
        - company (str)
        - location (str)
        - link (str)
        - source (str)
        """
        pass
