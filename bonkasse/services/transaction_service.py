"""
Transaction service for Bonkasse
Handles transaction business logic
"""

import json
from typing import Callable, Optional
from ..models import Transaction, TransactionItem
from ..database import BonkasseDatabase


class TransactionService:
    """Manages transaction operations and business logic"""

    def __init__(self, database: BonkasseDatabase):
        self.database = database
        self.current_transaction = Transaction()
        self.on_transaction_updated: Optional[Callable] = None

    def set_update_callback(self, callback: Callable):
        """Set callback to be called when transaction is updated"""
        self.on_transaction_updated = callback

    def add_item(self, item_id: int, name: str, price: float):
        """Add an item to the current transaction"""
        item = TransactionItem(id=item_id, name=name, price=price)
        self.current_transaction.add_item(item)

        if self.on_transaction_updated:
            self.on_transaction_updated()

    def remove_last_item(self):
        """Remove the last added item from transaction"""
        removed_item = self.current_transaction.remove_last_item()

        if removed_item and self.on_transaction_updated:
            self.on_transaction_updated()

        return removed_item

    def clear_transaction(self):
        """Clear the current transaction"""
        self.current_transaction.clear()

        if self.on_transaction_updated:
            self.on_transaction_updated()

    def get_total(self) -> float:
        """Get the current transaction total"""
        return self.current_transaction.get_total()

    def is_empty(self) -> bool:
        """Check if the current transaction is empty"""
        return self.current_transaction.is_empty()

    def get_items(self):
        """Get all items in the current transaction"""
        return list(self.current_transaction)

    def save_transaction(self):
        """Save the current transaction to database"""
        if self.current_transaction.is_empty():
            return

        total = self.get_total()
        items_json = json.dumps(self.current_transaction.to_dict_list())

        self.database.save_transaction(total, items_json)

    def finalize_transaction(self):
        """Save and clear the current transaction"""
        self.save_transaction()
        self.clear_transaction()


if __name__ == "__main__":
    import sys
    print(f"Error: This module should not be run directly. Please run main.py instead.")
    sys.exit(1)