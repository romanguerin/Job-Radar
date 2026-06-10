import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings
from app.services import collect_jobs
from database.session import SessionLocal


logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="UTC")


def run_collection() -> None:
    db = SessionLocal()
    try:
        result = asyncio.run(collect_jobs(db))
        logger.info("Job collection completed: %s", result)
    except Exception:
        logger.exception("Job collection failed")
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    settings = get_settings()
    scheduler.add_job(
        run_collection,
        "interval",
        minutes=settings.scheduler_minutes,
        id="job_collection",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    if settings.scrape_on_startup:
        scheduler.add_job(run_collection, id="startup_collection", replace_existing=True)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
