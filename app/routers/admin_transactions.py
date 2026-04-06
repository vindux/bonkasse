import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session as DBSession, joinedload
from sqlalchemy import func, cast, Date
from pathlib import Path

from ..database import get_db
from ..models import Transaction, TransactionItem, AppConfig
from ..auth import require_admin
from ..dependencies import get_printer_service
from ..services.printer_service import PrinterService

router = APIRouter(prefix="/admin/transactions", dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("", response_class=HTMLResponse)
def transactions_page(request: Request, db: DBSession = Depends(get_db)):
    transactions = (
        db.query(Transaction)
        .options(joinedload(Transaction.items))
        .order_by(Transaction.timestamp.desc())
        .all()
    )
    config = db.get(AppConfig, 1)
    return templates.TemplateResponse(request, name="admin/transactions.html", context={
        "transactions": transactions,
        "config": config,
        "active_tab": "transactions",
    })


@router.get("/export-csv")
def export_csv(db: DBSession = Depends(get_db)):
    transactions = (
        db.query(Transaction)
        .options(joinedload(Transaction.items))
        .order_by(Transaction.timestamp.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date/Time", "Transaction ID", "Item Name", "Price", "VAT %"])

    for txn in transactions:
        ts = txn.timestamp.strftime("%Y-%m-%d %H:%M:%S") if txn.timestamp else ""
        for item in txn.items:
            writer.writerow([ts, txn.id, item.name, f"{item.price:.2f}", f"{item.vat_rate:.1f}"])

    content = output.getvalue()
    filename = f"bonkasse_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/delete-all", response_class=HTMLResponse)
def delete_all(request: Request, db: DBSession = Depends(get_db)):
    count = db.query(Transaction).count()
    db.query(TransactionItem).delete()
    db.query(Transaction).delete()
    db.commit()

    config = db.get(AppConfig, 1)
    return templates.TemplateResponse(request, name="admin/transactions.html", context={
        "transactions": [],
        "config": config,
        "active_tab": "transactions",
        "message": f"Deleted {count} transactions.",
        "msg_type": "success",
    })


@router.post("/print-summary", response_class=HTMLResponse)
def print_summary(
    request: Request,
    date_filter: str = Form(""),
    db: DBSession = Depends(get_db),
    printer: PrinterService = Depends(get_printer_service),
):
    query = db.query(Transaction).options(joinedload(Transaction.items))

    title = "ALL TRANSACTIONS SUMMARY"
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(func.date(Transaction.timestamp) == filter_date)
            title = f"TRANSACTIONS SUMMARY - {date_filter}"
        except ValueError:
            pass

    transactions = query.all()

    item_summary = {}
    total_revenue = 0.0
    for txn in transactions:
        total_revenue += txn.total
        for item in txn.items:
            if item.name in item_summary:
                item_summary[item.name]["count"] += 1
                item_summary[item.name]["total"] += item.price
            else:
                item_summary[item.name] = {
                    "name": item.name,
                    "price": item.price,
                    "count": 1,
                    "total": item.price,
                }

    if item_summary:
        summary_data = {i: v for i, v in enumerate(item_summary.values())}
        printer.print_transaction_summary(summary_data, total_revenue)
        msg = f"Summary printed. Total: {total_revenue:.2f} \u20ac, Items: {sum(d['count'] for d in item_summary.values())}"
        mtype = "success"
    else:
        msg = "No transactions found for the selected period."
        mtype = "warning"

    all_transactions = (
        db.query(Transaction)
        .options(joinedload(Transaction.items))
        .order_by(Transaction.timestamp.desc())
        .all()
    )
    config = db.get(AppConfig, 1)
    return templates.TemplateResponse(request, name="admin/transactions.html", context={
        "transactions": all_transactions,
        "config": config,
        "active_tab": "transactions",
        "message": msg,
        "msg_type": mtype,
    })
