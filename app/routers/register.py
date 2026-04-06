from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from pathlib import Path

from ..database import get_db
from ..models import MenuItem, AppConfig, Transaction, TransactionItem
from ..services.cart import get_cart, CartItem
from ..dependencies import get_printer_service
from ..services.printer_service import PrinterService

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


def _get_sales_counts(db: DBSession) -> dict[int, int]:
    """Count items sold per menu_item_id across all transactions."""
    rows = (
        db.query(TransactionItem.menu_item_id, func.count())
        .filter(TransactionItem.menu_item_id.isnot(None))
        .group_by(TransactionItem.menu_item_id)
        .all()
    )
    return dict(rows)


def _cart_context(db: DBSession) -> dict:
    """Build common context needed for cart/total fragments."""
    cart = get_cart()
    menu_items = db.query(MenuItem).order_by(MenuItem.slot_number).all()
    config = db.get(AppConfig, 1)
    sales_counts = _get_sales_counts(db)
    return {
        "cart": cart,
        "menu_items": menu_items,
        "config": config,
        "session_counts": sales_counts,
    }


@router.get("/", response_class=HTMLResponse)
def register_page(request: Request, db: DBSession = Depends(get_db)):
    ctx = _cart_context(db)
    return templates.TemplateResponse(request, name="register.html", context=ctx)


@router.post("/cart/add/{menu_item_id}", response_class=HTMLResponse)
def cart_add(menu_item_id: int, request: Request, db: DBSession = Depends(get_db)):
    item = db.get(MenuItem, menu_item_id)
    if item and item.active and not item.is_empty:
        cart = get_cart()
        cart.add(CartItem(
            menu_item_id=item.id,
            name=item.name,
            price=item.price,
            vat_rate=item.vat_rate,
            print_bon=item.print_bon,
        ))

    ctx = _cart_context(db)
    cart_html = templates.get_template("fragments/cart.html").render(ctx)
    total_html = templates.get_template("fragments/total_button.html").render(ctx)
    return HTMLResponse(cart_html + f'\n<div id="total-button" hx-swap-oob="innerHTML">{total_html}</div>')


@router.post("/cart/remove-last", response_class=HTMLResponse)
def cart_remove_last(request: Request, db: DBSession = Depends(get_db)):
    cart = get_cart()
    cart.remove_last()

    ctx = _cart_context(db)
    cart_html = templates.get_template("fragments/cart.html").render(ctx)
    total_html = templates.get_template("fragments/total_button.html").render(ctx)
    return HTMLResponse(cart_html + f'\n<div id="total-button" hx-swap-oob="innerHTML">{total_html}</div>')


@router.post("/cart/clear", response_class=HTMLResponse)
def cart_clear(request: Request, db: DBSession = Depends(get_db)):
    cart = get_cart()
    cart.clear()

    ctx = _cart_context(db)
    cart_html = templates.get_template("fragments/cart.html").render(ctx)
    total_html = templates.get_template("fragments/total_button.html").render(ctx)
    return HTMLResponse(cart_html + f'\n<div id="total-button" hx-swap-oob="innerHTML">{total_html}</div>')


@router.post("/cart/finalize", response_class=HTMLResponse)
def cart_finalize(
    request: Request,
    db: DBSession = Depends(get_db),
    printer: PrinterService = Depends(get_printer_service),
):
    cart = get_cart()
    if cart.is_empty:
        ctx = _cart_context(db)
        return HTMLResponse(templates.get_template("fragments/cart.html").render(ctx))

    # Save transaction
    txn = Transaction(total=cart.total)
    db.add(txn)
    db.flush()

    for cart_item in cart.items:
        db.add(TransactionItem(
            transaction_id=txn.id,
            menu_item_id=cart_item.menu_item_id,
            name=cart_item.name,
            price=cart_item.price,
            vat_rate=cart_item.vat_rate,
            print_bon=cart_item.print_bon,
        ))
    db.commit()

    # Print individual bons for items with print_bon enabled
    bon_items = []
    for cart_item in cart.items:
        if cart_item.print_bon:
            bon_items.append({
                "name": cart_item.name,
                "price": cart_item.price,
                "quantity": 1,
            })
    if bon_items:
        printer.print_individual_items(bon_items)

    last_total = cart.total
    cart.clear()

    # Return updated cart + total + menu grid (sales counts) + last order
    ctx = _cart_context(db)
    cart_html = templates.get_template("fragments/cart.html").render(ctx)
    total_html = templates.get_template("fragments/total_button.html").render(ctx)
    grid_html = templates.get_template("fragments/menu_grid.html").render(ctx)

    oob = f'\n<div id="total-button" hx-swap-oob="innerHTML">{total_html}</div>'
    oob += f'\n<div id="menu-grid" hx-swap-oob="innerHTML">{grid_html}</div>'
    oob += f'\n<div id="last-order" hx-swap-oob="innerHTML">{last_total:.2f}&nbsp;&euro;</div>'

    return HTMLResponse(cart_html + oob)


@router.get("/change-modal", response_class=HTMLResponse)
def change_modal(request: Request, total: float):
    euro_notes = [5, 10, 20, 50, 100]
    applicable = [(note, note - total) for note in euro_notes if note >= total]
    return templates.TemplateResponse(request, name="fragments/change_modal.html", context={
        "total": total,
        "notes": applicable,
    })
