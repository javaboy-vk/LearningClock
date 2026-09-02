# =============================================================================
# File Name : launcherpad.py
# Artifact  : LearningClock - LauncherPad GUI
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.1
# Purpose:
#   Discovers configured clocks, observes their named mutexes, and launches
#   independent LearningClock GUI processes from one compact Tkinter window.
#
# LauncherPad flow:
#   main(configuration_dir, correlation_id)
#   |-- configure LauncherPad file, console, and optional Seq observability
#   |-- create Tk root and LauncherPad
#   |   |-- discover valid clock configurations
#   |   |-- create one launch control per valid clock
#   |   `-- refresh_running_states() every STATE_REFRESH_MS
#   |       |-- observe Local\Protepo.LearningClock.<clock-id>
#   |       `-- emit telemetry only when the running state changes
#   |-- launch(clock) creates a correlation ID and a detached child process
#   `-- on_close() cancels polling and closes only LauncherPad
#
# Ownership contract:
#   LauncherPad observes mutex existence but never owns a selected clock's
#   singleton guard, CSV state, or child-process lifetime. Closing LauncherPad
#   cannot terminate an independently running LearningClock process.
# =============================================================================

from __future__ import annotations

import os
import sys
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox
from typing import Any
from uuid import uuid4

from learningclock.configuration import (
    DEFAULT_CONFIGURATION_DIR,
    ConfiguredClock,
    discover_clock_configurations,
)
from learningclock.observability import (
    configure_observability,
    correlation_context,
    shutdown_observability,
)
from learningclock.process_launcher import launch_clock
from learningclock.singleton import is_clock_running
from learningclock.telemetry import (
    EXTERNAL_INSTANCE_DETECTED,
    LAUNCH_REQUESTED,
    LAUNCHERPAD_CLOSED,
    LAUNCHERPAD_CLOSING,
    LAUNCHERPAD_INITIALIZED,
    LAUNCHERPAD_STARTING,
    PROCESS_LAUNCH_FAILED,
    RUNNING_STATE_CHANGED,
)

LAUNCHERPAD_TITLE = "LearningClock LauncherPad 1.0"
AVAILABLE_BACKGROUND = "#069bff"
RUNNING_BACKGROUND = "#FF6600"
BUTTON_FOREGROUND = "#ffffff"
STATE_REFRESH_MS = 1500
GRID_COLUMNS = 3


@dataclass(frozen=True, slots=True)
class ClockControlState:
    """Presentation state for one configured clock launch control."""

    text: str
    widget_state: str
    background: str


# Source documentation: Maps authoritative mutex state to a clear LauncherPad button state.
def clock_control_state(clock: ConfiguredClock, running: bool) -> ClockControlState:
    if running:
        return ClockControlState(
            text=f"{clock.display_name} — Running",
            widget_state=tk.DISABLED,
            background=RUNNING_BACKGROUND,
        )
    return ClockControlState(
        text=clock.display_name,
        widget_state=tk.NORMAL,
        background=AVAILABLE_BACKGROUND,
    )


class LauncherPad:
    """Focused discover-display-observe-launch Tkinter application."""

    # Source documentation:
    #   What it does: Builds the discover-display-observe LauncherPad application.
    #   Why it exists: Initialization creates one valid-clock snapshot and schedules mutex
    #     observation without taking ownership of any clock.
    #   Designed use: main supplies Tk, configuration, and loggers; tests may inject observers and
    #     launchers. Construction schedules polling and emits the initialized event.
    def __init__(
        self,
        root: tk.Tk,
        configuration_dir: Path,
        *,
        loggers: Any,
        running_observer: Callable[..., bool] = is_clock_running,
        process_launcher: Callable[..., int] = launch_clock,
    ) -> None:
        self.root = root
        self.configuration_dir = configuration_dir.resolve()
        self.loggers = loggers
        self.running_observer = running_observer
        self.process_launcher = process_launcher
        self.buttons: dict[str, tk.Button] = {}
        self.running_states: dict[str, bool] = {}
        self.refresh_job: str | None = None
        self.closed = False

        self.root.title(LAUNCHERPAD_TITLE)
        self.root.minsize(700, 260)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        tk.Label(
            root,
            text=LAUNCHERPAD_TITLE,
            font=("Arial", 16, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        controls = tk.Frame(root)
        controls.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        for column in range(GRID_COLUMNS):
            controls.columnconfigure(column, weight=1, uniform="clock")

        result = discover_clock_configurations(
            self.configuration_dir, logger=self.loggers.configuration_v2
        )
        self.clocks = result.clocks
        for index, clock in enumerate(self.clocks):
            button = tk.Button(
                controls,
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
                controls,
                text=f"No valid .properties configurations were found in\n{self.configuration_dir}",
                justify="center",
            ).grid(row=0, column=0, columnspan=GRID_COLUMNS, pady=30)

        status = f"{len(self.clocks)} configured clocks"
        if result.issues:
            status += f"; {len(result.issues)} malformed or duplicate configurations skipped"
        self.status = tk.Label(root, text=status, anchor="w")
        self.status.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 12))

        self.refresh_running_states(initial=True)
        self.loggers.launcherpad.event(
            LAUNCHERPAD_INITIALIZED,
            configuration_dir=self.configuration_dir,
            clock_count=len(self.clocks),
            error_count=len(result.issues),
            process_id=os.getpid(),
            runtime_mode="packaged" if getattr(sys, "frozen", False) else "source",
            launch_mode="launcherpad",
            application_version="6.0",
        )

    # Source documentation:
    #   What it does: Launches one clock under a new correlation scope.
    #   Why it exists: Parent request and child startup must be traceable without making
    #     LauncherPad the owner or supervisor of the child.
    #   Designed use: Clock buttons pass a discovered configuration; failures appear in the parent
    #     UI and an early mutex refresh follows, while the child decides singleton ownership.
    def launch(self, clock: ConfiguredClock) -> None:
        correlation_id = str(uuid4())
        with correlation_context(correlation_id):
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
            try:
                child_process_id = self.process_launcher(
                    clock,
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
                    f"Unable to start {clock.display_name}.\n\n{exc}",
                    parent=self.root,
                )
                self.status.config(text=f"Launch failed for {clock.display_name}")
                return
            self.status.config(text=f"Started {clock.display_name} as process {child_process_id}")
        self.root.after(250, self.refresh_running_states)

    # Source documentation:
    #   What it does: Refreshes controls from authoritative mutex observations.
    #   Why it exists: Independent children can survive LauncherPad or start externally, so an
    #     in-memory process list is insufficient.
    #   Designed use: The Tk timer invokes it every STATE_REFRESH_MS; it cancels duplicate jobs,
    #     fails closed, updates controls, and emits only initial detections or real transitions.
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
                running = self.running_observer(
                    clock.clock_id,
                    logger=self.loggers.instance_guard,
                )
            except OSError:
                running = True  # Fail closed: the process guard remains authoritative.
            previous = self.running_states.get(clock.clock_id)
            state = clock_control_state(clock, running)
            self.buttons[clock.clock_id].config(
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
                continue
            if previous != running:
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

    # Source documentation:
    #   What it does: Closes only LauncherPad and its scheduled observation work.
    #   Why it exists: Running clocks must survive parent closure and own their persistence and
    #     singleton lifecycle independently.
    #   Designed use: Registered as WM_DELETE_WINDOW; repeat calls are safe, polling is canceled,
    #     and no clock process is signaled.
    def on_close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.loggers.launcherpad.event(
            LAUNCHERPAD_CLOSING,
            configuration_dir=self.configuration_dir,
            process_id=os.getpid(),
        )
        if self.refresh_job is not None:
            try:
                self.root.after_cancel(self.refresh_job)
            except tk.TclError:
                pass
        self.root.destroy()
        self.loggers.launcherpad.event(
            LAUNCHERPAD_CLOSED,
            configuration_dir=self.configuration_dir,
            process_id=os.getpid(),
        )


# Source documentation:
#   What it does: Starts the primary LearningClock LauncherPad GUI.
#   Why it exists: This boundary owns LauncherPad diagnostics and guarantees logging shutdown
#     around the Tk event loop.
#   Designed use: desktop.main calls it in normal GUI mode; tests/development may override the
#     configuration directory or correlation ID, and the return is a process exit status.
def main(
    configuration_dir: Path = DEFAULT_CONFIGURATION_DIR,
    correlation_id: str | None = None,
) -> int:
    diagnostic_dir = configuration_dir / "Tools" / "LearningClock"
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
            LauncherPad(root, configuration_dir, loggers=loggers)
            root.mainloop()
        return 0
    finally:
        shutdown_observability()


if __name__ == "__main__":
    raise SystemExit(main())
