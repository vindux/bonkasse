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


@router.post("", response_class=HTMLResponse)
def save_general(
    request: Request,
    title: str = Form(""),
    company_name: str = Form(""),
    company_address: str = Form(""),
    company_phone: str = Form(""),
    company_email: str = Form(""),
    change_enabled: bool = Form(False),
    printer_enabled: bool = Form(False),
    printer_type: str = Form("usb"),
    printer_interface: str = Form(""),
    cash_drawer_enabled: bool = Form(False),
    db: DBSession = Depends(get_db),
):
    config = db.get(AppConfig, 1)
    config.title = title.strip()
    config.company_name = company_name.strip()
    config.company_address = company_address.strip()
    config.company_phone = company_phone.strip()
    config.company_email = company_email.strip()
    config.change_enabled = change_enabled
    config.printer_enabled = printer_enabled
    config.printer_type = printer_type
    config.printer_interface = printer_interface.strip()
    config.cash_drawer_enabled = cash_drawer_enabled
    db.commit()

    return templates.TemplateResponse(request, name="admin/general.html", context={
        "config": config,
        "active_tab": "general",
        "message": "Settings saved successfully.",
        "msg_type": "success",
    })


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
        return templates.TemplateResponse(request, name="admin/general.html", context={
            "config": config,
            "active_tab": "general",
            "message": error,
            "msg_type": "error",
        })

    config.password_hash = hash_password(new_password)
    db.commit()

    return templates.TemplateResponse(request, name="admin/general.html", context={
        "config": config,
        "active_tab": "general",
        "message": "Password updated successfully.",
        "msg_type": "success",
    })


@router.post("/password/remove", response_class=HTMLResponse)
def remove_password(
    request: Request,
    current_password: str = Form(""),
    db: DBSession = Depends(get_db),
):
    config = db.get(AppConfig, 1)

    if config.password_hash:
        if not verify_password(current_password, config.password_hash):
            return templates.TemplateResponse(request, name="admin/general.html", context={
                "config": config,
                "active_tab": "general",
                "message": "Incorrect password.",
                "msg_type": "error",
            })

    config.password_hash = None
    db.commit()

    return templates.TemplateResponse(request, name="admin/general.html", context={
        "config": config,
        "active_tab": "general",
        "message": "Password removed.",
        "msg_type": "success",
    })


@router.post("/printer/test", response_class=HTMLResponse)
def test_printer(
    request: Request,
    db: DBSession = Depends(get_db),
    printer: PrinterService = Depends(get_printer_service),
):
    config = db.get(AppConfig, 1)
    success = printer.test_print()
    return templates.TemplateResponse(request, name="admin/general.html", context={
        "config": config,
        "active_tab": "general",
        "message": "Test print successful!" if success else "Test print failed. Check printer connection.",
        "msg_type": "success" if success else "error",
    })


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
    return templates.TemplateResponse(request, name="admin/general.html", context={
        "config": config,
        "active_tab": "general",
        "message": msg,
        "msg_type": mtype,
    })
