"""
Printer service for Bonkasse
Handles ESC/POS thermal printer integration with cash drawer control.
Ported from the original Tkinter app.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from escpos.printer import Usb, Network, Serial, Dummy
from escpos.exceptions import USBNotFoundError, Error as EscPosError

try:
    from escpos.printer import Win32Raw
    WINDOWS_PRINTER_AVAILABLE = True
except ImportError:
    WINDOWS_PRINTER_AVAILABLE = False


class PrinterService:
    """Handles ESC/POS thermal printer operations and cash drawer control."""

    def __init__(self):
        self.printer = None
        self.printer_type = None
        self.printer_interface = None
        self.printer_enabled = False
        self.cash_drawer_enabled = False
        self.company_info: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)

    def configure_printer(self, printer_type: str, interface: str, enabled: bool = True, cash_drawer: bool = True):
        self.printer_type = printer_type.lower()
        self.printer_interface = interface
        self.printer_enabled = enabled
        self.cash_drawer_enabled = cash_drawer
        if enabled:
            self._initialize_printer()

    def _initialize_printer(self):
        if not self.printer_enabled:
            self.printer = None
            return False

        try:
            if self.printer_type == "usb":
                if self.printer_interface and ":" in self.printer_interface:
                    vendor_id, product_id = self.printer_interface.split(":")
                    self.printer = Usb(int(vendor_id, 16), int(product_id, 16))
                else:
                    self.printer = Usb(0x04B8, 0x0202)

            elif self.printer_type == "network":
                if ":" in self.printer_interface:
                    host, port = self.printer_interface.split(":")
                    self.printer = Network(host, int(port))
                else:
                    self.printer = Network(self.printer_interface, 9100)

            elif self.printer_type == "serial":
                self.printer = Serial(self.printer_interface)

            elif self.printer_type == "windows":
                if WINDOWS_PRINTER_AVAILABLE:
                    self.printer = Win32Raw(self.printer_interface)
                else:
                    self.logger.error("Windows printer support not available (requires pywin32)")
                    self.printer = None
                    return False
            else:
                self.logger.warning(f"Unknown printer type: {self.printer_type}")
                self.printer = None
                return False

            self.logger.info(f"Printer initialized: {self.printer_type} - {self.printer_interface}")
            try:
                self.printer.charcode("CP858")
            except Exception as e:
                self.logger.warning(f"Could not set codepage to CP858: {e}")

            return True

        except (USBNotFoundError, EscPosError, Exception) as e:
            self.logger.error(f"Failed to initialize printer: {e}")
            self.printer = None
            return False

    def set_company_info(self, info: Dict[str, str]):
        self.company_info = info

    def is_printer_ready(self) -> bool:
        return bool(self.printer_enabled and self.printer)

    def _flush_printer(self):
        if self.printer and self.printer_type == "windows":
            try:
                self.printer.close()
                self._initialize_printer()
            except Exception as e:
                self.logger.warning(f"Error flushing printer: {e}")

    def test_print(self) -> bool:
        if not self.is_printer_ready():
            self.logger.warning("Printer test failed: printer not ready")
            return False

        try:
            self.printer.set(align="center", bold=True, width=2, height=2)
            self.printer.text("BONKASSE\n")
            self.printer.set()
            self.printer.text("Test Print\n")
            self.printer.text(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.printer.text("-" * 32 + "\n")
            self.printer.text("If you can read this,\n")
            self.printer.text("the printer is working!\n")
            self.printer.text("-" * 32 + "\n")
            self.printer.cut()

            if self.cash_drawer_enabled:
                self._open_cash_drawer()

            self._flush_printer()
            self.logger.info("Test print completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Test print failed: {e}")
            return False

    def print_receipt(self, items: List[Dict], total: float, payment_amount: float = None, change: float = None):
        if not self.is_printer_ready():
            self._print_to_console("Receipt", items, total, payment_amount, change)
            return False

        try:
            self._print_header()
            self.printer.set(align="left")

            for item in items:
                name = item.get("name", "Unknown Item")
                price = item.get("price", 0.0)
                quantity = item.get("quantity", 1)

                if quantity > 1:
                    self.printer.text(f"{quantity}x {name}\n")
                    self.printer.text(f"    @ {price:.2f} \u20ac each\n")
                    self.printer.text(f"    = {price * quantity:.2f} \u20ac\n")
                else:
                    price_str = f"{price:.2f} \u20ac"
                    max_name_len = 32 - len(price_str) - 1
                    if len(name) > max_name_len:
                        self.printer.text(f"{name}\n")
                        self.printer.set(align="right")
                        self.printer.text(f"{price_str}\n")
                        self.printer.set(align="left")
                    else:
                        spaces = 32 - len(name) - len(price_str)
                        self.printer.text(f"{name}{' ' * spaces}{price_str}\n")

            self._print_separator()
            self.printer.set(align="right", width=2, height=2)
            self.printer.text(f"TOTAL: {total:.2f} \u20ac\n")

            if payment_amount is not None:
                self.printer.set(align="right")
                self.printer.text(f"Payment: {payment_amount:.2f} \u20ac\n")
                if change is not None and change > 0:
                    self.printer.text(f"Change: {change:.2f} \u20ac\n")

            self._print_footer()
            self.printer.cut()

            if self.cash_drawer_enabled:
                self._open_cash_drawer()

            self._flush_printer()
            self.logger.info("Receipt printed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to print receipt: {e}")
            self._print_to_console("Receipt", items, total, payment_amount, change)
            return False

    def print_individual_items(self, items: List[Dict]):
        if not self.is_printer_ready():
            self._print_individual_to_console(items)
            return False

        try:
            for item in items:
                name = item.get("name", "Unknown Item")
                price = item.get("price", 0.0)
                quantity = item.get("quantity", 1)

                for _ in range(quantity):
                    event_name = self.company_info.get("title") or self.company_info.get("company_name") or "BONKASSE"
                    self.printer.set(align="center", bold=True, custom_size=True, width=1, height=1)
                    self.printer.text(f"{event_name}\n")
                    self._print_separator()
                    self.printer.set(align="center", custom_size=True, width=2, height=2)
                    self.printer.text(f"{name}\n\n")
                    self.printer.set(align="center", custom_size=True, width=1, height=1)
                    self.printer.text(f"{price:.2f} \u20ac\n")
                    self.printer.cut()

            self._flush_printer()
            self.logger.info(f"Printed individual bons for {len(items)} item types")
            return True
        except Exception as e:
            self.logger.error(f"Failed to print individual items: {e}")
            self._print_individual_to_console(items)
            return False

    def print_transaction_summary(self, session_sales: Dict[int, Dict], total_revenue: float):
        if not self.is_printer_ready():
            self._print_summary_to_console(session_sales, total_revenue)
            return False

        try:
            self._print_header("TRANSACTION SUMMARY")
            self.printer.set(align="center")
            self.printer.text(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self._print_separator()
            self.printer.set(align="left")

            for item_data in session_sales.values():
                if item_data["count"] > 0:
                    name = item_data["name"]
                    count = item_data["count"]
                    price = item_data["price"]
                    total_item = count * price
                    self.printer.text(f"{count} x {name}\n")
                    self.printer.set(align="right")
                    self.printer.text(f"{total_item:.2f} \u20ac\n")
                    self.printer.set(align="left")

            self._print_separator()
            self.printer.set(align="right", width=2, height=2)
            self.printer.text(f"TOTAL: {total_revenue:.2f} \u20ac\n")
            self._print_footer()
            self.printer.cut()
            self._flush_printer()
            self.logger.info("Transaction summary printed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to print transaction summary: {e}")
            self._print_summary_to_console(session_sales, total_revenue)
            return False

    def _print_header(self, title: str = "BONKASSE RECEIPT"):
        self.printer.set(align="center", bold=True, width=2, height=2)
        self.printer.text(f"{title}\n")
        if self.company_info.get("company_name"):
            self.printer.set(align="center", bold=True)
            self.printer.text(f"{self.company_info['company_name']}\n")
        if self.company_info.get("company_address"):
            self.printer.set(align="center")
            self.printer.text(f"{self.company_info['company_address']}\n")
        if self.company_info.get("company_phone"):
            self.printer.text(f"Tel: {self.company_info['company_phone']}\n")
        self._print_separator()
        self.printer.set(align="center")
        self.printer.text(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self._print_separator()

    def _print_footer(self):
        self._print_separator()
        self.printer.set(align="center")
        self.printer.text("Thank you for your purchase!\n")
        if self.company_info.get("title"):
            self.printer.text(f"{self.company_info['title']}\n")
        self._print_separator()

    def _print_separator(self):
        self.printer.set(align="center")
        self.printer.text("-" * 32 + "\n")

    def _open_cash_drawer(self):
        if self.cash_drawer_enabled and self.printer:
            try:
                self.printer.cashdraw(2)
                self.logger.info("Cash drawer opened")
            except Exception as e:
                self.logger.error(f"Failed to open cash drawer: {e}")

    def _print_to_console(self, title: str, items: List[Dict], total: float, payment_amount: float = None, change: float = None):
        print(f"\n{'=' * 40}")
        print(f"{title}")
        if self.company_info.get("company_name"):
            print(f"{self.company_info['company_name']}")
        print(f"{'=' * 40}")
        for item in items:
            name = item.get("name", "Unknown Item")
            price = item.get("price", 0.0)
            quantity = item.get("quantity", 1)
            if quantity > 1:
                print(f"{quantity}x {name} @ {price:.2f} \u20ac = {price * quantity:.2f} \u20ac")
            else:
                print(f"{name:<25} {price:>6.2f} \u20ac")
        print(f"{'-' * 40}")
        print(f"{'TOTAL':<25} {total:>6.2f} \u20ac")
        if payment_amount is not None:
            print(f"{'Payment':<25} {payment_amount:>6.2f} \u20ac")
        if change is not None and change > 0:
            print(f"{'Change':<25} {change:>6.2f} \u20ac")
        print(f"{'=' * 40}\n")

    def _print_individual_to_console(self, items: List[Dict]):
        print(f"\n{'=' * 20} INDIVIDUAL BONS {'=' * 20}")
        for item in items:
            name = item.get("name", "Unknown Item")
            price = item.get("price", 0.0)
            quantity = item.get("quantity", 1)
            for _ in range(quantity):
                print(f"\n--- BON ---")
                print(f"{name}")
                print(f"{price:.2f} \u20ac")
                print(f"{datetime.now().strftime('%H:%M:%S')}")
                print(f"----------")
        print()

    def _print_summary_to_console(self, session_sales: Dict[int, Dict], total_revenue: float):
        print(f"\n{'=' * 40}")
        print("TRANSACTION SUMMARY")
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 40}")
        for item_data in session_sales.values():
            if item_data["count"] > 0:
                name = item_data["name"]
                count = item_data["count"]
                price = item_data["price"]
                total_item = count * price
                print(f"{count} x {name:<20} {total_item:>8.2f} \u20ac")
        print(f"{'-' * 40}")
        print(f"{'TOTAL REVENUE':<25} {total_revenue:>6.2f} \u20ac")
        print(f"{'=' * 40}\n")

    def get_available_usb_printers(self) -> List[Dict[str, Any]]:
        return [
            {"name": "Epson TM-T88VII", "vendor_id": "0x04b8", "product_id": "0x0202"},
            {"name": "Epson TM-T88VI", "vendor_id": "0x04b8", "product_id": "0x0165"},
            {"name": "Epson TM-T88IV", "vendor_id": "0x04b8", "product_id": "0x0202"},
            {"name": "Epson TM-T20", "vendor_id": "0x04b8", "product_id": "0x0e28"},
            {"name": "Auto-detect", "vendor_id": "auto", "product_id": "auto"},
        ]

    def close(self):
        if self.printer:
            try:
                self.printer.close()
            except Exception as e:
                self.logger.error(f"Error closing printer: {e}")
            finally:
                self.printer = None
