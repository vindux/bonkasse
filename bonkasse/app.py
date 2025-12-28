"""
Main application class for Bonkasse
Coordinates all components and handles the application lifecycle
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime

from .database import BonkasseDatabase
from .services.transaction_service import TransactionService
from .services.receipt_service import ReceiptService
from .ui.menu_grid import MenuGrid
from .ui.transaction_panel import TransactionPanel
from .ui.total_button import TotalButton
from .ui.settings_window import SettingsWindow
from .ui.change_modal import ChangeModal


class BonkasseApp:
    """Main application class that coordinates all components"""

    def __init__(self, root):
        self.root = root
        self.root.title("Bonkasse - Sports Club Cash Register")

        try:
            self.root.iconbitmap("assets/icon.ico")
        except tk.TclError:
            try:
                icon_photo = tk.PhotoImage(file="assets/icon.png")
                self.root.iconphoto(True, icon_photo)
            except tk.TclError:
                pass

        self.root.attributes('-fullscreen', True)
        self.root.resizable(False, False)
        
        # self.root.overrideredirect(True)  # Commented out to maintain taskbar presence

        self.colors = {
            'bg_primary': '#f8f9fa',
            'bg_secondary': '#ffffff',
            'bg_accent': '#e9ecef',
            'text_primary': '#212529',
            'text_secondary': '#6c757d',
            'accent': '#0d6efd',
            'accent_hover': "#9cb9e4",
            'success': '#198754',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'border': '#dee2e6'
        }

        self.root.configure(bg=self.colors['bg_primary'])

        self.database = BonkasseDatabase()
        self.database.connect()
        self.database.init_tables()
        self.database.ensure_36_menu_slots()

        self.transaction_service = TransactionService(self.database)
        self.receipt_service = ReceiptService()

        self.transaction_service.set_update_callback(self._on_transaction_updated)

        self.menu_grid = None
        self.transaction_panel = None
        self.total_button = None
        self.system_button = None
        self.settings_button = None
        self.exit_button = None
        self.system_mode = False

        self.create_ui()

        self.setup_key_bindings()

        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def create_ui(self):
        """Create the main user interface"""
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        menu_items = self.database.get_menu_items()

        self.menu_grid = MenuGrid(main_frame, menu_items, self._on_item_click, self.colors, self.database)
        self.menu_grid.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        bottom_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        order_frame = tk.Frame(bottom_frame, bg=self.colors['bg_primary'])
        order_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))

        self.transaction_panel = TransactionPanel(order_frame, self.colors)
        self.transaction_panel.pack(fill=tk.BOTH, expand=True)

        middle_frame = tk.Frame(bottom_frame, bg=self.colors['bg_primary'])
        middle_frame.pack(side=tk.LEFT, fill=tk.Y, padx=30)

        buttons_frame = tk.Frame(middle_frame, bg=self.colors['bg_primary'])
        buttons_frame.pack(fill=tk.BOTH, expand=True)

        action_frame = tk.Frame(buttons_frame, bg=self.colors['bg_secondary'], relief='solid', bd=1, width=120)
        action_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=2)
        action_frame.pack_propagate(False)

        action_label = tk.Label(action_frame, text="Actions", font=('Arial', 10, 'bold'),
                               fg=self.colors['text_primary'], bg=self.colors['bg_secondary'])
        action_label.pack(pady=(5, 3))

        self.remove_last_btn = tk.Button(action_frame, text="Remove Last", command=self._on_remove_last,
                                   font=('Arial', 9, 'bold'), fg='white', bg=self.colors['warning'],
                                   relief='flat', bd=0, cursor='hand2')
        self.remove_last_btn.pack(fill=tk.X, pady=2, padx=5, ipady=12)

        self.clear_all_btn = tk.Button(action_frame, text="Clear All", command=self._on_clear_all,
                                 font=('Arial', 9, 'bold'), fg='white', bg=self.colors['danger'],
                                 relief='flat', bd=0, cursor='hand2')
        self.clear_all_btn.pack(fill=tk.X, pady=2, padx=5, ipady=12)

        self.print_last_order_btn = tk.Button(action_frame, text="Print Last Order", command=self._on_print_last_order,
                                            font=('Arial', 9, 'bold'), fg='white', bg=self.colors['success'],
                                            relief='flat', bd=0, cursor='hand2')
        self.print_last_order_btn.pack(fill=tk.X, pady=(2, 5), padx=5, ipady=12)

        system_frame = tk.Frame(buttons_frame, bg=self.colors['bg_secondary'], relief='solid', bd=1, width=120)
        system_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=2)
        system_frame.pack_propagate(False)

        system_label = tk.Label(system_frame, text="System", font=('Arial', 10, 'bold'),
                               fg=self.colors['text_primary'], bg=self.colors['bg_secondary'])
        system_label.pack(pady=(5, 3))

        self.system_button = tk.Button(system_frame, text="System", command=self._on_system_toggle,
                                      font=('Arial', 9, 'bold'), fg='white', bg=self.colors['accent'],
                                      relief='flat', bd=0, cursor='hand2')
        self.system_button.pack(fill=tk.X, pady=1, padx=5, ipady=8)

        self.settings_button = tk.Button(system_frame, text="Settings", command=self._on_settings,
                                        font=('Arial', 9, 'bold'), fg=self.colors['text_secondary'],
                                        bg=self.colors['bg_accent'], relief='flat', bd=0,
                                        cursor='hand2', state='disabled')
        self.settings_button.pack(fill=tk.X, pady=1, padx=5, ipady=8)

        self.exit_button = tk.Button(system_frame, text="Exit", command=self._on_exit,
                                    font=('Arial', 9, 'bold'), fg=self.colors['text_secondary'],
                                    bg=self.colors['bg_accent'], relief='flat', bd=0,
                                    cursor='hand2', state='disabled')
        self.exit_button.pack(fill=tk.X, pady=(1, 5), padx=5, ipady=8)

        last_order_frame = tk.Frame(middle_frame, bg=self.colors['bg_secondary'], relief='solid', bd=1)
        last_order_frame.pack(fill=tk.X, pady=(10, 0))

        last_order_label = tk.Label(last_order_frame, text="Last Order", font=('Arial', 10, 'bold'),
                                   fg=self.colors['text_primary'], bg=self.colors['bg_secondary'])
        last_order_label.pack(pady=(5, 3))

        self.last_order_display = tk.Label(last_order_frame, text="€0.00", font=('Arial', 16, 'bold'),
                                          fg=self.colors['accent'], bg=self.colors['bg_secondary'])
        self.last_order_display.pack(pady=(0, 5))

        total_frame = tk.Frame(bottom_frame, bg=self.colors['bg_primary'])
        total_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(40, 0))

        self.total_button = TotalButton(total_frame, self._on_print_receipt, self.colors)
        self.total_button.pack(fill=tk.BOTH, expand=True)

    def setup_key_bindings(self):
        """Setup keyboard shortcuts"""
        self.root.bind('<Return>', lambda event: self._on_print_receipt())

        self.root.bind('<BackSpace>', lambda event: self._on_remove_last())

        self.root.bind('<Escape>', lambda event: self._on_system_toggle())

        self.root.bind('<Up>', self._on_arrow_up)
        self.root.bind('<Down>', self._on_arrow_down)

        self.system_button_selection = 0

        self.root.focus_set()

    def disable_key_bindings(self):
        """Disable all key bindings (for when modal windows are open)"""
        self.root.unbind('<Return>')
        self.root.unbind('<BackSpace>')
        self.root.unbind('<Escape>')
        self.root.unbind('<Up>')
        self.root.unbind('<Down>')

    def enable_key_bindings(self):
        """Re-enable key bindings"""
        self.setup_key_bindings()


    def _on_item_click(self, item_id: int, name: str, price: float):
        """Handle menu item click"""
        self.transaction_service.add_item(item_id, name, price)

    def _on_remove_last(self):
        """Handle remove last item"""
        self.transaction_service.remove_last_item()

    def _on_clear_all(self):
        """Handle clear all items"""
        self.transaction_service.clear_transaction()

    def _on_print_receipt(self):
        """Handle print receipt"""
        if not self.transaction_service.is_empty():
            item_counts = {}
            current_transaction = self.transaction_service.current_transaction
            for item in current_transaction.items:
                item_counts[item.id] = item_counts.get(item.id, 0) + 1

            total_amount = current_transaction.get_total()

            event = self.database.get_event()
            change_enabled = bool(event[7]) if event and len(event) > 7 else False

            if change_enabled:
                self.disable_key_bindings()
                try:
                    ChangeModal(self.root, total_amount, self.colors)
                finally:
                    self.enable_key_bindings()

            self._print_individual_bons(current_transaction)

            self.transaction_service.finalize_transaction()
            self.database.update_session_sales(item_counts)

            if hasattr(self, 'last_order_display') and self.last_order_display:
                self.last_order_display.config(text=f"{total_amount:.2f} €")

            if hasattr(self, 'menu_grid') and self.menu_grid:
                self.menu_grid.refresh_display_counts()

    def _print_individual_bons(self, transaction):
        """Print individual 'bon' for each item in the transaction"""
        from .services.printer_service import PrinterService

        event = self.database.get_event()
        printer_enabled = bool(event[8]) if event and len(event) > 8 else False

        menu_items_data = {item[0]: item for item in self.database.get_menu_items()}

        printable_items = [item for item in transaction.items
                          if item.id in menu_items_data and menu_items_data[item.id][4]]

        if not printable_items:
            return

        if not printer_enabled:
            print(f"\n{'=' * 30} INDIVIDUAL BONS {'=' * 30}")
            for item in printable_items:
                print(f"\n--- BON ---")
                print(f"{item.name}")
                print(f"{item.price:.2f} €")
                print(f"----------")
            print()
            return

        printer_service = PrinterService()
        printer_type = event[9] if len(event) > 9 else "usb"
        printer_interface = event[10] if len(event) > 10 else ""
        cash_drawer_enabled = bool(event[11]) if len(event) > 11 else True

        printer_service.configure_printer(printer_type, printer_interface, True, cash_drawer_enabled)

        company_info = {
            'company_name': event[2] if len(event) > 2 else '',
            'company_address': event[3] if len(event) > 3 else '',
            'company_phone': event[4] if len(event) > 4 else '',
            'title': event[1] if len(event) > 1 else ''
        }
        printer_service.set_company_info(company_info)

        printer_items = []
        for item in printable_items:
            printer_items.append({
                'name': item.name,
                'price': item.price,
                'quantity': 1
            })

        printer_service.print_individual_items(printer_items)

    def _print_transaction_receipt(self, transaction, total_amount):
        """Print the main transaction receipt"""
        from .services.printer_service import PrinterService

        event = self.database.get_event()
        printer_enabled = bool(event[8]) if event and len(event) > 8 else False

        if not printer_enabled:
            self.receipt_service.print_receipt(transaction)
            return

        printer_service = PrinterService()
        printer_type = event[9] if len(event) > 9 else "usb"
        printer_interface = event[10] if len(event) > 10 else ""
        cash_drawer_enabled = bool(event[11]) if len(event) > 11 else True

        printer_service.configure_printer(printer_type, printer_interface, True, cash_drawer_enabled)

        company_info = {
            'company_name': event[2] if len(event) > 2 else '',
            'company_address': event[3] if len(event) > 3 else '',
            'company_phone': event[4] if len(event) > 4 else '',
            'title': event[1] if len(event) > 1 else ''
        }
        printer_service.set_company_info(company_info)

        printer_items = []
        for item in transaction.items:
            existing_item = None
            for printer_item in printer_items:
                if (printer_item['name'] == item.name and
                    printer_item['price'] == item.price):
                    existing_item = printer_item
                    break

            if existing_item:
                existing_item['quantity'] += 1
            else:
                printer_items.append({
                    'name': item.name,
                    'price': item.price,
                    'quantity': 1
                })

        printer_service.print_receipt(printer_items, total_amount)

    def _on_print_last_order(self):
        """Handle print last order"""
        transactions = self.database.get_all_transactions()
        if not transactions:
            messagebox.showinfo("Print Last Order", "No previous orders found.")
            return

        last_transaction = transactions[0]
        transaction_id, timestamp, total, items_json = last_transaction

        try:
            import json
            from .services.printer_service import PrinterService

            items = json.loads(items_json)

            printer_items = []
            for item in items:
                existing_item = None
                for printer_item in printer_items:
                    if (printer_item['name'] == item['name'] and
                        printer_item['price'] == item['price']):
                        existing_item = printer_item
                        break

                if existing_item:
                    existing_item['quantity'] += 1
                else:
                    printer_items.append({
                        'name': item['name'],
                        'price': item['price'],
                        'quantity': 1
                    })

            event = self.database.get_event()
            printer_enabled = bool(event[8]) if event and len(event) > 8 else False

            if printer_enabled:
                printer_service = PrinterService()
                printer_type = event[9] if len(event) > 9 else "usb"
                printer_interface = event[10] if len(event) > 10 else ""
                cash_drawer_enabled = bool(event[11]) if len(event) > 11 else True

                printer_service.configure_printer(printer_type, printer_interface, True, cash_drawer_enabled)

                company_info = {
                    'company_name': event[2] if len(event) > 2 else '',
                    'company_address': event[3] if len(event) > 3 else '',
                    'company_phone': event[4] if len(event) > 4 else '',
                    'title': event[1] if len(event) > 1 else ''
                }
                printer_service.set_company_info(company_info)

                success = printer_service.print_receipt(printer_items, total)
                if success:
                    messagebox.showinfo("Print Last Order", "Last order printed successfully!")
                else:
                    messagebox.showwarning("Print Last Order", "Failed to print. Check printer connection.")
            else:
                print(f"\n{'='*40}")
                print(f"REPRINT - Last Order ({total:.2f} €)")
                print(f"Transaction ID: {transaction_id}")
                print(f"Time: {timestamp}")
                print(f"{'='*40}")

                for item in printer_items:
                    if item['quantity'] > 1:
                        print(f"{item['quantity']}x {item['name']} @ {item['price']:.2f} € = {item['price'] * item['quantity']:.2f} €")
                    else:
                        print(f"{item['name']:<25} {item['price']:>6.2f} €")

                print(f"{'-'*40}")
                print(f"{'TOTAL':<25} {total:>6.2f} €")
                print(f"{'='*40}\n")

                messagebox.showinfo("Print Last Order", "Last order printed to console (printer disabled).")

        except json.JSONDecodeError:
            messagebox.showerror("Error", "Failed to parse last order data.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print last order: {e}")

    def print_transaction_summary(self):
        """Print transaction summary showing session sales totals"""
        from .services.printer_service import PrinterService
        import tkinter.messagebox as messagebox

        session_sales = self.database.get_all_session_sales()
        menu_items = self.database.get_menu_items()

        if not session_sales:
            messagebox.showinfo("Transaction Summary", "No sales recorded in current session.")
            return

        summary_data = {}
        total_revenue = 0.0

        item_details = {}
        for item in menu_items:
            item_id, name, price, vat_rate, print_receipt, active = item
            item_details[item_id] = {'name': name, 'price': price}

        for item_id, count in session_sales.items():
            if count > 0 and item_id in item_details:
                item_info = item_details[item_id]
                item_total = count * item_info['price']
                total_revenue += item_total

                summary_data[item_id] = {
                    'name': item_info['name'],
                    'price': item_info['price'],
                    'count': count,
                    'total': item_total
                }

        if not summary_data:
            messagebox.showinfo("Transaction Summary", "No items sold in current session.")
            return

        event = self.database.get_event()
        printer_enabled = bool(event[8]) if event and len(event) > 8 else False

        if not printer_enabled:
            print(f"\n{'=' * 50}")
            print("TRANSACTION SUMMARY - SESSION SALES")
            print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'=' * 50}")

            for item_data in summary_data.values():
                print(f"{item_data['count']:>3} x {item_data['name']:<30} {item_data['total']:>8.2f} €")

            print(f"{'-' * 50}")
            print(f"{'TOTAL REVENUE':<35} {total_revenue:>8.2f} €")
            print(f"{'ITEMS SOLD':<35} {sum(item['count'] for item in summary_data.values()):>8}")
            print(f"{'=' * 50}\n")

            messagebox.showinfo("Transaction Summary", f"Summary printed to console.\nTotal Revenue: {total_revenue:.2f} €")
            return

        try:
            printer_service = PrinterService()
            printer_type = event[9] if len(event) > 9 else "usb"
            printer_interface = event[10] if len(event) > 10 else ""
            cash_drawer_enabled = bool(event[11]) if len(event) > 11 else True

            printer_service.configure_printer(printer_type, printer_interface, True, cash_drawer_enabled)

            company_info = {
                'company_name': event[2] if len(event) > 2 else '',
                'company_address': event[3] if len(event) > 3 else '',
                'company_phone': event[4] if len(event) > 4 else '',
                'title': event[1] if len(event) > 1 else ''
            }
            printer_service.set_company_info(company_info)

            success = printer_service.print_transaction_summary(summary_data, total_revenue)
            if success:
                messagebox.showinfo("Transaction Summary", f"Summary printed successfully!\nTotal Revenue: {total_revenue:.2f} €")
            else:
                messagebox.showwarning("Transaction Summary", "Failed to print. Check printer connection.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to print transaction summary: {e}")

    def _on_system_toggle(self):
        """Handle System/Resume button toggle"""
        self.system_mode = not self.system_mode

        if self.system_mode:
            self.system_button.config(text="Resume", bg=self.colors['danger'])
            self.settings_button.config(state='normal', fg='white', bg=self.colors['accent'])
            self.exit_button.config(state='normal', fg='white', bg=self.colors['danger'])

            self.remove_last_btn.config(state='disabled', bg='#cccccc', fg='#666666', cursor='X_cursor')
            self.clear_all_btn.config(state='disabled', bg='#cccccc', fg='#666666', cursor='X_cursor')
            self.print_last_order_btn.config(state='disabled', bg='#cccccc', fg='#666666', cursor='X_cursor')

            if hasattr(self, 'menu_grid') and self.menu_grid:
                self.menu_grid.set_system_mode(True)
            if hasattr(self, 'total_button') and self.total_button:
                self.total_button.set_system_mode(True)

            self.system_button_selection = 0
            self._update_button_focus()
        else:
            self.system_button.config(text="System", bg=self.colors['accent'])
            self.settings_button.config(state='disabled', fg=self.colors['text_secondary'], bg=self.colors['bg_accent'])
            self.exit_button.config(state='disabled', fg=self.colors['text_secondary'], bg=self.colors['bg_accent'])

            self.remove_last_btn.config(state='normal', bg=self.colors['warning'], fg='white', cursor='hand2')
            self.clear_all_btn.config(state='normal', bg=self.colors['danger'], fg='white', cursor='hand2')
            self.print_last_order_btn.config(state='normal', bg=self.colors['success'], fg='white', cursor='hand2')

            if hasattr(self, 'menu_grid') and self.menu_grid:
                self.menu_grid.set_system_mode(False)
            if hasattr(self, 'total_button') and self.total_button:
                self.total_button.set_system_mode(False)

            self.system_button.config(relief='flat', bd=0)
            self.settings_button.config(relief='flat', bd=0)
            self.exit_button.config(relief='flat', bd=0)
            self.root.bind('<Return>', lambda event: self._on_print_receipt())

    def _refresh_main_window(self, data_changed=True):
        """Refresh the main window components after settings changes"""
        self.transaction_service.clear_transaction()

        if hasattr(self, 'menu_grid') and self.menu_grid and data_changed:
            self.menu_grid.data_changed_in_system_mode = True

        if hasattr(self, 'menu_grid') and self.menu_grid:
            menu_items = self.database.get_menu_items()
            self.menu_grid.update_menu_items(menu_items)

    def _on_settings(self):
        """Handle Settings button with password protection"""
        password_hash = self.database.get_password_hash()

        if password_hash:
            from .ui.password_dialog import PasswordDialog

            dialog = PasswordDialog(self.root, self.colors, "Enter Settings Password")
            success, entered_password = dialog.show()

            if not success:
                return

            if not PasswordDialog.verify_password(entered_password, password_hash):
                messagebox.showerror("Access Denied", "Incorrect password")
                return

        self.disable_key_bindings()

        try:
            settings_window = SettingsWindow(self.root, self.database, self.colors, self._refresh_main_window)

            self.root.wait_window(settings_window.window)

            if self.system_mode:
                self._on_system_toggle()

            self._refresh_main_window(data_changed=False)
        finally:
            self.enable_key_bindings()

    def _on_exit(self):
        """Handle Exit button with confirmation"""
        self._handle_exit_request()

    def _on_window_close(self):
        """Handle window close event (Alt+F4, clicking X button) with confirmation"""
        self._handle_exit_request()

    def _handle_exit_request(self):
        """Common exit handling logic with confirmation"""
        self.disable_key_bindings()

        try:
            if messagebox.askyesno("Exit Confirmation", "Are you sure you want to exit the application?"):
                self.cleanup()
                self.root.quit()
        finally:
            if not self.root.winfo_exists():
                return
            self.enable_key_bindings()

    def _on_transaction_updated(self):
        """Handle transaction updates - refresh UI"""
        if hasattr(self, 'transaction_panel') and self.transaction_panel:
            self.transaction_panel.clear_all()
            for item in self.transaction_service.get_items():
                self.transaction_panel.add_item(item.name, item.price)

        if hasattr(self, 'total_button') and self.total_button:
            total = self.transaction_service.get_total()
            self.total_button.update_total(total)

    def _on_arrow_up(self, event):
        """Handle up arrow key - navigate system buttons upward"""
        if self.system_mode:
            self.system_button_selection = (self.system_button_selection - 1) % 3
            self._update_button_focus()

    def _on_arrow_down(self, event):
        """Handle down arrow key - navigate system buttons downward"""
        if self.system_mode:
            self.system_button_selection = (self.system_button_selection + 1) % 3
            self._update_button_focus()

    def _update_button_focus(self):
        """Update button visual focus based on current selection"""
        if not self.system_mode:
            return

        self.system_button.config(relief='flat', bd=0)
        self.settings_button.config(relief='flat', bd=0)
        self.exit_button.config(relief='flat', bd=0)

        if self.system_button_selection == 0:
            self.system_button.config(relief='solid', bd=2)
            self.root.bind('<Return>', lambda event: self._on_system_toggle())
        elif self.system_button_selection == 1:
            self.settings_button.config(relief='solid', bd=2)
            self.root.bind('<Return>', lambda event: self._on_settings())
        elif self.system_button_selection == 2:
            self.exit_button.config(relief='solid', bd=2)
            self.root.bind('<Return>', lambda event: self._on_exit())

    def run(self):
        """Start the application main loop"""
        self.root.mainloop()

    def cleanup(self):
        """Cleanup resources before exit"""
        if self.database:
            self.database.close()


if __name__ == "__main__":
    from .exceptions import DoNotRunDirectly
    raise DoNotRunDirectly(__name__)