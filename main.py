#!/usr/bin/env python3

import tkinter as tk
from bonkasse.app import BonkasseApp


def main():
    root = tk.Tk()
    app = BonkasseApp(root)

    try:
        app.run()
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()