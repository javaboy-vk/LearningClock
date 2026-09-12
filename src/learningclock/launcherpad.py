# =============================================================================
# File Name : launcherpad.py
# Artifact  : LearningClock - LauncherPad GUI
# Author    : javaboy-vk
# Date      : 2026-09-11
# Version   : v2.4.0
# Purpose:
#   Discovers, provisions, launches, and reports across independently configured
#   LearningClock instances, including linked file/row diagnostics.
# =============================================================================

from __future__ import annotations

import os
import sys
import tkinter as tk
import webbrowser
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any
from uuid import uuid4

from learningclock.configuration import (
    DEFAULT_CENTRAL_CONFIGURATION,
    DEFAULT_CONFIGURATION_DIR,
    CentralConfiguration,
    ConfigurationError,
    ConfiguredClock,
    central_configuration_path,
    discover_clock_configurations,
    load_central_configuration,
    logs_directory,
)
from learningclock.date_picker import show_date_picker
from learningclock.observability import (
    configure_observability,
    correlation_context,
    shutdown_observability,
)
from learningclock.process_launcher import launch_clock
from learningclock.provisioning import provision_clock
from learningclock.reporting import (
    PERIOD_OPTIONS,
    ReportIssue,
    ReportResult,
    aggregate_clock_time,
    format_report_duration,
    resolve_date_range,
)
from learningclock.singleton import is_clock_running
from learningclock.telemetry import (
    CONFIG_MALFORMED,
    EXTERNAL_INSTANCE_DETECTED,
    LAUNCH_REQUESTED,
    LAUNCHERPAD_CLOSED,
    LAUNCHERPAD_CLOSING,
    LAUNCHERPAD_INITIALIZED,
    LAUNCHERPAD_STARTING,
    PROCESS_LAUNCH_FAILED,
    RUNNING_STATE_CHANGED,
)
from learningclock.window_icon import apply_window_icon

LAUNCHERPAD_TITLE = "LearningClock LauncherPad 2.0"
AVAILABLE_BACKGROUND = "#069bff"
RUNNING_BACKGROUND = "#FF6600"
BUTTON_FOREGROUND = "#ffffff"
STATE_REFRESH_MS = 1500
GRID_COLUMNS = 3


@dataclass(frozen=True, slots=True)
class ClockControlState:
    text: str
    widget_state: str
    background: str


def clock_control_state(clock: ConfiguredClock, running: bool) -> ClockControlState:
    if running:
        return ClockControlState(
            text=f"{clock.display_name} — Running",
            widget_state=tk.DISABLED,
            background=RUNNING_BACKGROUND,
        )
    return ClockControlState(clock.display_name, tk.NORMAL, AVAILABLE_BACKGROUND)


class LauncherPad:
    """Tkinter coordination surface; business rules remain in dedicated services."""

    def __init__(
        self,
        root: tk.Tk,
        configuration_dir: Path,
        *,
        loggers: Any,
        central_config_path: Path | None = None,
        running_observer: Callable[..., bool] = is_clock_running,
        process_launcher: Callable[..., int] = launch_clock,
        report_executor: ThreadPoolExecutor | None = None,
    ) -> None:
        self.root = root
        self.configuration_dir = configuration_dir.resolve()
        self.central_config_path = central_configuration_path(central_config_path)
        self.loggers = loggers
        self.running_observer = running_observer
        self.process_launcher = process_launcher
        self.buttons: dict[str, tk.Button] = {}
        self.running_states: dict[str, bool] = {}
        self.refresh_job: str | None = None
        self.report_job: str | None = None
        self.report_request_id = 0
        self.report_executor = report_executor or ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="learningclock-report"
        )
        self.closed = False
        self.clocks: tuple[ConfiguredClock, ...] = ()
        self.discovery_issue_count = 0
        self.custom_start: date | None = None
        self.custom_end: date | None = None
        self.report_issues: tuple[ReportIssue, ...] = ()
        self.report_issue_dialog: tk.Toplevel | None = None

        apply_window_icon(self.root)
        self.root.title(LAUNCHERPAD_TITLE)
        self.root.minsize(1080, 680)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        header = tk.Frame(root)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header.columnconfigure(0, weight=1)
        tk.Label(header, text=LAUNCHERPAD_TITLE, font=("Arial", 16, "bold"), anchor="w").grid(
            row=0, column=0, sticky="ew"
        )
        self.create_button = tk.Button(
            header,
            text="Create New Clock",
            font=("Arial", 10, "bold"),
            bg=AVAILABLE_BACKGROUND,
            fg=BUTTON_FOREGROUND,
            activebackground=AVAILABLE_BACKGROUND,
            activeforeground=BUTTON_FOREGROUND,
            command=self.open_create_dialog,
            padx=12,
            pady=6,
        )
        self.create_button.grid(row=0, column=1, padx=(12, 0))

        self.clock_controls = tk.LabelFrame(root, text="Configured clocks", padx=8, pady=8)
        self.clock_controls.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        for column in range(GRID_COLUMNS):
            self.clock_controls.columnconfigure(column, weight=1, uniform="clock")

        self.build_report_ui()
        self.status = tk.Label(root, text="", anchor="w")
        self.status.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 12))

        self.central_configuration: CentralConfiguration | None = None
        self.central_error: str | None = None
        self.reload_central_configuration()
        self.refresh_discovery(initial=True)
        self.refresh_report()
        self.loggers.launcherpad.event(
            LAUNCHERPAD_INITIALIZED,
            configuration_dir=self.configuration_dir,
            clock_count=len(self.clocks),
            error_count=self.discovery_issue_count + (1 if self.central_error else 0),
            process_id=os.getpid(),
            runtime_mode="packaged" if getattr(sys, "frozen", False) else "source",
            launch_mode="launcherpad",
            application_version="6.0",
        )

    def reload_central_configuration(self) -> None:
        try:
            self.central_configuration = load_central_configuration(self.central_config_path)
            self.central_error = None
        except (ConfigurationError, OSError) as exc:
            self.central_configuration = None
            self.central_error = (
                f"Central configuration is unavailable: {exc}. Configure pythonExe and "
                f"pyScriptPath in {self.central_config_path}."
            )
            self.loggers.configuration_v2.event(
                CONFIG_MALFORMED,
                configuration_path=self.central_config_path,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

    def refresh_discovery(self, *, initial: bool = False) -> None:
        for button in self.buttons.values():
            button.destroy()
        self.buttons.clear()
        self.running_states.clear()
        for child in self.clock_controls.grid_slaves():
            child.destroy()
        result = discover_clock_configurations(
            self.configuration_dir,
            logger=self.loggers.configuration_v2,
            excluded_paths=(self.central_config_path,),
        )
        self.clocks = result.clocks
        self.discovery_issue_count = len(result.issues)
        for index, clock in enumerate(self.clocks):
            button = tk.Button(
                self.clock_controls,
                text=clock.display_name,
                font=("Arial", 11, "bold"),
                bg=AVAILABLE_BACKGROUND,
                fg=BUTTON_FOREGROUND,
                activebackground=AVAILABLE_BACKGROUND,
                activeforeground=BUTTON_FOREGROUND,
                disabledforeground=BUTTON_FOREGROUND,
                command=lambda selected=clock: self.launch(selected),
                padx=8,
                pady=10,
            )
            button.grid(
                row=index // GRID_COLUMNS,
                column=index % GRID_COLUMNS,
                sticky="ew",
                padx=4,
                pady=4,
            )
            self.buttons[clock.clock_id] = button
        if not self.clocks:
            tk.Label(
                self.clock_controls,
                text=f"No valid clock configurations were found in\n{self.configuration_dir}",
                justify="center",
            ).grid(row=0, column=0, columnspan=GRID_COLUMNS, pady=20)
        self.update_status()
        self.refresh_running_states(initial=initial)

    def update_status(self, message: str | None = None) -> None:
        if message is None:
            message = f"{len(self.clocks)} configured clocks"
            if self.discovery_issue_count:
                message += f"; {self.discovery_issue_count} configuration warnings"
            if self.central_error:
                message += f". {self.central_error}"
        self.status.config(text=message)

    def launch(self, clock: ConfiguredClock) -> None:
        correlation_id = str(uuid4())
        with correlation_context(correlation_id):
            try:
                central = load_central_configuration(self.central_config_path, validate_paths=True)
                self.central_configuration = central
                self.central_error = None
                self.loggers.process_launcher.event(
                    LAUNCH_REQUESTED,
                    clock_id=clock.clock_id,
                    clock_name=clock.display_name,
                    configuration_path=clock.configuration_path,
                    parent_process_id=os.getpid(),
                    runtime_mode="launcherpad",
                    launch_mode="launcherpad",
                    application_version="6.0",
                )
                child_process_id = self.process_launcher(
                    clock,
                    central,
                    correlation_id,
                    logger=self.loggers.process_launcher,
                )
            except Exception as exc:
                if not isinstance(exc, OSError):
                    self.loggers.process_launcher.event(
                        PROCESS_LAUNCH_FAILED,
                        exc_info=exc,
                        clock_id=clock.clock_id,
                        clock_name=clock.display_name,
                        configuration_path=clock.configuration_path,
                        runtime_mode="launcherpad",
                        launch_mode="launcherpad",
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                messagebox.showerror(
                    "LearningClock Launch Failed",
                    f"Unable to start {clock.display_name}.\n\n{exc}\n\n"
                    f"Check {self.central_config_path}.",
                    parent=self.root,
                )
                self.update_status(f"Launch failed for {clock.display_name}")
                return
            self.update_status(f"Started {clock.display_name} as process {child_process_id}")
        self.root.after(250, self.refresh_running_states)

    def open_create_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Clock")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        apply_window_icon(dialog)
        body = tk.Frame(dialog, padx=16, pady=16)
        body.grid(sticky="nsew")
        body.columnconfigure(1, weight=1)
        name_value = tk.StringVar()
        log_dir_value = tk.StringVar()
        tk.Label(body, text="Learning path name", anchor="w").grid(
            row=0, column=0, sticky="w", pady=5
        )
        name_entry = tk.Entry(body, textvariable=name_value, width=44)
        name_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        tk.Label(body, text="Diavgeia clock directory", anchor="w").grid(
            row=1, column=0, sticky="w", pady=5
        )
        tk.Entry(body, textvariable=log_dir_value, width=44).grid(
            row=1, column=1, sticky="ew", pady=5
        )

        def browse() -> None:
            selected = filedialog.askdirectory(parent=dialog, mustexist=False)
            if selected:
                log_dir_value.set(selected)

        tk.Button(body, text="Browse…", command=browse).grid(row=1, column=2, padx=(8, 0))
        error_label = tk.Label(body, text="", fg="#b00020", anchor="w", justify="left")
        error_label.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))

        def submit() -> None:
            try:
                result = provision_clock(
                    self.configuration_dir,
                    name_value.get(),
                    log_dir_value.get(),
                    logger=self.loggers.launcherpad,
                )
            except Exception as exc:
                error_label.config(text=str(exc))
                messagebox.showerror("Create New Clock", str(exc), parent=dialog)
                return
            dialog.destroy()
            self.refresh_discovery()
            self.refresh_report()
            messagebox.showinfo(
                "Clock Created",
                f"Created {result.plan.learning_path_name}.\n\n"
                f"Diavgeia data location: {result.plan.learning_path_dir}",
                parent=self.root,
            )

        actions = tk.Frame(body)
        actions.grid(row=3, column=0, columnspan=3, sticky="e", pady=(14, 0))
        tk.Button(actions, text="Cancel", command=dialog.destroy).pack(side="left", padx=4)
        tk.Button(actions, text="Create", command=submit, default=tk.ACTIVE).pack(
            side="left", padx=4
        )
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.bind("<Return>", lambda _event: submit())
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.wait_visibility()
        dialog.grab_set()
        name_entry.focus_set()

    def build_report_ui(self) -> None:
        report = tk.LabelFrame(self.root, text="Time by category across all clocks", padx=10, pady=10)
        report.grid(row=2, column=0, sticky="nsew", padx=12, pady=8)
        report.columnconfigure(0, weight=1)
        report.rowconfigure(2, weight=1)
        selectors = tk.Frame(report)
        selectors.grid(row=0, column=0, sticky="ew")
        tk.Label(selectors, text="Period:").pack(side="left")
        self.period_value = tk.StringVar(value="This week")
        self.period_dropdown = ttk.Combobox(
            selectors,
            textvariable=self.period_value,
            values=PERIOD_OPTIONS,
            state="readonly",
            width=16,
        )
        self.period_dropdown.pack(side="left", padx=(6, 12))
        self.period_dropdown.bind("<<ComboboxSelected>>", self.on_period_changed)
        self.custom_range_frame = tk.Frame(selectors)
        self.start_value = tk.StringVar()
        self.end_value = tk.StringVar()
        tk.Label(self.custom_range_frame, text="Start:").pack(side="left")
        self.start_entry = tk.Entry(
            self.custom_range_frame, textvariable=self.start_value, state="readonly", width=12
        )
        self.start_entry.pack(side="left", padx=(4, 10))
        tk.Label(self.custom_range_frame, text="End:").pack(side="left")
        self.end_entry = tk.Entry(
            self.custom_range_frame, textvariable=self.end_value, state="readonly", width=12
        )
        self.end_entry.pack(side="left", padx=(4, 10))
        self.start_entry.bind("<Button-1>", lambda _event: self.open_custom_date_picker("start"))
        self.end_entry.bind("<Button-1>", lambda _event: self.open_custom_date_picker("end"))
        tk.Button(self.custom_range_frame, text="Apply", command=self.refresh_report).pack(side="left")
        self.range_label = tk.Label(report, text="", anchor="w")
        self.range_label.grid(row=1, column=0, sticky="ew", pady=(8, 2))
        self.chart = tk.Canvas(report, height=315, background="#f8fbff", highlightthickness=1)
        self.chart.grid(row=2, column=0, sticky="nsew")
        report_footer = tk.Frame(report)
        report_footer.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        self.report_summary = tk.Label(report_footer, text="", anchor="w")
        self.report_summary.pack(side="left")
        self.report_issue_link = tk.Label(
            report_footer,
            text="",
            anchor="w",
            foreground="#0067c0",
            activeforeground="#004578",
            cursor="hand2",
            font=("Arial", 9, "underline"),
        )
        self.report_issue_link.pack(side="left")
        self.report_issue_link.bind("<Button-1>", self.show_report_issues)

    def on_period_changed(self, _event: Any = None) -> None:
        if self.period_value.get() == "Define range":
            self.custom_range_frame.pack(side="left")
            if self.custom_start is None:
                self.custom_start = date.today()
                self.start_value.set(self.custom_start.isoformat())
            if self.custom_end is None:
                self.custom_end = date.today()
                self.end_value.set(self.custom_end.isoformat())
            return
        self.custom_range_frame.pack_forget()
        self.refresh_report()

    def open_custom_date_picker(self, which: str) -> None:
        initial = self.custom_start if which == "start" else self.custom_end

        def selected(value: date) -> None:
            if which == "start":
                self.custom_start = value
                self.start_value.set(value.isoformat())
            else:
                self.custom_end = value
                self.end_value.set(value.isoformat())

        show_date_picker(self.root, initial or date.today(), selected)

    def refresh_report(self) -> None:
        try:
            selected_range = resolve_date_range(
                self.period_value.get(),
                custom_start=self.custom_start,
                custom_end=self.custom_end,
            )
        except ValueError as exc:
            messagebox.showerror("LearningClock Report", str(exc), parent=self.root)
            return
        self.range_label.config(
            text=f"Inclusive range: {selected_range.start.isoformat()} through {selected_range.end.isoformat()}"
        )
        self.report_request_id += 1
        request_id = self.report_request_id
        self.report_issues = ()
        self.report_summary.config(text="Calculating…")
        self.report_issue_link.config(text="")
        future = self.report_executor.submit(
            aggregate_clock_time,
            tuple(self.clocks),
            selected_range,
            logger=self.loggers.launcherpad,
        )
        self.poll_report_future(request_id, future)

    def poll_report_future(self, request_id: int, future: Future[ReportResult]) -> None:
        if self.closed:
            return
        if not future.done():
            self.report_job = self.root.after(
                50, lambda: self.poll_report_future(request_id, future)
            )
            return
        try:
            result = future.result()
        except Exception as exc:
            if request_id == self.report_request_id:
                self.report_summary.config(text=f"Report could not be calculated: {exc}")
                self.report_issue_link.config(text="")
            return
        self.apply_report_result(request_id, result)

    def apply_report_result(self, request_id: int, result: ReportResult) -> None:
        if request_id != self.report_request_id or self.closed:
            return
        self.render_histogram(result)
        summary = (
            f"Total: {format_report_duration(result.total_seconds)} "
            f"({result.total_seconds / 3600:.2f} hours) · "
            f"{result.clock_count} clocks · {result.row_count} session rows"
        )
        self.report_summary.config(text=summary)
        self.report_issues = result.issues
        if result.warning_count:
            self.report_issue_link.config(
                text=f" · {result.warning_count} skipped/invalid inputs"
            )
        else:
            self.report_issue_link.config(text="")

    def show_report_issues(self, _event: Any = None) -> None:
        if not self.report_issues:
            return
        if self.report_issue_dialog is not None and self.report_issue_dialog.winfo_exists():
            self.report_issue_dialog.deiconify()
            self.report_issue_dialog.lift()
            self.report_issue_dialog.focus_force()
            return

        dialog = tk.Toplevel(self.root)
        self.report_issue_dialog = dialog
        dialog.title("Skipped and Invalid Report Inputs")
        dialog.geometry("920x520")
        dialog.minsize(720, 360)
        dialog.transient(self.root)
        apply_window_icon(dialog)

        header = tk.Frame(dialog, padx=14, pady=12)
        header.pack(fill="x")
        tk.Label(
            header,
            text=f"{len(self.report_issues)} skipped or invalid inputs",
            font=("Arial", 12, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            header,
            text=(
                "This report scan is read-only and does not rewrite CSV data. "
                "Each link identifies the source file and CSV row used by the scan."
            ),
            anchor="w",
            justify="left",
            wraplength=870,
        ).pack(fill="x", pady=(4, 0))

        body = tk.Frame(dialog, padx=14)
        body.pack(fill="both", expand=True)
        canvas = tk.Canvas(body, highlightthickness=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        issue_list = tk.Frame(canvas)
        issue_window = canvas.create_window((0, 0), window=issue_list, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        issue_list.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(issue_window, width=event.width),
        )

        for index, issue in enumerate(self.report_issues, start=1):
            item = tk.Frame(issue_list, relief="groove", borderwidth=1, padx=10, pady=8)
            item.pack(fill="x", pady=(0, 7))
            tk.Label(
                item,
                text=f"{index}. {issue.clock_name}: {issue.message}",
                font=("Arial", 9, "bold"),
                anchor="w",
                justify="left",
                wraplength=840,
            ).pack(fill="x")
            location = str(issue.source_path)
            if issue.row_number is not None:
                location += f" — row {issue.row_number}"
            link = tk.Label(
                item,
                text=location,
                anchor="w",
                justify="left",
                foreground="#0067c0",
                activeforeground="#004578",
                cursor="hand2",
                font=("Arial", 9, "underline"),
                wraplength=840,
            )
            link.pack(fill="x", pady=(3, 0))
            link.bind(
                "<Button-1>",
                lambda _click, selected=issue: self.open_report_issue_source(selected),
            )
            details: list[str] = [f"Type: {issue.input_kind}", f"Reason: {issue.reason}"]
            if issue.column:
                details.append(f"Column: {issue.column}")
            if issue.value is not None:
                visible_value = issue.value if len(issue.value) <= 240 else issue.value[:237] + "..."
                details.append(f"Value: {visible_value!r}")
            tk.Label(
                item,
                text=" · ".join(details),
                anchor="w",
                justify="left",
                foreground="#4f5f6f",
                wraplength=840,
            ).pack(fill="x", pady=(3, 0))

        footer = tk.Frame(dialog, padx=14, pady=10)
        footer.pack(fill="x")

        def close_dialog() -> None:
            dialog.destroy()
            self.report_issue_dialog = None

        tk.Button(footer, text="Close", command=close_dialog).pack(side="right")
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)

    def open_report_issue_source(self, issue: ReportIssue) -> None:
        target = issue.source_path
        while not target.exists() and target.parent != target:
            target = target.parent
        if not target.exists():
            messagebox.showerror(
                "Open Report Input",
                f"No existing location could be found for:\n{issue.source_path}",
                parent=self.report_issue_dialog or self.root,
            )
            return
        try:
            if os.name == "nt":
                os.startfile(str(target))
            else:
                webbrowser.open(target.resolve().as_uri())
        except OSError as exc:
            messagebox.showerror(
                "Open Report Input",
                f"Could not open {target}:\n{exc}",
                parent=self.report_issue_dialog or self.root,
            )

    def render_histogram(self, result: ReportResult) -> None:
        self.chart.delete("all")
        self.chart.update_idletasks()
        width = max(self.chart.winfo_width(), 1000)
        height = max(self.chart.winfo_height(), 315)
        left, right, top, bottom = 28, 18, 28, 76
        plot_height = height - top - bottom
        self.chart.create_line(left, top + plot_height, width - right, top + plot_height, fill="#8aa9c4")
        count = max(len(result.totals), 1)
        slot = (width - left - right) / count
        bar_width = max(12, slot * 0.62)
        maximum = max((seconds for _, seconds in result.totals), default=0)
        for index, (activity, seconds) in enumerate(result.totals):
            center = left + slot * (index + 0.5)
            bar_height = 0 if maximum == 0 else max(2, plot_height * seconds / maximum)
            x1, x2 = center - bar_width / 2, center + bar_width / 2
            y1, y2 = top + plot_height - bar_height, top + plot_height
            self.chart.create_rectangle(x1, y1, x2, y2, fill="#007ACC", outline="")
            self.chart.create_text(
                center,
                max(10, y1 - 10),
                text=format_report_duration(seconds),
                font=("Arial", 8, "bold"),
            )
            self.chart.create_text(
                center,
                top + plot_height + 8,
                text=activity,
                width=max(55, slot - 4),
                anchor="n",
                font=("Arial", 8),
            )
        if result.total_seconds == 0:
            self.chart.create_text(
                width / 2,
                top + plot_height / 2,
                text="No recorded time in this period",
                fill="#4f5f6f",
                font=("Arial", 12, "bold"),
            )

    def refresh_running_states(self, *, initial: bool = False) -> None:
        if self.closed:
            return
        if self.refresh_job is not None:
            try:
                self.root.after_cancel(self.refresh_job)
            except tk.TclError:
                pass
            self.refresh_job = None
        for clock in self.clocks:
            try:
                running = self.running_observer(clock.clock_id, logger=self.loggers.instance_guard)
            except OSError:
                running = True
            previous = self.running_states.get(clock.clock_id)
            state = clock_control_state(clock, running)
            button = self.buttons.get(clock.clock_id)
            if button is not None:
                button.config(
                    text=state.text,
                    state=state.widget_state,
                    bg=state.background,
                    activebackground=state.background,
                )
            self.running_states[clock.clock_id] = running
            if previous is None:
                if initial and running:
                    self.loggers.launcherpad.event(
                        EXTERNAL_INSTANCE_DETECTED,
                        clock_id=clock.clock_id,
                        clock_name=clock.display_name,
                        configuration_path=clock.configuration_path,
                        process_id=os.getpid(),
                    )
            elif previous != running:
                self.loggers.launcherpad.event(
                    RUNNING_STATE_CHANGED,
                    clock_id=clock.clock_id,
                    clock_name=clock.display_name,
                    configuration_path=clock.configuration_path,
                    previous_state="running" if previous else "available",
                    current_state="running" if running else "available",
                    process_id=os.getpid(),
                )
        self.refresh_job = self.root.after(STATE_REFRESH_MS, self.refresh_running_states)

    def on_close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.loggers.launcherpad.event(
            LAUNCHERPAD_CLOSING,
            configuration_dir=self.configuration_dir,
            process_id=os.getpid(),
        )
        for job in (self.refresh_job, self.report_job):
            if job is not None:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
        self.report_executor.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()
        self.loggers.launcherpad.event(
            LAUNCHERPAD_CLOSED,
            configuration_dir=self.configuration_dir,
            process_id=os.getpid(),
        )


def main(
    configuration_dir: Path = DEFAULT_CONFIGURATION_DIR,
    correlation_id: str | None = None,
    central_config_path: Path | None = DEFAULT_CENTRAL_CONFIGURATION,
) -> int:
    diagnostic_dir = logs_directory(configuration_dir)
    loggers = configure_observability(
        diagnostic_dir / "launcherpad_debug.log",
        seq_spool_path=diagnostic_dir / "launcherpad_seq_offline.clef",
    )
    try:
        with correlation_context(correlation_id):
            loggers.launcherpad.event(
                LAUNCHERPAD_STARTING,
                configuration_dir=configuration_dir,
                process_id=os.getpid(),
                parent_process_id=os.getppid(),
                runtime_mode="launcherpad",
                launch_mode="desktop",
                application_version="6.0",
            )
            root = tk.Tk()
            LauncherPad(
                root,
                configuration_dir,
                loggers=loggers,
                central_config_path=central_config_path,
            )
            root.mainloop()
        return 0
    finally:
        shutdown_observability()


if __name__ == "__main__":
    raise SystemExit(main())
