from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.services import dashboard_stats, get_active_user, get_users
from database.session import get_db


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, user_id: int | None = None, db: Session = Depends(get_db)) -> HTMLResponse:
    user = get_active_user(db, user_id)
    users = get_users(db)
    stats = dashboard_stats(db, user)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "active_page": "dashboard",
            "user": user,
            "users": users,
            **stats,
        },
    )
