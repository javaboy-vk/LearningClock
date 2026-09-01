# =============================================================================
# File Name : process_launcher.py
# Artifact  : LearningClock - Independent Windows GUI Process Launcher
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.1
# Purpose:
#   Constructs and starts source or packaged LearningClock GUI commands without
#   VBS, shells, console windows, pipes, or LauncherPad-owned process lifetime.
# =============================================================================

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from learningclock.configuration import ConfiguredClock
from learningclock.telemetry import (
    LAUNCH_COMMAND_CONSTRUCTED,
    PROCESS_CREATED,
    PROCESS_LAUNCH_FAILED,
)

CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008
CREATE_BREAKAWAY_FROM_JOB = 0x01000000
PACKAGED_EXECUTABLE_NAMES = {"learningclock.exe", "learningclock-gui.exe"}


def select_gui_python(python_executable: Path | str | None = None) -> Path:
    """Select pythonw.exe beside the active interpreter without hard-coded installations."""

    executable = Path(python_executable or sys.executable).resolve()
    if os.name == "nt":
        candidate = executable.with_name("pythonw.exe")
        if candidate.is_file():
            return candidate
    return executable


def detect_packaged_executable(argv0: str | None = None) -> Path | None:
    """Detect a frozen or installed GUI entry executable suitable for self-relaunch."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    candidate = Path(argv0 or sys.argv[0])
    if candidate.name.casefold() in PACKAGED_EXECUTABLE_NAMES and candidate.is_file():
        return candidate.resolve()
    return None


def build_clock_command(
    clock: ConfiguredClock,
    correlation_id: str,
    *,
    packaged_executable: Path | None = None,
    python_executable: Path | str | None = None,
) -> tuple[list[str], str]:
    """Build a quoted-argument-safe command for packaged or source execution."""

    packaged = packaged_executable or detect_packaged_executable()
    common = [
        "--clock",
        str(clock.configuration_path),
        "--correlation-id",
        correlation_id,
    ]
    if packaged is not None:
        return [str(packaged), *common], "packaged"
    pythonw = select_gui_python(python_executable)
    return [str(pythonw), "-m", "learningclock.desktop", *common], "source"


def launch_clock(
    clock: ConfiguredClock,
    correlation_id: str,
    *,
    logger: Any,
    packaged_executable: Path | None = None,
    python_executable: Path | str | None = None,
) -> int:
    """Start one detached GUI process and return its process ID without retaining ownership."""

    command, runtime_mode = build_clock_command(
        clock,
        correlation_id,
        packaged_executable=packaged_executable,
        python_executable=python_executable,
    )
    logger.event(
        LAUNCH_COMMAND_CONSTRUCTED,
        clock_id=clock.clock_id,
        clock_name=clock.display_name,
        configuration_path=clock.configuration_path,
        runtime_mode=runtime_mode,
        launch_mode="launcherpad",
        executable=command[0],
    )
    environment = os.environ.copy()
    source_root = str(Path(__file__).resolve().parents[1])
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_root + os.pathsep + existing_pythonpath if existing_pythonpath else source_root
    )
    creation_flags = (
        CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS | CREATE_BREAKAWAY_FROM_JOB
        if os.name == "nt"
        else 0
    )
    try:
        process = subprocess.Popen(
            command,
            cwd=clock.configuration_path.parent,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creation_flags,
        )
    except OSError as exc:
        logger.event(
            PROCESS_LAUNCH_FAILED,
            exc_info=exc,
            clock_id=clock.clock_id,
            clock_name=clock.display_name,
            configuration_path=clock.configuration_path,
            runtime_mode=runtime_mode,
            launch_mode="launcherpad",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise
    logger.event(
        PROCESS_CREATED,
        clock_id=clock.clock_id,
        clock_name=clock.display_name,
        configuration_path=clock.configuration_path,
        runtime_mode=runtime_mode,
        launch_mode="launcherpad",
        child_process_id=process.pid,
        parent_process_id=os.getpid(),
    )
    return process.pid
