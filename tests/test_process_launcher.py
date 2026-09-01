# =============================================================================
# File Name : test_process_launcher.py
# Artifact  : LearningClock - GUI Process Launcher Tests
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.1
# Purpose:
#   Verifies source and packaged commands, interpreter selection, and the
#   shell/VBS-free independent process contract.
# =============================================================================

from pathlib import Path

import pytest

from learningclock.configuration import ConfiguredClock
from learningclock.process_launcher import (
    CREATE_BREAKAWAY_FROM_JOB,
    CREATE_NEW_PROCESS_GROUP,
    DETACHED_PROCESS,
    build_clock_command,
    launch_clock,
    select_gui_python,
)
from learningclock.telemetry import PROCESS_CREATED, PROCESS_LAUNCH_FAILED


def clock(tmp_path: Path) -> ConfiguredClock:
    path = tmp_path / "Clock With Spaces.properties"
    return ConfiguredClock("clock", "Clock", "Clock", path, tmp_path / "logs")


def test_source_command_uses_module_and_gui_interpreter(tmp_path):
    python = tmp_path / "python.exe"
    pythonw = tmp_path / "pythonw.exe"
    python.write_bytes(b"")
    pythonw.write_bytes(b"")

    command, mode = build_clock_command(
        clock(tmp_path), "correlation-1", python_executable=python
    )

    assert mode == "source"
    assert Path(command[0]) == pythonw.resolve()
    assert command[1:3] == ["-m", "learningclock.desktop"]
    assert command[3:] == [
        "--clock",
        str(tmp_path / "Clock With Spaces.properties"),
        "--correlation-id",
        "correlation-1",
    ]
    assert select_gui_python(python) == pythonw.resolve()


def test_packaged_command_relaunches_gui_executable_directly(tmp_path):
    executable = tmp_path / "LearningClock.exe"

    command, mode = build_clock_command(
        clock(tmp_path), "correlation-2", packaged_executable=executable
    )

    assert mode == "packaged"
    assert command == [
        str(executable),
        "--clock",
        str(tmp_path / "Clock With Spaces.properties"),
        "--correlation-id",
        "correlation-2",
    ]


def test_normal_launcher_modules_have_no_vbs_or_shell_dependency():
    root = Path(__file__).resolve().parents[1] / "src" / "learningclock"
    text = "\n".join(
        (root / name).read_text(encoding="utf-8")
        for name in ("desktop.py", "launcherpad.py", "process_launcher.py")
    ).casefold()

    assert ".vbs" not in text
    assert "wscript" not in text
    assert "cscript" not in text
    assert "shell=true" not in text


class CaptureLogger:
    def __init__(self):
        self.events = []

    def event(self, definition, **properties):
        self.events.append((definition, properties))


def test_process_launch_is_detached_without_inherited_stream_pipes(tmp_path, monkeypatch):
    captured = {}

    class FakeProcess:
        pid = 4321

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return FakeProcess()

    monkeypatch.setattr("learningclock.process_launcher.subprocess.Popen", fake_popen)
    logger = CaptureLogger()

    process_id = launch_clock(
        clock(tmp_path),
        "correlation-3",
        logger=logger,
        packaged_executable=tmp_path / "LearningClock.exe",
    )

    assert process_id == 4321
    assert captured["stdin"] < 0 and captured["stdout"] < 0 and captured["stderr"] < 0
    assert captured["close_fds"] is True
    assert captured["creationflags"] == (
        CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS | CREATE_BREAKAWAY_FROM_JOB
    )
    assert "shell" not in captured
    assert any(definition is PROCESS_CREATED for definition, _ in logger.events)


def test_process_launch_failure_emits_formal_error_event(tmp_path, monkeypatch):
    def fail_popen(_command, **_kwargs):
        raise OSError("launch blocked")

    monkeypatch.setattr("learningclock.process_launcher.subprocess.Popen", fail_popen)
    logger = CaptureLogger()

    with pytest.raises(OSError, match="launch blocked"):
        launch_clock(
            clock(tmp_path),
            "correlation-4",
            logger=logger,
            packaged_executable=tmp_path / "LearningClock.exe",
        )

    failure = next(properties for definition, properties in logger.events if definition is PROCESS_LAUNCH_FAILED)
    assert failure["clock_id"] == "clock"
    assert failure["error_type"] == "OSError"
