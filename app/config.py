from functools import lru_cache
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """Runtime settings loaded from environment variables."""

    app_name: str = "Job Radar"
    database_url: str
    scheduler_minutes: int
    scrape_on_startup: bool
    generic_sources_json: str

    def __init__(self) -> None:
        database_path = BASE_DIR / "database" / "job_radar.db"
        self.database_url = os.getenv(
            "JOB_RADAR_DATABASE_URL",
            f"sqlite:///{database_path}",
        )
        self.scheduler_minutes = int(os.getenv("JOB_RADAR_SCHEDULER_MINUTES", "30"))
        self.scrape_on_startup = os.getenv("JOB_RADAR_SCRAPE_ON_STARTUP", "true").lower() in {
            "1",
            "true",
            "yes",
        }
        self.generic_sources_json = os.getenv("JOB_RADAR_GENERIC_SOURCES", "[]")


@lru_cache
def get_settings() -> Settings:
    return Settings()
