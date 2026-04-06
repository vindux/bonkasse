# Bonkasse

Sports club cash register (Kasse) — touchscreen kiosk POS system with ESC/POS thermal printer support.

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

Opens Chrome in kiosk mode at `http://127.0.0.1:8000`. Falls back to default browser if Chrome is not found.

## Architecture

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Frontend:** Jinja2 templates + htmx (no build step)
- **Printer:** python-escpos (USB, Network, Serial, Windows)
