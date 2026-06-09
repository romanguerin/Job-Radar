from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.services import get_active_user, get_users, remove_saved_job, saved_jobs
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


@router.post("/saved/{job_id}/remove")
def remove_saved_offer(
    job_id: int,
    user_id: int = Form(...),
    status: str = Form("all"),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    user = get_active_user(db, user_id)
    remove_saved_job(db, user, job_id)
    suffix = "" if status == "all" else f"&status={status}"
    return RedirectResponse(f"/saved?user_id={user.id}{suffix}", status_code=303)
