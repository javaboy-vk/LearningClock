# =============================================================================
# File Name : desktop.py
# Artifact  : LearningClock - Primary Windows GUI Entry Point
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.1
# Purpose:
#   Opens LauncherPad by default and dispatches the internal --clock mode used
#   for independent configured LearningClock GUI processes.
#
# Dispatch flow:
#   main(argv)
#   |-- parse_args(argv) without importing a Tkinter application module
#   |-- no --clock: import and run launcherpad.main(config_dir, correlation_id)
#   `-- --clock PATH: translate shared desktop flags and run app.main(arguments)
#
# Boundary contract:
#   This is the only packaged GUI entry point. Delayed imports keep LauncherPad
#   startup independent from the timer UI and ensure each selected clock is
#   initialized only inside its own process.
# =============================================================================

from __future__ import annotations

import argparse
import os
from pathlib import Path

from learningclock.configuration import DEFAULT_CONFIGURATION_DIR


# Source documentation:
#   What it does: Parses the shared GUI entry mode before importing a Tkinter application.
#   Why it exists: One packaged executable serves LauncherPad and child-clock modes, and delayed
#     imports prevent both Tkinter applications from initializing in the same process.
#   Designed use: main passes its arguments here; --clock selects child mode, --config-dir
#     controls discovery, and debug/correlation flags are forwarded to that child.
def parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="LearningClock desktop GUI")
    parser.add_argument("--clock", type=Path, default=None)
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path(os.getenv("LEARNINGCLOCK_CONFIG_DIR", str(DEFAULT_CONFIGURATION_DIR))),
    )
    parser.add_argument("--correlation-id", default=None)
    parser.add_argument("--debug-break-on-click", action="store_true")
    parser.add_argument("--debug-break-on-close", action="store_true")
    return parser.parse_args(argv)


# Source documentation:
#   What it does: Dispatches the one-icon GUI to LauncherPad or one selected clock process.
#   Why it exists: A single no-console entry point avoids per-clock shortcuts and provides one
#     stable installed command for both parent and detached child processes.
#   Designed use: Invoke without --clock for LauncherPad; ProcessLauncher reinvokes it with
#     --clock PATH and this function translates shared flags for app.main.
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.clock is None:
        from learningclock.launcherpad import main as launcherpad_main

        return launcherpad_main(args.config_dir, args.correlation_id)

    from learningclock.app import main as clock_main

    clock_arguments = ["--config", str(args.clock)]
    if args.correlation_id:
        clock_arguments.extend(["--correlation-id", args.correlation_id])
    if args.debug_break_on_click:
        clock_arguments.append("--debug-break-on-click")
    if args.debug_break_on_close:
        clock_arguments.append("--debug-break-on-close")
    return clock_main(clock_arguments)


if __name__ == "__main__":
    raise SystemExit(main())
