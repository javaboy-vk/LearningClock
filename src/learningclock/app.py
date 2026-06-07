# =============================================================================
# File Name : app.py
# Artifact  : LearningClock - Tkinter Application
# Author    : javaboy-vk
# Date      : 2026-06-06
# Version   : v0.1.0
# Purpose:
#   Provides the Tkinter UI, timer state, manual entry workflow, and shutdown
#   lifecycle for LearningClock.
#
# Application call tree:
#   main(argv)
#   |-- parse_args(argv)
#   |   |-- --learning-path
#   |   |-- --log-dir
#   |   |-- --debug-break-on-click
#   |   `-- --debug-break-on-close
#   |-- tk.Tk()
#   |-- LearningClock(root, ...)
#   |   |-- CsvStore(log_dir, learning_path_name)
#   |   |-- write_diagnostic_log("Application initialized ...")
#   |   |-- build_menu()
#   |   |   |-- About -> show_about()
#   |   |   |-- Add Time -> enter_add_time_mode()
#   |   |   `-- Add Page Count -> enter_add_page_count_mode()
#   |   |-- build_main_ui()
#   |   |   |-- create activity rows from ACTIVITIES
#   |   |   |-- activity button -> switch_to(activity)
#   |   |   |-- manual time entry -> add_all_manual_time()
#   |   |   |-- page count entry -> add_page_count()
#   |   |   |-- Stop -> stop_running_timer()
#   |   |   `-- Reset Timer -> reset_running_timer()
#   |   `-- update_display()
#   |       |-- current_total(activity)
#   |       `-- root.after(500, update_display)
#   `-- root.mainloop()
#
# Timer activity flow:
#   switch_to(activity)
#   |-- optional debug breakpoint
#   |-- write_diagnostic_log("Switch requested ...")
#   |-- close_active_timer(now)
#   |   |-- compute elapsed seconds
#   |   |-- add elapsed seconds to totals[active_activity]
#   |   `-- clear active activity state
#   |-- set active_activity
#   |-- set active_start
#   |-- mark session unsaved
#   `-- update status text
#
# Manual entry flow:
#   enter_add_time_mode()
#   `-- add_all_manual_time()
#       |-- parse_manual_input(value)
#       |-- collect validation errors
#       |-- add valid seconds to activity totals
#       |-- clear entry fields
#       |-- mark session unsaved
#       `-- exit_add_time_mode()
#
# Page-count flow:
#   enter_add_page_count_mode()
#   `-- add_page_count()
#       |-- validate whole-number page input
#       |-- add pages to session total
#       |-- clear page field
#       |-- mark session unsaved
#       `-- exit_add_page_count_mode()
#
# Shutdown save flow:
#   on_close()
#   |-- mark closing
#   |-- cancel scheduled update_display callback
#   |-- close_active_timer(session_end)
#   |-- save_session_summary(session_end)
#   |   |-- create_session_row(session_end)
#   |   |   |-- current_total(activity) for every activity
#   |   |   `-- CsvStore.create_session_row(...)
#   |   `-- CsvStore.save_session_summary(...)
#   |-- on normal-save failure: save_emergency_session_file(session_end, error)
#   |   |-- create_session_row(session_end)
#   |   `-- CsvStore.save_emergency_session_file(...)
#   |-- show save warning when needed
#   |-- root.quit()
#   `-- root.destroy()
# =============================================================================

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

if __package__ in (None, ""):
    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(script_dir.parent))

try:
    from learningclock.csv_store import (
        ACTIVITIES,
        CSV_DATE_FORMAT_DESCRIPTION,
        CsvStore,
        format_seconds,
    )
except ModuleNotFoundError:
    from csv_store import (  # type: ignore[no-redef]
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


# Operational algorithm:
#   What this function does:
#     Parses direct Python, launcher, and VS Code debug arguments for the GUI app.
#   Success:
#     Returns the learning path, log directory, and optional debug-break flags.
#   Error handling:
#     argparse reports invalid arguments before Tkinter starts.
def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Learning Clock")      # Create CLI parser for app launch.
    parser.add_argument("--learning-path", default=None)                 # Optional display/persisted path name.
    parser.add_argument("--log-dir", default=None)                       # Optional CSV/log output directory.
    parser.add_argument("--debug-break-on-click", action="store_true")   # Developer breakpoint on activity click.
    parser.add_argument("--debug-break-on-close", action="store_true")   # Developer breakpoint on close.
    return parser.parse_args(argv)                                       # Return parsed launch settings.


class LearningClock:
    # Operational algorithm:
    #   What this class does:
    #     Tracks activity timers in a Tkinter UI and persists one session summary on shutdown.
    #   Success:
    #     The user can switch timers, add manual time/pages, see live totals, and close to save CSV.
    #   Error handling:
    #     Save failures are logged and routed through emergency CSV persistence during shutdown.

    # Operational algorithm:
    #   What this method does:
    #     Initializes app state, storage paths, window behavior, controls, and the update loop.
    #   Success:
    #     The window is ready, CsvStore is configured, diagnostics identify paths, and labels update.
    #   Error handling:
    #     CsvStore directory creation errors propagate because the app cannot run without storage.
    def __init__(
        self,
        root,
        learning_path_name=None,
        log_dir=None,
        debug_break_on_click=False,
        debug_break_on_close=False,
    ):
        self.root = root                                                            # Tk root window owned by this app.
        self.learning_path_name = learning_path_name or Path.cwd().name             # Default to current folder name.
        self.debug_break_on_click = debug_break_on_click                            # Developer click breakpoint flag.
        self.debug_break_on_close = debug_break_on_close                            # Developer close breakpoint flag.
        self.root.title(self.build_window_title())                                  # Put app/version/path in title.
        self.root.geometry(NORMAL_GEOMETRY)                                         # Start in compact timer layout.
        self.root.resizable(False, False)                                           # Keep fixed geometry predictable.
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)                       # Route window close through save flow.

        self.store = CsvStore(log_dir or Path.cwd(), self.learning_path_name)       # Configure CSV persistence.
        self.log_dir = self.store.log_dir                                           # Expose resolved log directory.
        self.log_file = self.store.log_file                                         # Expose resolved CSV file path.
        self.diagnostic_log_file = self.store.diagnostic_log_file                   # Expose diagnostic log path.

        self.write_diagnostic_log(
            "Application initialized\n"
            f"learning_path={self.learning_path_name}\n"
            f"cwd={Path.cwd()}\n"
            f"log_dir={self.log_dir}\n"
            f"log_file={self.log_file}\n"
            f"diagnostic_log_file={self.diagnostic_log_file}\n"
            f"python={sys.executable}\n"
            f"csv_date_format={CSV_DATE_FORMAT_DESCRIPTION}"
        )

        self.session_start = datetime.now()                                         # Timestamp this app session.
        self.session_saved = False                                                  # Save happens only during close.
        self.is_closing = False                                                     # Prevent duplicate close handling.
        self.after_job_id = None                                                    # Tkinter scheduled update handle.

        self.active_activity = None                                                 # Currently running activity name.
        self.active_start = None                                                    # Start timestamp for active timer.
        self.add_time_mode = False                                                  # Manual-time UI mode flag.
        self.add_page_count_mode = False                                            # Page-count UI mode flag.

        self.totals = {activity: 0 for activity in ACTIVITIES}                      # Accumulated seconds by activity.
        self.pages_read = 0                                                         # Accumulated session pages.

        self.labels = {}                                                            # Activity -> visible timer label.
        self.manual_entries = {}                                                    # Activity -> manual-time entry.
        self.page_count_entry = None                                                # Entry widget for pages.
        self.add_time_button = None                                                 # Button shown in add-time mode.
        self.add_pages_button = None                                                # Button shown in add-page mode.

        self.build_menu()                                                           # Create menu commands.
        self.build_main_ui()                                                        # Create timer controls.
        self.update_display()                                                       # Start recurring label updates.

    # Operational algorithm:
    #   What this method does:
    #     Delegates diagnostic logging to the CsvStore so the app and persistence share one log.
    #   Success:
    #     App events appear in the same log file as CSV read/write events.
    #   Error handling:
    #     CsvStore absorbs logging failures so app actions are not blocked by diagnostics.
    def write_diagnostic_log(self, message, exc=None):
        self.store.write_diagnostic_log(message, exc)                              # Share CsvStore diagnostic log.

    # Operational algorithm:
    #   What this method does:
    #     Builds the title shown in the Tkinter title bar.
    #   Success:
    #     The title identifies the app, version, and configured learning path.
    #   Error handling:
    #     No special error handling is needed because values are plain strings.
    def build_window_title(self):
        return f"{APP_TITLE} - {APP_VERSION} - {self.learning_path_name}"          # Compose visible window title.

    # Operational algorithm:
    #   What this method does:
    #     Creates the top menu commands for app info and temporary input modes.
    #   Success:
    #     Menu commands call the correct mode/about handlers.
    #   Error handling:
    #     Tkinter construction errors propagate because the UI cannot run without a menu.
    def build_menu(self):
        menu_bar = tk.Menu(self.root)                                               # Create menu bar.
        menu_bar.add_command(label="About", command=self.show_about)                # Show runtime/path info.
        menu_bar.add_command(label="Add Time", command=self.enter_add_time_mode)    # Enter manual duration mode.
        menu_bar.add_command(label="Add Page Count", command=self.enter_add_page_count_mode)  # Enter pages mode.
        self.root.config(menu=menu_bar)                                             # Attach menu to window.

    # Operational algorithm:
    #   What this method does:
    #     Creates the visible timer controls, counters, hidden manual-entry widgets, and buttons.
    #   Success:
    #     Every activity has a start/switch button, a live label, and a hidden manual-time entry.
    #   Error handling:
    #     Tkinter construction errors propagate because the window is unusable without controls.
    def build_main_ui(self):
        self.status = tk.Label(
            self.root,                                                        # Parent window.
            text="No timer running",                                          # Initial status.
            font=("Arial", 13, "bold"),                                       # Emphasize current state.
            anchor="w",                                                       # Left-align status text.
        )
        self.status.pack(fill="x", padx=16, pady=(6, 3))                      # Place status above timers.

        self.timer_frame = tk.Frame(self.root)                                # Container for activity rows.
        self.timer_frame.pack(fill="x", padx=16, pady=0)                      # Keep rows compact.

        for activity in ACTIVITIES:                                           # Create one row per activity.
            row = tk.Frame(self.timer_frame)                                  # Row owns button/label/entries.
            row.pack(fill="x", pady=1)                                        # Stack rows vertically.

            button = tk.Button(
                row,                                                          # Parent row.
                text=activity,                                                # Activity label on button.
                font=("Arial", 12),                                           # Readable button font.
                width=24,                                                     # Fixed width keeps rows aligned.
                anchor="w",                                                   # Left-align activity text.
                command=lambda a=activity: self.switch_to(a),                 # Capture activity for callback.
            )
            button.pack(side="left")                                          # Button starts each row.

            label = tk.Label(row, text="00:00:00", font=("Consolas", 14), width=12)  # Live duration label.
            label.pack(side="left", padx=(10, 0))                              # Place label after button.
            self.labels[activity] = label                                      # Store for update_display.

            entry = tk.Entry(row, font=("Arial", 11), width=11)                # Hidden manual duration entry.
            entry.bind("<Return>", lambda _event: self.add_all_manual_time())  # Enter submits all manual values.
            self.manual_entries[activity] = entry                              # Store for add-time mode.

            if activity == "Reading":                                         # Put page entry on reading row.
                self.page_count_entry = tk.Entry(row, font=("Arial", 11), width=8)  # Hidden page-count entry.
                self.page_count_entry.bind("<Return>", lambda _event: self.add_page_count())  # Enter adds pages.

        controls_frame = tk.Frame(self.root)                                   # Container for command buttons.
        controls_frame.pack(fill="x", padx=16, pady=(4, 0), anchor="w")        # Place below activity rows.

        stop_button = tk.Button(
            controls_frame,                                                    # Parent controls row.
            text="Stop",                                                       # Stop current timer.
            font=("Arial", 10),                                                # Compact button font.
            width=12,                                                          # Fixed width for alignment.
            command=self.stop_running_timer,                                   # Stop without resetting totals.
        )
        stop_button.pack(side="left", padx=(0, 6))                             # First command button.

        reset_button = tk.Button(
            controls_frame,                                                    # Parent controls row.
            text="Reset Timer",                                                # Reset currently running activity.
            font=("Arial", 10),                                                # Compact button font.
            width=12,                                                          # Fixed width for alignment.
            command=self.reset_running_timer,                                  # Reset active timer only.
        )
        reset_button.pack(side="left", padx=(0, 6))                            # Second command button.

        self.add_time_button = tk.Button(
            controls_frame,                                                    # Parent controls row.
            text="Add Time",                                                   # Submit manual time entries.
            font=("Arial", 10),                                                # Compact button font.
            width=12,                                                          # Fixed width for alignment.
            command=self.add_all_manual_time,                                  # Validate/add durations.
        )

        self.add_pages_button = tk.Button(
            controls_frame,                                                    # Parent controls row.
            text="Add Pages",                                                  # Submit page-count entry.
            font=("Arial", 10),                                                # Compact button font.
            width=12,                                                          # Fixed width for alignment.
            command=self.add_page_count,                                       # Validate/add pages.
        )

    # Operational algorithm:
    #   What this method does:
    #     Shows runtime information, output paths, and persistence behavior.
    #   Success:
    #     The user can inspect exactly where CSV and diagnostic log files are written.
    #   Error handling:
    #     messagebox errors are left to Tkinter; this method has no persistence side effects.
    def show_about(self):
        about_text = "\n".join([
            f"{APP_TITLE} - {APP_VERSION}",                                   # App identity.
            f"Learning Path: {self.learning_path_name}",                       # Configured learning path.
            f"CSV: {self.log_file}",                                           # Main CSV path.
            f"Diagnostic Log: {self.diagnostic_log_file}",                     # Diagnostic log path.
            f"CSV Date Format: {CSV_DATE_FORMAT_DESCRIPTION}",                 # Persisted date contract.
            "Manual Add accepts minutes, HH:MM, or HH:MM:SS.",                 # Manual time input contract.
            "The session is saved only when the app closes.",                  # Save lifecycle note.
            "Emergency CSV files are merged automatically on the next successful save.",  # Recovery note.
        ])
        messagebox.showinfo("About Learning Clock", about_text)                # Display the information.

    # Operational algorithm:
    #   What this method does:
    #     Switches the UI into manual time-entry mode.
    #   Success:
    #     Manual entry fields and Add Time button are visible, and the first field has focus.
    #   Error handling:
    #     Re-entering the same mode is a no-op; page-count mode is closed first.
    def enter_add_time_mode(self):
        if self.add_page_count_mode:                                           # Only one temporary input mode at a time.
            self.exit_add_page_count_mode()
        if self.add_time_mode:                                                 # Already in add-time mode.
            return

        self.add_time_mode = True                                              # Mark mode active.
        self.root.geometry(ADD_TIME_GEOMETRY)                                  # Widen window for entries.

        for activity in ACTIVITIES:                                            # Show one manual entry per activity.
            self.manual_entries[activity].pack(side="left", padx=(8, 0))

        self.add_time_button.pack(side="left", padx=(0, 0))                    # Show submit button.

        first_entry = self.manual_entries.get(ACTIVITIES[0])                   # Focus first activity entry.
        if first_entry is not None:                                            # Defensive check for UI setup.
            first_entry.focus_set()

        self.status.config(text="Add Time mode")                               # Tell user the active mode.

    # Operational algorithm:
    #   What this method does:
    #     Leaves manual time-entry mode and restores the normal timer layout.
    #   Success:
    #     Manual entries/buttons are hidden and status returns to the running timer state.
    #   Error handling:
    #     Exiting when not in add-time mode is a no-op.
    def exit_add_time_mode(self):
        if not self.add_time_mode:                                             # Already in normal layout.
            return

        self.add_time_mode = False                                             # Mark mode inactive.

        for entry in self.manual_entries.values():                             # Hide all manual entry fields.
            entry.pack_forget()

        self.add_time_button.pack_forget()                                     # Hide submit button.
        self.root.geometry(NORMAL_GEOMETRY)                                    # Restore compact layout.
        self.restore_running_status()                                          # Restore status text.

    # Operational algorithm:
    #   What this method does:
    #     Switches the UI into page-count mode.
    #   Success:
    #     The page-count entry and Add Pages button are visible and focused.
    #   Error handling:
    #     Re-entering the same mode is a no-op; add-time mode is closed first.
    def enter_add_page_count_mode(self):
        if self.add_time_mode:                                                 # Only one temporary input mode at a time.
            self.exit_add_time_mode()
        if self.add_page_count_mode:                                           # Already in page-count mode.
            return

        self.add_page_count_mode = True                                        # Mark mode active.
        self.root.geometry(ADD_PAGE_COUNT_GEOMETRY)                            # Widen window for page entry.

        if self.page_count_entry is not None:                                  # Page entry exists on Reading row.
            self.page_count_entry.pack(side="left", padx=(8, 0))               # Show page-count input.
            self.page_count_entry.focus_set()                                  # Put cursor in page entry.

        self.add_pages_button.pack(side="left", padx=(0, 0))                   # Show submit button.
        self.status.config(text="Add Page Count mode")                         # Tell user the active mode.

    # Operational algorithm:
    #   What this method does:
    #     Leaves page-count mode and restores the normal timer layout.
    #   Success:
    #     Page entry/button are hidden and status returns to the running timer state.
    #   Error handling:
    #     Exiting when not in page-count mode is a no-op.
    def exit_add_page_count_mode(self):
        if not self.add_page_count_mode:                                       # Already in normal layout.
            return

        self.add_page_count_mode = False                                       # Mark mode inactive.

        if self.page_count_entry is not None:                                  # Page entry may be absent in tests.
            self.page_count_entry.pack_forget()                                # Hide page-count input.

        self.add_pages_button.pack_forget()                                    # Hide submit button.
        self.root.geometry(NORMAL_GEOMETRY)                                    # Restore compact layout.
        self.restore_running_status()                                          # Restore status text.

    # Operational algorithm:
    #   What this method does:
    #     Restores the status label after a temporary input mode closes.
    #   Success:
    #     The status reflects the running activity or the idle state.
    #   Error handling:
    #     No special error handling is needed because it only updates one label.
    def restore_running_status(self):
        if self.active_activity:                                               # A timer is currently active.
            self.status.config(text=f"Running: {self.active_activity}")        # Show active timer.
        else:
            self.status.config(text="No timer running")                        # Show idle state.

    # Operational algorithm:
    #   What this method does:
    #     Handles an activity-button click by stopping any previous timer and starting a new one.
    #   Success:
    #     Elapsed time is credited to the old activity and the selected activity starts timing.
    #   Error handling:
    #     Optional debug breakpoint allows inspection before state changes.
    def switch_to(self, activity):
        if self.debug_break_on_click:                                         # Developer debugging hook.
            breakpoint()

        self.write_diagnostic_log(f"Switch requested | activity={activity}")   # Record requested activity.
        self.close_active_timer(datetime.now())                                # Credit previous active timer.
        self.active_activity = activity                                        # Store new active activity.
        self.active_start = datetime.now()                                     # Start new timer now.
        self.session_saved = False                                             # Session changed since last save.
        self.status.config(text=f"Running: {activity}")                        # Show running activity.
        self.write_diagnostic_log(
            f"Timer started | activity={activity} | "
            f"active_start={self.active_start:%H:%M:%S}"                       # Record start time.
        )

    # Operational algorithm:
    #   What this method does:
    #     Accumulates elapsed seconds for the active timer and clears active timer state.
    #   Success:
    #     The active activity's total increases by elapsed seconds and no timer remains active.
    #   Error handling:
    #     Calling with no active timer is a no-op.
    def close_active_timer(self, now):
        if self.active_activity is None or self.active_start is None:          # Nothing is currently running.
            return
        elapsed_seconds = (now - self.active_start).total_seconds()            # Compute elapsed runtime.
        self.totals[self.active_activity] += elapsed_seconds                   # Add time to active activity total.
        self.write_diagnostic_log(
            "Timer closed | "
            f"activity={self.active_activity} | "
            f"elapsed={format_seconds(round(elapsed_seconds))} | "
            f"activity_total={format_seconds(round(self.totals[self.active_activity]))}"  # Record new total.
        )
        self.active_activity = None                                            # Clear active activity.
        self.active_start = None                                               # Clear active start time.

    # Operational algorithm:
    #   What this method does:
    #     Stops the active timer without resetting accumulated session totals.
    #   Success:
    #     Active elapsed time is credited and the status shows which activity stopped.
    #   Error handling:
    #     If no timer is running, the status stays idle and no totals change.
    def stop_running_timer(self):
        if self.active_activity is None:                                       # Nothing to stop.
            self.status.config(text="No timer running")                        # Keep idle status visible.
            return
        stopped_activity = self.active_activity                                # Remember label before clearing state.
        self.close_active_timer(datetime.now())                                # Credit elapsed time and clear active state.
        self.status.config(text=f"Stopped: {stopped_activity}")                # Tell user what stopped.

    # Operational algorithm:
    #   What this method does:
    #     Resets only the currently running activity total and continues timing it from now.
    #   Success:
    #     The active activity total becomes zero and the active start timestamp resets.
    #   Error handling:
    #     If no timer is running, a warning is shown and no totals change.
    def reset_running_timer(self):
        if self.active_activity is None:                                       # Reset requires an active timer.
            messagebox.showwarning("Reset Timer", "No timer is currently running.")  # Explain no-op to user.
            return
        activity = self.active_activity                                        # Capture active activity name.
        self.totals[activity] = 0                                              # Drop accumulated time for that activity.
        self.active_start = datetime.now()                                     # Restart timing from now.
        self.session_saved = False                                             # Session changed since last save.
        self.status.config(text=f"Reset running timer: {activity}")            # Show reset result.
        self.update_display()                                                  # Refresh labels immediately.

    # Operational algorithm:
    #   What this method does:
    #     Validates every manual time entry and adds valid durations to the session totals.
    #   Success:
    #     All valid entries are applied together, fields are cleared, and add-time mode exits.
    #   Error handling:
    #     Any invalid field blocks the entire add operation and reports all field errors.
    def add_all_manual_time(self):
        additions = []                                                        # Valid (activity, seconds) pairs.
        errors = []                                                           # Validation messages to show together.

        for activity, entry in self.manual_entries.items():                    # Validate every visible/manual field.
            raw_value = entry.get().strip()                                    # Normalize user input.
            if not raw_value:                                                  # Blank field means no addition.
                continue
            try:
                seconds = self.parse_manual_input(raw_value)                   # Convert accepted format to seconds.
            except ValueError as exc:
                errors.append(f"{activity}: {exc}")                            # Keep field-specific error.
                continue
            if seconds <= 0:                                                   # Zero/negative time is not useful.
                errors.append(f"{activity}: manual time must be greater than zero.")  # Explain invalid value.
                continue
            additions.append((activity, seconds))                              # Keep valid addition for batch apply.

        if errors:                                                             # Do not partially apply invalid form.
            messagebox.showerror("Invalid Manual Time", "\n".join(errors))     # Show all errors at once.
            return
        if not additions:                                                      # No fields contained values.
            messagebox.showwarning("Manual Time", "Enter time for at least one timer.")  # Ask user for input.
            return

        for activity, seconds in additions:                                    # Apply validated additions.
            self.totals[activity] += seconds                                  # Add manual seconds to activity total.
            self.write_diagnostic_log(
                f"Manual time added | activity={activity} | added={format_seconds(seconds)} | "
                f"activity_total={format_seconds(round(self.totals[activity]))}"  # Record updated activity total.
            )

        for entry in self.manual_entries.values():                             # Clear all manual fields after success.
            entry.delete(0, tk.END)

        self.session_saved = False                                             # Session changed since last save.
        self.update_display()                                                  # Refresh labels immediately.
        self.exit_add_time_mode()                                              # Return to normal timer layout.

    # Operational algorithm:
    #   What this method does:
    #     Validates and adds manual page-count input to the current session.
    #   Success:
    #     Positive whole-number pages are added, the field is cleared, and page-count mode exits.
    #   Error handling:
    #     Missing, non-numeric, or non-positive values show warnings/errors and do not change totals.
    def add_page_count(self):
        if self.page_count_entry is None:                                      # Page field may not exist in tests.
            return

        raw_value = self.page_count_entry.get().strip()                        # Normalize user input.

        if not raw_value:                                                      # Empty field is not a page count.
            messagebox.showwarning("Add Page Count", "Enter the number of pages read.")  # Ask for input.
            return
        if not raw_value.isdigit():                                            # Only whole-number pages are supported.
            messagebox.showerror("Add Page Count", "Page count must be a whole number.")  # Explain invalid value.
            return

        pages = int(raw_value)                                                 # Convert validated text to int.
        if pages <= 0:                                                         # Defensive check after digit validation.
            messagebox.showwarning("Add Page Count", "Page count must be greater than zero.")  # Reject zero.
            return

        self.pages_read += pages                                               # Add pages to session total.
        self.write_diagnostic_log(
            f"Pages added | added={pages} | pages_read_session_total={self.pages_read}"  # Record page total.
        )
        self.page_count_entry.delete(0, tk.END)                                # Clear input field.
        self.session_saved = False                                             # Session changed since last save.
        self.exit_add_page_count_mode()                                        # Return to normal timer layout.
        self.status.config(text=f"Added pages read: {pages}")                  # Confirm addition to user.

    # Operational algorithm:
    #   What this method does:
    #     Converts manual time text into seconds.
    #   Success:
    #     Accepts minutes, HH:MM, and HH:MM:SS.
    #   Error handling:
    #     Blank or malformed text raises ValueError with user-facing guidance.
    @staticmethod
    def parse_manual_input(value):
        normalized = value.strip()                                             # Remove surrounding whitespace.
        if not normalized:                                                     # Blank input is not meaningful.
            raise ValueError("Manual time cannot be blank.")

        if normalized.isdigit():                                               # Plain number means minutes.
            return int(normalized) * 60

        parts = normalized.split(":")                                          # Try clock-style formats.
        if len(parts) == 2:                                                    # HH:MM format.
            hours, minutes = parts
            if not hours.isdigit() or not minutes.isdigit():                   # Both pieces must be numeric.
                raise ValueError("Use minutes, HH:MM, or HH:MM:SS.")
            return int(hours) * 3600 + int(minutes) * 60                       # Convert hours/minutes to seconds.

        if len(parts) == 3:                                                    # HH:MM:SS format.
            hours, minutes, seconds = parts
            if not hours.isdigit() or not minutes.isdigit() or not seconds.isdigit():  # All pieces numeric.
                raise ValueError("Use minutes, HH:MM, or HH:MM:SS.")
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)        # Convert to seconds.

        raise ValueError("Use minutes, HH:MM, or HH:MM:SS.")                   # Reject unsupported shapes.

    # Operational algorithm:
    #   What this method does:
    #     Returns the current displayed total for an activity.
    #   Success:
    #     Stored seconds plus live elapsed seconds are included for the active activity.
    #   Error handling:
    #     Activity keys are expected to come from ACTIVITIES; invalid keys naturally raise KeyError.
    def current_total(self, activity):
        total = self.totals[activity]                                          # Start with accumulated stored seconds.
        if self.active_activity == activity and self.active_start is not None:  # Include live timer when active.
            total += (datetime.now() - self.active_start).total_seconds()
        return round(total)                                                    # Display/persist rounded seconds.

    # Operational algorithm:
    #   What this method does:
    #     Builds the session row that will be handed to CsvStore.
    #   Success:
    #     The row reflects current totals for every activity and the current page count.
    #   Error handling:
    #     CsvStore owns date/time formatting validation for the final row.
    def create_session_row(self, session_end):
        activity_seconds = {
            activity: self.current_total(activity)                             # Include live totals per activity.
            for activity in ACTIVITIES                                         # Preserve configured activity order.
        }
        return self.store.create_session_row(
            self.session_start,                                                # Session start timestamp.
            session_end,                                                       # Session end timestamp.
            activity_seconds,                                                  # Activity seconds dictionary.
            self.pages_read,                                                   # Session page total.
        )

    # Operational algorithm:
    #   What this method does:
    #     Saves the current session through CsvStore and records whether the save wrote rows.
    #   Success:
    #     session_saved mirrors CsvStore.save_session_summary's boolean result.
    #   Error handling:
    #     Exceptions propagate to on_close, which can create an emergency file.
    def save_session_summary(self, session_end):
        saved = self.store.save_session_summary(self.create_session_row(session_end))  # Persist current session.
        self.session_saved = saved                                             # Remember save result.
        return saved                                                           # Return result to caller.

    # Operational algorithm:
    #   What this method does:
    #     Saves the current session to an emergency CSV file after normal persistence fails.
    #   Success:
    #     CsvStore returns the emergency file path.
    #   Error handling:
    #     Exceptions propagate to on_close, which logs emergency-save failure.
    def save_emergency_session_file(self, session_end, error):
        session_row = self.create_session_row(session_end)                     # Rebuild row for emergency save.
        return self.store.save_emergency_session_file(session_row, session_end, error)  # Persist fallback CSV.

    # Operational algorithm:
    #   What this method does:
    #     Refreshes visible activity labels and schedules the next refresh.
    #   Success:
    #     Every label shows current HH:MM:SS totals and updates roughly twice per second.
    #   Error handling:
    #     Closing state and Tkinter teardown errors stop the loop quietly.
    def update_display(self):
        if self.is_closing:                                                    # Do not update widgets during shutdown.
            return
        try:
            for activity in ACTIVITIES:                                        # Refresh each activity label.
                self.labels[activity].config(text=format_seconds(self.current_total(activity)))  # Show current total.
            self.after_job_id = self.root.after(500, self.update_display)      # Schedule next refresh.
        except tk.TclError:
            return                                                             # Window is likely being destroyed.

    # Operational algorithm:
    #   What this method does:
    #     Saves the current session during window close and tears down Tkinter.
    #   Success:
    #     Active timer time is credited, CsvStore saves the session, and the window closes cleanly.
    #   Error handling:
    #     Normal save failures are logged; emergency save is attempted; the user sees a warning.
    def on_close(self):
        if self.is_closing:                                                    # Prevent duplicate close processing.
            return

        if self.debug_break_on_close:                                          # Developer debugging hook.
            breakpoint()

        self.is_closing = True                                                 # Stop display loop and duplicate close.
        session_end = datetime.now()                                           # Timestamp the end of this session.
        self.write_diagnostic_log(
            f"Close requested | session_start={self.session_start:%Y-%m-%d %H:%M:%S} | "
            f"session_end={session_end:%Y-%m-%d %H:%M:%S} | session_saved={self.session_saved}"  # Record close state.
        )

        try:
            if self.after_job_id is not None:                                  # Cancel scheduled label refresh.
                try:
                    self.root.after_cancel(self.after_job_id)                  # Stop future update_display call.
                except tk.TclError:
                    pass                                                       # Window may already be tearing down.

            if not self.session_saved:                                         # Avoid duplicate save attempts.
                self.close_active_timer(session_end)                           # Credit running timer before saving.

                try:
                    self.save_session_summary(session_end)                     # Normal persistence path.
                except Exception as exc:
                    self.write_diagnostic_log("Normal CSV save failed.", exc)  # Preserve failure details.
                    emergency_file = None                                      # Track fallback result.
                    try:
                        emergency_file = self.save_emergency_session_file(session_end, exc)  # Fallback persistence.
                    except Exception as emergency_exc:
                        self.write_diagnostic_log("Emergency save failed.", emergency_exc)  # Preserve fallback failure.
                        emergency_file = None                                  # No fallback file available.

                    error_message = (
                        "The normal CSV save failed, but the application will close.\n\n"
                        f"Error: {exc}"                                       # Show normal-save failure.
                    )
                    if emergency_file is not None:                             # Fallback succeeded.
                        error_message += f"\n\nEmergency session file created:\n{emergency_file}"
                    else:
                        error_message += (
                            "\n\nEmergency save also failed. "
                            "Run the debug .bat launcher to see the Python error."  # Tell user how to inspect failure.
                        )
                    messagebox.showerror("Learning Clock Save Warning", error_message)  # Surface save problem.
        finally:
            self.write_diagnostic_log("Application shutdown finalization started.")  # Record final teardown.
            try:
                self.root.quit()                                                # Exit Tk main loop.
            except tk.TclError:
                pass                                                            # Window may already be closed.
            try:
                self.root.destroy()                                             # Destroy widgets/native window.
            except tk.TclError:
                pass                                                            # Ignore duplicate destroy.


    # Operational algorithm:
    #   What this function does:
    #     Starts the Tkinter application from command-line arguments.
    #   Success:
    #     Tkinter mainloop runs until the app is closed, then returns process status zero.
    #   Error handling:
    #     Startup exceptions propagate because an app that cannot initialize should fail visibly.
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)                                                     # Parse CLI/debug launch arguments.
    root = tk.Tk()                                                              # Create root Tk window.
    LearningClock(
        root,                                                                   # Window root.
        learning_path_name=args.learning_path,                                  # Optional configured path name.
        log_dir=args.log_dir,                                                   # Optional CSV/log output directory.
        debug_break_on_click=args.debug_break_on_click,                         # Developer click breakpoint.
        debug_break_on_close=args.debug_break_on_close,                         # Developer close breakpoint.
    )
    root.mainloop()                                                             # Run UI event loop.
    return 0                                                                    # Successful process exit code.


if __name__ == "__main__":
    raise SystemExit(main())
