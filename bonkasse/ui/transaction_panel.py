"""
Transaction panel component for Bonkasse
Displays current order with scrollable list and controls
"""

import tkinter as tk
from tkinter import ttk
from .components import BaseComponent


class TransactionPanel(BaseComponent):
    """Current order panel with scrollable list"""

    def __init__(self, parent, colors: dict = None):
        super().__init__(parent)
        self.listbox = None
        self.colors = colors or {
            'bg_primary': '#f8f9fa',
            'bg_secondary': '#ffffff',
            'text_primary': '#212529',
            'text_secondary': '#6c757d',
            'border': '#dee2e6'
        }
        self.create_widget()

    def create_widget(self):
        """Create the transaction panel widget"""
        self.frame = tk.Frame(self.parent, bg=self.colors['bg_secondary'], relief='solid', bd=1)

        title_label = tk.Label(self.frame, text="Current Order", font=('Arial', 12, 'bold'),
                              fg=self.colors['text_primary'], bg=self.colors['bg_secondary'])
        title_label.pack(pady=(8, 5))

        listbox_frame = tk.Frame(self.frame, bg=self.colors['bg_secondary'])
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.listbox = tk.Listbox(
            listbox_frame,
            font=('Courier New', 14),
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            selectbackground=self.colors['bg_primary'],
            selectforeground=self.colors['text_primary'],
            relief='flat',
            bd=0,
            highlightthickness=1,
            highlightcolor=self.colors['border'],
            highlightbackground=self.colors['border'],
            exportselection=False,
            selectmode=tk.NONE,
            activestyle='none'
        )
        scrollbar = tk.Scrollbar(
            listbox_frame,
            orient=tk.VERTICAL,
            command=self.listbox.yview,
            bg=self.colors['bg_secondary'],
            troughcolor=self.colors['bg_primary'],
            width=12
        )
        self.listbox.configure(yscrollcommand=scrollbar.set)

        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def add_item(self, name: str, price: float):
        """Add an item to the display list"""
        self.listbox.insert(tk.END, f"{name:<20} {price:>6.2f} €")
        self.listbox.see(tk.END)

    def remove_last_item(self):
        """Remove the last item from the display list"""
        last_index = self.listbox.size() - 1
        if last_index >= 0:
            self.listbox.delete(last_index)

    def clear_all(self):
        """Clear all items from the display list"""
        self.listbox.delete(0, tk.END)


if __name__ == "__main__":
    import sys
    print(f"Error: This module should not be run directly. Please run main.py instead.")
    sys.exit(1)