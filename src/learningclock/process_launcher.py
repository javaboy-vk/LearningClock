# =============================================================================
# File Name : process_launcher.py
# Artifact  : LearningClock - Independent Windows GUI Process Launcher
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v2.1.0
# Purpose:
#   Combines central and per-clock configuration and starts the configured
#   LearningClock script without shells, console windows, pipes, or ownership.
#
# Launch flow:
#   launch_clock(clock, central, correlation_id)
#   |-- build_clock_command(...)
#   |   `-- pythonExe pyScriptPath --learning-path NAME --log-dir PATH
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
from pathlib import Path
from typing import Any

from learningclock.configuration import (
    LEARNING_PATH_DIRECTORY_NAME,
    CentralConfiguration,
    ConfiguredClock,
)
from learningclock.telemetry import (
    LAUNCH_COMMAND_CONSTRUCTED,
    PROCESS_CREATED,
    PROCESS_LAUNCH_FAILED,
)

CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008
CREATE_BREAKAWAY_FROM_JOB = 0x01000000
# Source documentation:
#   What it does: Builds the centrally configured runtime command for one clock.
#   Why it exists: Central list-based construction keeps paths safe and gives telemetry a stable
#     packaged/source runtime classification.
#   Designed use: launch_clock supplies validated central/per-clock models and a correlation ID;
#     the returned list goes directly to subprocess.Popen without a shell.
def build_clock_command(
    clock: ConfiguredClock,
    central: CentralConfiguration,
    correlation_id: str,
) -> tuple[list[str], str]:
    command = [
        str(central.python_executable),
        str(central.script_path),
        "--learning-path",
        clock.learning_path_name,
        "--log-dir",
        str(clock.log_dir / LEARNING_PATH_DIRECTORY_NAME),
        "--clock-id",
        clock.clock_id,
        "--correlation-id",
        correlation_id,
    ]
    return command, "configured-python"


# Source documentation:
#   What it does: Starts one independent GUI clock and returns its process ID.
#   Why it exists: Clocks must survive LauncherPad or IDE shutdown without inherited pipes or
#     parent job-object lifetime.
#   Designed use: LauncherPad passes a discovered clock, correlation ID, and logger; the function
#     detaches streams/lifetime, emits telemetry, and returns only the PID rather than ownership.
def launch_clock(
    clock: ConfiguredClock,
    central: CentralConfiguration,
    correlation_id: str,
    *,
    logger: Any,
) -> int:
    command, runtime_mode = build_clock_command(
        clock,
        central,
        correlation_id,
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
            cwd=central.script_path.parent,
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
