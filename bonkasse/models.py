"""
Data models for Bonkasse
Contains data structures and model classes
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class MenuItem:
    """Represents a menu item"""
    id: int
    name: str
    price: float
    category: str = "General"
    active: bool = True

    def __str__(self):
        return f"{self.name} - {self.price:.2f} €"


@dataclass
class TransactionItem:
    """Represents an item in a transaction"""
    id: int
    name: str
    price: float
    print_receipt: bool = True

    def __str__(self):
        return f"{self.name:<20} {self.price:>6.2f} €"


class Transaction:
    """Represents a complete transaction"""

    def __init__(self):
        self.items: List[TransactionItem] = []
        self.timestamp = datetime.now()

    def add_item(self, item: TransactionItem):
        """Add an item to the transaction"""
        self.items.append(item)

    def remove_last_item(self):
        """Remove the last added item"""
        if self.items:
            return self.items.pop()
        return None

    def clear(self):
        """Clear all items from transaction"""
        self.items.clear()

    def get_total(self) -> float:
        """Calculate total price of all items"""
        return sum(item.price for item in self.items)

    def is_empty(self) -> bool:
        """Check if transaction has no items"""
        return len(self.items) == 0

    def to_dict_list(self) -> List[dict]:
        """Convert transaction items to list of dictionaries for JSON storage"""
        return [
            {
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'print_receipt': item.print_receipt
            }
            for item in self.items
        ]

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)


if __name__ == "__main__":
    import sys
    print(f"Error: This module should not be run directly. Please run main.py instead.")
    sys.exit(1)