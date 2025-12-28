"""
Change calculation modal for displaying euro notes and change amounts
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os


class ChangeModal:
    """Modal window for calculating and displaying change for euro notes"""

    def __init__(self, parent, total_amount, colors):
        self.parent = parent
        self.total_amount = total_amount
        self.colors = colors

        self.euro_notes = [5, 10, 20, 50, 100]

        applicable_notes = [note for note in self.euro_notes if note >= total_amount]
        window_width = max(400, 100 + (len(applicable_notes) * 130))
        window_height = 300

        self.window = tk.Toplevel(parent)
        self.window.title("Change Calculator")
        self.window.geometry(f"{window_width}x{window_height}")
        self.window.configure(bg=colors['bg_primary'])
        self.window.transient(parent)
        self.window.grab_set()

        self.window.geometry(f"{window_width}x{window_height}")

        self.window.bind("<Button-1>", self.close_modal)

        self.window.focus_set()
        self.window.focus_force()

        self.window.attributes('-topmost', True)

        self.window.after(100, self.setup_key_bindings)

        self.create_ui()

        self.center_window()

    def create_ui(self):
        """Create the modal UI"""
        title_label = tk.Label(
            self.window,
            text=f"Total: {self.total_amount:.2f} €",
            font=('Arial', 16, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_primary']
        )
        title_label.pack(pady=20)

        subtitle_label = tk.Label(
            self.window,
            text="Select payment amount:",
            font=('Arial', 12),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_primary']
        )
        subtitle_label.pack(pady=(0, 20))

        notes_frame = tk.Frame(self.window, bg=self.colors['bg_primary'])
        notes_frame.pack(pady=10)

        applicable_notes = [note for note in self.euro_notes if note >= self.total_amount]

        if not applicable_notes:
            no_change_label = tk.Label(
                notes_frame,
                text="Amount exceeds largest note denomination",
                font=('Arial', 12),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_primary']
            )
            no_change_label.pack(pady=20)
        else:
            for col, note in enumerate(applicable_notes):
                change_amount = note - self.total_amount

                note_frame = tk.Frame(notes_frame, bg=self.colors['bg_secondary'], relief='raised', bd=2)
                note_frame.grid(row=0, column=col, padx=10, pady=10, sticky='nsew')

                image_label = self.create_note_image(note_frame, note)
                image_label.pack(padx=5, pady=5)

                if change_amount == 0:
                    change_text = "0.00 €"
                else:
                    change_text = f"{change_amount:.2f} €"

                change_label = tk.Label(
                    note_frame,
                    text=change_text,
                    font=('Arial', 12, 'bold'),
                    fg=self.colors['text_primary'],
                    bg=self.colors['bg_secondary']
                )
                change_label.pack(pady=(0, 5))

                note_frame.bind("<Button-1>", self.close_modal)
                image_label.bind("<Button-1>", self.close_modal)
                change_label.bind("<Button-1>", self.close_modal)

            for i in range(len(applicable_notes)):
                notes_frame.columnconfigure(i, weight=1)
            notes_frame.rowconfigure(0, weight=1)

        instructions_label = tk.Label(
            self.window,
            text="Click anywhere or press any key to close",
            font=('Arial', 10, 'italic'),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_primary']
        )
        instructions_label.pack(side=tk.BOTTOM, pady=20)

    def create_note_image(self, parent, note_value):
        """Create image label for euro note"""
        try:
            image_filename = f"{note_value:02d}.png"
            image_path = os.path.join("assets", image_filename)

            pil_image = Image.open(image_path)
            pil_image = pil_image.resize((100, 50), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(pil_image)

            image_label = tk.Label(
                parent,
                image=photo,
                bg=self.colors['bg_secondary'],
                relief='sunken',
                bd=1
            )
            image_label.image = photo

            return image_label

        except (FileNotFoundError, Exception) as e:
            return tk.Label(
                parent,
                text=f"{note_value} €",
                font=('Arial', 12, 'bold'),
                fg=self.colors['text_primary'],
                bg=self.colors['bg_secondary'],
                width=8,
                height=4,
                relief='sunken',
                bd=1
            )

    def setup_key_bindings(self):
        """Set up key bindings after a short delay to avoid immediate closure"""
        if self.window.winfo_exists():
            self.window.bind_all("<KeyPress>", self.on_key_press)

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()

        width = self.window.winfo_width()
        height = self.window.winfo_height()

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def on_key_press(self, event):
        """Handle any key press to close modal"""
        self.close_modal()
        return "break"

    def close_modal(self, event=None):
        """Close the modal window"""
        try:
            self.window.unbind_all("<KeyPress>")
        except:
            pass
        self.window.destroy()


if __name__ == "__main__":
    from .exceptions import DoNotRunDirectly
    raise DoNotRunDirectly(__name__)