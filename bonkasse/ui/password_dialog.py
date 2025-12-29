import tkinter as tk
from tkinter import messagebox
import hashlib


class PasswordDialog:

    def __init__(self, parent, colors, title="Enter Password"):
        self.parent = parent
        self.colors = colors
        self.title = title
        self.password = None
        self.result = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x150")
        self.dialog.configure(bg=colors['bg_primary'])
        self.dialog.resizable(False, False)

        try:
            self.dialog.iconbitmap("assets/icon.ico")
        except tk.TclError:
            try:
                icon_photo = tk.PhotoImage(file="assets/icon.png")
                self.dialog.iconphoto(True, icon_photo)
            except tk.TclError:
                pass

        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.center_on_parent()

        self.create_ui()

        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)

        self.password_entry.focus_set()

    def center_on_parent(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()

        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        dialog_width = self.dialog.winfo_reqwidth()
        dialog_height = self.dialog.winfo_reqheight()

        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)

        self.dialog.geometry(f"+{x}+{y}")

    def create_ui(self):
        """Create the password dialog UI"""
        main_frame = tk.Frame(self.dialog, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        title_label = tk.Label(
            main_frame,
            text=self.title,
            font=('Arial', 12, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_primary']
        )
        title_label.pack(pady=(0, 15))

        self.password_entry = tk.Entry(
            main_frame,
            font=('Arial', 11),
            show='*',
            width=25,
            justify='center'
        )
        self.password_entry.pack(pady=(0, 15))
        self.password_entry.bind('<Return>', self.on_ok)

        button_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        button_frame.pack()

        ok_button = tk.Button(
            button_frame,
            text="OK",
            command=self.on_ok,
            font=('Arial', 10, 'bold'),
            fg='white',
            bg=self.colors['success'],
            relief='flat',
            bd=0,
            cursor='hand2',
            width=8
        )
        ok_button.pack(side=tk.LEFT, padx=(0, 10))

        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            font=('Arial', 10, 'bold'),
            fg='white',
            bg=self.colors['danger'],
            relief='flat',
            bd=0,
            cursor='hand2',
            width=8
        )
        cancel_button.pack(side=tk.LEFT)

    def on_ok(self, event=None):
        """Handle OK button click"""
        self.password = self.password_entry.get()
        if self.password:
            self.result = True
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Please enter a password")

    def on_cancel(self, event=None):
        """Handle Cancel button click"""
        self.result = False
        self.dialog.destroy()

    def show(self):
        """Show the dialog and return the result"""
        self.dialog.wait_window()
        return self.result, self.password

    @staticmethod
    def hash_password(password):
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_password(password, password_hash):
        """Verify a password against its hash"""
        return PasswordDialog.hash_password(password) == password_hash


if __name__ == "__main__":
    import sys
    print(f"Error: This module should not be run directly. Please run main.py instead.")
    sys.exit(1)