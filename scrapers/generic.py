import json
from typing import Any
from urllib.parse import quote_plus

from playwright.async_api import async_playwright

from app.config import get_settings
from scrapers.base import JobScraper, ScrapedJob, SearchQuery
from scrapers.utils import absolute_url, parse_salary, safe_attr, safe_text


class GenericScraper(JobScraper):
    source_name = "Generic"

    def _sources(self) -> list[dict[str, Any]]:
        try:
            sources = json.loads(get_settings().generic_sources_json)
        except json.JSONDecodeError:
            return []
        if not isinstance(sources, list):
            return []
        return [source for source in sources if isinstance(source, dict) and source.get("url")]

    def _source_urls(self, source: dict[str, Any], search_queries: list[SearchQuery]) -> list[tuple[str, SearchQuery | None]]:
        url = str(source["url"])
        if "{term}" not in url and "{location}" not in url and "{raw_term}" not in url and "{raw_location}" not in url:
            return [(url, None)]

        queries = search_queries or [SearchQuery("")]
        urls: list[tuple[str, SearchQuery | None]] = []
        for query in queries[:8]:
            urls.append(
                (
                    url.format(
                        term=quote_plus(query.term),
                        location=quote_plus(query.location),
                        raw_term=query.term,
                        raw_location=query.location,
                    ),
                    query,
                )
            )
        return urls

    async def fetch_jobs(self, search_queries: list[SearchQuery]) -> list[ScrapedJob]:
        jobs: list[ScrapedJob] = []
        sources = self._sources()
        if not sources:
            return jobs

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                for source in sources:
                    selectors = source.get("selectors", {})
                    if not isinstance(selectors, dict):
                        selectors = {}

                    for url, query in self._source_urls(source, search_queries):
                        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        cards = page.locator(selectors.get("card", "article, .job, .job-card, .result"))
                        count = min(await cards.count(), int(source.get("limit", 20)))
                        for index in range(count):
                            card = cards.nth(index)
                            title = await safe_text(card.locator(selectors.get("title", "h2, h3, .title")), "Untitled job")
                            company = await safe_text(card.locator(selectors.get("company", ".company")), "")
                            location = await safe_text(
                                card.locator(selectors.get("location", ".location")),
                                query.location if query else "",
                            )
                            salary_text = await safe_text(card.locator(selectors.get("salary", ".salary")), "")
                            contract = await safe_text(card.locator(selectors.get("contract", ".contract")), "")
                            description = await safe_text(card.locator(selectors.get("description", "p, .description")), "")
                            href = await safe_attr(card.locator(selectors.get("link", "a")), "href", url)

                            jobs.append(
                                ScrapedJob(
                                    title=title,
                                    company=company,
                                    location=location,
                                    salary=parse_salary(salary_text),
                                    contract_type=contract,
                                    category=str(source.get("category") or (query.term if query else "")),
                                    description=description,
                                    source=str(source.get("name", self.source_name)),
                                    url=absolute_url(url, href),
                                )
                            )
            finally:
                await browser.close()

        return jobs
