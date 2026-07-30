import logging
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from .database import init_db, SessionLocal
from .models import AppConfig, MenuItem
from .auth import _AdminRedirectException
from .config import MENU_SLOTS


class NoCacheStaticFiles(StaticFiles):
    """Static files that always revalidate.

    Starlette sends ETag/Last-Modified but no Cache-Control, so the kiosk browser
    invents its own freshness window and keeps serving a stale style.css long after
    it changed on disk. "no-cache" means "revalidate before reusing", not "don't
    store" — the ETag still turns an unchanged file into an empty 304, which costs
    nothing over loopback.
    """

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


def create_app() -> FastAPI:
    app = FastAPI(title="Bonkasse", docs_url=None, redoc_url=None)

    @app.exception_handler(_AdminRedirectException)
    async def admin_redirect_handler(request: Request, exc: _AdminRedirectException):
        return RedirectResponse("/admin/login", status_code=303)

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", NoCacheStaticFiles(directory=str(static_dir)), name="static")

    from .routers import register, admin, admin_menu, admin_general, admin_transactions
    app.include_router(register.router)
    app.include_router(admin.router)
    app.include_router(admin_menu.router)
    app.include_router(admin_general.router)
    app.include_router(admin_transactions.router)

    init_db()
    _seed_data()

    return app


def _seed_data():
    db = SessionLocal()
    try:
        if not db.get(AppConfig, 1):
            db.add(AppConfig(id=1))
            db.commit()

        count = db.query(MenuItem).count()
        if count < MENU_SLOTS:
            for i in range(count + 1, MENU_SLOTS + 1):
                db.add(MenuItem(slot_number=i, name="", price=0.0, active=False))
            db.commit()
    finally:
        db.close()
