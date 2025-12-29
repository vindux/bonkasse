"""
Menu grid component for Bonkasse
Displays menu items in a 3-column grid layout
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable
from .components import BaseComponent


class MenuGrid(BaseComponent):
    """3-column grid of menu item buttons"""

    def __init__(self, parent, menu_items: List[tuple], on_item_click: Callable, colors: dict = None, database=None):
        super().__init__(parent)
        self.menu_items = menu_items
        self.on_item_click = on_item_click
        self.database = database
        self.system_mode = False
        self.data_changed_in_system_mode = False
        self.original_widget_states = {}
        self.colors = colors or {
            'bg_primary': '#f8f9fa',
            'bg_secondary': '#ffffff',
            'text_primary': '#212529',
            'accent': '#0d6efd',
            'border': '#dee2e6'
        }
        self.create_widget()

    def create_widget(self):
        """Create the menu grid widget"""
        self.frame = tk.Frame(self.parent, bg=self.colors['bg_secondary'], relief='solid', bd=1)
        self._create_grid_content()

    def _create_grid_content(self):
        """Create the grid content inside the existing frame"""
        title_label = tk.Label(self.frame, text="Menu Items", font=('Arial', 12, 'bold'),
                              fg=self.colors['text_primary'], bg=self.colors['bg_secondary'])
        title_label.pack(pady=(8, 5))

        grid_frame = tk.Frame(self.frame, bg=self.colors['bg_secondary'])
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        if not hasattr(self, 'item_panels'):
            self.item_panels = {}
        for i, item in enumerate(self.menu_items):
            if len(item) == 3:
                item_id, name, price = item
                active = True
            elif len(item) == 5:
                item_id, name, price, vat_rate, print_receipt = item
                active = True
            elif len(item) == 6:
                item_id, name, price, vat_rate, print_receipt, active = item
            else:
                item_id, name, price, category, vat_rate, print_receipt = item
                active = True
            col = i // 12
            row = i % 12

            is_empty = not name or name.strip() == ""
            is_blank = is_empty and price == 0.0
            is_inactive = not active

            if is_blank:
                panel_bg = self.colors['bg_primary']
                cursor_style = 'arrow'
                clickable = False
            elif is_empty:
                panel_bg = self.colors['bg_accent']
                cursor_style = 'arrow'
                clickable = False
            elif is_inactive:
                panel_bg = '#f0f0f0'
                cursor_style = 'X_cursor'
                clickable = False
            else:
                panel_bg = self.colors['bg_primary']
                cursor_style = 'hand2'
                clickable = True

            panel = tk.Frame(
                grid_frame,
                bg=panel_bg,
                relief='solid',
                bd=1,
                cursor=cursor_style
            )
            panel.grid(row=row, column=col, padx=2, pady=2, sticky="nsew", ipady=8)

            item_number = i + 1
            number_label = tk.Label(
                panel,
                text=str(item_number),
                font=('Arial', 8),
                fg=self.colors['text_secondary'],
                bg=panel_bg,
                cursor=cursor_style
            )
            number_label.place(x=2, y=2)

            inner_bg = panel_bg
            inner_frame = tk.Frame(panel, bg=inner_bg)
            inner_frame.pack(fill=tk.BOTH, expand=True, padx=22, pady=4)

            if is_blank:
                display_name = ""
                name_color = self.colors['text_primary']
            elif is_empty:
                display_name = "[Empty Slot]"
                name_color = self.colors['text_secondary']
            elif is_inactive:
                display_name = name + " (Disabled)"
                name_color = '#888888'
            else:
                display_name = name
                name_color = self.colors['text_primary']

            max_length = 70
            if len(display_name) > max_length:
                display_name = display_name[:max_length - 5].rstrip() + " (...)"

            name_label = tk.Label(
                inner_frame,
                text=display_name,
                font=('Arial', 12, 'bold'),
                fg=name_color,
                bg=inner_bg,
                anchor='w',
                cursor=cursor_style
            )
            name_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            if not is_empty and not is_blank and active:
                session_count = self.database.get_session_sales_count(item_id) if self.database else 0
                count_label = tk.Label(
                    inner_frame,
                    text=str(session_count),
                    font=('Arial', 11, 'bold'),
                    fg=self.colors['text_secondary'],
                    bg=inner_bg,
                    width=3,
                    anchor='center',
                    cursor=cursor_style
                )
                count_label.pack(side=tk.RIGHT, padx=(5, 0))

                price_label = tk.Label(
                    inner_frame,
                    text=f"{price:.2f} €",
                    font=('Arial', 11, 'bold'),
                    fg=self.colors['accent'],
                    bg=inner_bg,
                    anchor='e',
                    cursor=cursor_style
                )
                price_label.pack(side=tk.RIGHT, padx=(10, 5))
            else:
                count_label = None
                price_label = None

            self.item_panels[item_id] = {
                'panel': panel,
                'name_label': name_label,
                'price_label': price_label,
                'count_label': count_label,
                'number_label': number_label
            }

            if not is_empty and not is_blank and active and not self.system_mode:
                def make_click_handler(inner_item_id=item_id, inner_name=name, inner_price=price, inner_panel=panel, inner_inner_frame=inner_frame,
                                       inner_name_label=name_label, inner_price_label=price_label, inner_count_label=count_label, inner_number_label=number_label):
                    def handler(event):
                        click_bg = self.colors.get('click_bg')
                        for widget in [inner_panel, inner_inner_frame, inner_name_label]:
                            widget.config(bg=click_bg)
                        if inner_price_label:
                            inner_price_label.config(bg=click_bg, fg='white')
                        if inner_count_label:
                            inner_count_label.config(bg=click_bg, fg='white')
                        inner_number_label.config(bg=click_bg, fg='white')

                        def restore():
                            hover_bg = self.colors.get('accent_hover', self.colors['accent'])
                            for widget in [inner_panel, inner_inner_frame, inner_name_label]:
                                widget.config(bg=hover_bg)
                            if inner_price_label:
                                inner_price_label.config(bg=hover_bg, fg='white')
                            if inner_count_label:
                                inner_count_label.config(bg=hover_bg, fg='white')
                            inner_number_label.config(bg=hover_bg, fg='white')

                        inner_panel.after(100, restore)

                        self.on_item_click(inner_item_id, inner_name, inner_price)
                    return handler

                click_handler = make_click_handler()
                panel.bind("<Button-1>", click_handler)
                inner_frame.bind("<Button-1>", click_handler)
                name_label.bind("<Button-1>", click_handler)
                number_label.bind("<Button-1>", click_handler)
                if price_label:
                    price_label.bind("<Button-1>", click_handler)
                if count_label:
                    count_label.bind("<Button-1>", click_handler)

            if not is_empty and not is_blank and active and not self.system_mode:
                def make_hover_handlers(p, f, nl, pl, cl, numl):
                    def on_enter(event):
                        hover_bg = self.colors.get('accent_hover', self.colors['accent'])
                        for widget in [p, f, nl]:
                            widget.config(bg=hover_bg)
                        if pl:
                            pl.config(bg=hover_bg, fg='white')
                        if cl:
                            cl.config(bg=hover_bg, fg='white')
                        nl.config(fg='white')
                        numl.config(bg=hover_bg, fg='white')

                    def on_leave(event):
                        for widget in [p, f, nl]:
                            widget.config(bg=self.colors['bg_primary'])
                        if pl:
                            pl.config(bg=self.colors['bg_primary'], fg=self.colors['accent'])
                        if cl:
                            cl.config(bg=self.colors['bg_primary'], fg=self.colors['text_secondary'])
                        nl.config(fg=self.colors['text_primary'])
                        numl.config(bg=self.colors['bg_primary'], fg=self.colors['text_secondary'])

                    return on_enter, on_leave

                on_enter, on_leave = make_hover_handlers(panel, inner_frame, name_label, price_label, count_label, number_label)

                hover_widgets = [panel, inner_frame, name_label, number_label]
                if price_label:
                    hover_widgets.append(price_label)
                if count_label:
                    hover_widgets.append(count_label)

                for widget in hover_widgets:
                    widget.bind("<Enter>", on_enter)
                    widget.bind("<Leave>", on_leave)

        for i in range(3):
            grid_frame.columnconfigure(i, weight=1, uniform="menu_columns")

        max_rows = (len(self.menu_items) + 2) // 3
        for i in range(max_rows):
            grid_frame.rowconfigure(i, weight=1)

    def refresh_display_counts(self):
        """Refresh all displayed counts from database"""
        if not self.database:
            return

        for item_id in self.item_panels:
            count = self.database.get_session_sales_count(item_id)
            count_label = self.item_panels[item_id]['count_label']
            if count_label is not None:
                count_label.config(text=str(count))

    def update_menu_items(self, menu_items: List[tuple]):
        """Update the menu items and recreate the grid"""
        self.menu_items = menu_items

        for widget in self.frame.winfo_children():
            widget.destroy()

        self.item_panels = {}

        self._create_grid_content()

    def set_system_mode(self, system_mode: bool):
        """Enable or disable the menu grid based on system mode"""
        self.system_mode = system_mode

        if system_mode:
            self.original_widget_states = {}

            for item_id, panel_data in self.item_panels.items():
                panel = panel_data['panel']
                name_label = panel_data['name_label']
                price_label = panel_data['price_label']
                count_label = panel_data['count_label']

                inner_frame = None
                for child in panel.winfo_children():
                    if isinstance(child, tk.Frame):
                        inner_frame = child
                        break

                self.original_widget_states[item_id] = {
                    'panel_bg': panel.cget('bg'),
                    'panel_cursor': panel.cget('cursor'),
                    'inner_frame_bg': inner_frame.cget('bg') if inner_frame else None,
                    'name_label_bg': name_label.cget('bg') if name_label else None,
                    'name_label_fg': name_label.cget('fg') if name_label else None,
                    'name_label_cursor': name_label.cget('cursor') if name_label else None,
                    'price_label_bg': price_label.cget('bg') if price_label else None,
                    'price_label_fg': price_label.cget('fg') if price_label else None,
                    'price_label_cursor': price_label.cget('cursor') if price_label else None,
                    'count_label_bg': count_label.cget('bg') if count_label else None,
                    'count_label_fg': count_label.cget('fg') if count_label else None,
                    'count_label_cursor': count_label.cget('cursor') if count_label else None,
                }

                disabled_bg = '#e0e0e0'
                disabled_text = '#999999'

                panel.configure(cursor='X_cursor', bg=disabled_bg)
                if name_label:
                    name_label.configure(cursor='X_cursor', bg=disabled_bg, fg=disabled_text)
                if price_label:
                    price_label.configure(cursor='X_cursor', bg=disabled_bg, fg=disabled_text)
                if count_label:
                    count_label.configure(cursor='X_cursor', bg=disabled_bg, fg=disabled_text)

                inner_frame = None
                for child in panel.winfo_children():
                    if isinstance(child, tk.Frame):
                        child.configure(bg=disabled_bg)
                        inner_frame = child
                        break

                panel.unbind("<Button-1>")
                if name_label:
                    name_label.unbind("<Button-1>")
                if price_label:
                    price_label.unbind("<Button-1>")
                if count_label:
                    count_label.unbind("<Button-1>")

                panel.unbind("<Enter>")
                panel.unbind("<Leave>")
                if name_label:
                    name_label.unbind("<Enter>")
                    name_label.unbind("<Leave>")
                if price_label:
                    price_label.unbind("<Enter>")
                    price_label.unbind("<Leave>")
                if count_label:
                    count_label.unbind("<Enter>")
                    count_label.unbind("<Leave>")

                for child in panel.winfo_children():
                    if isinstance(child, tk.Frame):
                        child.unbind("<Enter>")
                        child.unbind("<Leave>")
                        break
        else:
            if not self.data_changed_in_system_mode and self.original_widget_states:
                self._restore_widget_states()
            else:
                self.update_menu_items(self.menu_items)

            self.data_changed_in_system_mode = False

    def _restore_widget_states(self):
        """Fast restoration of widget states without rebuilding"""
        for item_id, panel_data in self.item_panels.items():
            if item_id not in self.original_widget_states:
                continue

            panel = panel_data['panel']
            name_label = panel_data['name_label']
            price_label = panel_data['price_label']
            count_label = panel_data['count_label']
            original_states = self.original_widget_states[item_id]

            panel.configure(
                bg=original_states['panel_bg'],
                cursor=original_states['panel_cursor']
            )

            for child in panel.winfo_children():
                if isinstance(child, tk.Frame) and original_states['inner_frame_bg']:
                    child.configure(bg=original_states['inner_frame_bg'])
                    break

            if name_label and original_states['name_label_bg']:
                name_label.configure(
                    bg=original_states['name_label_bg'],
                    fg=original_states['name_label_fg'],
                    cursor=original_states['name_label_cursor']
                )

            if price_label and original_states['price_label_bg']:
                price_label.configure(
                    bg=original_states['price_label_bg'],
                    fg=original_states['price_label_fg'],
                    cursor=original_states['price_label_cursor']
                )

            if count_label and original_states['count_label_bg']:
                count_label.configure(
                    bg=original_states['count_label_bg'],
                    fg=original_states['count_label_fg'],
                    cursor=original_states['count_label_cursor']
                )

            self._rebind_events_for_item(item_id, panel_data)

    def _rebind_events_for_item(self, item_id: int, panel_data: dict):
        """Re-bind click and hover events for an active menu item"""
        menu_item = None
        for item in self.menu_items:
            if len(item) >= 6 and item[0] == item_id:
                menu_item = item
                break
            elif len(item) >= 3 and item[0] == item_id:
                menu_item = item
                break

        if not menu_item:
            return

        if len(menu_item) == 3:
            item_id, name, price = menu_item
            active = True
        elif len(menu_item) == 5:
            item_id, name, price, vat_rate, print_receipt = menu_item
            active = True
        elif len(menu_item) == 6:
            item_id, name, price, vat_rate, print_receipt, active = menu_item
        else:
            item_id, name, price, category, vat_rate, print_receipt = menu_item
            active = True

        is_empty = not name or name.strip() == ""
        is_blank = is_empty and price == 0.0
        if is_empty or is_blank or not active:
            return

        panel = panel_data['panel']
        name_label = panel_data['name_label']
        price_label = panel_data['price_label']
        count_label = panel_data['count_label']

        inner_frame = None
        for child in panel.winfo_children():
            if isinstance(child, tk.Frame):
                inner_frame = child
                break

        def make_click_handler(id=item_id, n=name, p=price):
            return lambda event: self.on_item_click(id, n, p)

        click_handler = make_click_handler()
        panel.bind("<Button-1>", click_handler)
        if inner_frame:
            inner_frame.bind("<Button-1>", click_handler)
        if name_label:
            name_label.bind("<Button-1>", click_handler)
        if price_label:
            price_label.bind("<Button-1>", click_handler)
        if count_label:
            count_label.bind("<Button-1>", click_handler)

        def make_hover_handlers(p, f, nl, pl, cl):
            def on_enter(event):
                hover_bg = self.colors.get('accent_hover', self.colors['accent'])
                for widget in [p, f, nl]:
                    if widget:
                        widget.config(bg=hover_bg)
                if pl:
                    pl.config(bg=hover_bg, fg='white')
                if cl:
                    cl.config(bg=hover_bg, fg='white')
                if nl:
                    nl.config(fg='white')

            def on_leave(event):
                for widget in [p, f, nl]:
                    if widget:
                        widget.config(bg=self.colors['bg_primary'])
                if pl:
                    pl.config(bg=self.colors['bg_primary'], fg=self.colors['accent'])
                if cl:
                    cl.config(bg=self.colors['bg_primary'], fg=self.colors['text_secondary'])
                if nl:
                    nl.config(fg=self.colors['text_primary'])

            return on_enter, on_leave

        on_enter, on_leave = make_hover_handlers(panel, inner_frame, name_label, price_label, count_label)

        hover_widgets = [panel, inner_frame, name_label]
        if price_label:
            hover_widgets.append(price_label)
        if count_label:
            hover_widgets.append(count_label)

        for widget in hover_widgets:
            if widget:
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)


if __name__ == "__main__":
    import sys
    print(f"Error: This module should not be run directly. Please run main.py instead.")
    sys.exit(1)