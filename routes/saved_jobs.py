from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.services import get_active_user, get_users, saved_jobs
from database.session import get_db


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/saved", response_class=HTMLResponse)
def saved_jobs_page(
    request: Request,
    user_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user = get_active_user(db, user_id)
    users = get_users(db)
    rows = saved_jobs(db, user, status)
    return templates.TemplateResponse(
        request,
        "saved_jobs.html",
        {
            "request": request,
            "active_page": "saved",
            "user": user,
            "users": users,
            "rows": rows,
            "status": status or "all",
        },
    )
