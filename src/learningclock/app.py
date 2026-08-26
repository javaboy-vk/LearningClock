# =============================================================================
# File Name : app.py
# Artifact  : LearningClock - Tkinter Application
# Author    : javaboy-vk
# Date      : 2026-06-06
# Version   : v5.4
# Purpose:
#   Provides the Tkinter UI, timer state, manual entry workflow, semantic
#   application events, and shutdown lifecycle for LearningClock.
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
#   |   |-- emit APPLC-1002 application-initialized event
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
#   |-- emit TIMER-3001 switch-requested event
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
import calendar
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox

# Operational algorithm:
#   What this block does:
#     Makes direct script execution resolve package modules like an installed entry point.
#   Success:
#     Running src/learningclock/app.py directly can still import learningclock.csv_store.
#   Error handling:
#     If the package import cannot resolve, the fallback import block handles local module loading.
if __package__ in (None, ""):
    script_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(script_dir.parent))

from learningclock.events import (
    ApplicationEvents,
    ConfigurationEvents,
    TimerEvents,
    UiEvents,
)
from learningclock.observability import (
    configure_observability,
    correlation_context,
    shutdown_observability,
)

# Operational algorithm:
#   What this block does:
#     Imports CSV persistence contracts from the package first, then from the local module fallback.
#   Success:
#     The app can run from package entry points, direct Python execution, and launcher scripts.
#   Error handling:
#     ModuleNotFoundError switches to the direct local import used when the package name is unavailable.
try:
    from learningclock.csv_store import (
        ACTIVITIES,
        ACTIVITY_TO_FIELD,
        CSV_DATE_FORMAT_DESCRIPTION,
        DIAGNOSTIC_LOG_FILE_NAME,
        CsvStore,
        format_seconds,
        parse_duration,
    )
except ModuleNotFoundError:
    from csv_store import (  # type: ignore[no-redef]
        ACTIVITIES,
        ACTIVITY_TO_FIELD,
        CSV_DATE_FORMAT_DESCRIPTION,
        DIAGNOSTIC_LOG_FILE_NAME,
        CsvStore,
        format_seconds,
        parse_duration,
    )

# Operational algorithm:
#   What this constant group does:
#     Defines the visible app identity used by the window title and about dialog.
#   Success:
#     UI identity text stays centralized and consistent across app surfaces.
#   Error handling:
#     No special error handling is needed because the values are static strings.
APP_TITLE = "Learning Clock"
APP_VERSION = "v5.3"
BUTTON_BACKGROUND = "#069bff"
ACTIVE_TIMER_BUTTON_BACKGROUND = "#FF6600"
BUTTON_FOREGROUND = "#ffffff"
ACTIVITY_BUTTON_FONT = ("Arial", 12, "bold")
CONTROL_BUTTON_FONT = ("Arial", 10, "bold")
MENU_FONT = ("Arial", 10, "bold")

# Operational algorithm:
#   What this constant group does:
#     Defines fixed Tkinter window sizes for normal, manual-time, and page-count modes.
#   Success:
#     Mode changes resize the app predictably without recalculating geometry at runtime.
#   Error handling:
#     Tkinter reports invalid geometry strings when the window applies them.
NORMAL_GEOMETRY = "450x420"
ADD_TIME_GEOMETRY = "540x420"
PROGRESS_GEOMETRY = "1320x465"
DEFAULT_AUTOSAVE_MINUTES = 5
AUTOSAVE_PROPERTIES_FILE = Path(__file__).resolve().with_name("clock.properties")


def load_autosave_minutes(
    properties_file: Path = AUTOSAVE_PROPERTIES_FILE,
    configuration_logger=None,
) -> int:

    """Return the positive autosave interval configured beside this application."""
    try:
        for raw_line in properties_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("#", ";")) or "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key == "autosave_minutes":
                minutes = int(value)
                if minutes > 0:
                    if configuration_logger is not None:
                        configuration_logger.info(
                            ConfigurationEvents.AUTOSAVE_LOADED,
                            str(properties_file),
                            minutes,
                        )
                    return minutes
                raise ValueError("autosave_minutes must be greater than zero")
    except (OSError, ValueError) as exc:
        if configuration_logger is not None:
            configuration_logger.warning(
                ConfigurationEvents.AUTOSAVE_FALLBACK,
                DEFAULT_AUTOSAVE_MINUTES,
                type(exc).__name__,
                exc_info=(type(exc), exc, exc.__traceback__),
            )
        else:
            print(
                f"LearningClock autosave configuration ignored ({exc}); "
                f"using {DEFAULT_AUTOSAVE_MINUTES} minutes.",
                file=sys.stderr,
            )
        return DEFAULT_AUTOSAVE_MINUTES
    if configuration_logger is not None:
        configuration_logger.info(
            ConfigurationEvents.AUTOSAVE_DEFAULT,
            DEFAULT_AUTOSAVE_MINUTES,
        )
    return DEFAULT_AUTOSAVE_MINUTES


def parse_session_date(value: str) -> date | None:

    """Parse the optional Set Date value entered in the application's MM/DD/YYYY format."""
    normalized = value.strip()
    if not normalized:
        return None
    return datetime.strptime(normalized, "%m/%d/%Y").date()


def build_progress_summary(rows):

    """Aggregate normalized CSV session rows for the in-app progress chart."""
    totals = {activity: 0 for activity in ACTIVITIES}
    total_seconds = 0
    pages_read = 0
    for row in rows:
        for activity, field_name in ACTIVITY_TO_FIELD.items():
            totals[activity] += parse_duration(row.get(field_name, "00:00:00"))
        total_seconds += parse_duration(row.get("total", "00:00:00"))
        try:
            pages_read += int(row.get("pages_read", "0") or 0)
        except ValueError:
            pass
    return {
        "totals": totals,
        "total_seconds": total_seconds,
        "pages_read": pages_read,
        "first_date": rows[0].get("date") if rows else None,
        "last_date": rows[-1].get("date") if rows else None,
    }


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

# Operational algorithm:
#   What this class does:
#     Tracks activity timers in a Tkinter UI and persists one session summary on shutdown.
#   Success:
#     The user can switch timers, add manual time/pages, see live totals, and close to save CSV.
#   Error handling:
#     Save failures are logged and routed through emergency CSV persistence during shutdown.
class LearningClock:


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
        loggers=None,
    ):

        self.root = root                                                            # Tk root window owned by this app.
        self.learning_path_name = learning_path_name or Path.cwd().name             # Default to current folder name.
        self.debug_break_on_click = debug_break_on_click                            # Developer click breakpoint flag.
        self.debug_break_on_close = debug_break_on_close                            # Developer close breakpoint flag.
        self.root.title(self.build_window_title())                                  # Put app/version/path in title.
        self.root.geometry(NORMAL_GEOMETRY)                                         # Start in compact timer layout.
        self.root.resizable(False, False)                                           # Keep fixed geometry predictable.
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)                       # Route window close through save flow.

        self.store = CsvStore(
            log_dir or Path.cwd(),
            self.learning_path_name,
            loggers=loggers,
        )                                                                           # Configure CSV persistence.
        self.loggers = self.store.loggers                                            # Share semantic application loggers.
        self.log_dir = self.store.log_dir                                           # Expose resolved log directory.
        self.log_file = self.store.log_file                                         # Expose resolved CSV file path.
        self.diagnostic_log_file = self.store.diagnostic_log_file                   # Expose diagnostic log path.
        self.autosave_minutes = load_autosave_minutes(
            configuration_logger=self.loggers.configuration,
        )                                                                           # Read deployed app-local setting.

        self.loggers.application.info(
            ApplicationEvents.INITIALIZED,
            self.learning_path_name,
            str(self.log_file),
            str(self.diagnostic_log_file),
            self.autosave_minutes,
        )

        self.session_start = datetime.now()                                         # Timestamp this app session.
        self.session_saved = False                                                  # Save happens only during close.
        self.is_closing = False                                                     # Prevent duplicate close handling.
        self.after_job_id = None                                                    # Tkinter scheduled update handle.
        self.autosave_after_job_id = None                                           # Tkinter scheduled autosave handle.

        self.active_activity = None                                                 # Currently running activity name.
        self.active_start = None                                                    # Start timestamp for active timer.
        self.add_time_mode = False                                                  # Manual-time UI mode flag.
        self.add_page_count_mode = False                                            # Page-count UI mode flag.
        self.set_date_mode = False                                                  # Optional backdated-session date editor flag.
        self.progress_mode = False                                                  # CSV progress-chart UI mode flag.
        self.selected_session_date = None                                           # Date written to CSV when Set Date is used.

        self.totals = {activity: 0 for activity in ACTIVITIES}                      # Accumulated seconds by activity.
        self.persisted_manual_totals = {activity: 0 for activity in ACTIVITIES}     # Manual seconds already written immediately.
        self.manual_totals_by_date = {}                                              # Date -> manual seconds kept in that date's CSV row.
        self.manual_pages_by_date = {}                                               # Date -> manual page count kept in that date's CSV row.
        self.manual_session_starts = {}                                              # Date -> stable CSV session start used to replace that row.
        self.persisted_manual_pages = 0                                              # Manual pages already written immediately.
        self.pages_read = 0                                                         # Accumulated session pages.

        self.labels = {}                                                            # Activity -> visible timer label.
        self.manual_entries = {}                                                    # Activity -> manual-time entry.
        self.page_count_entry = None                                                # Entry widget for pages.
        self.date_frame = None                                                      # Hidden Set Date controls below the timer buttons.
        self.date_entry = None                                                      # Optional MM/DD/YYYY session date entry.
        self.date_picker_field = None                                               # Date field used to anchor the calendar popup.
        self.progress_panel = None                                                  # Right-side CSV chart panel.
        self.progress_canvas = None                                                 # Canvas used to render progress bars.
        self.progress_footer = None                                                 # Obsidian-style progress summary row.
        self.activity_buttons = {}                                                  # Activity buttons keyed for active-timer color updates.

        self.build_menu()                                                           # Create menu commands.
        self.build_main_ui()                                                        # Create timer controls.
        self.update_display()                                                       # Start recurring label updates.
        self.schedule_autosave()                                                    # Start recurring session checkpoints.

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

        menu_bar = tk.Menu(self.root, font=MENU_FONT)                                # Create a more legible bold menu bar.
        menu_bar.add_command(label="About", command=self.show_about)                # Show runtime/path info.
        menu_bar.add_command(label="Add Time", command=self.toggle_add_time_mode)   # Open manual fields or save their entered durations.
        menu_bar.add_command(label="Set Date", command=self.toggle_set_date_mode)  # Show/hide the backdated-session date editor.
        menu_bar.add_command(label="Add Page Count", command=self.toggle_add_page_count_mode)  # Open page field or save its entered count.
        menu_bar.add_command(label="View Progress", command=self.toggle_progress_mode)  # Show/hide CSV dashboard beside timers.
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

        self.main_content = tk.Frame(self.root)                                # Holds the timer controls and optional progress pane.
        self.main_content.pack(fill="both", expand=True, padx=16, pady=0)    # Permit the progress pane to expand right.
        self.timer_panel = tk.Frame(self.main_content)                         # Left-side timer controls.
        self.timer_panel.pack(side="left", fill="y")                         # Keep timer controls at their natural width.
        self.timer_frame = tk.Frame(self.timer_panel)                          # Container for activity rows.
        self.timer_frame.pack(fill="x", pady=0)                               # Keep rows compact.

        for activity in ACTIVITIES:                                           # Create one row per activity.
            row = tk.Frame(self.timer_frame)                                  # Row owns button/label/entries.
            row.pack(fill="x", pady=1)                                        # Stack rows vertically.

            button = tk.Button(
                row,                                                          # Parent row.
                text=activity,                                                # Activity label on button.
                font=ACTIVITY_BUTTON_FONT,                                     # Bold white text stays visible against blue.
                width=30,                                                     # Leaves a narrow trailing gap comparable to the timer-to-chart gap.
                anchor="w",                                                   # Left-align activity text.
                bg=BUTTON_BACKGROUND,                                         # Match the approved blue-button visual.
                fg=BUTTON_FOREGROUND,                                         # Keep blue-button labels readable.
                activebackground=BUTTON_BACKGROUND,                           # Preserve the approved blue while pressed.
                activeforeground=BUTTON_FOREGROUND,                           # Preserve white text while pressed.
                command=lambda a=activity: self.switch_to(a),                 # Capture activity for callback.
            )
            button.pack(side="left")                                          # Button starts each row.
            self.activity_buttons[activity] = button                            # Keep the button available for active-state styling.

            label = tk.Label(row, text="00:00:00", font=("Consolas", 14), width=12)  # Live duration label.
            label.pack(side="left", padx=(10, 0))                              # Place label after button.
            self.labels[activity] = label                                      # Store for update_display.

            entry = tk.Entry(row, font=("Arial", 11), width=11)                # Hidden manual duration entry.
            entry.bind("<Return>", lambda _event: self.add_all_manual_time())  # Enter submits all manual values.
            self.manual_entries[activity] = entry                              # Store for add-time mode.

        self.controls_frame = tk.Frame(self.timer_panel)                       # Container for command buttons.
        self.controls_frame.pack(fill="x", pady=(4, 0), anchor="w")         # Place below timer rows and optional date controls.

        stop_button = tk.Button(
            self.controls_frame,                                               # Parent controls row.
            text="Stop",                                                       # Stop current timer.
            font=CONTROL_BUTTON_FONT,                                          # Bold white text stays visible against blue.
            width=12,                                                          # Fixed width for alignment.
            bg=BUTTON_BACKGROUND,                                              # Match the approved blue-button visual.
            fg=BUTTON_FOREGROUND,                                              # Keep blue-button labels readable.
            activebackground=BUTTON_BACKGROUND,                                # Preserve the approved blue while pressed.
            activeforeground=BUTTON_FOREGROUND,                                # Preserve white text while pressed.
            command=self.stop_running_timer,                                   # Stop without resetting totals.
        )
        stop_button.pack(side="left", padx=(0, 6))                             # First command button.

        reset_button = tk.Button(
            self.controls_frame,                                               # Parent controls row.
            text="Reset Timer",                                                # Reset currently running activity.
            font=CONTROL_BUTTON_FONT,                                          # Bold white text stays visible against blue.
            width=12,                                                          # Fixed width for alignment.
            bg=BUTTON_BACKGROUND,                                              # Match the approved blue-button visual.
            fg=BUTTON_FOREGROUND,                                              # Keep blue-button labels readable.
            activebackground=BUTTON_BACKGROUND,                                # Preserve the approved blue while pressed.
            activeforeground=BUTTON_FOREGROUND,                                # Preserve white text while pressed.
            command=self.reset_running_timer,                                  # Reset active timer only.
        )
        reset_button.pack(side="left", padx=(0, 6))                            # Second command button.

        self.page_count_frame = tk.Frame(self.controls_frame)                  # Hidden page-count control shares the Set Date location.
        self.page_count_entry = tk.Entry(self.page_count_frame, font=("Arial", 11), width=8)
        self.page_count_entry.pack(side="left")
        self.page_count_entry.bind("<Return>", lambda _event: self.add_page_count())

        self.date_frame = tk.Frame(self.controls_frame)                        # Hidden date control shares the Stop/Reset row.
        self.date_picker_field = tk.Frame(self.date_frame, bd=1, relief="sunken")  # Outlook-like date field with embedded picker icon.
        self.date_picker_field.pack(side="left")
        self.date_entry = tk.Entry(self.date_picker_field, font=("Arial", 10), width=12, bd=0)
        self.date_entry.pack(side="left", padx=(3, 0), pady=2)
        self.date_entry.bind("<Return>", lambda _event: self.apply_session_date())
        tk.Button(self.date_picker_field, text="▦", width=2, bd=0, command=self.open_date_picker).pack(side="left", padx=(2, 1), pady=1)


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
            f"The current session autosaves every {self.autosave_minutes} minutes.",  # Save lifecycle note.
            "Emergency CSV files are merged automatically on the next successful save.",  # Recovery note.
        ])
        messagebox.showinfo("About Learning Clock", about_text)                # Display the information.

    def toggle_set_date_mode(self):

        if self.set_date_mode:
            if not self.apply_session_date():
                return
            self.date_frame.pack_forget()
            self.set_date_mode = False
            self.root.geometry(NORMAL_GEOMETRY)
            self.restore_running_status()
            return

        if self.add_page_count_mode:                                           # Both controls use the same aligned location.
            self.exit_add_page_count_mode()
        self.set_date_mode = True
        if self.selected_session_date is not None:
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, self.selected_session_date.strftime("%m/%d/%Y"))
        self.show_control_at_timer_column(self.date_frame)
        self.date_entry.focus_set()

    def show_control_at_timer_column(self, control):

        control.pack(side="left", padx=0)
        self.root.update_idletasks()
        timer_label = self.labels[ACTIVITIES[0]]
        label_font = tkfont.Font(font=timer_label.cget("font"))
        text_inset = max(0, (timer_label.winfo_width() - label_font.measure(timer_label.cget("text"))) // 2)
        timer_value_x = timer_label.winfo_x() + text_inset                    # Align to the visible digits, not the label's outer edge.
        control_offset = max(0, timer_value_x - control.winfo_x())             # Keep Stop/Reset fixed while aligning the control.
        control.pack_configure(padx=(control_offset, 0))

    def apply_session_date(self):

        try:
            self.selected_session_date = parse_session_date(self.date_entry.get())
        except ValueError:
            self.loggers.ui.warning(
                UiEvents.SESSION_DATE_VALIDATION_FAILED,
            )
            messagebox.showerror("Set Date", "Use a valid date in MM/DD/YYYY format.")
            self.date_entry.focus_set()
            return False
        if self.selected_session_date is not None:
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, self.selected_session_date.strftime("%m/%d/%Y"))
            self.status.config(text=f"Session date set to {self.date_entry.get()}")
        self.loggers.ui.info(
            UiEvents.SESSION_DATE_APPLIED,
            self.selected_session_date.isoformat()
            if self.selected_session_date is not None
            else "current session date",
        )
        return True

    def open_date_picker(self):

        try:
            initial_date = parse_session_date(self.date_entry.get()) or self.selected_session_date or date.today()
        except ValueError:
            self.loggers.ui.warning(
                UiEvents.SESSION_DATE_VALIDATION_FAILED,
            )
            initial_date = self.selected_session_date or date.today()

        picker = tk.Toplevel(self.root)
        picker.title("Select Session Date")
        picker.transient(self.root)
        picker.resizable(False, False)
        state = {"year": initial_date.year, "month": initial_date.month}
        header = tk.Frame(picker)
        header.pack(fill="x", padx=8, pady=(8, 4))
        calendar_frame = tk.Frame(picker)
        calendar_frame.pack(padx=8, pady=(0, 8))
        month_label = tk.Label(header, font=("Arial", 11, "bold"))

        def select_day(day):
            selected = date(state["year"], state["month"], day)
            self.selected_session_date = selected
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, selected.strftime("%m/%d/%Y"))
            self.status.config(text=f"Session date set to {self.date_entry.get()}")
            self.loggers.ui.info(
                UiEvents.SESSION_DATE_APPLIED,
                selected.isoformat(),
            )
            picker.destroy()

        def render_calendar():
            for child in calendar_frame.winfo_children():
                child.destroy()
            month_label.config(text=f"{calendar.month_name[state['month']]} {state['year']}")
            for column, weekday in enumerate(("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")):
                tk.Label(calendar_frame, text=weekday, width=4, font=("Arial", 9, "bold")).grid(row=0, column=column)
            for row, week in enumerate(calendar.monthcalendar(state["year"], state["month"]), start=1):
                for column, day_number in enumerate(week):
                    if day_number:
                        tk.Button(calendar_frame, text=str(day_number), width=3, command=lambda day=day_number: select_day(day)).grid(row=row, column=column)
                    else:
                        tk.Label(calendar_frame, text="", width=4).grid(row=row, column=column)

        def change_month(delta):
            state["month"] += delta
            if state["month"] == 0:
                state["year"] -= 1
                state["month"] = 12
            elif state["month"] == 13:
                state["year"] += 1
                state["month"] = 1
            render_calendar()

        tk.Button(header, text="<", width=3, command=lambda: change_month(-1)).pack(side="left")
        month_label.pack(side="left", expand=True)
        tk.Button(header, text=">", width=3, command=lambda: change_month(1)).pack(side="right")
        render_calendar()
        picker.update_idletasks()
        picker.geometry(f"+{self.date_picker_field.winfo_rootx()}+{self.date_picker_field.winfo_rooty() + self.date_picker_field.winfo_height()}")
        picker.grab_set()

    def toggle_add_time_mode(self):

        if self.add_time_mode:
            self.add_all_manual_time()                                         # The second Add Time action submits before hiding the fields.
        else:
            self.enter_add_time_mode()

    def toggle_add_page_count_mode(self):

        if self.add_page_count_mode:
            self.add_page_count()                                             # The second Add Page Count action submits before hiding the field.
        else:
            self.enter_add_page_count_mode()

    # Operational algorithm:
    #   What this method does:
    #     Switches the UI into manual time-entry mode.
    #   Success:
    #     Manual entry fields and Add Time button are visible, and the first field has focus.
    #   Error handling:
    #     Re-entering the same mode is a no-op; page-count mode is closed first.
    def enter_add_time_mode(self):

        if self.progress_mode:                                                  # Keep the progress pane separate from data-entry modes.
            self.exit_progress_mode()
        if self.add_page_count_mode:                                           # Only one temporary input mode at a time.
            self.exit_add_page_count_mode()
        if self.add_time_mode:                                                 # Already in add-time mode.
            return

        self.add_time_mode = True                                              # Mark mode active.
        self.root.geometry(ADD_TIME_GEOMETRY)                                  # Widen window for entries.

        for activity in ACTIVITIES:                                            # Show one manual entry per activity.
            self.manual_entries[activity].pack(side="left", padx=(8, 0))

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

        if self.progress_mode:                                                  # Keep the progress pane separate from data-entry modes.
            self.exit_progress_mode()
        if self.add_time_mode:                                                 # Only one temporary input mode at a time.
            self.exit_add_time_mode()
        if self.set_date_mode:                                                 # Both controls occupy the timer-value column.
            if not self.apply_session_date():
                return
            self.date_frame.pack_forget()
            self.set_date_mode = False
        if self.add_page_count_mode:                                           # Already in page-count mode.
            return

        self.add_page_count_mode = True                                        # Mark mode active.

        if self.page_count_entry is not None:                                  # Page entry is below the timers, aligned with values.
            self.show_control_at_timer_column(self.page_count_frame)
            self.page_count_entry.focus_set()                                  # Put cursor in page entry.

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
            self.page_count_frame.pack_forget()                                # Hide page-count input.

        self.root.geometry(NORMAL_GEOMETRY)                                    # Restore compact layout.
        self.restore_running_status()                                          # Restore status text.

    def enter_progress_mode(self):

        if self.add_time_mode:                                                 # Progress uses the same expanded workspace as entry modes.
            self.exit_add_time_mode()
        if self.add_page_count_mode:
            self.exit_add_page_count_mode()
        if not self.persist_session_for_progress():                             # The chart must always read the latest persisted state.
            return
        if self.progress_mode:                                                 # Re-open acts as a refresh for the saved CSV data.
            self.refresh_progress_chart()
            return

        self.progress_mode = True
        self.root.geometry(PROGRESS_GEOMETRY)                                  # Expand horizontally for the dashboard pane.
        self.build_progress_panel()
        self.progress_panel.pack(side="right", fill="both", expand=True, padx=(20, 0))
        self.refresh_progress_chart()
        self.status.config(text="Viewing CSV progress")

    def toggle_progress_mode(self):

        if self.progress_mode:
            self.exit_progress_mode()
        else:
            self.enter_progress_mode()

    def exit_progress_mode(self):

        if not self.progress_mode:
            return
        self.progress_mode = False
        if self.progress_panel is not None:
            self.progress_panel.pack_forget()
        self.root.geometry(NORMAL_GEOMETRY)
        self.restore_running_status()

    def build_progress_panel(self):

        if self.progress_panel is not None:
            return
        progress_background = "#f4f8fc"
        self.progress_panel = tk.Frame(
            self.main_content,
            bg=progress_background,
            highlightbackground="#c5d8ec",
            highlightthickness=1,
            width=730,
        )
        header = tk.Frame(self.progress_panel, bg=progress_background)
        header.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(header, text="Progress", font=("Arial", 14, "bold"), bg=progress_background).pack(side="left")
        tk.Button(header, text="Refresh", command=self.refresh_progress_from_session).pack(side="right")
        self.progress_canvas = tk.Canvas(self.progress_panel, width=710, height=300, bg=progress_background, highlightthickness=0)
        self.progress_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 2))
        self.progress_footer = tk.Frame(self.progress_panel, bg=progress_background)
        self.progress_footer.pack(fill="x", padx=10, pady=(8, 14))

    @staticmethod
    def progress_label_lines(activity):

        explicit_lines = {
            "AI-Assisted Architecture & Design": ("AI-Assisted", "Architecture", "& Design"),
            "AI-Assisted Engineering": ("AI-Assisted", "Engineering"),
            "Classical Software Engineering": ("Classical", "Software", "Engineering"),
            "Promote Stable Concept": ("Promote", "Stable Concept"),
            "Update Diavgeia": ("Update", "Diavgeia"),
            "Active Recall": ("Active", "Recall"),
        }
        return explicit_lines.get(activity, (activity,))

    def refresh_progress_chart(self):

        if self.progress_canvas is None or self.progress_footer is None:
            return
        try:
            summary = build_progress_summary(self.store.read_existing_session_rows())
        except Exception:
            self.loggers.ui.exception(
                UiEvents.PROGRESS_READ_FAILED,
            )
            self.progress_canvas.delete("all")
            self.progress_canvas.create_text(355, 150, text="Unable to read the progress CSV.", font=("Arial", 12))
            self.render_progress_footer(message="Unable to read the progress CSV.")
            return

        canvas = self.progress_canvas
        canvas.delete("all")
        canvas.update_idletasks()
        width = max(canvas.winfo_width(), 710)
        baseline, top, left, right, gap = 210, 28, 12, 12, 9
        bar_width = (width - left - right - gap * (len(ACTIVITIES) - 1)) / len(ACTIVITIES)
        max_seconds = max(summary["totals"].values(), default=0) or 1
        canvas.create_line(left, baseline, width - right, baseline, fill="#a9c5df", width=2)

        for index, activity in enumerate(ACTIVITIES):
            seconds = summary["totals"][activity]
            x1 = left + index * (bar_width + gap)
            x2 = x1 + bar_width
            height = 18 if seconds == 0 else max(18, round((seconds / max_seconds) * (baseline - top)))
            y1 = baseline - height
            canvas.create_rectangle(x1, y1, x2, baseline, fill="#007ACC", outline="")
            value_y = y1 + 5                                                   # Keep each bold value five pixels below the bar's top edge.
            canvas.create_text((x1 + x2) / 2, value_y, text=format_seconds(seconds), fill="#FFFFFF", font=("Segoe UI", 10, "bold"), anchor="n")
            canvas.create_text((x1 + x2) / 2, baseline + 8, text="\n".join(self.progress_label_lines(activity)), font=("Arial", 8), anchor="n", width=bar_width + 4)

        self.render_progress_footer(summary=summary)

    def refresh_progress_from_session(self):

        """Save the latest session state before refreshing the CSV-backed chart."""
        if self.persist_session_for_progress():
            self.refresh_progress_chart()

    def persist_session_for_progress(self):

        """Checkpoint all tracked session time before rendering CSV-backed progress."""
        session_end = datetime.now()
        try:
            saved = self.save_session_summary(session_end, replace_session=True)
            self.loggers.ui.info(
                UiEvents.PROGRESS_CHECKPOINT_COMPLETED,
                saved,
                f"{session_end:%Y-%m-%d %H:%M:%S}",
            )
            return True
        except Exception:
            self.loggers.ui.exception(
                UiEvents.PROGRESS_CHECKPOINT_FAILED,
            )
            messagebox.showerror("View Progress", "Unable to save the current session before showing progress.")
            return False

    def render_progress_footer(self, summary=None, message=None):

        for child in self.progress_footer.winfo_children():
            child.destroy()
        if message is not None:
            tk.Label(self.progress_footer, text=message, bg="#f4f8fc", anchor="w").pack(fill="x")
            return
        if summary["first_date"] is None:
            tk.Label(
                self.progress_footer,
                text="No saved sessions yet. Start a timer and wait for autosave, or close the app to save a session.",
                bg="#f4f8fc",
                anchor="w",
            ).pack(fill="x")
            return

        stats = [
            ("Total time: ", format_seconds(summary["total_seconds"])),
            ("Total pages read: ", str(summary["pages_read"])),
            ("Start Date: ", self.format_progress_date(summary["first_date"])),
            ("Last Update: ", self.format_progress_date(summary["last_date"])),
        ]
        for column, (label, value) in enumerate(stats):
            stat = tk.Frame(self.progress_footer, bg="#f4f8fc")
            stat.grid(row=0, column=column, padx=(0, 24 if column < len(stats) - 1 else 0), sticky="w")
            tk.Label(stat, text=label, bg="#f4f8fc", font=("Arial", 10)).pack(side="left")
            tk.Label(stat, text=value, bg="#f4f8fc", fg="#164f86", font=("Arial", 10, "bold")).pack(side="left")

    @staticmethod
    def format_progress_date(value):

        parts = (value or "").split("-")
        if len(parts) == 3:
            return f"{parts[1]}-{parts[2]}-{parts[0][-2:]}"
        return value or "N/A"

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
    #     Colors only the running activity button orange and restores all other activity buttons to blue.
    #   Success:
    #     The active timer has a clear visual state while inactive timer controls retain the standard color.
    #   Error handling:
    #     Tkinter reports invalid widget configuration if a button is unavailable.
    def refresh_activity_button_colors(self):

        for activity, button in self.activity_buttons.items():                  # Keep every activity button synchronized with timer state.
            background = (
                ACTIVE_TIMER_BUTTON_BACKGROUND
                if activity == self.active_activity
                else BUTTON_BACKGROUND
            )
            button.config(bg=background, activebackground=background)           # Match resting and pressed colors for the state.

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

        self.loggers.timer.info(
            TimerEvents.SWITCH_REQUESTED,
            activity,
        )
        self.close_active_timer(datetime.now())                                # Credit previous active timer.
        self.active_activity = activity                                        # Store new active activity.
        self.active_start = datetime.now()                                     # Start new timer now.
        self.refresh_activity_button_colors()                                  # Highlight the new running timer orange.
        self.session_saved = False                                             # Session changed since last save.
        self.status.config(text=f"Running: {activity}")                        # Show running activity.
        self.loggers.timer.info(
            TimerEvents.STARTED,
            activity,
            f"{self.active_start:%H:%M:%S}",
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
        self.loggers.timer.info(
            TimerEvents.CLOSED,
            self.active_activity,
            format_seconds(round(elapsed_seconds)),
            format_seconds(round(self.totals[self.active_activity])),
        )
        self.active_activity = None                                            # Clear active activity.
        self.active_start = None                                               # Clear active start time.
        self.refresh_activity_button_colors()                                  # Restore the stopped activity button to blue.

    # Operational algorithm:
    #   What this method does:
    #     Stops the active timer without resetting accumulated session totals.
    #   Success:
    #     Active elapsed time is credited and the status shows which activity stopped.
    #   Error handling:
    #     If no timer is running, the status stays idle and no totals change.
    def stop_running_timer(self):

        if self.active_activity is None:                                       # Nothing to stop.
            self.loggers.timer.info(TimerEvents.STOP_REJECTED)
            self.status.config(text="No timer running")                        # Keep idle status visible.
            return
        stopped_activity = self.active_activity                                # Remember label before clearing state.
        self.close_active_timer(datetime.now())                                # Credit elapsed time and clear active state.
        self.status.config(text=f"Stopped: {stopped_activity}")                # Tell user what stopped.
        self.loggers.timer.info(TimerEvents.STOPPED)

    # Operational algorithm:
    #   What this method does:
    #     Resets only the currently running activity total and continues timing it from now.
    #   Success:
    #     The active activity total becomes zero and the active start timestamp resets.
    #   Error handling:
    #     If no timer is running, a warning is shown and no totals change.
    def reset_running_timer(self):

        if self.active_activity is None:                                       # Reset requires an active timer.
            self.loggers.timer.warning(TimerEvents.RESET_REJECTED)
            messagebox.showwarning("Reset Timer", "No timer is currently running.")  # Explain no-op to user.
            return
        activity = self.active_activity                                        # Capture active activity name.
        self.totals[activity] = 0                                              # Drop accumulated time for that activity.
        self.active_start = datetime.now()                                     # Restart timing from now.
        self.session_saved = False                                             # Session changed since last save.
        self.status.config(text=f"Reset running timer: {activity}")            # Show reset result.
        self.loggers.timer.info(TimerEvents.RESET, activity)
        self.update_display()                                                  # Refresh labels immediately.

    # Operational algorithm:
    #   What this method does:
    #     Validates every manual time entry, writes it immediately to the selected date, and updates the visible totals.
    #   Success:
    #     All valid entries are written together, fields are cleared, and add-time mode exits.
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
            if seconds == 0:                                                   # Zero is an accepted no-op entry.
                continue
            additions.append((activity, seconds))                              # Keep valid addition for batch apply.

        if errors:                                                             # Do not partially apply invalid form.
            self.loggers.ui.warning(
                UiEvents.MANUAL_TIME_VALIDATION_FAILED,
                len(errors),
            )
            messagebox.showerror("Invalid Manual Time", "\n".join(errors))     # Show all errors at once.
            return
        if not additions:                                                      # Blank/zero-only submission is an accepted no-op.
            for entry in self.manual_entries.values():                         # Clear any submitted zero values.
                entry.delete(0, tk.END)
            self.exit_add_time_mode()                                          # Return to timer view without an error.
            return

        saved_at = datetime.now()
        session_date = self.current_session_date() or saved_at.date()
        manual_seconds = dict(self.manual_totals_by_date.get(session_date, {}))
        if not manual_seconds:
            manual_seconds = {activity: 0 for activity in ACTIVITIES}
        for activity, seconds in additions:
            manual_seconds[activity] += seconds

        manual_session_start = self.manual_session_starts.get(session_date, saved_at)
        try:
            manual_row = self.store.create_session_row(
                manual_session_start,
                saved_at,
                manual_seconds,
                self.manual_pages_by_date.get(session_date, 0),
                session_date=session_date,
            )
            self.store.save_session_summary(manual_row, replace_session=True)
        except Exception:
            self.loggers.ui.exception(
                UiEvents.MANUAL_TIME_SAVE_FAILED,
            )
            messagebox.showerror("Add Time", "Unable to save the manual time. No time was added.")
            return

        self.manual_totals_by_date[session_date] = manual_seconds              # Retain this date's aggregate for the next Add Time submission.
        self.manual_session_starts[session_date] = manual_session_start        # Reuse the same row identity when updating it.
        for activity, seconds in additions:                                    # Reflect successfully persisted additions in the UI.
            self.totals[activity] += seconds
            self.persisted_manual_totals[activity] += seconds                  # Keep later checkpoints from duplicating this row.
            self.loggers.ui.info(
                UiEvents.MANUAL_TIME_SAVED,
                activity,
                manual_row["date"],
                format_seconds(seconds),
                format_seconds(round(self.totals[activity])),
            )

        for entry in self.manual_entries.values():                             # Clear all manual fields after success.
            entry.delete(0, tk.END)

        self.session_saved = True                                              # The submitted manual time is already persisted.
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

        if not raw_value:                                                      # Blank submission is an accepted no-op.
            self.exit_add_page_count_mode()                                    # Return to timer view without an error.
            self.status.config(text="No pages added")                          # Confirm the harmless no-op.
            return
        if not raw_value.isdigit():                                            # Only whole-number pages are supported.
            self.loggers.ui.warning(
                UiEvents.PAGE_COUNT_VALIDATION_FAILED,
            )
            messagebox.showerror("Add Page Count", "Page count must be a whole number.")  # Explain invalid value.
            return

        pages = int(raw_value)                                                 # Convert validated text to int.
        if pages == 0:                                                         # Zero submission is an accepted no-op.
            self.page_count_entry.delete(0, tk.END)                            # Clear the accepted zero.
            self.exit_add_page_count_mode()                                    # Return to timer view without an error.
            self.status.config(text="No pages added")                          # Confirm the harmless no-op.
            return

        saved_at = datetime.now()
        session_date = self.current_session_date() or saved_at.date()
        manual_seconds = self.manual_totals_by_date.get(
            session_date,
            {activity: 0 for activity in ACTIVITIES},
        )
        manual_pages = self.manual_pages_by_date.get(session_date, 0) + pages
        manual_session_start = self.manual_session_starts.get(session_date, saved_at)
        try:
            page_row = self.store.create_session_row(
                manual_session_start,
                saved_at,
                manual_seconds,
                manual_pages,
                session_date=session_date,
            )
            self.store.save_session_summary(page_row, replace_session=True)
        except Exception:
            self.loggers.ui.exception(
                UiEvents.PAGE_COUNT_SAVE_FAILED,
            )
            messagebox.showerror("Add Page Count", "Unable to save the page count. No pages were added.")
            return

        self.manual_pages_by_date[session_date] = manual_pages                # Retain this date's page total for the next manual update.
        self.manual_session_starts[session_date] = manual_session_start       # Reuse the same dated row identity.
        self.pages_read += pages                                               # Reflect the saved pages in the session counter.
        self.persisted_manual_pages += pages                                   # Keep later checkpoints from duplicating these pages.
        self.loggers.ui.info(
            UiEvents.PAGE_COUNT_SAVED,
            pages,
            page_row["date"],
            self.pages_read,
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
            activity: max(0, self.current_total(activity) - self.persisted_manual_totals[activity])  # Exclude manual time already written immediately.
            for activity in ACTIVITIES                                         # Preserve configured activity order.
        }
        return self.store.create_session_row(
            self.session_start,                                                # Session start timestamp.
            session_end,                                                       # Session end timestamp.
            activity_seconds,                                                  # Activity seconds dictionary.
            max(0, self.pages_read - self.persisted_manual_pages),             # Exclude pages already written immediately.
            session_date=self.current_session_date(),                          # Optional user-selected date for backdated sessions.
        )

    def current_session_date(self):

        """Return the selected CSV date, including a typed but not yet hidden Set Date value."""
        if self.date_entry is not None and self.date_entry.get().strip():
            return parse_session_date(self.date_entry.get())
        return self.selected_session_date

    # Operational algorithm:
    #   What this method does:
    #     Saves the current session through CsvStore and records whether the save wrote rows.
    #   Success:
    #     session_saved mirrors CsvStore.save_session_summary's boolean result.
    #   Error handling:
    #     Exceptions propagate to on_close, which can create an emergency file.
    def save_session_summary(self, session_end, replace_session=False):

        saved = self.store.save_session_summary(                                  # Persist current session.
            self.create_session_row(session_end),
            replace_session=replace_session,
        )
        self.session_saved = saved                                             # Remember save result.
        return saved                                                           # Return result to caller.

    def schedule_autosave(self):

        if not self.is_closing:
            self.autosave_after_job_id = self.root.after(
                self.autosave_minutes * 60_000,
                self.autosave_session,
            )

    def autosave_session(self):

        if self.is_closing:
            return
        session_end = datetime.now()
        try:
            saved = self.save_session_summary(session_end, replace_session=True)
            self.loggers.ui.info(
                UiEvents.AUTOSAVE_COMPLETED,
                self.autosave_minutes,
                saved,
                f"{session_end:%Y-%m-%d %H:%M:%S}",
            )
        except Exception as exc:
            self.loggers.ui.exception(
                UiEvents.AUTOSAVE_FAILED,
            )
            try:
                emergency_file = self.save_emergency_session_file(session_end, exc)
                self.loggers.ui.warning(
                    UiEvents.AUTOSAVE_EMERGENCY_CREATED,
                    str(emergency_file),
                )
            except Exception:
                self.loggers.ui.exception(
                    UiEvents.AUTOSAVE_EMERGENCY_FAILED,
                )
        finally:
            self.schedule_autosave()

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
        self.loggers.application.info(
            ApplicationEvents.CLOSE_REQUESTED,
            f"{self.session_start:%Y-%m-%d %H:%M:%S}",
            f"{session_end:%Y-%m-%d %H:%M:%S}",
            self.session_saved,
        )

        try:
            if self.after_job_id is not None:                                  # Cancel scheduled label refresh.
                try:
                    self.root.after_cancel(self.after_job_id)                  # Stop future update_display call.
                except tk.TclError:
                    pass                                                       # Window may already be tearing down.

            if self.autosave_after_job_id is not None:
                try:
                    self.root.after_cancel(self.autosave_after_job_id)
                except tk.TclError:
                    pass

            self.close_active_timer(session_end)                               # Credit running timer before saving.

            try:
                self.save_session_summary(session_end, replace_session=True)   # Replace latest autosave with final totals.
            except Exception as exc:
                self.loggers.ui.exception(
                    UiEvents.SHUTDOWN_SAVE_FAILED,
                )
                emergency_file = None                                      # Track fallback result.
                try:
                    emergency_file = self.save_emergency_session_file(session_end, exc)  # Fallback persistence.
                except Exception:
                    self.loggers.ui.exception(
                        UiEvents.SHUTDOWN_EMERGENCY_FAILED,
                    )
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
            self.loggers.application.info(
                ApplicationEvents.SHUTDOWN_FINALIZING,
            )
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
    resolved_log_dir = Path(args.log_dir or Path.cwd())                         # Resolve the app persistence boundary.
    loggers = configure_observability(
        resolved_log_dir / DIAGNOSTIC_LOG_FILE_NAME,
    )                                                                           # Configure file/optional Seq sinks.
    try:
        with correlation_context():                                             # Correlate one desktop application session.
            loggers.application.info(
                ApplicationEvents.STARTING,
                args.learning_path or Path.cwd().name,
                str(resolved_log_dir),
            )
            root = tk.Tk()                                                      # Create root Tk window.
            LearningClock(
                root,                                                           # Window root.
                learning_path_name=args.learning_path,                          # Optional configured path name.
                log_dir=resolved_log_dir,                                       # Resolved CSV/log output directory.
                debug_break_on_click=args.debug_break_on_click,                 # Developer click breakpoint.
                debug_break_on_close=args.debug_break_on_close,                 # Developer close breakpoint.
                loggers=loggers,                                                # Shared semantic logging composition.
            )
            root.mainloop()                                                     # Run UI event loop.
            loggers.application.info(ApplicationEvents.STOPPED)
        return 0                                                                # Successful process exit code.
    except Exception:
        loggers.application.exception(
            ApplicationEvents.STARTUP_FAILED,
        )
        raise
    finally:
        shutdown_observability()                                                # Flush/close framework-owned sinks.


if __name__ == "__main__":
    raise SystemExit(main())
