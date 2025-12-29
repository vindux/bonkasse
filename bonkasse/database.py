"""
Database module for Bonkasse
Handles SQLite database initialization and operations
"""

import sqlite3
import shutil
import os
from datetime import datetime
from pathlib import Path


class BonkasseDatabase:
    """Manages SQLite database operations for Bonkasse"""

    def __init__(self, db_path: str = "bonkasse.db"):
        self.db_path = Path(db_path)
        self.conn = None

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def init_tables(self):
        """Initialize database tables"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category TEXT DEFAULT 'General',
                vat_rate REAL DEFAULT 0.0,
                print_receipt INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1
            )
        """)

        cursor.execute("PRAGMA table_info(menu_items)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'vat_rate' not in columns:
            cursor.execute("ALTER TABLE menu_items ADD COLUMN vat_rate REAL DEFAULT 0.0")
        if 'print_receipt' not in columns:
            cursor.execute("ALTER TABLE menu_items ADD COLUMN print_receipt INTEGER DEFAULT 1")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total REAL NOT NULL,
                items TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_sales (
                item_id INTEGER PRIMARY KEY,
                count INTEGER DEFAULT 0,
                FOREIGN KEY (item_id) REFERENCES menu_items (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event (
                id INTEGER PRIMARY KEY DEFAULT 1,
                title TEXT DEFAULT '',
                company_name TEXT DEFAULT '',
                company_address TEXT DEFAULT '',
                company_phone TEXT DEFAULT '',
                company_email TEXT DEFAULT '',
                change_enabled INTEGER DEFAULT 0,
                printer_enabled INTEGER DEFAULT 0,
                printer_type TEXT DEFAULT 'usb',
                printer_interface TEXT DEFAULT '',
                cash_drawer_enabled INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("PRAGMA table_info(event)")
        event_columns = [column[1] for column in cursor.fetchall()]

        if 'change_enabled' not in event_columns:
            cursor.execute("ALTER TABLE event ADD COLUMN change_enabled INTEGER DEFAULT 0")
        if 'printer_enabled' not in event_columns:
            cursor.execute("ALTER TABLE event ADD COLUMN printer_enabled INTEGER DEFAULT 0")
        if 'printer_type' not in event_columns:
            cursor.execute("ALTER TABLE event ADD COLUMN printer_type TEXT DEFAULT 'usb'")
        if 'printer_interface' not in event_columns:
            cursor.execute("ALTER TABLE event ADD COLUMN printer_interface TEXT DEFAULT ''")
        if 'cash_drawer_enabled' not in event_columns:
            cursor.execute("ALTER TABLE event ADD COLUMN cash_drawer_enabled INTEGER DEFAULT 1")
        if 'password_hash' not in event_columns:
            cursor.execute("ALTER TABLE event ADD COLUMN password_hash TEXT DEFAULT NULL")

        cursor.execute("INSERT OR IGNORE INTO event (id) VALUES (1)")

        self.conn.commit()

    def ensure_36_menu_slots(self):
        """Ensure database has exactly 36 menu item slots"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM menu_items")
        current_count = cursor.fetchone()[0]

        if current_count == 0:
            sample_items = [
                ("temp", 2.50),
                ("temp", 2.00),
                ("temp", 3.00),
                ("temp", 3.50),
                ("temp", 4.00),
                ("temp", 2.25),

                ("temp", 1.50),
                ("temp", 2.50),
                ("temp", 4.00),
                ("temp", 3.00),
                ("temp", 2.75),
                ("temp", 3.50),

                ("temp", 6.50),
                ("temp", 7.00),
                ("temp", 5.50),
                ("temp", 6.00),
                ("temp", 4.50),
                ("temp", 3.50),
                ("temp", 8.50),
                ("temp", 7.50),
                ("temp", 9.00),
                ("temp", 6.50),
                ("temp", 5.00),
                ("temp", 4.00),

                ("temp", 1.50),
                ("temp", 2.00),
                ("temp", 1.75),
                ("temp", 2.50),
                ("temp", 1.25),
                ("temp", 2.00),

                ("temp", 3.00),
                ("temp", 4.50),
                ("temp", 2.00),
                ("temp", 5.00),
                ("temp", 2.25),
                ("temp", 3.50)
            ]
            cursor.executemany(
                "INSERT INTO menu_items (name, price) VALUES (?, ?)",
                sample_items
            )
            self.conn.commit()

        cursor.execute("SELECT COUNT(*) FROM menu_items")
        current_count = cursor.fetchone()[0]

        if current_count < 36:
            empty_slots_needed = 36 - current_count
            empty_items = [("", 0.0) for _ in range(empty_slots_needed)]
            cursor.executemany(
                "INSERT INTO menu_items (name, price) VALUES (?, ?)",
                empty_items
            )
            self.conn.commit()

    def get_menu_items(self):
        """Get all menu items with their active status"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, price, vat_rate, print_receipt, active FROM menu_items ORDER BY id"
        )
        return cursor.fetchall()

    def get_all_menu_items(self):
        """Get all menu items for editing"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, price, vat_rate, print_receipt, active FROM menu_items ORDER BY id"
        )
        return cursor.fetchall()

    def save_transaction(self, total: float, items: str):
        """Save a transaction to the database with local timestamp"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        local_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO transactions (timestamp, total, items) VALUES (?, ?, ?)",
            (local_timestamp, total, items)
        )
        self.conn.commit()

    def get_all_transactions(self):
        """Get all transactions from the database"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, total, items FROM transactions ORDER BY timestamp DESC"
        )
        return cursor.fetchall()

    def get_session_sales_count(self, item_id: int):
        """Get the session sales count for a specific item"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("SELECT count FROM session_sales WHERE item_id = ?", (item_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def get_all_session_sales(self):
        """Get session sales counts for all items"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("SELECT item_id, count FROM session_sales")
        return dict(cursor.fetchall())

    def update_session_sales(self, item_counts: dict):
        """Update session sales counts for multiple items"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        for item_id, count in item_counts.items():
            cursor.execute("""
                INSERT OR REPLACE INTO session_sales (item_id, count)
                VALUES (?, COALESCE((SELECT count FROM session_sales WHERE item_id = ?), 0) + ?)
            """, (item_id, item_id, count))
        self.conn.commit()

    def reset_session_sales(self):
        """Reset all session sales counts to 0"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM session_sales")
        self.conn.commit()

    def update_menu_item(self, item_id: int, name: str, price: float, vat_rate: float, print_receipt: bool, active: bool):
        """Update a menu item"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE menu_items
            SET name = ?, price = ?, vat_rate = ?, print_receipt = ?, active = ?
            WHERE id = ?
        """, (name, price, vat_rate, int(print_receipt), int(active), item_id))
        self.conn.commit()

    def add_menu_item(self, name: str, price: float, vat_rate: float, print_receipt: bool):
        """Add a new menu item"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO menu_items (name, price, vat_rate, print_receipt)
            VALUES (?, ?, ?, ?)
        """, (name, price, vat_rate, int(print_receipt)))
        self.conn.commit()
        return cursor.lastrowid

    def clear_all_menu_items(self):
        """Clear all menu items from the database"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM menu_items")
        self.conn.commit()

    def get_event(self):
        """Get the current event"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM event WHERE id = 1")
        return cursor.fetchone()

    def save_event(self, title: str, company_name: str, company_address: str, company_phone: str, company_email: str, change_enabled: bool = None, printer_enabled: bool = None, printer_type: str = None, printer_interface: str = None, cash_drawer_enabled: bool = None):
        """Save event data including printer settings"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()

        local_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        update_fields = ["title = ?", "company_name = ?", "company_address = ?", "company_phone = ?", "company_email = ?", "created_at = ?"]
        values = [title, company_name, company_address, company_phone, company_email, local_timestamp]

        if change_enabled is not None:
            update_fields.append("change_enabled = ?")
            values.append(int(change_enabled))

        if printer_enabled is not None:
            update_fields.append("printer_enabled = ?")
            values.append(int(printer_enabled))

        if printer_type is not None:
            update_fields.append("printer_type = ?")
            values.append(printer_type)

        if printer_interface is not None:
            update_fields.append("printer_interface = ?")
            values.append(printer_interface)

        if cash_drawer_enabled is not None:
            update_fields.append("cash_drawer_enabled = ?")
            values.append(int(cash_drawer_enabled))

        query = f"UPDATE event SET {', '.join(update_fields)} WHERE id = 1"
        cursor.execute(query, values)
        self.conn.commit()

    def export_database(self, export_path: str):
        """Export only menu items to specified path"""
        import json

        if not self.conn:
            self.connect()

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, name, price, vat_rate, print_receipt, active
                FROM menu_items
                ORDER BY id
            """)
            menu_items = cursor.fetchall()

            export_data = {
                "version": "1.0",
                "export_type": "menu_items",
                "timestamp": datetime.now().isoformat(),
                "menu_items": []
            }

            for item in menu_items:
                item_id, name, price, vat_rate, print_receipt, active = item
                export_data["menu_items"].append({
                    "id": item_id,
                    "name": name,
                    "price": price,
                    "vat_rate": vat_rate,
                    "print_receipt": bool(print_receipt),
                    "active": bool(active)
                })

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            raise Exception(f"Failed to export menu items: {str(e)}")

    def import_database(self, import_path: str, backup_current: bool = True):
        """Import only menu items from specified JSON file"""
        import json

        if not os.path.exists(import_path):
            raise Exception(f"Import file does not exist: {import_path}")

        if not self.conn:
            self.connect()

        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if not isinstance(import_data, dict):
                raise Exception("Invalid import file format")

            if import_data.get("export_type") != "menu_items":
                raise Exception("Import file is not a menu items export")

            if "menu_items" not in import_data:
                raise Exception("No menu items found in import file")

            menu_items = import_data["menu_items"]
            if not isinstance(menu_items, list):
                raise Exception("Invalid menu items format")

            backup_items = []
            if backup_current:
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, name, price, vat_rate, print_receipt, active FROM menu_items ORDER BY id")
                backup_items = cursor.fetchall()

            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM menu_items")
            cursor.execute("DELETE FROM session_sales")

            for item in menu_items:
                required_fields = ["id", "name", "price", "vat_rate", "print_receipt", "active"]
                for field in required_fields:
                    if field not in item:
                        raise Exception(f"Missing required field: {field}")

                cursor.execute("""
                    INSERT INTO menu_items (id, name, price, vat_rate, print_receipt, active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    item["id"],
                    item["name"],
                    float(item["price"]),
                    float(item["vat_rate"]),
                    int(item["print_receipt"]),
                    int(item["active"])
                ))

            self.conn.commit()
            return True

        except json.JSONDecodeError:
            raise Exception("Invalid JSON format in import file")
        except Exception as e:
            if backup_current and backup_items:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("DELETE FROM menu_items")
                    for item in backup_items:
                        cursor.execute("""
                            INSERT INTO menu_items (id, name, price, vat_rate, print_receipt, active)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, item)
                    self.conn.commit()
                except:
                    pass
            raise Exception(f"Failed to import menu items: {str(e)}")


    def create_backup(self):
        """Create a backup of the current database"""
        backup_path = f"{self.db_path}.backup"
        return self.export_database(backup_path)

    def get_password_hash(self):
        """Get the stored password hash"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash FROM event WHERE id = 1")
        result = cursor.fetchone()
        return result[0] if result else None

    def set_password_hash(self, password_hash):
        """Set the password hash"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("UPDATE event SET password_hash = ? WHERE id = 1", (password_hash,))
        self.conn.commit()

    def clear_password(self):
        """Remove the password (set to NULL)"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("UPDATE event SET password_hash = NULL WHERE id = 1")
        self.conn.commit()

    def delete_all_transactions(self):
        """Delete all transactions from the database"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM transactions")
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None


if __name__ == "__main__":
    import sys
    print(f"Error: This module should not be run directly. Please run main.py instead.")
    sys.exit(1)