from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.services import get_active_user, get_users, update_user_preferences
from database.session import get_db


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request,
    user_id: int | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user = get_active_user(db, user_id)
    users = get_users(db)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "request": request,
            "active_page": "settings",
            "user": user,
            "users": users,
        },
    )


@router.post("/settings")
def update_settings(
    user_id: int = Form(...),
    name: str = Form(...),
    categories: str = Form(""),
    locations: str = Form(""),
    keywords: str = Form(""),
    excluded_keywords: str = Form(""),
    minimum_salary: int = Form(0),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    user = get_active_user(db, user_id)
    update_user_preferences(
        db=db,
        user=user,
        name=name,
        categories=categories,
        locations=locations,
        keywords=keywords,
        excluded_keywords=excluded_keywords,
        minimum_salary=minimum_salary,
    )
    return RedirectResponse(f"/settings?user_id={user.id}", status_code=303)
