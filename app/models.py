from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime


class Base(DeclarativeBase):
    pass


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_number = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False, default="")
    price = Column(Float, nullable=False, default=0.0)
    vat_rate = Column(Float, default=7.0)
    print_bon = Column(Boolean, default=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    transaction_items = relationship("TransactionItem", back_populates="menu_item")

    @property
    def is_empty(self) -> bool:
        return not self.name or not self.name.strip()

    @property
    def is_blank(self) -> bool:
        return self.is_empty and self.price == 0.0


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    total = Column(Float, nullable=False)
    # Use local machine time, not SQLite's func.now() (which stores UTC).
    # This kiosk runs on a single local machine; receipts/CSV/date-filters
    # all expect local wall-clock time.
    timestamp = Column(DateTime, default=datetime.now)

    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")


class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    vat_rate = Column(Float, default=7.0)
    print_bon = Column(Boolean, default=True)

    transaction = relationship("Transaction", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="transaction_items")



class AppConfig(Base):
    __tablename__ = "app_config"

    id = Column(Integer, primary_key=True, default=1)
    title = Column(String, default="")
    company_name = Column(String, default="")
    company_address = Column(String, default="")
    company_phone = Column(String, default="")
    company_email = Column(String, default="")
    change_enabled = Column(Boolean, default=False)
    printer_enabled = Column(Boolean, default=False)
    printer_type = Column(String, default="usb")
    printer_interface = Column(String, default="")
    cash_drawer_enabled = Column(Boolean, default=True)
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
