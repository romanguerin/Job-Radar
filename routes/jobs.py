from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.services import (
    filtered_jobs_query,
    get_active_user,
    get_job_with_score,
    get_users,
    job_filter_values,
    search_jobs,
    set_job_status,
)
from database.session import get_db


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/jobs", response_class=HTMLResponse)
def jobs_list(
    request: Request,
    user_id: int | None = None,
    category: str | None = None,
    location: str | None = None,
    source: str | None = None,
    min_score: str | None = None,
    sort: str = "score",
    q: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user = get_active_user(db, user_id)
    users = get_users(db)
    try:
        parsed_min_score = int(min_score) if min_score not in (None, "") else None
    except ValueError:
        parsed_min_score = None
    if q:
        jobs = search_jobs(db, user, q)
    else:
        jobs = list(
            db.execute(
                filtered_jobs_query(
                    user=user,
                    category=category,
                    location=location,
                    source=source,
                    min_score=parsed_min_score,
                    sort=sort,
                )
            ).all()
        )
    return templates.TemplateResponse(
        request,
        "jobs.html",
        {
            "request": request,
            "active_page": "jobs",
            "user": user,
            "users": users,
            "jobs": jobs,
            "filters": {
                "category": category or "",
                "location": location or "",
                "source": source or "",
                "min_score": parsed_min_score if parsed_min_score is not None else "",
                "sort": sort,
                "q": q or "",
            },
            **job_filter_values(db),
        },
    )


@router.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(
    request: Request,
    job_id: int,
    user_id: int | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user = get_active_user(db, user_id)
    users = get_users(db)
    result = get_job_with_score(db, job_id, user)
    if result is None:
        return templates.TemplateResponse(
            request,
            "404.html",
            {"request": request, "user": user, "users": users, "active_page": "jobs"},
            status_code=404,
        )
    job, score = result
    return templates.TemplateResponse(
        request,
        "job_detail.html",
        {
            "request": request,
            "active_page": "jobs",
            "user": user,
            "users": users,
            "job": job,
            "score": score,
        },
    )


@router.post("/jobs/{job_id}/status")
def update_job_status(
    job_id: int,
    user_id: int = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    user = get_active_user(db, user_id)
    set_job_status(db, user, job_id, status)
    return RedirectResponse(f"/jobs/{job_id}?user_id={user.id}", status_code=303)
