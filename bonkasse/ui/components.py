"""
Base UI components and utilities for Bonkasse
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod


class BaseComponent(ABC):
    """Base class for all UI components"""

    def __init__(self, parent):
        self.parent = parent
        self.frame = None

    @abstractmethod
    def create_widget(self):
        """Create the widget - must be implemented by subclasses"""
        pass

    def pack(self, **kwargs):
        """Pack the component's frame"""
        if self.frame:
            self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the component's frame"""
        if self.frame:
            self.frame.grid(**kwargs)


if __name__ == "__main__":
    import sys
    print(f"Error: This module should not be run directly. Please run main.py instead.")
    sys.exit(1)