from pathlib import Path

import pytest

from learningclock.configuration import CentralConfiguration, ConfiguredClock
from learningclock.process_launcher import (
    CREATE_BREAKAWAY_FROM_JOB,
    CREATE_NEW_PROCESS_GROUP,
    DETACHED_PROCESS,
    build_clock_command,
    launch_clock,
)
from learningclock.telemetry import PROCESS_CREATED, PROCESS_LAUNCH_FAILED


def clock(tmp_path: Path) -> ConfiguredClock:
    path = tmp_path / "Clock With Spaces.properties"
    return ConfiguredClock("clock", "Clock", "Clock With Spaces", path, tmp_path / "Log Dir")


def central(tmp_path: Path) -> CentralConfiguration:
    return CentralConfiguration(
        tmp_path / "clock.properties",
        tmp_path / "Python With Spaces" / "pythonw.exe",
        tmp_path / "App With Spaces" / "app.py",
    )


def test_command_combines_central_and_per_clock_configuration(tmp_path):
    command, mode = build_clock_command(clock(tmp_path), central(tmp_path), "correlation-1")
    assert mode == "configured-python"
    assert command == [
        str(tmp_path / "Python With Spaces" / "pythonw.exe"),
        str(tmp_path / "App With Spaces" / "app.py"),
        "--learning-path",
        "Clock With Spaces",
        "--log-dir",
        str(tmp_path / "Log Dir" / "LearningPath"),
        "--clock-id",
        "clock",
        "--correlation-id",
        "correlation-1",
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
    process_id = launch_clock(clock(tmp_path), central(tmp_path), "correlation-3", logger=logger)
    assert process_id == 4321
    assert captured["cwd"] == central(tmp_path).script_path.parent
    assert captured["stdin"] < 0 and captured["stdout"] < 0 and captured["stderr"] < 0
    assert captured["close_fds"] is True
    assert captured["creationflags"] == (
        CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS | CREATE_BREAKAWAY_FROM_JOB
    )
    assert "shell" not in captured
    assert any(definition is PROCESS_CREATED for definition, _ in logger.events)


def test_process_launch_failure_emits_formal_error_event(tmp_path, monkeypatch):
    def fail(*_args, **_kwargs):
        raise OSError("launch blocked")

    monkeypatch.setattr("learningclock.process_launcher.subprocess.Popen", fail)
    logger = CaptureLogger()
    with pytest.raises(OSError, match="launch blocked"):
        launch_clock(clock(tmp_path), central(tmp_path), "correlation-4", logger=logger)
    failure = next(
        properties
        for definition, properties in logger.events
        if definition is PROCESS_LAUNCH_FAILED
    )
    assert failure["clock_id"] == "clock"
    assert failure["error_type"] == "OSError"
