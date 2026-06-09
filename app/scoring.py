from dataclasses import dataclass

from models.entities import Job, User


@dataclass(frozen=True)
class ScoreResult:
    score: int
    reasons: list[str]


def split_preferences(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_csv(value: str | None) -> str:
    return ", ".join(split_preferences(value))


def _contains_any(haystack: str, needles: list[str]) -> bool:
    haystack_lower = haystack.lower()
    return any(needle.lower() in haystack_lower for needle in needles)


def calculate_match_score(job: Job, user: User) -> ScoreResult:
    categories = split_preferences(user.categories)
    locations = split_preferences(user.locations)
    keywords = split_preferences(user.keywords)
    excluded_keywords = split_preferences(user.excluded_keywords)

    searchable_text = " ".join(
        [
            job.title or "",
            job.company or "",
            job.category or "",
            job.description or "",
            job.contract_type or "",
        ]
    )
    score = 20
    reasons: list[str] = ["Base relevance"]

    if categories and _contains_any(f"{job.category} {job.title} {job.description}", categories):
        score += 20
        reasons.append("Category match")

    if locations and _contains_any(job.location or "", locations):
        score += 20
        reasons.append("Location match")

    if job.salary is not None and job.salary >= user.minimum_salary:
        score += 20
        reasons.append("Salary above minimum")

    if keywords and _contains_any(searchable_text, keywords):
        score += 20
        reasons.append("Preferred keyword found")

    if excluded_keywords and _contains_any(searchable_text, excluded_keywords):
        score -= 20
        reasons.append("Excluded keyword found")

    return ScoreResult(score=max(0, min(score, 100)), reasons=reasons)
