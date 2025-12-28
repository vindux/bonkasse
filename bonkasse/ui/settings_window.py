"""
Settings window for menu and event management
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
from datetime import datetime
from tkcalendar import Calendar


class SettingsWindow:
    """Settings window for managing menu items and events"""

    def __init__(self, parent, database, colors, refresh_callback=None):
        self.parent = parent
        self.database = database
        self.colors = colors
        self.refresh_callback = refresh_callback

        self.window = tk.Toplevel(parent)
        self.window.title("Bonkasse Settings")
        self.window.geometry("1200x800")
        self.window.configure(bg=colors['bg_primary'])
        self.window.transient(parent)
        self.window.grab_set()

        try:
            self.window.iconbitmap("assets/icon.ico")
        except tk.TclError:
            try:
                icon_photo = tk.PhotoImage(file="assets/icon.png")
                self.window.iconphoto(True, icon_photo)
            except tk.TclError:
                pass

        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.window.winfo_screenheight() // 2) - (800 // 2)
        self.window.geometry(f"1200x800+{x}+{y}")

        self.selected_item_id = None
        self.selected_tree_item = None
        self.current_item_vars = {}

        self.original_event_values = {}

        self.create_ui()

    def create_ui(self):
        """Create the settings UI"""
        main_frame = tk.Frame(self.window, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        title_label = tk.Label(main_frame, text="Bonkasse Settings",
                              font=('Arial', 18, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=self.colors['bg_primary'])
        title_label.pack(pady=(0, 20))

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.menu_frame = tk.Frame(self.notebook, bg=self.colors['bg_secondary'])
        self.notebook.add(self.menu_frame, text="Menu Items")
        self.create_menu_tab()

        self.general_frame = tk.Frame(self.notebook, bg=self.colors['bg_secondary'])
        self.notebook.add(self.general_frame, text="General")
        self.create_general_tab()

        self.transactions_frame = tk.Frame(self.notebook, bg=self.colors['bg_secondary'])
        self.notebook.add(self.transactions_frame, text="Transactions")
        self.create_transactions_tab()

        button_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        button_frame.pack(fill=tk.X, pady=(20, 0))

        export_btn = tk.Button(button_frame, text="Export Menu Items",
                              command=self.export_event,
                              font=('Arial', 10, 'bold'),
                              fg='white', bg=self.colors['accent'],
                              relief='flat', bd=0, cursor='hand2')
        export_btn.pack(side=tk.LEFT, padx=(0, 10), ipady=8, ipadx=15)

        import_btn = tk.Button(button_frame, text="Import Menu Items",
                              command=self.import_event,
                              font=('Arial', 10, 'bold'),
                              fg='white', bg=self.colors['success'],
                              relief='flat', bd=0, cursor='hand2')
        import_btn.pack(side=tk.LEFT, padx=(0, 10), ipady=8, ipadx=15)

        self.save_button = tk.Button(button_frame, text="Save Changes",
                                    command=self.save_current_changes,
                                    font=('Arial', 10, 'bold'),
                                    fg='white', bg=self.colors['success'],
                                    relief='flat', bd=0, cursor='hand2',
                                    state='disabled')
        self.save_button.pack(side=tk.RIGHT, padx=(10, 0), ipady=8, ipadx=20)

        close_btn = tk.Button(button_frame, text="Close",
                             command=self.close_window,
                             font=('Arial', 10, 'bold'),
                             fg='white', bg=self.colors['danger'],
                             relief='flat', bd=0, cursor='hand2')
        close_btn.pack(side=tk.RIGHT, ipady=8, ipadx=20)

    def create_menu_tab(self):
        """Create menu items management tab"""

        list_frame = tk.Frame(self.menu_frame, bg=self.colors['bg_secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        columns = ("Name", "Price", "VAT %", "Receipt", "Active")
        self.menu_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)

        self.menu_tree.heading("Name", text="Name")
        self.menu_tree.heading("Price", text="Price")
        self.menu_tree.heading("VAT %", text="VAT %")
        self.menu_tree.heading("Receipt", text="Receipt")
        self.menu_tree.heading("Active", text="Active")

        self.menu_tree.column("Name", width=250, minwidth=200)
        self.menu_tree.column("Price", width=100, minwidth=80)
        self.menu_tree.column("VAT %", width=80, minwidth=60)
        self.menu_tree.column("Receipt", width=80, minwidth=60)
        self.menu_tree.column("Active", width=80, minwidth=60)

        self.menu_tree.tag_configure('evenrow', background='#f8f8f8')
        self.menu_tree.tag_configure('oddrow', background='#ffffff')

        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.menu_tree.yview)
        self.menu_tree.configure(yscrollcommand=v_scrollbar.set)

        self.menu_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.menu_tree.bind("<<TreeviewSelect>>", self.on_item_select)

        self.create_edit_form()

        self.refresh_menu_items()

    def create_general_tab(self):
        """Create general settings tab"""
        form_frame = tk.Frame(self.general_frame, bg=self.colors['bg_secondary'])
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(form_frame, text="General Configuration",
                font=('Arial', 14, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).pack(anchor=tk.W, pady=(0, 10))

        fields_frame = tk.Frame(form_frame, bg=self.colors['bg_secondary'])
        fields_frame.pack(fill=tk.X)

        tk.Label(fields_frame, text="Business Title:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.event_title_var = tk.StringVar()
        event_title_entry = tk.Entry(fields_frame, textvariable=self.event_title_var,
                font=('Arial', 10), width=40)
        event_title_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        event_title_entry.bind('<KeyRelease>', self.on_event_field_change)

        tk.Label(fields_frame, text="Company Name:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.company_name_var = tk.StringVar()
        company_name_entry = tk.Entry(fields_frame, textvariable=self.company_name_var,
                font=('Arial', 10), width=40)
        company_name_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        company_name_entry.bind('<KeyRelease>', self.on_event_field_change)

        tk.Label(fields_frame, text="Company Address:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.company_address_var = tk.StringVar()
        company_address_entry = tk.Entry(fields_frame, textvariable=self.company_address_var,
                font=('Arial', 10), width=40)
        company_address_entry.grid(row=2, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        company_address_entry.bind('<KeyRelease>', self.on_event_field_change)

        tk.Label(fields_frame, text="Company Phone:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=3, column=0, sticky=tk.W, pady=2)
        self.company_phone_var = tk.StringVar()
        company_phone_entry = tk.Entry(fields_frame, textvariable=self.company_phone_var,
                font=('Arial', 10), width=40)
        company_phone_entry.grid(row=3, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        company_phone_entry.bind('<KeyRelease>', self.on_event_field_change)

        tk.Label(fields_frame, text="Company Email:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=4, column=0, sticky=tk.W, pady=2)
        self.company_email_var = tk.StringVar()
        company_email_entry = tk.Entry(fields_frame, textvariable=self.company_email_var,
                font=('Arial', 10), width=40)
        company_email_entry.grid(row=4, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        company_email_entry.bind('<KeyRelease>', self.on_event_field_change)

        tk.Label(fields_frame, text="Change Function:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=5, column=0, sticky=tk.W, pady=(10, 2))
        self.change_var = tk.BooleanVar()
        change_check = tk.Checkbutton(fields_frame, variable=self.change_var,
                text="Enable change calculation modal",
                font=('Arial', 10),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary'],
                activebackground=self.colors['bg_secondary'],
                activeforeground=self.colors['text_primary'],
                command=self.on_change_toggle)
        change_check.grid(row=5, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 2))

        password_separator = tk.Frame(fields_frame, height=2, bg=self.colors['border'])
        password_separator.grid(row=6, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(20, 15))

        tk.Label(fields_frame, text="Password Protection:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=7, column=0, sticky=tk.W, pady=(0, 5))

        password_frame = tk.Frame(fields_frame, bg=self.colors['bg_secondary'])
        password_frame.grid(row=7, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 5))

        self.password_status_var = tk.StringVar()
        password_status_label = tk.Label(password_frame, textvariable=self.password_status_var,
                                       font=('Arial', 9, 'italic'),
                                       fg=self.colors['text_secondary'],
                                       bg=self.colors['bg_secondary'])
        password_status_label.pack(side=tk.LEFT, padx=(0, 10))

        change_password_btn = tk.Button(password_frame, text="Change Password",
                                      command=self.change_password,
                                      font=('Arial', 9, 'bold'),
                                      fg='white', bg=self.colors['accent'],
                                      relief='flat', bd=0, cursor='hand2')
        change_password_btn.pack(side=tk.LEFT, padx=(0, 5), ipady=2, ipadx=8)

        self.remove_password_btn = tk.Button(password_frame, text="Remove Password",
                                           command=self.remove_password,
                                           font=('Arial', 9, 'bold'),
                                           fg='white', bg=self.colors['danger'],
                                           relief='flat', bd=0, cursor='hand2')
        self.remove_password_btn.pack(side=tk.LEFT, ipady=2, ipadx=8)

        separator = tk.Frame(fields_frame, height=2, bg=self.colors['border'])
        separator.grid(row=8, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(20, 15))

        tk.Label(fields_frame, text="Printer Settings:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=9, column=0, sticky=tk.W, pady=(0, 5))
        self.printer_enabled_var = tk.BooleanVar()
        printer_enabled_cb = tk.Checkbutton(fields_frame, text="Enable Printer",
                                          variable=self.printer_enabled_var,
                                          font=('Arial', 10),
                                          fg=self.colors['text_primary'],
                                          bg=self.colors['bg_secondary'],
                                          activebackground=self.colors['bg_secondary'],
                                          activeforeground=self.colors['text_primary'],
                                          command=self.on_printer_settings_changed)
        printer_enabled_cb.grid(row=9, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 5))

        tk.Label(fields_frame, text="Printer Type:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=10, column=0, sticky=tk.W, pady=2)

        printer_type_frame = tk.Frame(fields_frame, bg=self.colors['bg_secondary'])
        printer_type_frame.grid(row=10, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        self.printer_type_var = tk.StringVar(value="usb")
        printer_type_combo = ttk.Combobox(printer_type_frame, textvariable=self.printer_type_var,
                                        values=["windows", "usb", "network", "serial"],
                                        state="readonly", width=12)
        printer_type_combo.pack(side=tk.LEFT)
        printer_type_combo.bind("<<ComboboxSelected>>", self.on_printer_type_changed)

        self.auto_detect_btn = tk.Button(printer_type_frame, text="Auto-detect",
                                       command=self.auto_detect_printer,
                                       font=('Arial', 8),
                                       fg='white', bg=self.colors['accent'],
                                       relief='flat', bd=0, cursor='hand2')
        self.auto_detect_btn.pack(side=tk.LEFT, padx=(5, 0), ipady=1, ipadx=8)

        tk.Label(fields_frame, text="Connection:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=13, column=0, sticky=tk.W, pady=2)
        self.printer_interface_var = tk.StringVar()
        self.printer_interface_entry = tk.Entry(fields_frame, textvariable=self.printer_interface_var,
                                              font=('Arial', 10), width=40)
        self.printer_interface_entry.grid(row=11, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        self.printer_interface_entry.bind('<KeyRelease>', lambda e: self.on_printer_settings_changed())

        self.connection_help_label = tk.Label(fields_frame, text="",
                                            font=('Arial', 8, 'italic'),
                                            fg=self.colors['text_secondary'],
                                            bg=self.colors['bg_secondary'])
        self.connection_help_label.grid(row=12, column=1, sticky=tk.W, padx=(10, 0), pady=(2, 5))

        tk.Label(fields_frame, text="Cash Drawer:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).grid(row=13, column=0, sticky=tk.W, pady=2)
        self.cash_drawer_enabled_var = tk.BooleanVar(value=True)
        cash_drawer_cb = tk.Checkbutton(fields_frame, text="Open cash drawer on print",
                                      variable=self.cash_drawer_enabled_var,
                                      font=('Arial', 10),
                                      fg=self.colors['text_primary'],
                                      bg=self.colors['bg_secondary'],
                                      activebackground=self.colors['bg_secondary'],
                                      activeforeground=self.colors['text_primary'],
                                      command=self.on_printer_settings_changed)
        cash_drawer_cb.grid(row=13, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        test_frame = tk.Frame(fields_frame, bg=self.colors['bg_secondary'])
        test_frame.grid(row=14, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))

        test_print_btn = tk.Button(test_frame, text="Test Print",
                                 command=self.test_printer,
                                 font=('Arial', 9, 'bold'),
                                 fg='white', bg=self.colors['success'],
                                 relief='flat', bd=0, cursor='hand2')
        test_print_btn.pack(side=tk.LEFT, padx=(0, 5), ipady=4, ipadx=10)

        test_drawer_btn = tk.Button(test_frame, text="Test Cash Drawer",
                                  command=self.test_cash_drawer,
                                  font=('Arial', 9, 'bold'),
                                  fg='white', bg=self.colors['warning'],
                                  relief='flat', bd=0, cursor='hand2')
        test_drawer_btn.pack(side=tk.LEFT, ipady=4, ipadx=10)

        self.printer_status_label = tk.Label(fields_frame, text="Status: Not configured",
                                           font=('Arial', 9, 'italic'),
                                           fg=self.colors['text_secondary'],
                                           bg=self.colors['bg_secondary'])
        self.printer_status_label.grid(row=15, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))

        fields_frame.columnconfigure(1, weight=1)

        self.load_current_event()

        self.load_printer_settings()
        self.update_printer_interface_help()

        self.update_password_status()

    def create_transactions_tab(self):
        """Create transactions management tab"""
        title_frame = tk.Frame(self.transactions_frame, bg=self.colors['bg_secondary'])
        title_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        tk.Label(title_frame, text="Transaction History",
                font=('Arial', 14, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary']).pack(side=tk.LEFT)

        print_btn = tk.Button(title_frame, text="Print Transactions",
                              command=self.print_transactions_dialog,
                              font=('Arial', 10, 'bold'),
                              fg='white', bg=self.colors['success'],
                              relief='flat', bd=0, cursor='hand2')
        print_btn.pack(side=tk.RIGHT, padx=(10, 0), ipady=5, ipadx=15)

        delete_all_btn = tk.Button(title_frame, text="Delete All Transactions",
                                  command=self.delete_all_transactions,
                                  font=('Arial', 10, 'bold'),
                                  fg='white', bg=self.colors['danger'],
                                  relief='flat', bd=0, cursor='hand2')
        delete_all_btn.pack(side=tk.RIGHT, padx=(10, 0), ipady=5, ipadx=15)

        export_btn = tk.Button(title_frame, text="Export to CSV",
                              command=self.export_transactions_csv,
                              font=('Arial', 10, 'bold'),
                              fg='white', bg=self.colors['accent'],
                              relief='flat', bd=0, cursor='hand2')
        export_btn.pack(side=tk.RIGHT, padx=(10, 0), ipady=5, ipadx=15)

        list_frame = tk.Frame(self.transactions_frame, bg=self.colors['bg_secondary'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("Date/Time", "Item", "Price", "VAT %")
        self.transactions_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)

        self.transactions_tree.heading("Date/Time", text="Date/Time")
        self.transactions_tree.heading("Item", text="Item")
        self.transactions_tree.heading("Price", text="Price")
        self.transactions_tree.heading("VAT %", text="VAT %")

        self.transactions_tree.column("Date/Time", width=150, minwidth=120)
        self.transactions_tree.column("Item", width=250, minwidth=200)
        self.transactions_tree.column("Price", width=100, minwidth=80)
        self.transactions_tree.column("VAT %", width=80, minwidth=60)

        self.transactions_tree.tag_configure('evenrow', background='#f8f8f8')
        self.transactions_tree.tag_configure('oddrow', background='#ffffff')

        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.transactions_tree.yview)
        self.transactions_tree.configure(yscrollcommand=v_scrollbar.set)

        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.transactions_tree.xview)
        self.transactions_tree.configure(xscrollcommand=h_scrollbar.set)

        self.transactions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.refresh_transactions()

    def create_edit_form(self):
        """Create edit form at bottom of menu tab"""
        edit_frame = tk.Frame(self.menu_frame, bg=self.colors['bg_accent'], relief='solid', bd=1)
        edit_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        title_label = tk.Label(edit_frame, text="Item Settings",
                              font=('Arial', 12, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=self.colors['bg_accent'])
        title_label.pack(pady=(10, 5))

        form_container = tk.Frame(edit_frame, bg=self.colors['bg_accent'])
        form_container.pack(fill=tk.X, padx=20, pady=(0, 10))

        left_frame = tk.Frame(form_container, bg=self.colors['bg_accent'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_frame = tk.Frame(form_container, bg=self.colors['bg_accent'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))

        tk.Label(left_frame, text="Name:", font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'], bg=self.colors['bg_accent']).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.current_item_vars['name'] = tk.StringVar()
        name_entry = tk.Entry(left_frame, textvariable=self.current_item_vars['name'],
                             font=('Arial', 10), width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        name_entry.bind('<KeyRelease>', self.on_field_change)

        tk.Label(left_frame, text="Price (€):", font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'], bg=self.colors['bg_accent']).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.current_item_vars['price'] = tk.StringVar()
        price_entry = tk.Entry(left_frame, textvariable=self.current_item_vars['price'],
                              font=('Arial', 10), width=30)
        price_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=(10, 0), pady=2)
        price_entry.bind('<KeyRelease>', self.on_field_change)

        left_frame.columnconfigure(1, weight=1)

        tk.Label(right_frame, text="VAT Rate:", font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'], bg=self.colors['bg_accent']).grid(row=0, column=0, sticky=tk.W, pady=2)

        self.current_item_vars['vat_rate'] = tk.StringVar(value="0.0")
        vat_frame = tk.Frame(right_frame, bg=self.colors['bg_accent'])
        vat_frame.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        vat_0 = tk.Radiobutton(vat_frame, text="0%", variable=self.current_item_vars['vat_rate'], value="0.0",
                              font=('Arial', 10), fg=self.colors['text_primary'], bg=self.colors['bg_accent'],
                              selectcolor=self.colors['bg_accent'], command=self.on_field_change)
        vat_0.pack(side=tk.LEFT, padx=(0, 10))

        vat_7 = tk.Radiobutton(vat_frame, text="7%", variable=self.current_item_vars['vat_rate'], value="7.0",
                              font=('Arial', 10), fg=self.colors['text_primary'], bg=self.colors['bg_accent'],
                              selectcolor=self.colors['bg_accent'], command=self.on_field_change)
        vat_7.pack(side=tk.LEFT, padx=(0, 10))

        vat_19 = tk.Radiobutton(vat_frame, text="19%", variable=self.current_item_vars['vat_rate'], value="19.0",
                               font=('Arial', 10), fg=self.colors['text_primary'], bg=self.colors['bg_accent'],
                               selectcolor=self.colors['bg_accent'], command=self.on_field_change)
        vat_19.pack(side=tk.LEFT)

        self.current_item_vars['print_receipt'] = tk.BooleanVar(value=True)
        receipt_check = tk.Checkbutton(right_frame, text="Print bon",
                                      variable=self.current_item_vars['print_receipt'],
                                      font=('Arial', 10), fg=self.colors['text_primary'],
                                      bg=self.colors['bg_accent'], selectcolor=self.colors['bg_accent'],
                                      command=self.on_field_change)
        receipt_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

        self.current_item_vars['active'] = tk.BooleanVar(value=True)
        active_check = tk.Checkbutton(right_frame, text="Active",
                                     variable=self.current_item_vars['active'],
                                     font=('Arial', 10), fg=self.colors['text_primary'],
                                     bg=self.colors['bg_accent'], selectcolor=self.colors['bg_accent'],
                                     command=self.on_field_change)
        active_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

        right_frame.columnconfigure(1, weight=1)

        self.save_button = None

    def refresh_menu_items(self):
        """Refresh the menu items list"""
        for item in self.menu_tree.get_children():
            self.menu_tree.delete(item)

        items = self.database.get_all_menu_items()

        self.menu_items_data = {}

        for item in items:
            item_id, name, price, vat_rate, print_receipt, active = item
            self.menu_items_data[name] = {
                'id': item_id,
                'name': name,
                'price': price,
                'vat_rate': vat_rate,
                'print_receipt': print_receipt,
                'active': active
            }

            row_tag = 'evenrow' if len(self.menu_tree.get_children()) % 2 == 0 else 'oddrow'
            self.menu_tree.insert("", "end", values=(
                name,
                f"{price:.2f} €",
                f"{vat_rate:.1f}%",
                "Yes" if print_receipt else "No",
                "Yes" if active else "No"
            ), tags=(row_tag,))

    def on_item_select(self, event):
        """Handle item selection in the tree"""
        selection = self.menu_tree.selection()
        if selection:
            self.selected_tree_item = selection[0]
            item = self.menu_tree.item(self.selected_tree_item)
            values = item['values']

            item_name = values[0]

            if item_name in self.menu_items_data:
                item_data = self.menu_items_data[item_name]
                self.selected_item_id = item_data['id']

                self.current_item_vars['name'].set(item_data['name'])
                self.current_item_vars['price'].set(str(item_data['price']))
                self.current_item_vars['vat_rate'].set(str(item_data['vat_rate']))
                self.current_item_vars['print_receipt'].set(item_data['print_receipt'])
                self.current_item_vars['active'].set(item_data['active'])

                self.save_button.config(state='normal')

    def on_field_change(self, event=None):
        """Handle field changes - enable save button and update display"""
        if hasattr(self, 'save_button') and self.selected_item_id is not None:
            self.save_button.config(state='normal')
            self.update_list_display()

    def update_list_display(self):
        """Update the list display with current form values"""
        if self.selected_item_id is None or self.selected_tree_item is None:
            return

        name = self.current_item_vars['name'].get().strip()
        try:
            price = float(self.current_item_vars['price'].get()) if self.current_item_vars['price'].get().strip() else 0.0
        except ValueError:
            price = 0.0

        try:
            vat_rate = float(self.current_item_vars['vat_rate'].get())
        except ValueError:
            vat_rate = 0.0

        print_receipt = self.current_item_vars['print_receipt'].get()
        active = self.current_item_vars['active'].get()

        display_name = name if name else "[Empty Slot]"
        self.menu_tree.item(self.selected_tree_item, values=(
            display_name,
            f"{price:.2f} €",
            f"{vat_rate:.1f}%",
            "Yes" if print_receipt else "No",
            "Yes" if active else "No"
        ))

        for stored_name, data in list(self.menu_items_data.items()):
            if data['id'] == self.selected_item_id:
                if stored_name != display_name:
                    self.menu_items_data[display_name] = self.menu_items_data.pop(stored_name)
                else:
                    pass

                self.menu_items_data[display_name] = data
                self.menu_items_data[display_name].update({
                    'name': name,
                    'price': price,
                    'vat_rate': vat_rate,
                    'print_receipt': print_receipt,
                    'active': active
                })
                break

    def save_current_item(self):
        """Save current item changes to database"""
        if self.selected_item_id is None:
            return

        try:
            name = self.current_item_vars['name'].get().strip()
            price_str = self.current_item_vars['price'].get().strip()
            price = float(price_str) if price_str else 0.0
            vat_rate = float(self.current_item_vars['vat_rate'].get())
            print_receipt = self.current_item_vars['print_receipt'].get()
            active = self.current_item_vars['active'].get()

            if price < 0:
                messagebox.showerror("Error", "Price cannot be negative")
                return

            if not name:
                active = False

            self.database.update_menu_item(
                self.selected_item_id, name, price,
                vat_rate, print_receipt, active
            )

            self.refresh_menu_items()

            self.save_button.config(state='disabled')

            self.save_button.config(text="Saved!", bg=self.colors['success'])
            self.window.after(1000, lambda: self.save_button.config(text="Save Changes"))

            if self.refresh_callback:
                self.refresh_callback()

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric value for price")

    def on_event_field_change(self, event=None):
        """Handle event field changes - enable save button"""
        if hasattr(self, 'save_button') and hasattr(self, 'original_event_values'):
            current_values = {
                'title': self.event_title_var.get(),
                'company_name': self.company_name_var.get(),
                'company_address': self.company_address_var.get(),
                'company_phone': self.company_phone_var.get(),
                'company_email': self.company_email_var.get(),
                'change_enabled': self.change_var.get()
            }

            if hasattr(self, 'printer_enabled_var'):
                current_values.update({
                    'printer_enabled': self.printer_enabled_var.get(),
                    'printer_type': self.printer_type_var.get(),
                    'printer_interface': self.printer_interface_var.get(),
                    'cash_drawer_enabled': self.cash_drawer_enabled_var.get()
                })

            has_changes = any(
                current_values[key] != self.original_event_values.get(key, '')
                for key in current_values
            )

            if has_changes:
                self.save_button.config(state='normal')

    def on_change_toggle(self):
        """Handle change toggle changes"""
        self.on_event_field_change()

    def enable_save_button(self):
        """Enable the save button"""
        self.save_button.config(state='normal')

    def save_current_changes(self):
        """Save current changes - either menu item or general settings depending on active tab"""
        current_tab = self.notebook.tab(self.notebook.select(), "text")

        if current_tab == "Menu Items" and self.selected_item_id is not None:
            self.save_current_item()
        elif current_tab == "General":
            self.save_event_and_printer_settings()

    def load_current_event(self):
        """Load current event data into form"""
        event = self.database.get_event()
        if event:
            title = event[1] or ""
            company_name = event[2] or ""
            company_address = event[3] or ""
            company_phone = event[4] or ""
            company_email = event[5] or ""
            change_enabled = bool(event[7]) if len(event) > 7 else False

            self.event_title_var.set(title)
            self.company_name_var.set(company_name)
            self.company_address_var.set(company_address)
            self.company_phone_var.set(company_phone)
            self.company_email_var.set(company_email)
            self.change_var.set(change_enabled)

            self.original_event_values = {
                'title': title,
                'company_name': company_name,
                'company_address': company_address,
                'company_phone': company_phone,
                'company_email': company_email,
                'change_enabled': change_enabled
            }
        else:
            self.event_title_var.set("")
            self.company_name_var.set("")
            self.company_address_var.set("")
            self.company_phone_var.set("")
            self.company_email_var.set("")
            self.change_var.set(False)

            self.original_event_values = {
                'title': "",
                'company_name': "",
                'company_address': "",
                'company_phone': "",
                'company_email': "",
                'change_enabled': False
            }

    def save_event_and_printer_settings(self):
        """Save both event and printer configuration"""
        title = self.event_title_var.get().strip()
        company_name = self.company_name_var.get().strip()
        company_address = self.company_address_var.get().strip()
        company_phone = self.company_phone_var.get().strip()
        company_email = self.company_email_var.get().strip()
        change_enabled = self.change_var.get()

        if not title:
            messagebox.showerror("Error", "Business title is required")
            return

        try:
            self.database.save_event(
                title, company_name, company_address, company_phone, company_email,
                change_enabled=change_enabled,
                printer_enabled=self.printer_enabled_var.get(),
                printer_type=self.printer_type_var.get(),
                printer_interface=self.printer_interface_var.get().strip(),
                cash_drawer_enabled=self.cash_drawer_enabled_var.get()
            )

            self.original_event_values = {
                'title': title,
                'company_name': company_name,
                'company_address': company_address,
                'company_phone': company_phone,
                'company_email': company_email,
                'change_enabled': change_enabled,
                'printer_enabled': self.printer_enabled_var.get(),
                'printer_type': self.printer_type_var.get(),
                'printer_interface': self.printer_interface_var.get(),
                'cash_drawer_enabled': self.cash_drawer_enabled_var.get()
            }

            self.save_button.config(state='disabled')

            self.save_button.config(text="Saved!", bg=self.colors['success'])
            self.window.after(1000, lambda: self.save_button.config(text="Save Changes"))

            if self.refresh_callback:
                self.refresh_callback()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def save_event(self):
        """Save event configuration (legacy method for compatibility)"""
        self.save_event_and_printer_settings()


    def export_event(self):
        """Export menu items to JSON file"""
        filename = filedialog.asksaveasfilename(
            title="Export Menu Items",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=".",
            initialfile=f"bonkasse_menu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if filename:
            try:
                self.database.export_database(filename)
                messagebox.showinfo("Success", f"Menu items exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export menu items: {e}")

    def import_event(self):
        """Import menu items from JSON file"""
        filename = filedialog.askopenfilename(
            title="Import Menu Items",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="."
        )

        if not filename:
            return

        if not messagebox.askyesno("Import Menu Items",
                                  "This will replace all your current menu items.\n\n"
                                  "Your current menu items will be backed up automatically.\n\n"
                                  "Event settings, printer settings, and transactions will NOT be affected.\n\n"
                                  "Are you sure you want to continue?"):
            return

        try:
            self.database.import_database(filename, backup_current=True)

            self.refresh_menu_items()

            if self.refresh_callback:
                self.refresh_callback()

            messagebox.showinfo("Success", "Menu items imported successfully!\n\n"
                                          "Your previous menu items have been backed up.\n"
                                          "Session sales have been reset.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import menu items: {e}")

    def refresh_transactions(self):
        """Refresh the transactions list"""
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)

        transactions = self.database.get_all_transactions()

        for transaction in transactions:
            transaction_id, timestamp, total, items_json = transaction

            try:
                items = json.loads(items_json)

                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')

                for item in items:
                    item_name = item.get('name', 'Unknown Item')
                    item_price = item.get('price', 0.0)
                    item_vat = item.get('vat_rate', 0.0)
                    quantity = item.get('quantity', 1)

                    for _ in range(quantity):
                        row_tag = 'evenrow' if len(self.transactions_tree.get_children()) % 2 == 0 else 'oddrow'
                        self.transactions_tree.insert("", "end", values=(
                            formatted_time,
                            item_name,
                            f"{item_price:.2f} €",
                            f"{item_vat:.1f}%"
                        ), tags=(row_tag,))

            except (json.JSONDecodeError, ValueError) as e:
                row_tag = 'evenrow' if len(self.transactions_tree.get_children()) % 2 == 0 else 'oddrow'
                self.transactions_tree.insert("", "end", values=(
                    timestamp,
                    "Error parsing transaction",
                    "€0.00",
                    "0.0%"
                ), tags=(row_tag,))

    def export_transactions_csv(self):
        """Export transactions to CSV file"""
        filename = filedialog.asksaveasfilename(
            title="Export Transactions",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=".",
            initialfile=f"bonkasse_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if not filename:
            return

        try:
            transactions = self.database.get_all_transactions()

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                writer.writerow(['Date/Time', 'Item Name', 'Price', 'VAT %'])

                for transaction in transactions:
                    transaction_id, timestamp, total, items_json = transaction

                    try:
                        items = json.loads(items_json)

                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')

                        for item in items:
                            item_name = item.get('name', 'Unknown Item')
                            item_price = item.get('price', 0.0)
                            item_vat = item.get('vat_rate', 0.0)
                            quantity = item.get('quantity', 1)

                            for _ in range(quantity):
                                writer.writerow([
                                    formatted_time,
                                    item_name,
                                    f"{item_price:.2f}",
                                    f"{item_vat:.1f}"
                                ])

                    except (json.JSONDecodeError, ValueError):
                        writer.writerow([
                            timestamp,
                            "Error parsing transaction",
                            "0.00",
                            "0.0"
                        ])

            messagebox.showinfo("Success", f"Transactions exported to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export transactions: {e}")

    def delete_all_transactions(self):
        """Delete all transactions from the current event"""
        transactions = self.database.get_all_transactions()
        transaction_count = len(transactions)

        if transaction_count == 0:
            messagebox.showinfo("No Transactions", "There are no transactions to delete.")
            return

        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete all {transaction_count} transaction(s)?\n\n"
            "This action cannot be undone."
        )

        if result:
            try:
                self.database.delete_all_transactions()
                self.refresh_transactions()
                messagebox.showinfo("Success", f"All {transaction_count} transactions have been deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete transactions: {e}")

    def print_transactions_dialog(self):
        """Show dialog to choose print options"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Print Transactions")
        dialog.geometry("500x550")
        dialog.configure(bg=self.colors['bg_primary'])
        dialog.transient(self.window)
        dialog.grab_set()

        try:
            dialog.iconbitmap("assets/icon.ico")
        except tk.TclError:
            try:
                icon_photo = tk.PhotoImage(file="assets/icon.png")
                dialog.iconphoto(True, icon_photo)
            except tk.TclError:
                pass

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (550 // 2)
        dialog.geometry(f"500x550+{x}+{y}")

        main_frame = tk.Frame(dialog, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        title_label = tk.Label(main_frame, text="Print Transaction Summary",
                              font=('Arial', 16, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=self.colors['bg_primary'])
        title_label.pack(pady=(0, 20))

        print_option = tk.StringVar(value="all")

        all_radio = tk.Radiobutton(main_frame, text="Print All Transactions Summary",
                                  variable=print_option, value="all",
                                  font=('Arial', 12),
                                  fg=self.colors['text_primary'],
                                  bg=self.colors['bg_primary'],
                                  selectcolor=self.colors['bg_secondary'])
        all_radio.pack(anchor=tk.W, pady=(0, 10))

        date_radio = tk.Radiobutton(main_frame, text="Print Summary for Specific Date",
                                   variable=print_option, value="date",
                                   font=('Arial', 12),
                                   fg=self.colors['text_primary'],
                                   bg=self.colors['bg_primary'],
                                   selectcolor=self.colors['bg_secondary'])
        date_radio.pack(anchor=tk.W, pady=(0, 20))

        date_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        date_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        tk.Label(date_frame, text="Select Date:",
                font=('Arial', 10, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_primary']).pack(anchor=tk.W, pady=(0, 15))

        calendar = Calendar(date_frame,
                           selectmode='day',
                           date_pattern='yyyy-mm-dd',
                           font=('Arial', 11),
                           cursor='hand2',
                           borderwidth=2,
                           background='white',
                           foreground='black',
                           selectbackground='#0078d4',
                           selectforeground='white',
                           normalbackground='white',
                           normalforeground='black',
                           weekendbackground='#f0f0f0',
                           weekendforeground='black',
                           headersbackground='#e0e0e0',
                           headersforeground='black',
                           showweeknumbers=False,
                           firstweekday='monday')
        calendar.pack(pady=(0, 20), padx=20, fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        button_frame.pack(fill=tk.X, pady=(20, 0))

        def on_print():
            option = print_option.get()
            if option == "all":
                self.print_all_transactions_summary()
            elif option == "date":
                try:
                    selected_date = calendar.get_date()
                    self.print_transactions_summary_for_date(selected_date)
                except Exception as e:
                    messagebox.showerror("Error", f"Error getting selected date: {e}")
                    return
            dialog.destroy()

        print_btn = tk.Button(button_frame, text="Print",
                             command=on_print,
                             font=('Arial', 10, 'bold'),
                             fg='white', bg=self.colors['success'],
                             relief='flat', bd=0, cursor='hand2')
        print_btn.pack(side=tk.RIGHT, padx=(10, 0), ipady=8, ipadx=20)

        cancel_btn = tk.Button(button_frame, text="Cancel",
                              command=dialog.destroy,
                              font=('Arial', 10, 'bold'),
                              fg='white', bg=self.colors['danger'],
                              relief='flat', bd=0, cursor='hand2')
        cancel_btn.pack(side=tk.RIGHT, ipady=8, ipadx=20)

    def print_all_transactions_summary(self):
        """Print summary of all transactions (quantities per item and totals)"""
        transactions = self.database.get_all_transactions()

        if not transactions:
            messagebox.showinfo("Print Summary", "No transactions found.")
            return

        item_summary = {}
        total_revenue = 0.0

        for transaction in transactions:
            transaction_id, timestamp, total, items_json = transaction
            total_revenue += total

            try:
                items = json.loads(items_json)

                for item in items:
                    item_name = item.get('name', 'Unknown Item')
                    item_price = item.get('price', 0.0)
                    quantity = item.get('quantity', 1)

                    for _ in range(quantity):
                        if item_name in item_summary:
                            item_summary[item_name]['count'] += 1
                            item_summary[item_name]['total'] += item_price
                        else:
                            item_summary[item_name] = {
                                'count': 1,
                                'price': item_price,
                                'total': item_price
                            }

            except (json.JSONDecodeError, ValueError):
                continue

        self._print_item_summary(item_summary, total_revenue, "ALL TRANSACTIONS SUMMARY")

    def _print_item_summary(self, item_summary, total_revenue, title):
        """Helper method to print item summary using printer or console"""
        if not item_summary:
            messagebox.showinfo("Print Summary", "No items found to summarize.")
            return

        event = self.database.get_event()
        printer_enabled = bool(event[8]) if event and len(event) > 8 else False

        if not printer_enabled:
            print(f"\n{'=' * 50}")
            print(title)
            print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'=' * 50}")

            for item_name, data in item_summary.items():
                print(f"{data['count']:>3} x {item_name:<30} {data['total']:>8.2f} €")

            print(f"{'-' * 50}")
            print(f"{'TOTAL REVENUE':<35} {total_revenue:>8.2f} €")
            print(f"{'ITEMS SOLD':<35} {sum(data['count'] for data in item_summary.values()):>8}")
            print(f"{'=' * 50}\n")

            total_items = sum(data['count'] for data in item_summary.values())
            messagebox.showinfo("Print Complete", f"Summary printed to console.\nTotal Revenue: {total_revenue:.2f} €\nItems Sold: {total_items}")
            return

        try:
            from ..services.printer_service import PrinterService

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

            summary_data = {}
            for i, (item_name, data) in enumerate(item_summary.items()):
                summary_data[i] = {
                    'name': item_name,
                    'price': data['price'],
                    'count': data['count']
                }

            success = printer_service.print_transaction_summary(summary_data, total_revenue)
            if success:
                total_items = sum(data['count'] for data in item_summary.values())
                messagebox.showinfo("Print Complete", f"Summary printed successfully!\nTotal Revenue: {total_revenue:.2f} €\nItems Sold: {total_items}")
            else:
                messagebox.showwarning("Print Summary", "Failed to print. Check printer connection.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to print summary: {e}")

    def print_transactions_summary_for_date(self, date_str):
        """Print summary of transactions for a specific date (quantities per item and totals)"""
        transactions = self.database.get_all_transactions()

        filtered_transactions = []
        for transaction in transactions:
            transaction_id, timestamp, total, items_json = transaction

            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                transaction_date = dt.strftime('%Y-%m-%d')

                if transaction_date == date_str:
                    filtered_transactions.append(transaction)
            except ValueError:
                continue

        if not filtered_transactions:
            messagebox.showinfo("No Data", f"No transactions found for {date_str}")
            return

        item_summary = {}
        total_revenue = 0.0

        for transaction in filtered_transactions:
            transaction_id, timestamp, total, items_json = transaction
            total_revenue += total

            try:
                items = json.loads(items_json)

                for item in items:
                    item_name = item.get('name', 'Unknown Item')
                    item_price = item.get('price', 0.0)
                    quantity = item.get('quantity', 1)

                    for _ in range(quantity):
                        if item_name in item_summary:
                            item_summary[item_name]['count'] += 1
                            item_summary[item_name]['total'] += item_price
                        else:
                            item_summary[item_name] = {
                                'count': 1,
                                'price': item_price,
                                'total': item_price
                            }

            except (json.JSONDecodeError, ValueError):
                continue

        self._print_item_summary(item_summary, total_revenue, f"TRANSACTIONS SUMMARY - {date_str}")

    def print_session_summary(self):
        """Print session sales summary"""
        from ..services.printer_service import PrinterService
        from datetime import datetime

        session_sales = self.database.get_all_session_sales()
        menu_items = self.database.get_menu_items()

        if not session_sales:
            messagebox.showinfo("Session Summary", "No sales recorded in current session.")
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
            messagebox.showinfo("Session Summary", "No items sold in current session.")
            return

        event = self.database.get_event()
        printer_enabled = bool(event[8]) if event and len(event) > 8 else False

        if not printer_enabled:
            print(f"\n{'=' * 50}")
            print("SESSION SALES SUMMARY")
            print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'=' * 50}")

            for item_data in summary_data.values():
                print(f"{item_data['count']:>3} x {item_data['name']:<30} {item_data['total']:>8.2f} €")

            print(f"{'-' * 50}")
            print(f"{'TOTAL REVENUE':<35} {total_revenue:>8.2f} €")
            print(f"{'ITEMS SOLD':<35} {sum(item['count'] for item in summary_data.values()):>8}")
            print(f"{'=' * 50}\n")

            messagebox.showinfo("Session Summary", f"Summary printed to console.\nTotal Revenue: {total_revenue:.2f} €\nItems Sold: {sum(item['count'] for item in summary_data.values())}")
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
                total_items = sum(item['count'] for item in summary_data.values())
                messagebox.showinfo("Session Summary", f"Summary printed successfully!\nTotal Revenue: {total_revenue:.2f} €\nItems Sold: {total_items}")
            else:
                messagebox.showwarning("Session Summary", "Failed to print. Check printer connection.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to print session summary: {e}")

    def on_printer_type_changed(self, event=None):
        """Handle printer type selection change"""
        self.update_printer_interface_help()
        self.on_printer_settings_changed()

    def update_printer_interface_help(self):
        """Update the help text based on selected printer type"""
        printer_type = self.printer_type_var.get()

        if printer_type == "windows":
            self.connection_help_label.config(text="Windows: Printer name (e.g., EPSON TM-T88IV Receipt)")
            self.auto_detect_btn.config(state='disabled')
        elif printer_type == "usb":
            self.connection_help_label.config(text="USB: vendor_id:product_id (e.g., 04b8:0202) or leave blank for auto-detect")
            self.auto_detect_btn.config(state='normal')
        elif printer_type == "network":
            self.connection_help_label.config(text="Network: IP address or hostname (e.g., 192.168.1.100)")
            self.auto_detect_btn.config(state='disabled')
        elif printer_type == "serial":
            self.connection_help_label.config(text="Serial: COM port (e.g., COM1, COM2)")
            self.auto_detect_btn.config(state='disabled')

    def auto_detect_printer(self):
        """Auto-detect USB printer"""
        try:
            from ..services.printer_service import PrinterService
            printer_service = PrinterService()
            available_printers = printer_service.get_available_usb_printers()

            if available_printers:
                self.show_printer_selection_dialog(available_printers)
            else:
                messagebox.showinfo("Auto-detect", "No USB printers found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to auto-detect printers: {e}")

    def show_printer_selection_dialog(self, printers):
        """Show dialog to select from detected printers"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Select Printer")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors['bg_primary'])
        dialog.transient(self.window)
        dialog.grab_set()

        try:
            dialog.iconbitmap("assets/icon.ico")
        except tk.TclError:
            try:
                icon_photo = tk.PhotoImage(file="assets/icon.png")
                dialog.iconphoto(True, icon_photo)
            except tk.TclError:
                pass

        tk.Label(dialog, text="Select USB Printer:",
                font=('Arial', 12, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_primary']).pack(pady=10)

        listbox_frame = tk.Frame(dialog, bg=self.colors['bg_primary'])
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar_dialog = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
        printer_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar_dialog.set, font=('Arial', 10))
        scrollbar_dialog.config(command=printer_listbox.yview)

        for printer in printers:
            display_text = f"{printer['name']} ({printer['vendor_id']}:{printer['product_id']})"
            printer_listbox.insert(tk.END, display_text)

        printer_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_dialog.pack(side=tk.RIGHT, fill=tk.Y)

        button_frame = tk.Frame(dialog, bg=self.colors['bg_primary'])
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def select_printer():
            selection = printer_listbox.curselection()
            if selection:
                selected_printer = printers[selection[0]]
                if selected_printer['vendor_id'] == "auto":
                    self.printer_interface_var.set("")
                else:
                    interface_value = f"{selected_printer['vendor_id']}:{selected_printer['product_id']}"
                    self.printer_interface_var.set(interface_value)
                self.on_printer_settings_changed()
                dialog.destroy()

        select_btn = tk.Button(button_frame, text="Select",
                             command=select_printer,
                             font=('Arial', 10, 'bold'),
                             fg='white', bg=self.colors['success'],
                             relief='flat', bd=0, cursor='hand2')
        select_btn.pack(side=tk.RIGHT, padx=(10, 0), ipady=5, ipadx=15)

        cancel_btn = tk.Button(button_frame, text="Cancel",
                             command=dialog.destroy,
                             font=('Arial', 10, 'bold'),
                             fg='white', bg=self.colors['danger'],
                             relief='flat', bd=0, cursor='hand2')
        cancel_btn.pack(side=tk.RIGHT, ipady=5, ipadx=15)

    def load_printer_settings(self):
        """Load printer settings from database"""
        event = self.database.get_event()
        if event and len(event) > 8:
            self.printer_enabled_var.set(bool(event[8]) if len(event) > 8 else False)
            self.printer_type_var.set(event[9] if len(event) > 9 else "usb")
            self.printer_interface_var.set(event[10] if len(event) > 10 else "")
            self.cash_drawer_enabled_var.set(bool(event[11]) if len(event) > 11 else True)

        self.original_event_values.update({
            'printer_enabled': self.printer_enabled_var.get(),
            'printer_type': self.printer_type_var.get(),
            'printer_interface': self.printer_interface_var.get(),
            'cash_drawer_enabled': self.cash_drawer_enabled_var.get()
        })

    def on_printer_settings_changed(self):
        """Handle printer settings changes"""
        self.on_event_field_change()
        self.update_printer_status()

    def update_printer_status(self):
        """Update printer status based on current settings"""
        if self.printer_enabled_var.get():
            printer_type = self.printer_type_var.get()
            interface = self.printer_interface_var.get().strip()

            if not interface and printer_type != "usb":
                status = "Status: Missing connection details"
                color = self.colors['warning']
            else:
                status = f"Status: Configured ({printer_type.upper()})"
                color = self.colors['success']
        else:
            status = "Status: Disabled"
            color = self.colors['text_secondary']

        self.printer_status_label.config(text=status, fg=color)

    def test_printer(self):
        """Test printer functionality"""
        try:
            from ..services.printer_service import PrinterService

            printer_service = PrinterService()
            printer_service.configure_printer(
                self.printer_type_var.get(),
                self.printer_interface_var.get().strip(),
                self.printer_enabled_var.get(),
                self.cash_drawer_enabled_var.get()
            )

            event = self.database.get_event()
            if event:
                company_info = {
                    'company_name': event[2] if len(event) > 2 else '',
                    'company_address': event[3] if len(event) > 3 else '',
                    'company_phone': event[4] if len(event) > 4 else '',
                    'title': event[1] if len(event) > 1 else ''
                }
                printer_service.set_company_info(company_info)

            success = printer_service.test_print()
            if success:
                messagebox.showinfo("Test Print", "Test print completed successfully!")
            else:
                messagebox.showwarning("Test Print", "Test print failed. Check printer connection and settings.")

        except Exception as e:
            messagebox.showerror("Test Print Error", f"Failed to test printer: {e}")

    def test_cash_drawer(self):
        """Test cash drawer functionality"""
        if not self.cash_drawer_enabled_var.get():
            messagebox.showwarning("Cash Drawer", "Cash drawer is disabled in settings.")
            return

        try:
            from ..services.printer_service import PrinterService

            printer_service = PrinterService()
            printer_service.configure_printer(
                self.printer_type_var.get(),
                self.printer_interface_var.get().strip(),
                self.printer_enabled_var.get(),
                self.cash_drawer_enabled_var.get()
            )

            if printer_service.is_printer_ready():
                printer_service._open_cash_drawer()
                messagebox.showinfo("Cash Drawer", "Cash drawer command sent successfully!")
            else:
                messagebox.showwarning("Cash Drawer", "Printer not ready. Check connection and settings.")

        except Exception as e:
            messagebox.showerror("Cash Drawer Error", f"Failed to open cash drawer: {e}")


    def update_password_status(self):
        """Update the password status display"""
        password_hash = self.database.get_password_hash()
        if password_hash:
            self.password_status_var.set("Password: Set")
            self.remove_password_btn.config(state=tk.NORMAL)
        else:
            self.password_status_var.set("Password: Not Set")
            self.remove_password_btn.config(state=tk.DISABLED)

    def change_password(self):
        """Handle changing password"""
        from .password_dialog import PasswordDialog

        current_hash = self.database.get_password_hash()

        if current_hash:
            dialog = PasswordDialog(self.window, self.colors, "Enter Current Password")
            success, current_password = dialog.show()

            if not success:
                return

            if not PasswordDialog.verify_password(current_password, current_hash):
                messagebox.showerror("Access Denied", "Incorrect current password")
                return

        dialog = PasswordDialog(self.window, self.colors, "Enter New Password")
        success, new_password = dialog.show()

        if not success or not new_password:
            return

        dialog = PasswordDialog(self.window, self.colors, "Confirm New Password")
        success, confirm_password = dialog.show()

        if not success or new_password != confirm_password:
            if success:
                messagebox.showerror("Error", "Passwords do not match")
            return

        new_hash = PasswordDialog.hash_password(new_password)
        self.database.set_password_hash(new_hash)
        self.update_password_status()

        messagebox.showinfo("Success", "Password has been updated successfully")

    def remove_password(self):
        """Handle removing password"""
        from .password_dialog import PasswordDialog

        current_hash = self.database.get_password_hash()
        if not current_hash:
            return

        dialog = PasswordDialog(self.window, self.colors, "Enter Current Password to Remove")
        success, current_password = dialog.show()

        if not success:
            return

        if not PasswordDialog.verify_password(current_password, current_hash):
            messagebox.showerror("Access Denied", "Incorrect password")
            return

        result = messagebox.askyesno("Confirm", "Are you sure you want to remove the password?\n\nSettings will be accessible without password protection.")

        if result:
            self.database.clear_password()
            self.update_password_status()
            messagebox.showinfo("Success", "Password protection has been removed")

    def close_window(self):
        """Close the settings window"""
        self.window.destroy()


if __name__ == "__main__":
    from ..exceptions import DoNotRunDirectly
    raise DoNotRunDirectly(__name__)