# =============================================================================
# File Name : desktop.py
# Artifact  : LearningClock - Primary Windows GUI Entry Point
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.0
# Purpose:
#   Opens LauncherPad by default and dispatches the internal --clock mode used
#   for independent configured LearningClock GUI processes.
# =============================================================================

from __future__ import annotations

import argparse
import os
from pathlib import Path

from learningclock.configuration import DEFAULT_CONFIGURATION_DIR


def parse_args(argv: list[str] | None = None):
    """Parse GUI entry mode without importing either Tkinter application prematurely."""

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


def main(argv: list[str] | None = None) -> int:
    """Dispatch the one-icon GUI to LauncherPad or one selected clock process."""

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

