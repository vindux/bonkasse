from fastapi import APIRouter, Depends, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession
from pathlib import Path

from ..database import get_db
from ..models import AppConfig
from ..auth import verify_password, create_admin_token, revoke_admin_token

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: DBSession = Depends(get_db)):
    config = db.get(AppConfig, 1)
    if not config or not config.password_hash:
        token = create_admin_token()
        resp = RedirectResponse("/admin/menu-items", status_code=303)
        resp.set_cookie("admin_token", token, httponly=True, samesite="strict")
        return resp
    return templates.TemplateResponse(request, name="admin/login.html", context={})


@router.post("/login")
def login_submit(request: Request, password: str = Form(...), db: DBSession = Depends(get_db)):
    config = db.get(AppConfig, 1)
    if config and config.password_hash:
        if not verify_password(password, config.password_hash):
            return templates.TemplateResponse(request, name="admin/login.html", context={
                "error": "Incorrect password",
            })

    token = create_admin_token()
    resp = RedirectResponse("/admin/menu-items", status_code=303)
    resp.set_cookie("admin_token", token, httponly=True, samesite="strict")
    return resp


@router.get("/back")
def back_to_register(admin_token: str | None = Cookie(default=None)):
    """Return to register and invalidate admin token so password is required next time."""
    if admin_token:
        revoke_admin_token(admin_token)
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("admin_token")
    return resp
