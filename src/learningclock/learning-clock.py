#!/usr/bin/env python3
# =============================================================================
# File Name : learning-clock.py
# Artifact  : LearningClock - Compatibility Launcher
# Author    : javaboy-vk
# Date      : 2026-06-06
# Version   : v0.1.0
# Purpose:
#   Preserves existing launcher/debug paths while the implementation lives in
#   learningclock.app and learningclock.csv_store.
#
# Why this file exists:
#   Older scripts, debug launchers, and user habits may still point at the historical
#   learning-clock.py filename. Keeping this thin wrapper avoids breaking those entry paths while
#   the real application code stays in importable package modules.
#
# Value added:
#   1. Compatibility: existing commands can keep calling this file.
#   2. Separation: the wrapper does not duplicate application logic from app.py.
#   3. Testability: the real main function remains importable from learningclock.app.
#
# Launcher call tree:
#   learning-clock.py
#   |-- import learningclock.app.main
#   `-- when executed directly:
#       `-- raise SystemExit(main())
# =============================================================================

# Operational algorithm:
#   What this import does:
#     Loads the Tkinter application entry function from the package implementation.
#   Success:
#     The compatibility launcher delegates startup to learningclock.app.main.
#   Error handling:
#     Import errors surface immediately because the wrapper cannot run without the app entry point.
from learningclock.app import main  # Import real desktop app entry point.

# Operational algorithm:
#   What this block does:
#     Runs the app only when the compatibility file is executed directly.
#   Success:
#     main() returns an exit status and SystemExit passes it to the invoking process.
#   Error handling:
#     Startup exceptions propagate so broken launcher/app wiring remains visible.
if __name__ == "__main__":
    raise SystemExit(main())                                                 # Run app and exit with its status code.
