from scrapers.base import JobScraper
from scrapers.france_travail import FranceTravailScraper
from scrapers.generic import GenericScraper
from scrapers.indeed import IndeedScraper


def get_scrapers() -> list[JobScraper]:
    return [
        FranceTravailScraper(),
        IndeedScraper(),
        GenericScraper(),
    ]
