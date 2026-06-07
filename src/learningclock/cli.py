# =============================================================================
# File Name : cli.py
# Artifact  : LearningClock - CLI Entrypoint
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Provides the command-line entrypoint for the LearningClock package.
#
# Why this file exists:
#   The LearningClock project has more than one way to start or inspect the package. The Tkinter
#   application in app.py owns the desktop timer experience, while this file owns the lightweight
#   command-line surface. Keeping the CLI in its own module gives packaging tools, tests, scripts,
#   and python -m learningclock one small stable target that can run without importing Tkinter.
#
# Value added:
#   1. It provides a fast health check: running the CLI with no arguments proves the package can be
#      imported and the command entrypoint is wired correctly.
#   2. It exposes version information without starting the GUI, which is useful for release checks,
#      automation, and support diagnostics.
#   3. It centralizes command-line parsing in one place, so future CLI commands can be added without
#      mixing package metadata, module-runner behavior, and desktop UI startup code.
#   4. It is easy to test because main(argv) accepts an explicit argument list and returns an exit
#      status instead of reading sys.argv or exiting the process directly.
#
# How to use it:
#   python -m learningclock
#     Prints "LearningClock is ready." and returns exit code 0.
#   python -m learningclock --version
#     Prints the package version from learningclock.__version__ and returns exit code 0.
#   from learningclock.cli import main
#     Allows tests or automation to call main([]) or main(["--version"]) without spawning a process.
#
# CLI call tree:
#   python -m learningclock
#   `-- __main__.py
#       `-- main(argv)
#           |-- build_parser()
#           |   |-- argparse.ArgumentParser(prog="learningclock")
#           |   `-- --version
#           |-- parser.parse_args(argv)
#           |-- when --version: print(__version__)
#           `-- otherwise: print readiness message
# =============================================================================

from __future__ import annotations

import argparse

from learningclock import __version__


# Operational algorithm:
#   What this function does:
#     Builds the argparse parser for the lightweight LearningClock command-line interface.
#   Success:
#     The parser knows the command name and supports --version for non-GUI version checks.
#   Error handling:
#     argparse owns invalid-option reporting when parse_args is called by main.
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="learningclock")                    # Create parser with stable command name.
    parser.add_argument(
        "--version",                                                          # Optional metadata command.
        action="store_true",                                                  # Store True when the flag is present.
        help="Print the application version.",                                # Help text shown by argparse.
    )
    return parser                                                             # Return parser for main/tests.


# Operational algorithm:
#   What this function does:
#     Runs the CLI command using explicit arguments supplied by tests, scripts, or __main__.py.
#   Success:
#     --version prints package metadata; no arguments print a readiness message; both return zero.
#   Error handling:
#     argparse raises SystemExit for malformed arguments, preserving standard command-line behavior.
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)                                    # Parse supplied args or sys.argv via argparse.
    if args.version:                                                          # Version-only command path.
        print(__version__)                                                    # Emit package version for scripts/users.
        return 0                                                              # Successful version command.

    print("LearningClock is ready.")                                          # Default health-check/readiness message.
    return 0                                                                  # Successful default command.
