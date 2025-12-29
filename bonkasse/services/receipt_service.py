"""
Receipt service for Bonkasse
Handles receipt formatting and printing
"""

from ..models import Transaction


class ReceiptService:
    """Handles receipt generation and printing operations"""

    def __init__(self):
        self.club_name = "Sports Club Cash Register"
        self.receipt_header = "BONKASSE RECEIPT"

    def format_receipt(self, transaction: Transaction) -> str:
        """Format a transaction as a receipt string"""
        lines = []

        lines.append("=" * 40)
        lines.append(self.receipt_header)
        lines.append(self.club_name)
        lines.append("=" * 40)

        for item in transaction:
            lines.append(f"{item.name:<25} {item.price:>6.2f} €")

        lines.append("-" * 40)
        lines.append(f"{'TOTAL':<25} {transaction.get_total():>6.2f} €")
        lines.append("=" * 40)
        lines.append("Thank you for your purchase!")
        lines.append("=" * 40)

        return "\n".join(lines)

    def print_receipt_to_console(self, transaction: Transaction):
        """Print receipt to console (for testing/development)"""
        receipt_text = self.format_receipt(transaction)
        print("\n" + receipt_text + "\n")

    def print_receipt_to_printer(self, transaction: Transaction):
        """Print receipt to ESC/POS printer (future implementation)"""
        print("Printing to ESC/POS printer...")
        self.print_receipt_to_console(transaction)

    def print_receipt(self, transaction: Transaction, use_printer: bool = False):
        """Print receipt using the specified method"""
        if use_printer:
            self.print_receipt_to_printer(transaction)
        else:
            self.print_receipt_to_console(transaction)


if __name__ == "__main__":
    import sys
    print(f"Error: This module should not be run directly. Please run main.py instead.")
    sys.exit(1)