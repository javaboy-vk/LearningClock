# =============================================================================
# File Name : test_dev_launcherpad.py
# Artifact  : LearningClock - LauncherPad Developer Command Tests
# Author    : javaboy-vk
# Date      : 2026-09-01
# Version   : v1.1.0
# Purpose:
#   Verifies detached source startup and current-user Start Menu registration
#   command construction without launching a GUI or changing the live Start Menu.
# =============================================================================

import os
import subprocess

from scripts import dev


def test_launcherpad_target_starts_detached_source_gui(tmp_path, monkeypatch, capsys):
    pythonw = tmp_path / "pythonw.exe"
    pythonw.write_bytes(b"")
    config_dir = tmp_path / "Learning Path"
    captured = {}

    class FakeProcess:
        pid = 54321

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return FakeProcess()

    monkeypatch.setattr(dev, "VENV_PYTHONW", pythonw)
    monkeypatch.setattr(dev.subprocess, "Popen", fake_popen)

    dev.launcherpad(["--config-dir", str(config_dir)])

    assert captured["command"] == [
        str(pythonw),
        "-m",
        "learningclock.desktop",
        "--config-dir",
        str(config_dir),
    ]
    assert captured["cwd"] == dev.ROOT
    assert captured["env"]["PYTHONPATH"] == str(dev.ROOT / "src")
    assert captured["stdin"] is subprocess.DEVNULL
    assert captured["stdout"] is subprocess.DEVNULL
    assert captured["stderr"] is subprocess.DEVNULL
    assert captured["close_fds"] is True
    expected_flags = dev.WINDOWS_DETACHED_CREATION_FLAGS if os.name == "nt" else 0
    assert captured["creationflags"] == expected_flags
    assert "process ID 54321" in capsys.readouterr().out


def test_launcherpad_register_builds_current_user_shortcut_command(tmp_path, monkeypatch):
    pythonw = tmp_path / "pythonw.exe"
    icon = tmp_path / "Learning-Clock.ico"
    registration_script = tmp_path / "Register-LauncherPad.ps1"
    config_dir = tmp_path / "Learning Path"
    for path in (pythonw, icon, registration_script):
        path.write_bytes(b"")
    captured = []

    monkeypatch.setattr(dev, "VENV_PYTHONW", pythonw)
    monkeypatch.setattr(dev, "LAUNCHER_ICON", icon)
    monkeypatch.setattr(dev, "REGISTER_LAUNCHERPAD_SCRIPT", registration_script)
    monkeypatch.setattr(dev, "run", lambda command: captured.append(command))

    dev.register_launcherpad(["--config-dir", str(config_dir)])

    command = captured[0]
    assert command[:6] == [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(registration_script),
    ]
    assert command[command.index("-TargetPath") + 1] == str(pythonw)
    assert command[command.index("-WorkingDirectory") + 1] == str(dev.ROOT)
    assert command[command.index("-IconPath") + 1] == str(icon)
    assert str(config_dir) in command[command.index("-ShortcutArguments") + 1]
    assert command[-1] == "-PinToStart"


def test_launcherpad_register_can_skip_pin_request(tmp_path, monkeypatch):
    pythonw = tmp_path / "pythonw.exe"
    icon = tmp_path / "Learning-Clock.ico"
    registration_script = tmp_path / "Register-LauncherPad.ps1"
    for path in (pythonw, icon, registration_script):
        path.write_bytes(b"")
    captured = []

    monkeypatch.setattr(dev, "VENV_PYTHONW", pythonw)
    monkeypatch.setattr(dev, "LAUNCHER_ICON", icon)
    monkeypatch.setattr(dev, "REGISTER_LAUNCHERPAD_SCRIPT", registration_script)
    monkeypatch.setattr(dev, "run", lambda command: captured.append(command))

    dev.register_launcherpad(["--no-pin"])

    assert "-PinToStart" not in captured[0]


def test_registration_script_uses_current_user_start_menu_and_product_icon():
    script = dev.REGISTER_LAUNCHERPAD_SCRIPT.read_text(encoding="utf-8")

    assert '[Environment]::GetFolderPath("Programs")' in script
    assert "Set-LauncherPadShortcut -Path $shortcutPath" in script
    assert '$shortcut.IconLocation = "$resolvedIcon,0"' in script
    assert '"Microsoft\\Internet Explorer\\Quick Launch\\User Pinned\\TaskBar"' in script
    assert "Set-LauncherPadShortcut -Path $taskbarShortcutPath" in script
    assert "SHChangeNotify" in script
    assert '"Pin to Start"' in script
