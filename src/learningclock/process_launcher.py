# =============================================================================
# File Name : process_launcher.py
# Artifact  : LearningClock - Independent Windows GUI Process Launcher
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.2
# Purpose:
#   Constructs and starts source or packaged LearningClock GUI commands without
#   VBS, shells, console windows, pipes, or LauncherPad-owned process lifetime.
#
# Launch flow:
#   launch_clock(clock, correlation_id)
#   |-- build_clock_command(...)
#   |   |-- packaged: relaunch the GUI executable with --clock
#   |   `-- source: select adjacent pythonw.exe and run learningclock.desktop
#   |-- propagate the source root through PYTHONPATH when required
#   |-- start a detached process with standard streams connected to DEVNULL
#   `-- emit PROCESS_CREATED or PROCESS_LAUNCH_FAILED with structured context
#
# Safety contract:
#   Commands are argument lists, never shell strings. No pipe is retained, and
#   the returned process ID is diagnostic information rather than ownership.
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


# Source documentation:
#   What it does: Selects the GUI interpreter beside the active Python executable.
#   Why it exists: Source launches must avoid a console while honoring the active environment.
#   Designed use: Source-mode command construction calls it; Windows prefers a sibling
#     pythonw.exe and other environments fall back to the supplied/current interpreter.
def select_gui_python(python_executable: Path | str | None = None) -> Path:
    executable = Path(python_executable or sys.executable).resolve()
    if os.name == "nt":
        candidate = executable.with_name("pythonw.exe")
        if candidate.is_file():
            return candidate
    return executable


# Source documentation:
#   What it does: Detects a GUI executable that can safely relaunch itself.
#   Why it exists: Packaged deployments should not assume a source checkout or Python exists.
#   Designed use: build_clock_command calls it when no executable is injected; it accepts only
#     frozen runtimes or known installed GUI names and otherwise enables source mode.
def detect_packaged_executable(argv0: str | None = None) -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    candidate = Path(argv0 or sys.argv[0])
    if candidate.name.casefold() in PACKAGED_EXECUTABLE_NAMES and candidate.is_file():
        return candidate.resolve()
    return None


# Source documentation:
#   What it does: Builds the packaged or source command for one configured clock.
#   Why it exists: Central list-based construction keeps paths safe and gives telemetry a stable
#     packaged/source runtime classification.
#   Designed use: launch_clock supplies a validated clock and correlation ID; tests can inject
#     executables, and the returned list goes directly to subprocess.Popen without a shell.
def build_clock_command(
    clock: ConfiguredClock,
    correlation_id: str,
    *,
    packaged_executable: Path | None = None,
    python_executable: Path | str | None = None,
) -> tuple[list[str], str]:
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


# Source documentation:
#   What it does: Starts one independent GUI clock and returns its process ID.
#   Why it exists: Clocks must survive LauncherPad or IDE shutdown without inherited pipes or
#     parent job-object lifetime.
#   Designed use: LauncherPad passes a discovered clock, correlation ID, and logger; the function
#     detaches streams/lifetime, emits telemetry, and returns only the PID rather than ownership.
def launch_clock(
    clock: ConfiguredClock,
    correlation_id: str,
    *,
    logger: Any,
    packaged_executable: Path | None = None,
    python_executable: Path | str | None = None,
) -> int:
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
