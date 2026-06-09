from urllib.parse import quote_plus

from playwright.async_api import async_playwright

from scrapers.base import JobScraper, ScrapedJob, SearchQuery
from scrapers.utils import absolute_url, parse_salary, safe_attr, safe_text


class FranceTravailScraper(JobScraper):
    source_name = "France Travail"
    base_url = "https://candidat.francetravail.fr"

    async def fetch_jobs(self, search_queries: list[SearchQuery]) -> list[ScrapedJob]:
        jobs: list[ScrapedJob] = []
        queries = search_queries or [SearchQuery("python"), SearchQuery("marketing")]

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for query in queries[:6]:
                    search_phrase = f"{query.term} {query.location}".strip()
                    search_url = f"{self.base_url}/offres/recherche?motsCles={quote_plus(search_phrase)}"
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                    cards = page.locator("article, .result, .media, [data-cy='search-result']")
                    count = min(await cards.count(), 15)
                    for index in range(count):
                        card = cards.nth(index)
                        title = await safe_text(card.locator("h2, h3, .t4, [data-cy='job-title']"), query.term.title())
                        company = await safe_text(card.locator(".subtext, .company, [data-cy='company']"), "")
                        location = await safe_text(card.locator(".location, [data-cy='job-location']"), query.location)
                        description = await safe_text(card.locator("p, .description"), "")
                        contract = await safe_text(card.locator(".contract, [data-cy='contract-type']"), "")
                        salary_text = await safe_text(card.locator(".salary, [data-cy='salary']"), "")
                        href = await safe_attr(card.locator("a"), "href", search_url)

                        jobs.append(
                            ScrapedJob(
                                title=title,
                                company=company,
                                location=location,
                                salary=parse_salary(salary_text),
                                contract_type=contract,
                                category=query.term,
                                description=description,
                                source=self.source_name,
                                url=absolute_url(self.base_url, href),
                            )
                        )
            finally:
                await browser.close()

        return jobs
