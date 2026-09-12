# =============================================================================
# File Name : date_picker.py
# Artifact  : LearningClock - Reusable Tkinter Date Picker
# Author    : javaboy-vk
# Date      : 2026-09-11
# Version   : v1.0.0
# Purpose:
#   Provides the LauncherPad report with mouse/keyboard calendar selection
#   without adding a third-party GUI dependency.
# =============================================================================

from __future__ import annotations

import calendar
import tkinter as tk
from collections.abc import Callable
from datetime import date


class DatePickerDialog:
    """Small modal calendar that returns one local calendar date."""

    def __init__(
        self, parent: tk.Misc, initial: date, on_selected: Callable[[date], None]
    ) -> None:
        self.parent = parent
        self.current = initial.replace(day=1)
        self.on_selected = on_selected
        self.window = tk.Toplevel(parent)
        self.window.title("Select date")
        self.window.transient(parent)
        self.window.resizable(False, False)
        self.window.bind("<Escape>", lambda _event: self.close())
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.body = tk.Frame(self.window, padx=10, pady=10)
        self.body.pack(fill="both", expand=True)
        self.render()
        self.window.wait_visibility()
        self.window.grab_set()
        self.window.focus_force()

    def render(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()
        tk.Button(self.body, text="◀", command=lambda: self.move_month(-1)).grid(row=0, column=0)
        tk.Label(
            self.body,
            text=self.current.strftime("%B %Y"),
            font=("Arial", 11, "bold"),
            width=18,
        ).grid(row=0, column=1, columnspan=5)
        tk.Button(self.body, text="▶", command=lambda: self.move_month(1)).grid(row=0, column=6)
        for column, label in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
            tk.Label(self.body, text=label, width=4).grid(row=1, column=column, pady=(8, 2))
        for row_index, week in enumerate(calendar.monthcalendar(self.current.year, self.current.month)):
            for column, day_number in enumerate(week):
                if not day_number:
                    tk.Label(self.body, text="", width=4).grid(row=row_index + 2, column=column)
                    continue
                selected = date(self.current.year, self.current.month, day_number)
                tk.Button(
                    self.body,
                    text=str(day_number),
                    width=3,
                    command=lambda value=selected: self.select(value),
                ).grid(row=row_index + 2, column=column, padx=1, pady=1)

    def move_month(self, amount: int) -> None:
        index = self.current.year * 12 + self.current.month - 1 + amount
        self.current = date(index // 12, index % 12 + 1, 1)
        self.render()

    def select(self, selected: date) -> None:
        self.on_selected(selected)
        self.close()

    def close(self) -> None:
        try:
            self.window.grab_release()
        except tk.TclError:
            pass
        self.window.destroy()


def show_date_picker(
    parent: tk.Misc, initial: date, on_selected: Callable[[date], None]
) -> DatePickerDialog:
    return DatePickerDialog(parent, initial, on_selected)
