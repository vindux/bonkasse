import logging
import threading
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession, joinedload
from sqlalchemy import func
from pathlib import Path

from ..database import get_db
from ..models import MenuItem, AppConfig, Transaction, TransactionItem
from ..services.cart import get_cart, CartItem
from ..dependencies import get_printer_service
from ..services.printer_service import PrinterService

log = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

# Serializes finalize so a double-tap (two concurrent requests for the SAME
# order) can't create duplicate transactions / double-print. The shared global
# cart is mutable state with no other synchronization.
_finalize_lock = threading.Lock()


def _get_sales_counts(db: DBSession) -> dict[int, int]:
    """Count items sold per menu_item_id across all transactions."""
    rows = (
        db.query(TransactionItem.menu_item_id, func.count())
        .filter(TransactionItem.menu_item_id.isnot(None))
        .group_by(TransactionItem.menu_item_id)
        .all()
    )
    return dict(rows)


def _get_last_transaction(db: DBSession) -> Transaction | None:
    """Most recently finalized transaction (for the customer-receipt reprint)."""
    return (
        db.query(Transaction)
        .options(joinedload(Transaction.items))
        .order_by(Transaction.id.desc())
        .first()
    )


def _toast(message: str, type: str = "success") -> HTMLResponse:
    html = templates.get_template("components/toast.html").render({"message": message, "type": type})
    return HTMLResponse(html)


def _consolidate_items(items) -> list[dict]:
    """Group identical line items into name/price/quantity rows for a receipt."""
    consolidated: list[dict] = []
    for item in items:
        match = next((c for c in consolidated if c["name"] == item.name and c["price"] == item.price), None)
        if match:
            match["quantity"] += 1
        else:
            consolidated.append({"name": item.name, "price": item.price, "quantity": 1, "vat_rate": item.vat_rate})
    return consolidated


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
def register_page(
    request: Request,
    db: DBSession = Depends(get_db),
    printer: PrinterService = Depends(get_printer_service),
):
    ctx = _cart_context(db)
    config = ctx["config"]
    ctx["printer_ready"] = printer.is_printer_ready() if config and config.printer_enabled else None
    ctx["last_transaction"] = _get_last_transaction(db)
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

    # Snapshot the order and clear the cart atomically. Doing this under the
    # lock (and clearing BEFORE we persist/print) means a duplicate request
    # from a double-tap finds an empty cart and no-ops, instead of creating a
    # second phantom transaction and re-printing.
    with _finalize_lock:
        if cart.is_empty:
            ctx = _cart_context(db)
            return HTMLResponse(templates.get_template("fragments/cart.html").render(ctx))
        items = list(cart.items)
        last_total = cart.total
        cart.clear()

    # Save transaction from the snapshot
    try:
        txn = Transaction(total=last_total)
        db.add(txn)
        db.flush()

        for cart_item in items:
            db.add(TransactionItem(
                transaction_id=txn.id,
                menu_item_id=cart_item.menu_item_id,
                name=cart_item.name,
                price=cart_item.price,
                vat_rate=cart_item.vat_rate,
                print_bon=cart_item.print_bon,
            ))
        db.commit()
    except Exception:
        db.rollback()
        log.exception("Failed to save transaction")
        # Restore the order so the cashier can retry rather than losing it.
        with _finalize_lock:
            for cart_item in items:
                cart.add(cart_item)
        ctx = _cart_context(db)
        cart_html = templates.get_template("fragments/cart.html").render(ctx)
        total_html = templates.get_template("fragments/total_button.html").render(ctx)
        oob = f'\n<div id="total-button" hx-swap-oob="innerHTML">{total_html}</div>'
        return HTMLResponse(cart_html + oob)

    # Print individual bons for items with print_bon enabled
    bon_items = []
    for cart_item in items:
        if cart_item.print_bon:
            bon_items.append({
                "name": cart_item.name,
                "price": cart_item.price,
                "quantity": 1,
            })
    if bon_items:
        try:
            printer.print_individual_items(bon_items)
        except Exception:
            log.exception("Printer error during finalize")

    # The sale is committed and cash is changing hands, so open the till. This
    # sits outside the `if bon_items:` block on purpose — an order with nothing
    # printable is still a cash sale. The call is a no-op when the drawer is
    # switched off in settings or the printer is unavailable.
    printer._open_cash_drawer()

    # Return updated cart + total + menu grid (sales counts) + last order
    ctx = _cart_context(db)
    cart_html = templates.get_template("fragments/cart.html").render(ctx)
    total_html = templates.get_template("fragments/total_button.html").render(ctx)
    grid_html = templates.get_template("fragments/menu_grid.html").render(ctx)

    last_order_html = templates.get_template("fragments/last_order.html").render({"last_transaction": txn})

    oob = f'\n<div id="total-button" hx-swap-oob="innerHTML">{total_html}</div>'
    oob += f'\n<div id="menu-grid" hx-swap-oob="innerHTML">{grid_html}</div>'
    oob += f'\n<div id="last-order" hx-swap-oob="innerHTML">{last_order_html}</div>'

    # Show change modal if enabled
    config = db.get(AppConfig, 1)
    if config and config.change_enabled:
        euro_notes = [5, 10, 20, 50, 100]
        applicable = [(note, note - last_total) for note in euro_notes if note >= last_total]
        change_html = templates.get_template("fragments/change_modal.html").render({
            "total": last_total,
            "notes": applicable,
        })
        oob += f'\n<div id="modal-container" hx-swap-oob="innerHTML">{change_html}</div>'

    return HTMLResponse(cart_html + oob)


@router.post("/receipt/print-last", response_class=HTMLResponse)
def print_last_receipt(
    request: Request,
    db: DBSession = Depends(get_db),
    printer: PrinterService = Depends(get_printer_service),
):
    """Reprint the most recent finalized order as a consolidated customer receipt."""
    txn = _get_last_transaction(db)
    if not txn or not txn.items:
        return _toast("No previous order to print.", "warning")

    items = _consolidate_items(txn.items)
    try:
        ok = printer.print_receipt(items, txn.total)
    except Exception:
        log.exception("Failed to print customer receipt")
        ok = False

    if ok:
        return _toast("Receipt printed.", "success")
    return _toast("Could not print receipt. Check the printer.", "error")
