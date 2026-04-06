from fastapi import Depends
from sqlalchemy.orm import Session as DBSession

from .database import get_db
from .models import AppConfig
from .services.printer_service import PrinterService

_printer_service: PrinterService | None = None


def get_printer_service(db: DBSession = Depends(get_db)) -> PrinterService:
    global _printer_service
    if _printer_service is None:
        _printer_service = PrinterService()

    config = db.get(AppConfig, 1)
    if config and config.printer_enabled:
        _printer_service.configure_printer(
            config.printer_type or "usb",
            config.printer_interface or "",
            True,
            config.cash_drawer_enabled,
        )
        _printer_service.set_company_info({
            "company_name": config.company_name or "",
            "company_address": config.company_address or "",
            "company_phone": config.company_phone or "",
            "title": config.title or "",
        })
    else:
        _printer_service.printer_enabled = False

    return _printer_service
