import json
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession
from pathlib import Path
from datetime import datetime
import io

from ..database import get_db
from ..models import MenuItem, AppConfig
from ..auth import require_admin
from ..config import MENU_SLOTS

router = APIRouter(prefix="/admin/menu-items", dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("", response_class=HTMLResponse)
def menu_items_page(request: Request, db: DBSession = Depends(get_db)):
    items = db.query(MenuItem).order_by(MenuItem.slot_number).all()
    config = db.get(AppConfig, 1)
    return templates.TemplateResponse(request, name="admin/menu_items.html", context={
        "menu_items": items,
        "config": config,
        "active_tab": "menu-items",
    })


@router.get("/{item_id}/edit", response_class=HTMLResponse)
def edit_item_form(item_id: int, request: Request, db: DBSession = Depends(get_db)):
    item = db.get(MenuItem, item_id)
    if not item:
        return HTMLResponse("Item not found", status_code=404)
    return templates.TemplateResponse(request, name="admin/menu_item_form.html", context={
        "item": item,
    })


@router.post("/{item_id}", response_class=HTMLResponse)
def save_item(
    item_id: int,
    request: Request,
    name: str = Form(""),
    price: float = Form(0.0),
    vat_rate: float = Form(0.0),
    print_bon: bool = Form(False),
    active: bool = Form(False),
    db: DBSession = Depends(get_db),
):
    item = db.get(MenuItem, item_id)
    if not item:
        return HTMLResponse("Item not found", status_code=404)

    item.name = name.strip()
    item.price = max(0.0, price)
    item.vat_rate = vat_rate
    item.print_bon = print_bon
    item.active = active if item.name else False
    db.commit()

    return HTMLResponse(status_code=204)


@router.get("/export/json")
def export_json(db: DBSession = Depends(get_db)):
    items = db.query(MenuItem).order_by(MenuItem.slot_number).all()
    export_data = {
        "version": "1.0",
        "export_type": "menu_items",
        "timestamp": datetime.now().isoformat(),
        "menu_items": [
            {
                "id": item.id,
                "slot_number": item.slot_number,
                "name": item.name,
                "price": item.price,
                "vat_rate": item.vat_rate,
                "print_bon": item.print_bon,
                "active": item.active,
            }
            for item in items
        ],
    }
    content = json.dumps(export_data, indent=2, ensure_ascii=False)
    filename = f"bonkasse_menu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import/json", response_class=HTMLResponse)
async def import_json(request: Request, file: UploadFile = File(...), db: DBSession = Depends(get_db)):
    try:
        content = await file.read()
        data = json.loads(content)

        if data.get("export_type") != "menu_items" or "menu_items" not in data:
            raise ValueError("Invalid menu items export file")

        menu_data = data["menu_items"]
        if not isinstance(menu_data, list):
            raise ValueError("menu_items must be a list")

        # Validate each item before modifying the database
        for i, item_data in enumerate(menu_data):
            if not isinstance(item_data, dict):
                raise ValueError(f"Item {i + 1} is not a valid object")
            price = float(item_data.get("price", 0.0))
            if price < 0:
                raise ValueError(f"Item {i + 1} has a negative price")

        # Clear and re-insert
        db.query(MenuItem).delete()
        db.flush()

        for i, item_data in enumerate(menu_data):
            vat = float(item_data.get("vat_rate", 7.0))
            if vat not in (7.0, 19.0):
                vat = 7.0
            db.add(MenuItem(
                slot_number=item_data.get("slot_number", i + 1),
                name=str(item_data.get("name", "")),
                price=max(0.0, float(item_data.get("price", 0.0))),
                vat_rate=vat,
                print_bon=bool(item_data.get("print_bon", item_data.get("print_receipt", True))),
                active=bool(item_data.get("active", True)),
            ))

        # Ensure we have all slots
        count = len(menu_data)
        for i in range(count + 1, MENU_SLOTS + 1):
            db.add(MenuItem(slot_number=i, name="", price=0.0, active=False))

        db.commit()
        message = f"Imported {len(menu_data)} menu items successfully."
        msg_type = "success"
    except Exception as e:
        db.rollback()
        message = f"Import failed: {e}"
        msg_type = "error"

    items = db.query(MenuItem).order_by(MenuItem.slot_number).all()
    config = db.get(AppConfig, 1)
    return templates.TemplateResponse(request, name="admin/menu_items.html", context={
        "menu_items": items,
        "config": config,
        "active_tab": "menu-items",
        "message": message,
        "msg_type": msg_type,
    })
