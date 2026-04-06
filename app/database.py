from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker
from .models import Base
from .config import DB_PATH


def _make_engine(db_path=None):
    path = db_path or DB_PATH
    engine = create_engine(f"sqlite:///{path}", echo=False)

    @sa_event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
