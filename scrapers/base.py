from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapedJob:
    title: str
    company: str
    location: str
    salary: int | None
    contract_type: str
    category: str
    description: str
    source: str
    url: str


class JobScraper(ABC):
    source_name: str

    @abstractmethod
    async def fetch_jobs(self, search_terms: list[str]) -> list[ScrapedJob]:
        """Fetch jobs from a source and return normalized job records."""
