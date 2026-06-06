# =============================================================================
# File Name : app.py
# Artifact  : LearningClock - Tkinter Application
# Author    : javaboy-vk
# Date      : 2026-06-06
# Version   : v0.1.0
# Purpose:
#   Provides the Tkinter UI, timer state, manual entry workflow, and shutdown
#   lifecycle for LearningClock.
# =============================================================================

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from learningclock.csv_store import (
    ACTIVITIES,
    CSV_DATE_FORMAT_DESCRIPTION,
    CsvStore,
    format_seconds,
)

APP_TITLE = "Learning Clock"
APP_VERSION = "v3.3"

NORMAL_GEOMETRY = "420x345"
ADD_TIME_GEOMETRY = "580x345"
ADD_PAGE_COUNT_GEOMETRY = "530x345"


# Parse command-line options used by direct Python launches and VS Code debug configs.
def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Learning Clock")
    parser.add_argument("--learning-path", default=None)
    parser.add_argument("--log-dir", default=None)
    parser.add_argument("--debug-break-on-click", action="store_true")
    parser.add_argument("--debug-break-on-close", action="store_true")
    return parser.parse_args(argv)


# Tkinter application that tracks learning-time activities and saves one CSV on close.
class LearningClock:
    # Initialize app state, log locations, window wiring, and the initial UI.
    def __init__(
        self,
        root,
        learning_path_name=None,
        log_dir=None,
        debug_break_on_click=False,
        debug_break_on_close=False,
    ):
        self.root = root
        self.learning_path_name = learning_path_name or Path.cwd().name
        self.debug_break_on_click = debug_break_on_click
        self.debug_break_on_close = debug_break_on_close
        self.root.title(self.build_window_title())
        self.root.geometry(NORMAL_GEOMETRY)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.store = CsvStore(log_dir or Path.cwd(), self.learning_path_name)
        self.log_dir = self.store.log_dir
        self.log_file = self.store.log_file
        self.diagnostic_log_file = self.store.diagnostic_log_file

        self.write_diagnostic_log(
            "Application initialized | "
            f"learning_path={self.learning_path_name} | "
            f"cwd={Path.cwd()} | "
            f"log_dir={self.log_dir} | "
            f"log_file={self.log_file} | "
            f"diagnostic_log_file={self.diagnostic_log_file} | "
            f"python={sys.executable} | "
            f"csv_date_format={CSV_DATE_FORMAT_DESCRIPTION}"
        )

        self.session_start = datetime.now()
        self.session_saved = False
        self.is_closing = False
        self.after_job_id = None

        self.active_activity = None
        self.active_start = None
        self.add_time_mode = False
        self.add_page_count_mode = False

        self.totals = {activity: 0 for activity in ACTIVITIES}
        self.pages_read = 0

        self.labels = {}
        self.manual_entries = {}
        self.page_count_entry = None
        self.add_time_button = None
        self.add_pages_button = None

        self.build_menu()
        self.build_main_ui()
        self.update_display()

    def write_diagnostic_log(self, message, exc=None):
        self.store.write_diagnostic_log(message, exc)

    # Build the main window title shown in the Tkinter title bar.
    def build_window_title(self):
        return f"{APP_TITLE} - {APP_VERSION} - {self.learning_path_name}"

    # Create the menu commands for About, manual time entry, and page-count entry.
    def build_menu(self):
        menu_bar = tk.Menu(self.root)
        menu_bar.add_command(label="About", command=self.show_about)
        menu_bar.add_command(label="Add Time", command=self.enter_add_time_mode)
        menu_bar.add_command(label="Add Page Count", command=self.enter_add_page_count_mode)
        self.root.config(menu=menu_bar)

    # Create all main timer controls, counters, manual-entry widgets, and action buttons.
    def build_main_ui(self):
        self.status = tk.Label(
            self.root,
            text="No timer running",
            font=("Arial", 13, "bold"),
            anchor="w",
        )
        self.status.pack(fill="x", padx=16, pady=(6, 3))

        self.timer_frame = tk.Frame(self.root)
        self.timer_frame.pack(fill="x", padx=16, pady=0)

        for activity in ACTIVITIES:
            row = tk.Frame(self.timer_frame)
            row.pack(fill="x", pady=1)

            button = tk.Button(
                row,
                text=activity,
                font=("Arial", 12),
                width=24,
                anchor="w",
                command=lambda a=activity: self.switch_to(a),
            )
            button.pack(side="left")

            label = tk.Label(row, text="00:00:00", font=("Consolas", 14), width=12)
            label.pack(side="left", padx=(10, 0))
            self.labels[activity] = label

            entry = tk.Entry(row, font=("Arial", 11), width=11)
            entry.bind("<Return>", lambda _event: self.add_all_manual_time())
            self.manual_entries[activity] = entry

            if activity == "Reading":
                self.page_count_entry = tk.Entry(row, font=("Arial", 11), width=8)
                self.page_count_entry.bind("<Return>", lambda _event: self.add_page_count())

        controls_frame = tk.Frame(self.root)
        controls_frame.pack(fill="x", padx=16, pady=(4, 0), anchor="w")

        stop_button = tk.Button(
            controls_frame,
            text="Stop",
            font=("Arial", 10),
            width=12,
            command=self.stop_running_timer,
        )
        stop_button.pack(side="left", padx=(0, 6))

        reset_button = tk.Button(
            controls_frame,
            text="Reset Timer",
            font=("Arial", 10),
            width=12,
            command=self.reset_running_timer,
        )
        reset_button.pack(side="left", padx=(0, 6))

        self.add_time_button = tk.Button(
            controls_frame,
            text="Add Time",
            font=("Arial", 10),
            width=12,
            command=self.add_all_manual_time,
        )

        self.add_pages_button = tk.Button(
            controls_frame,
            text="Add Pages",
            font=("Arial", 10),
            width=12,
            command=self.add_page_count,
        )

    # Show runtime information, configured output paths, and save-behavior notes.
    def show_about(self):
        about_text = "\n".join([
            f"{APP_TITLE} - {APP_VERSION}",
            f"Learning Path: {self.learning_path_name}",
            f"CSV: {self.log_file}",
            f"Diagnostic Log: {self.diagnostic_log_file}",
            f"CSV Date Format: {CSV_DATE_FORMAT_DESCRIPTION}",
            "Manual Add accepts minutes, HH:MM, or HH:MM:SS.",
            "The session is saved only when the app closes.",
            "Emergency CSV files are merged automatically on the next successful save.",
        ])
        messagebox.showinfo("About Learning Clock", about_text)

    # Switch the UI into manual time-entry mode so durations can be added by hand.
    def enter_add_time_mode(self):
        if self.add_page_count_mode:
            self.exit_add_page_count_mode()
        if self.add_time_mode:
            return

        self.add_time_mode = True
        self.root.geometry(ADD_TIME_GEOMETRY)

        for activity in ACTIVITIES:
            self.manual_entries[activity].pack(side="left", padx=(8, 0))

        self.add_time_button.pack(side="left", padx=(0, 0))

        first_entry = self.manual_entries.get(ACTIVITIES[0])
        if first_entry is not None:
            first_entry.focus_set()

        self.status.config(text="Add Time mode")

    # Leave manual time-entry mode and restore the normal timer layout.
    def exit_add_time_mode(self):
        if not self.add_time_mode:
            return

        self.add_time_mode = False

        for entry in self.manual_entries.values():
            entry.pack_forget()

        self.add_time_button.pack_forget()
        self.root.geometry(NORMAL_GEOMETRY)
        self.restore_running_status()

    # Switch the UI into page-count mode so pages can be added to the current session.
    def enter_add_page_count_mode(self):
        if self.add_time_mode:
            self.exit_add_time_mode()
        if self.add_page_count_mode:
            return

        self.add_page_count_mode = True
        self.root.geometry(ADD_PAGE_COUNT_GEOMETRY)

        if self.page_count_entry is not None:
            self.page_count_entry.pack(side="left", padx=(8, 0))
            self.page_count_entry.focus_set()

        self.add_pages_button.pack(side="left", padx=(0, 0))
        self.status.config(text="Add Page Count mode")

    # Leave page-count mode and restore the normal timer layout.
    def exit_add_page_count_mode(self):
        if not self.add_page_count_mode:
            return

        self.add_page_count_mode = False

        if self.page_count_entry is not None:
            self.page_count_entry.pack_forget()

        self.add_pages_button.pack_forget()
        self.root.geometry(NORMAL_GEOMETRY)
        self.restore_running_status()

    # Refresh the status label after returning from a temporary input mode.
    def restore_running_status(self):
        if self.active_activity:
            self.status.config(text=f"Running: {self.active_activity}")
        else:
            self.status.config(text="No timer running")

    # Handle an activity-button click by closing the old timer and starting the new one.
    def switch_to(self, activity):
        if self.debug_break_on_click:
            breakpoint()

        self.write_diagnostic_log(f"Switch requested | activity={activity}")
        self.close_active_timer(datetime.now())
        self.active_activity = activity
        self.active_start = datetime.now()
        self.session_saved = False
        self.status.config(text=f"Running: {activity}")
        self.write_diagnostic_log(
            f"Timer started | activity={activity} | "
            f"active_start={self.active_start:%H:%M:%S}"
        )

    # Accumulate elapsed seconds for the currently active timer and clear active state.
    def close_active_timer(self, now):
        if self.active_activity is None or self.active_start is None:
            return
        elapsed_seconds = (now - self.active_start).total_seconds()
        self.totals[self.active_activity] += elapsed_seconds
        self.write_diagnostic_log(
            "Timer closed | "
            f"activity={self.active_activity} | "
            f"elapsed={format_seconds(round(elapsed_seconds))} | "
            f"activity_total={format_seconds(round(self.totals[self.active_activity]))}"
        )
        self.active_activity = None
        self.active_start = None

    # Stop the active timer without resetting the accumulated session totals.
    def stop_running_timer(self):
        if self.active_activity is None:
            self.status.config(text="No timer running")
            return
        stopped_activity = self.active_activity
        self.close_active_timer(datetime.now())
        self.status.config(text=f"Stopped: {stopped_activity}")

    # Reset only the currently running timer back to zero and continue timing it.
    def reset_running_timer(self):
        if self.active_activity is None:
            messagebox.showwarning("Reset Timer", "No timer is currently running.")
            return
        activity = self.active_activity
        self.totals[activity] = 0
        self.active_start = datetime.now()
        self.session_saved = False
        self.status.config(text=f"Reset running timer: {activity}")
        self.update_display()

    # Validate all manual time fields and add their durations to the current session.
    def add_all_manual_time(self):
        additions = []
        errors = []

        for activity, entry in self.manual_entries.items():
            raw_value = entry.get().strip()
            if not raw_value:
                continue
            try:
                seconds = self.parse_manual_input(raw_value)
            except ValueError as exc:
                errors.append(f"{activity}: {exc}")
                continue
            if seconds <= 0:
                errors.append(f"{activity}: manual time must be greater than zero.")
                continue
            additions.append((activity, seconds))

        if errors:
            messagebox.showerror("Invalid Manual Time", "\n".join(errors))
            return
        if not additions:
            messagebox.showwarning("Manual Time", "Enter time for at least one timer.")
            return

        for activity, seconds in additions:
            self.totals[activity] += seconds
            self.write_diagnostic_log(
                f"Manual time added | activity={activity} | added={format_seconds(seconds)} | "
                f"activity_total={format_seconds(round(self.totals[activity]))}"
            )

        for entry in self.manual_entries.values():
            entry.delete(0, tk.END)

        self.session_saved = False
        self.update_display()
        self.exit_add_time_mode()

    # Validate the page-count field and add the value to the current session.
    def add_page_count(self):
        if self.page_count_entry is None:
            return

        raw_value = self.page_count_entry.get().strip()

        if not raw_value:
            messagebox.showwarning("Add Page Count", "Enter the number of pages read.")
            return
        if not raw_value.isdigit():
            messagebox.showerror("Add Page Count", "Page count must be a whole number.")
            return

        pages = int(raw_value)
        if pages <= 0:
            messagebox.showwarning("Add Page Count", "Page count must be greater than zero.")
            return

        self.pages_read += pages
        self.write_diagnostic_log(
            f"Pages added | added={pages} | pages_read_session_total={self.pages_read}"
        )
        self.page_count_entry.delete(0, tk.END)
        self.session_saved = False
        self.exit_add_page_count_mode()
        self.status.config(text=f"Added pages read: {pages}")

    # Convert minutes, HH:MM, or HH:MM:SS manual input into seconds.
    @staticmethod
    def parse_manual_input(value):
        normalized = value.strip()
        if not normalized:
            raise ValueError("Manual time cannot be blank.")

        if normalized.isdigit():
            return int(normalized) * 60

        parts = normalized.split(":")
        if len(parts) == 2:
            hours, minutes = parts
            if not hours.isdigit() or not minutes.isdigit():
                raise ValueError("Use minutes, HH:MM, or HH:MM:SS.")
            return int(hours) * 3600 + int(minutes) * 60

        if len(parts) == 3:
            hours, minutes, seconds = parts
            if not hours.isdigit() or not minutes.isdigit() or not seconds.isdigit():
                raise ValueError("Use minutes, HH:MM, or HH:MM:SS.")
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)

        raise ValueError("Use minutes, HH:MM, or HH:MM:SS.")

    # Return stored seconds for an activity, including the still-running timer if active.
    def current_total(self, activity):
        total = self.totals[activity]
        if self.active_activity == activity and self.active_start is not None:
            total += (datetime.now() - self.active_start).total_seconds()
        return round(total)

    def create_session_row(self, session_end):
        activity_seconds = {
            activity: self.current_total(activity)
            for activity in ACTIVITIES
        }
        return self.store.create_session_row(
            self.session_start,
            session_end,
            activity_seconds,
            self.pages_read,
        )

    def save_session_summary(self, session_end):
        saved = self.store.save_session_summary(self.create_session_row(session_end))
        self.session_saved = saved
        return saved

    def save_emergency_session_file(self, session_end, error):
        session_row = self.create_session_row(session_end)
        return self.store.save_emergency_session_file(session_row, session_end, error)

    # Refresh visible activity labels every 500 ms while the window is alive.
    def update_display(self):
        if self.is_closing:
            return
        try:
            for activity in ACTIVITIES:
                self.labels[activity].config(text=format_seconds(self.current_total(activity)))
            self.after_job_id = self.root.after(500, self.update_display)
        except tk.TclError:
            return

    # Save the current session during window close and always tear down Tkinter cleanly.
    def on_close(self):
        if self.is_closing:
            return

        if self.debug_break_on_close:
            breakpoint()

        self.is_closing = True
        session_end = datetime.now()
        self.write_diagnostic_log(
            f"Close requested | session_start={self.session_start:%Y-%m-%d %H:%M:%S} | "
            f"session_end={session_end:%Y-%m-%d %H:%M:%S} | session_saved={self.session_saved}"
        )

        try:
            if self.after_job_id is not None:
                try:
                    self.root.after_cancel(self.after_job_id)
                except tk.TclError:
                    pass

            if not self.session_saved:
                self.close_active_timer(session_end)

                try:
                    self.save_session_summary(session_end)
                except Exception as exc:
                    self.write_diagnostic_log("Normal CSV save failed.", exc)
                    emergency_file = None
                    try:
                        emergency_file = self.save_emergency_session_file(session_end, exc)
                    except Exception as emergency_exc:
                        self.write_diagnostic_log("Emergency save failed.", emergency_exc)
                        emergency_file = None

                    error_message = (
                        "The normal CSV save failed, but the application will close.\n\n"
                        f"Error: {exc}"
                    )
                    if emergency_file is not None:
                        error_message += f"\n\nEmergency session file created:\n{emergency_file}"
                    else:
                        error_message += (
                            "\n\nEmergency save also failed. "
                            "Run the debug .bat launcher to see the Python error."
                        )
                    messagebox.showerror("Learning Clock Save Warning", error_message)
        finally:
            self.write_diagnostic_log("Application shutdown finalization started.")
            try:
                self.root.quit()
            except tk.TclError:
                pass
            try:
                self.root.destroy()
            except tk.TclError:
                pass


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = tk.Tk()
    LearningClock(
        root,
        learning_path_name=args.learning_path,
        log_dir=args.log_dir,
        debug_break_on_click=args.debug_break_on_click,
        debug_break_on_close=args.debug_break_on_close,
    )
    root.mainloop()
    return 0
