from urllib.parse import quote_plus

from playwright.async_api import async_playwright

from scrapers.base import JobScraper, ScrapedJob, SearchQuery
from scrapers.utils import absolute_url, parse_salary, safe_attr, safe_text


class IndeedScraper(JobScraper):
    source_name = "Indeed"
    base_url = "https://fr.indeed.com"

    async def fetch_jobs(self, search_queries: list[SearchQuery]) -> list[ScrapedJob]:
        jobs: list[ScrapedJob] = []
        queries = search_queries or [SearchQuery("python"), SearchQuery("marketing")]

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for query in queries[:6]:
                    search_url = f"{self.base_url}/jobs?q={quote_plus(query.term)}"
                    if query.location:
                        search_url = f"{search_url}&l={quote_plus(query.location)}"
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
                    cards = page.locator("[data-testid='slider_item'], .job_seen_beacon, .result")
                    count = min(await cards.count(), 15)
                    for index in range(count):
                        card = cards.nth(index)
                        title = await safe_text(card.locator("h2 a span, h2 span, .jobTitle"), query.term.title())
                        company = await safe_text(card.locator("[data-testid='company-name'], .companyName"), "")
                        location = await safe_text(card.locator("[data-testid='text-location'], .companyLocation"), query.location)
                        description = await safe_text(card.locator(".job-snippet, [data-testid='jobsnippet']"), "")
                        salary_text = await safe_text(card.locator(".salary-snippet, [data-testid='attribute_snippet_testid']"), "")
                        contract = await safe_text(card.locator(".metadata, .jobMetaDataGroup"), "")
                        href = await safe_attr(card.locator("h2 a, a"), "href", search_url)

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
