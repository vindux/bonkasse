"""
Total button component for Bonkasse
Large button displaying total and handling receipt printing
"""

import tkinter as tk
from typing import Callable
from .components import BaseComponent


class TotalButton(BaseComponent):
    """Large total/print receipt button"""

    def __init__(self, parent, on_print_receipt: Callable, colors: dict = None):
        super().__init__(parent)
        self.on_print_receipt = on_print_receipt
        self.colors = colors or {
            'success': '#198754',
            'success_disabled': '#6c757d',
            'bg_secondary': '#ffffff',
            'text_primary': '#212529'
        }
        if colors:
            self.colors['success_disabled'] = colors.get('bg_accent', '#e9ecef')
        self.system_mode = False
        self.total_var = None
        self.button = None
        self.create_widget()

    def create_widget(self):
        """Create the total button widget"""
        self.frame = tk.Frame(self.parent, bg=self.colors['bg_primary'])

        self.total_var = tk.StringVar(value="€0.00\nPrint Receipt")
        self.button = tk.Button(
            self.frame,
            textvariable=self.total_var,
            font=('Arial', 18, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['success_disabled'],
            relief='flat',
            bd=0,
            command=self.on_print_receipt,
            cursor='hand2',
            state='disabled',
            justify='center'
        )
        self.button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def update_total(self, total: float):
        """Update the total display"""
        self.total_var.set(f"{total:.2f} €\nPrint Receipt")

        if self.system_mode:
            return

        if total > 0:
            self.button.config(state='normal', bg=self.colors['success'], fg='white', cursor='hand2')
        else:
            self.button.config(state='disabled', bg=self.colors['success_disabled'], fg=self.colors['text_primary'], cursor='arrow')

    def enable(self):
        """Enable the button"""
        self.button.config(state='normal', bg=self.colors['success'], fg='white', cursor='hand2')

    def disable(self):
        """Disable the button"""
        self.button.config(state='disabled', bg=self.colors['success_disabled'], fg=self.colors['text_primary'], cursor='arrow')

    def set_system_mode(self, system_mode: bool):
        """Enable or disable the button based on system mode"""
        self.system_mode = system_mode

        if system_mode:
            self.button.config(state='disabled', bg='#cccccc', fg='#666666', cursor='X_cursor')
        else:
            current_text = self.button.cget('text')
            if '€0.00' in current_text:
                self.disable()
            else:
                self.enable()


if __name__ == "__main__":
    import sys
    print(f"Error: This module should not be run directly. Please run main.py instead.")
    sys.exit(1)
