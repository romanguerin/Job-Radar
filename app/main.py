from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.scheduler import start_scheduler, stop_scheduler
from database.init_db import init_db, seed_default_users
from database.session import SessionLocal
from routes import dashboard, jobs, saved_jobs, settings


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    init_db()
    db = SessionLocal()
    try:
        seed_default_users(db)
    finally:
        db.close()
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


settings_obj = get_settings()
app = FastAPI(title=settings_obj.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(dashboard.router)
app.include_router(jobs.router)
app.include_router(saved_jobs.router)
app.include_router(settings.router)
