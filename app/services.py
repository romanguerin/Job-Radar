from datetime import datetime, time
from hashlib import sha256
from typing import Iterable

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.orm import Session

from app.scoring import calculate_match_score, normalize_csv, split_preferences
from models.entities import Job, JobScore, SavedJob, User
from scrapers.base import ScrapedJob
from scrapers.registry import get_scrapers


def job_fingerprint(source: str, url: str, title: str, company: str, location: str) -> str:
    key = "|".join(
        [
            source.strip().lower(),
            url.strip().lower(),
            title.strip().lower(),
            company.strip().lower(),
            location.strip().lower(),
        ]
    )
    return sha256(key.encode("utf-8")).hexdigest()


def get_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


def get_active_user(db: Session, user_id: int | None) -> User:
    if user_id:
        user = db.get(User, user_id)
        if user:
            return user
    return db.scalar(select(User).order_by(User.id))  # type: ignore[return-value]


def update_user_preferences(
    db: Session,
    user: User,
    name: str,
    categories: str,
    locations: str,
    keywords: str,
    excluded_keywords: str,
    minimum_salary: int,
) -> None:
    user.name = name.strip() or user.name
    user.categories = normalize_csv(categories)
    user.locations = normalize_csv(locations)
    user.keywords = normalize_csv(keywords)
    user.excluded_keywords = normalize_csv(excluded_keywords)
    user.minimum_salary = max(0, minimum_salary)
    db.commit()
    recalculate_scores(db)


def search_terms_for_users(users: Iterable[User]) -> list[str]:
    terms: list[str] = []
    for user in users:
        terms.extend(split_preferences(user.categories))
        terms.extend(split_preferences(user.keywords))
    seen: set[str] = set()
    unique_terms: list[str] = []
    for term in terms:
        key = term.lower()
        if key not in seen:
            seen.add(key)
            unique_terms.append(term)
    return unique_terms[:8] or ["python", "marketing"]


def _upsert_job(db: Session, scraped: ScrapedJob) -> tuple[Job, bool]:
    fingerprint = job_fingerprint(
        scraped.source,
        scraped.url,
        scraped.title,
        scraped.company,
        scraped.location,
    )
    existing = db.scalar(select(Job).where(Job.fingerprint == fingerprint))
    if existing:
        return existing, False

    job = Job(
        title=scraped.title[:255],
        company=scraped.company[:255],
        location=scraped.location[:255],
        salary=scraped.salary,
        contract_type=scraped.contract_type[:120],
        category=scraped.category[:120],
        description=scraped.description,
        source=scraped.source[:120],
        url=scraped.url,
        fingerprint=fingerprint,
        date_found=datetime.utcnow(),
    )
    db.add(job)
    db.flush()
    return job, True


def upsert_score(db: Session, job: Job, user: User) -> JobScore:
    result = calculate_match_score(job, user)
    score = db.scalar(
        select(JobScore).where(and_(JobScore.job_id == job.id, JobScore.user_id == user.id))
    )
    if score is None:
        score = JobScore(job_id=job.id, user_id=user.id)
        db.add(score)
    score.score = result.score
    score.reasons = ", ".join(result.reasons)
    score.updated_at = datetime.utcnow()
    return score


def recalculate_scores(db: Session) -> None:
    users = get_users(db)
    jobs = list(db.scalars(select(Job)))
    for job in jobs:
        for user in users:
            upsert_score(db, job, user)
    db.commit()


async def collect_jobs(db: Session) -> dict[str, int]:
    users = get_users(db)
    search_terms = search_terms_for_users(users)
    added = 0
    seen = 0
    errors = 0

    for scraper in get_scrapers():
        try:
            scraped_jobs = await scraper.fetch_jobs(search_terms)
        except Exception:
            errors += 1
            continue
        for scraped in scraped_jobs:
            seen += 1
            if not scraped.title or not scraped.url:
                continue
            job, created = _upsert_job(db, scraped)
            if created:
                added += 1
            for user in users:
                upsert_score(db, job, user)
        db.commit()

    return {"seen": seen, "added": added, "errors": errors}


def dashboard_stats(db: Session, user: User) -> dict[str, object]:
    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    total_jobs = db.scalar(select(func.count(Job.id))) or 0
    jobs_today = db.scalar(select(func.count(Job.id)).where(Job.date_found >= today_start)) or 0
    top_jobs = db.execute(
        select(Job, JobScore)
        .join(JobScore, JobScore.job_id == Job.id)
        .where(JobScore.user_id == user.id)
        .order_by(JobScore.score.desc(), Job.date_found.desc())
        .limit(6)
    ).all()
    recent_jobs = db.execute(
        select(Job, JobScore)
        .join(JobScore, JobScore.job_id == Job.id)
        .where(JobScore.user_id == user.id)
        .order_by(Job.date_found.desc())
        .limit(8)
    ).all()
    return {
        "total_jobs": total_jobs,
        "jobs_today": jobs_today,
        "top_jobs": top_jobs,
        "recent_jobs": recent_jobs,
    }


def filtered_jobs_query(
    user: User,
    category: str | None = None,
    location: str | None = None,
    source: str | None = None,
    min_score: int | None = None,
    sort: str = "score",
) -> Select[tuple[Job, JobScore]]:
    query = (
        select(Job, JobScore)
        .join(JobScore, JobScore.job_id == Job.id)
        .where(JobScore.user_id == user.id)
    )
    if category:
        query = query.where(Job.category.ilike(f"%{category}%"))
    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
    if source:
        query = query.where(Job.source == source)
    if min_score is not None:
        query = query.where(JobScore.score >= min_score)

    if sort == "newest":
        return query.order_by(Job.date_found.desc())
    if sort == "salary":
        return query.order_by(Job.salary.desc().nullslast(), JobScore.score.desc())
    return query.order_by(JobScore.score.desc(), Job.date_found.desc())


def job_filter_values(db: Session) -> dict[str, list[str]]:
    categories = list(db.scalars(select(Job.category).where(Job.category != "").distinct().order_by(Job.category)))
    locations = list(db.scalars(select(Job.location).where(Job.location != "").distinct().order_by(Job.location)))
    sources = list(db.scalars(select(Job.source).distinct().order_by(Job.source)))
    return {"categories": categories, "locations": locations, "sources": sources}


def get_job_with_score(db: Session, job_id: int, user: User) -> tuple[Job, JobScore] | None:
    return db.execute(
        select(Job, JobScore)
        .join(JobScore, JobScore.job_id == Job.id)
        .where(and_(Job.id == job_id, JobScore.user_id == user.id))
    ).first()


def set_job_status(db: Session, user: User, job_id: int, status: str) -> None:
    if status not in {"saved", "applied", "rejected"}:
        return
    saved = db.scalar(
        select(SavedJob).where(and_(SavedJob.user_id == user.id, SavedJob.job_id == job_id))
    )
    if saved is None:
        saved = SavedJob(user_id=user.id, job_id=job_id)
        db.add(saved)
    saved.status = status
    saved.updated_at = datetime.utcnow()
    db.commit()


def saved_jobs(db: Session, user: User, status: str | None = None) -> list[tuple[SavedJob, Job, JobScore]]:
    query = (
        select(SavedJob, Job, JobScore)
        .join(Job, SavedJob.job_id == Job.id)
        .join(JobScore, and_(JobScore.job_id == Job.id, JobScore.user_id == user.id))
        .where(SavedJob.user_id == user.id)
    )
    if status in {"saved", "applied", "rejected"}:
        query = query.where(SavedJob.status == status)
    return list(db.execute(query.order_by(SavedJob.updated_at.desc())).all())


def search_jobs(db: Session, user: User, query_text: str) -> list[tuple[Job, JobScore]]:
    text = f"%{query_text}%"
    return list(
        db.execute(
            select(Job, JobScore)
            .join(JobScore, JobScore.job_id == Job.id)
            .where(
                and_(
                    JobScore.user_id == user.id,
                    or_(
                        Job.title.ilike(text),
                        Job.company.ilike(text),
                        Job.description.ilike(text),
                    ),
                )
            )
            .order_by(JobScore.score.desc())
        ).all()
    )
