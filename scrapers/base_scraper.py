from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""

    @abstractmethod
    async def search(self, keywords: list[str]) -> list[dict]:
        """
        Searches for jobs based on a list of keywords.

        Args:
            keywords: A list of search terms.

        Returns:
            A list of dictionaries, where each dictionary represents a job posting.
            Required keys: 'title', 'company', 'location', 'link', 'source'.
        """
        pass
