from fastapi import Depends
from sqlalchemy.orm import Session as DBSession

from .database import get_db
from .models import AppConfig
from .services.printer_service import PrinterService

_printer_service: PrinterService | None = None
# Signature of the printer/company config last applied. We only (re)open the
# hardware connection when this changes — opening a fresh USB/Win32 handle on
# every request leaks handles and can eventually lock the device over a long
# event.
_printer_sig: tuple | None = None


def get_printer_service(db: DBSession = Depends(get_db)) -> PrinterService:
    global _printer_service, _printer_sig
    if _printer_service is None:
        _printer_service = PrinterService()

    config = db.get(AppConfig, 1)
    sig = (
        bool(config.printer_enabled),
        config.printer_type or "usb",
        config.printer_interface or "",
        bool(config.cash_drawer_enabled),
        config.company_name or "",
        config.company_address or "",
        config.company_phone or "",
        config.title or "",
    ) if config else None

    if sig != _printer_sig:
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
            _printer_service.close()
            _printer_service.printer_enabled = False
        _printer_sig = sig

    return _printer_service
