from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.locations import REMOTE_LABEL, is_remote_location


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


@dataclass(frozen=True)
class SearchQuery:
    term: str
    location: str = ""

    @property
    def is_remote(self) -> bool:
        return is_remote_location(self.location)

    @property
    def source_location(self) -> str:
        if self.is_remote:
            return REMOTE_LABEL
        return self.location

    @property
    def label(self) -> str:
        if self.location:
            return f"{self.term} in {self.location}"
        return self.term


class JobScraper(ABC):
    source_name: str

    @abstractmethod
    async def fetch_jobs(self, search_queries: list[SearchQuery]) -> list[ScrapedJob]:
        """Fetch jobs from a source and return normalized job records."""
