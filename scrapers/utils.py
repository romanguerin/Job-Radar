import re
from urllib.parse import urljoin

from playwright.async_api import Locator


SALARY_PATTERN = re.compile(r"(\d[\d\s.]{2,})")


def parse_salary(value: str | None) -> int | None:
    if not value:
        return None
    match = SALARY_PATTERN.search(value.replace("\u202f", " "))
    if not match:
        return None
    digits = re.sub(r"\D", "", match.group(1))
    if not digits:
        return None
    salary = int(digits)
    if salary < 1000:
        return None
    return salary


def absolute_url(base_url: str, href: str | None) -> str:
    if not href:
        return base_url
    return urljoin(base_url, href)


async def safe_text(locator: Locator, default: str = "") -> str:
    try:
        text = await locator.first.text_content(timeout=1500)
        return " ".join((text or default).split())
    except Exception:
        return default


async def safe_attr(locator: Locator, name: str, default: str = "") -> str:
    try:
        return await locator.first.get_attribute(name, timeout=1500) or default
    except Exception:
        return default
