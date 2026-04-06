from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession
from pathlib import Path

from ..database import get_db
from ..models import AppConfig
from ..auth import require_admin, hash_password, verify_password
from ..dependencies import get_printer_service
from ..services.printer_service import PrinterService

router = APIRouter(prefix="/admin/general", dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("", response_class=HTMLResponse)
def general_page(request: Request, db: DBSession = Depends(get_db)):
    config = db.get(AppConfig, 1)
    return templates.TemplateResponse(request, name="admin/general.html", context={
        "config": config,
        "active_tab": "general",
    })


def _general_response(request: Request, config, message: str, msg_type: str = "success"):
    return templates.TemplateResponse(request, name="admin/general.html", context={
        "config": config,
        "active_tab": "general",
        "message": message,
        "msg_type": msg_type,
    })


@router.post("/event", response_class=HTMLResponse)
def save_event(
    request: Request,
    title: str = Form(""),
    db: DBSession = Depends(get_db),
):
    config = db.get(AppConfig, 1)
    config.title = title.strip()
    db.commit()
    return _general_response(request, config, "Event settings saved.")


@router.post("/business", response_class=HTMLResponse)
def save_business(
    request: Request,
    company_name: str = Form(""),
    company_address: str = Form(""),
    company_phone: str = Form(""),
    company_email: str = Form(""),
    db: DBSession = Depends(get_db),
):
    config = db.get(AppConfig, 1)
    config.company_name = company_name.strip()
    config.company_address = company_address.strip()
    config.company_phone = company_phone.strip()
    config.company_email = company_email.strip()
    db.commit()
    return _general_response(request, config, "Business info saved.")


@router.post("/change", response_class=HTMLResponse)
def save_change(
    request: Request,
    change_enabled: bool = Form(False),
    db: DBSession = Depends(get_db),
):
    config = db.get(AppConfig, 1)
    config.change_enabled = change_enabled
    db.commit()
    return _general_response(request, config, "Change settings saved.")


@router.post("/printer", response_class=HTMLResponse)
def save_printer(
    request: Request,
    printer_enabled: bool = Form(False),
    printer_type: str = Form("usb"),
    printer_interface: str = Form(""),
    cash_drawer_enabled: bool = Form(False),
    db: DBSession = Depends(get_db),
):
    config = db.get(AppConfig, 1)
    config.printer_enabled = printer_enabled
    config.printer_type = printer_type
    config.printer_interface = printer_interface.strip()
    config.cash_drawer_enabled = cash_drawer_enabled
    db.commit()
    return _general_response(request, config, "Printer settings saved.")


@router.post("/password", response_class=HTMLResponse)
def set_password(
    request: Request,
    current_password: str = Form(""),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
    db: DBSession = Depends(get_db),
):
    config = db.get(AppConfig, 1)
    error = None

    if config.password_hash:
        if not verify_password(current_password, config.password_hash):
            error = "Current password is incorrect."

    if not error and new_password != confirm_password:
        error = "New passwords do not match."

    if not error and len(new_password) < 1:
        error = "Password cannot be empty."

    if error:
        return _general_response(request, config, error, "error")

    config.password_hash = hash_password(new_password)
    db.commit()
    return _general_response(request, config, "Password updated successfully.")


@router.post("/password/remove", response_class=HTMLResponse)
def remove_password(
    request: Request,
    current_password: str = Form(""),
    db: DBSession = Depends(get_db),
):
    config = db.get(AppConfig, 1)

    if config.password_hash:
        if not verify_password(current_password, config.password_hash):
            return _general_response(request, config, "Incorrect password.", "error")

    config.password_hash = None
    db.commit()
    return _general_response(request, config, "Password removed.")


@router.post("/printer/test", response_class=HTMLResponse)
def test_printer(
    request: Request,
    db: DBSession = Depends(get_db),
    printer: PrinterService = Depends(get_printer_service),
):
    config = db.get(AppConfig, 1)
    success = printer.test_print()
    msg = "Test print successful!" if success else "Test print failed. Check printer connection."
    return _general_response(request, config, msg, "success" if success else "error")


@router.post("/printer/test-drawer", response_class=HTMLResponse)
def test_drawer(
    request: Request,
    db: DBSession = Depends(get_db),
    printer: PrinterService = Depends(get_printer_service),
):
    config = db.get(AppConfig, 1)
    if printer.is_printer_ready():
        printer._open_cash_drawer()
        msg, mtype = "Cash drawer command sent.", "success"
    else:
        msg, mtype = "Printer not ready.", "error"
    return _general_response(request, config, msg, mtype)
