#!/usr/bin/env python3
# =============================================================================
# File Name   : learning-clock.py
# Artifact    : Learning Clock - Timer Engine - v3.3
# Author      : javaboy-vk
# Date        : 2026-06-01
# Version     : 3.3
# Description :
#   Seven-mode learning-path timer with save-on-close lifecycle, page counting,
#   manual time entry, emergency save fallback, and automatic recovery/merge of
#   emergency session files into the normal CSV on the next successful save.
#
# Change Log  :
#   v3.3 - Added class, method, and persistence-flow documentation comments.
#   v3.2 - Added opt-in debugger break on application close for save debugging.
#   v3.1 - Added opt-in debugger break on activity button click for development.
#   v3.0 - Standardized CSV dates to one canonical format: YYYY-MM-DD.
#          Existing legacy CSV dates are normalized during the next save.
#   v2.8 - Updated window title to include the active learning path name.
#          Example: "Learning Clock - v2.8 - ManteioLab".
#   v2.7 - Added automatic recovery/merge of learning_time_log_emergency_*.csv.
#          If the main CSV is locked, the app still closes and writes emergency.
#          On the next successful close, emergency session rows are merged into
#          learning_time_log.csv and the emergency files are renamed .merged.
#   v2.6 - Fixed close-window lifecycle so the app always closes.
#   v2.5 - Stop button now stops only the active timer.
#          CSV is written only when the application closes.
#          Reset applies only to the currently running timer.
#          Added Add Page Count mode and pages_read CSV column.
# =============================================================================

import argparse
import csv
import os
import sys
import traceback
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox


APP_TITLE = "Learning Clock"
APP_VERSION = "v3.3"

NORMAL_GEOMETRY = "420x345"
ADD_TIME_GEOMETRY = "580x345"
ADD_PAGE_COUNT_GEOMETRY = "530x345"

ACTIVITIES = [
    "Reading",
    "Outlining",
    "Memorizing",
    "Experimenting",
    "Audiobook",
    "Update Diavgeia",
    "Promote stable concept",
]

LOG_FILE_NAME = "learning_time_log.csv"
EMERGENCY_FILE_PREFIX = "learning_time_log_emergency_"
DIAGNOSTIC_LOG_FILE_NAME = "learning_clock_debug.log"
CSV_DATE_FORMAT = "%Y-%m-%d"
CSV_DATE_FORMAT_DESCRIPTION = "YYYY-MM-DD"
LEGACY_CSV_DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%m-%d-%Y",
    "%m-%d-%y",
]

FIELDNAMES = [
    "date",
    "learning_path",
    "session_start",
    "session_end",
    "reading",
    "outlining",
    "memorizing",
    "experimenting",
    "audiobook",
    "update_diavgeia",
    "promote_stable_concept",
    "pages_read",
    "total",
]

ACTIVITY_TO_FIELD = {
    "Reading": "reading",
    "Outlining": "outlining",
    "Memorizing": "memorizing",
    "Experimenting": "experimenting",
    "Audiobook": "audiobook",
    "Update Diavgeia": "update_diavgeia",
    "Promote stable concept": "promote_stable_concept",
}

LEGACY_FIELD_MAPPINGS = {
    "document_in_diavgeia": "update_diavgeia",
}


# Parse command-line options used by direct Python launches and VS Code debug configs.
def parse_args():
    parser = argparse.ArgumentParser(description="Learning Clock")
    parser.add_argument("--learning-path", default=None)
    parser.add_argument("--log-dir", default=None)
    parser.add_argument("--debug-break-on-click", action="store_true")
    parser.add_argument("--debug-break-on-close", action="store_true")
    return parser.parse_args()


# Tkinter application that tracks learning-time activities and saves one CSV on close.
#
# The app keeps activity totals in memory while the window is open and writes the CSV during the
# close lifecycle. If the normal CSV write fails, it creates an emergency CSV that is merged on
# the next successful close.
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

        self.log_dir = Path(log_dir) if log_dir else Path.cwd()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / LOG_FILE_NAME
        self.diagnostic_log_file = self.log_dir / DIAGNOSTIC_LOG_FILE_NAME

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

    # Append a diagnostic message to the Learning Clock debug log.
    #
    # This intentionally avoids message boxes because the normal launcher uses pythonw.exe and
    # hides the console. The log file is the primary evidence trail for silent save/path/lifecycle
    # failures.
    def write_diagnostic_log(self, message, exc=None):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines = [f"[{timestamp}] {message}"]
            if exc is not None:
                lines.extend(traceback.format_exception(type(exc), exc, exc.__traceback__))
            with self.diagnostic_log_file.open("a", encoding="utf-8") as log:
                log.write("\n".join(line.rstrip() for line in lines))
                log.write("\n")
        except Exception:
            # Logging must never break the timer itself.
            pass

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
        self.write_diagnostic_log(f"Switch requested | activity={activity}")
        
        self.close_active_timer(datetime.now())
        self.active_activity = activity
        self.active_start = datetime.now()
        self.session_saved = False
        self.status.config(text=f"Running: {activity}")
        self.write_diagnostic_log(f"Timer started | activity={activity} | active_start={self.active_start:%H:%M:%S}")

    # Accumulate elapsed seconds for the currently active timer and clear active state.
    def close_active_timer(self, now):
        if self.active_activity is None or self.active_start is None:
            return
        elapsed_seconds = (now - self.active_start).total_seconds()
        self.totals[self.active_activity] += elapsed_seconds
        self.write_diagnostic_log(
            "Timer closed | "
            f"activity={self.active_activity} | "
            f"elapsed={self.format_seconds(round(elapsed_seconds))} | "
            f"activity_total={self.format_seconds(round(self.totals[self.active_activity]))}"
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
                f"Manual time added | activity={activity} | added={self.format_seconds(seconds)} | "
                f"activity_total={self.format_seconds(round(self.totals[activity]))}"
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
        self.write_diagnostic_log(f"Pages added | added={pages} | pages_read_session_total={self.pages_read}")
        self.page_count_entry.delete(0, tk.END)
        self.session_saved = False
        self.exit_add_page_count_mode()
        self.status.config(text=f"Added pages read: {pages}")

    # Convert minutes, HH:MM, or HH:MM:SS manual input into seconds.
    def parse_manual_input(self, value):
        normalized = value.strip()
        if not normalized:
            raise ValueError("Manual time cannot be blank.")

        # A plain integer is treated as minutes because it is the fastest manual entry form
        # during a learning session.
        if normalized.isdigit():
            return int(normalized) * 60

        parts = normalized.split(":")
        # HH:MM input is converted to seconds so manual additions and live timers share the
        # same in-memory total representation.
        if len(parts) == 2:
            hours, minutes = parts
            if not hours.isdigit() or not minutes.isdigit():
                raise ValueError("Use minutes, HH:MM, or HH:MM:SS.")
            return int(hours) * 3600 + int(minutes) * 60

        # HH:MM:SS is accepted for exact corrections copied from another timer or log.
        if len(parts) == 3:
            hours, minutes, seconds = parts
            if not hours.isdigit() or not minutes.isdigit() or not seconds.isdigit():
                raise ValueError("Use minutes, HH:MM, or HH:MM:SS.")
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)

        raise ValueError("Use minutes, HH:MM, or HH:MM:SS.")

    # Persist session rows and a recalculated TOTAL row when the window closes.
    def save_session_summary(self, session_end):
        self.write_diagnostic_log(f"Save started | session_end={session_end:%Y-%m-%d %H:%M:%S} | log_file={self.log_file}")

        # Read the previous CSV rows first, then read emergency rows from failed prior saves.
        # The method rewrites the full CSV every time instead of appending blindly, because the
        # TOTAL row must be recalculated from the current normalized schema.
        existing_rows = self.read_existing_session_rows()
        emergency_rows, emergency_files = self.read_emergency_session_rows()

        self.write_diagnostic_log(
            f"Rows loaded | existing_rows={len(existing_rows)} | "
            f"emergency_rows={len(emergency_rows)} | emergency_files={len(emergency_files)}"
        )

        session_row = self.create_session_row(session_end)
        has_data = self.has_session_data(session_row)

        self.write_diagnostic_log(
            "Session row created | "
            f"date={session_row.get('date')} | "
            f"start={session_row.get('session_start')} | "
            f"end={session_row.get('session_end')} | "
            f"reading={session_row.get('reading')} | "
            f"outlining={session_row.get('outlining')} | "
            f"memorizing={session_row.get('memorizing')} | "
            f"experimenting={session_row.get('experimenting')} | "
            f"audiobook={session_row.get('audiobook')} | "
            f"update_diavgeia={session_row.get('update_diavgeia')} | "
            f"promote_stable_concept={session_row.get('promote_stable_concept')} | "
            f"pages_read={session_row.get('pages_read')} | "
            f"total={session_row.get('total')} | "
            f"has_data={has_data}"
        )

        if has_data:
            existing_rows.append(session_row)
        else:
            # A close event without recorded time or pages should not produce a fake session row.
            self.write_diagnostic_log("Session row skipped because it had no time or pages.")

        # Emergency rows are merged after the current row is prepared. They are marked as merged
        # only after the main CSV write succeeds.
        existing_rows.extend(emergency_rows)

        if not existing_rows:
            self.write_diagnostic_log("Save skipped because there were no rows to write.")
            return False

        # Rebuild the synthetic TOTAL row from all session rows so stale totals are not carried
        # forward from older CSV files or failed shutdown attempts.
        total_row = self.create_total_row(existing_rows)
        rows_to_write = len(existing_rows) + 1

        self.write_diagnostic_log(
            f"Writing CSV | rows_to_write_including_total={rows_to_write} | total={total_row.get('total')} | "
            f"pages_total={total_row.get('pages_read')}"
        )

        with self.log_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(existing_rows)
            writer.writerow(total_row)

        self.mark_emergency_files_merged(emergency_files)
        self.session_saved = True
        self.write_diagnostic_log("Save completed successfully.")
        return True

    # Return true when a row contains useful session data worth saving.
    def has_session_data(self, session_row):
        if self.parse_duration(session_row.get("total", "00:00:00")) > 0:
            return True
        try:
            return int(session_row.get("pages_read", 0)) > 0
        except (TypeError, ValueError):
            return False

    # Read the main CSV and return normalized session rows, excluding the TOTAL row.
    def read_existing_session_rows(self):
        if not self.log_file.exists():
            self.write_diagnostic_log(f"Main CSV does not exist yet | log_file={self.log_file}")
            return []

        rows = []
        with self.log_file.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("date") == "TOTAL":
                    continue
                rows.append(self.normalize_existing_row(row))
        self.write_diagnostic_log(f"Main CSV read completed | session_rows={len(rows)}")
        return rows

    # Read unmerged emergency CSV files created after failed normal saves.
    def read_emergency_session_rows(self):
        rows = []
        files = []

        for emergency_file in sorted(self.log_dir.glob(f"{EMERGENCY_FILE_PREFIX}*.csv")):
            try:
                # Emergency files use the same header as the main CSV. Only rows with time or
                # pages are recovered, preventing empty failure artifacts from affecting totals.
                with emergency_file.open("r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("date") == "TOTAL":
                            continue
                        normalized_row = self.normalize_existing_row(row)
                        if self.has_session_data(normalized_row):
                            rows.append(normalized_row)
                files.append(emergency_file)
            except OSError as exc:
                self.write_diagnostic_log(f"Emergency CSV read failed | file={emergency_file}", exc)
                continue

        self.write_diagnostic_log(f"Emergency CSV scan completed | rows={len(rows)} | files={len(files)}")
        return rows, files

    # Rename recovered emergency files after their rows have been written to the main CSV.
    def mark_emergency_files_merged(self, emergency_files):
        for emergency_file in emergency_files:
            merged_file = emergency_file.with_suffix(emergency_file.suffix + ".merged")
            try:
                if merged_file.exists():
                    merged_file.unlink()
                emergency_file.rename(merged_file)
            except OSError:
                pass

    # Convert a row from any supported CSV version into the current schema.
    def normalize_existing_row(self, row):
        normalized_row = {field: row.get(field, "") for field in FIELDNAMES}
        normalized_row["date"] = self.normalize_csv_date_value(normalized_row.get("date", ""))

        # Copy legacy column names into the current schema so older CSV files remain readable.
        for legacy_field, current_field in LEGACY_FIELD_MAPPINGS.items():
            legacy_value = row.get(legacy_field, "")
            current_value = normalized_row.get(current_field, "")
            if legacy_value and not current_value:
                normalized_row[current_field] = legacy_value

        # Fill missing durations with zero values so later duration parsing is predictable.
        for field in ACTIVITY_TO_FIELD.values():
            if not normalized_row.get(field):
                normalized_row[field] = "00:00:00"

        if not normalized_row.get("pages_read"):
            normalized_row["pages_read"] = "0"
        if not normalized_row.get("total"):
            normalized_row["total"] = self.recalculate_row_total(normalized_row)

        return normalized_row

    # Build the CSV row for the session ending at the supplied timestamp.
    def create_session_row(self, session_end):
        activity_seconds = {
            activity: self.current_total(activity)
            for activity in ACTIVITIES
        }
        total_seconds = sum(activity_seconds.values())

        # Session start is captured at app startup; session end is captured during close. The
        # individual activity values come from accumulated timer totals plus any active segment.
        row = {
            "date": self.format_csv_date(session_end),
            "learning_path": self.learning_path_name,
            "session_start": self.session_start.strftime("%H:%M:%S"),
            "session_end": session_end.strftime("%H:%M:%S"),
            "pages_read": str(self.pages_read),
            "total": self.format_seconds(total_seconds),
        }

        for activity, field_name in ACTIVITY_TO_FIELD.items():
            row[field_name] = self.format_seconds(activity_seconds.get(activity, 0))

        return row

    # Aggregate all session rows into the final synthetic TOTAL CSV row.
    def create_total_row(self, rows):
        total_seconds_by_field = {field_name: 0 for field_name in ACTIVITY_TO_FIELD.values()}
        grand_total = 0
        pages_total = 0

        for row in rows:
            # Each activity is summed separately so dashboard code can draw per-activity bars
            # directly from the TOTAL row if needed.
            for field_name in ACTIVITY_TO_FIELD.values():
                total_seconds_by_field[field_name] += self.parse_duration(row.get(field_name, "00:00:00"))
            grand_total += self.parse_duration(row.get("total", "00:00:00"))
            try:
                pages_total += int(row.get("pages_read", "0") or 0)
            except ValueError:
                pages_total += 0

        total_row = {
            "date": "TOTAL",
            "learning_path": "",
            "session_start": "",
            "session_end": "",
            "pages_read": str(pages_total),
            "total": self.format_seconds(grand_total),
        }

        for field_name, seconds in total_seconds_by_field.items():
            total_row[field_name] = self.format_seconds(seconds)

        return total_row

    # Recompute a row total from activity fields when an older row has no total value.
    def recalculate_row_total(self, row):
        return self.format_seconds(
            sum(self.parse_duration(row.get(field_name, "00:00:00")) for field_name in ACTIVITY_TO_FIELD.values())
        )

    # Return stored seconds for an activity, including the still-running timer if active.
    def current_total(self, activity):
        total = self.totals[activity]
        if self.active_activity == activity and self.active_start is not None:
            total += (datetime.now() - self.active_start).total_seconds()
        return round(total)

    # Normalize all persisted CSV session dates to one canonical format.
    #
    # Canonical format: YYYY-MM-DD. Legacy formats are accepted only so old rows can be converted
    # on the next successful save. Unknown non-empty values are preserved to avoid accidental data
    # loss, and a diagnostic warning is written.
    def normalize_csv_date_value(self, value):
        raw_value = (value or "").strip()

        if not raw_value or raw_value == "TOTAL":
            return raw_value

        for date_format in LEGACY_CSV_DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(raw_value, date_format).date()
                normalized_value = parsed_date.strftime(CSV_DATE_FORMAT)
                if normalized_value != raw_value:
                    self.write_diagnostic_log(
                        "CSV date normalized | "
                        f"original={raw_value} | normalized={normalized_value} | "
                        f"canonical_format={CSV_DATE_FORMAT_DESCRIPTION}"
                    )
                return normalized_value
            except ValueError:
                continue

        self.write_diagnostic_log(
            "CSV date could not be normalized; preserving original value | "
            f"value={raw_value} | canonical_format={CSV_DATE_FORMAT_DESCRIPTION}"
        )
        return raw_value

    # Format a datetime or date-like value as the canonical CSV date string.
    @staticmethod
    def format_csv_date(value):
        if isinstance(value, datetime):
            return value.strftime(CSV_DATE_FORMAT)
        return datetime.strptime(str(value), CSV_DATE_FORMAT).strftime(CSV_DATE_FORMAT)

    # Format integer seconds as HH:MM:SS for display and CSV storage.
    @staticmethod
    def format_seconds(seconds):
        seconds = int(seconds)
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

    # Parse an HH:MM:SS value from CSV or UI state into seconds.
    @staticmethod
    def parse_duration(duration):
        try:
            hours, minutes, seconds = duration.split(":")
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        except (AttributeError, ValueError):
            return 0

    # Refresh visible activity labels every 500 ms while the window is alive.
    def update_display(self):
        if self.is_closing:
            return
        try:
            for activity in ACTIVITIES:
                self.labels[activity].config(text=self.format_seconds(self.current_total(activity)))
            self.after_job_id = self.root.after(500, self.update_display)
        except tk.TclError:
            return

    # Write a fallback one-session CSV when the normal main CSV cannot be saved.
    def save_emergency_session_file(self, session_end, error):
        emergency_file = self.log_dir / (
            EMERGENCY_FILE_PREFIX
            + session_end.strftime("%Y%m%d_%H%M%S")
            + ".csv"
        )

        session_row = self.create_session_row(session_end)

        # The emergency file mirrors the main CSV schema so read_emergency_session_rows() can
        # merge it without special-case conversion on the next successful save.
        with emergency_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
            writer.writerow(session_row)

        self.write_diagnostic_log(f"Emergency session file created | file={emergency_file} | original_error={error}")
        return emergency_file

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
                    # Stop the periodic UI callback before widgets are destroyed.
                    self.root.after_cancel(self.after_job_id)
                except tk.TclError:
                    pass

            if not self.session_saved:
                # The active timer is closed at the same timestamp used for the session end so
                # the final running segment is included in the row about to be written.
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

                    # Normal-save failures are reported, but the window still closes. This keeps
                    # the app usable even when the main CSV is locked by another program.
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


if __name__ == "__main__":
    args = parse_args()
    root = tk.Tk()
    LearningClock(
        root,
        learning_path_name=args.learning_path,
        log_dir=args.log_dir,
        debug_break_on_click=args.debug_break_on_click,
        debug_break_on_close=args.debug_break_on_close,
    )
    root.mainloop()
