from abc import ABC, abstractmethod
from typing import Dict, List


class BaseScraper(ABC):
    source_name: str = "unknown"

    @abstractmethod
    async def fetch_jobs(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        raise NotImplementedError
