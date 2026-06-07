# =============================================================================
# File Name : __main__.py
# Artifact  : LearningClock - Module Runner
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Runs the LearningClock CLI when invoked with python -m learningclock.
# =============================================================================

# Operational algorithm:
#   What this import does:
#     Loads the package CLI entry function used by python -m learningclock.
#   Success:
#     The module runner delegates all command handling to learningclock.cli.main.
#   Error handling:
#     Import errors surface immediately because the package cannot run without the CLI entry point.
from learningclock.cli import main

# Operational algorithm:
#   What this block does:
#     Starts the CLI only when this file is executed as the package module runner.
#   Success:
#     main() returns a process status code and SystemExit passes that code to Python.
#   Error handling:
#     CLI exceptions propagate through SystemExit/main so failures remain visible to the caller.
if __name__ == "__main__":
    raise SystemExit(main())
