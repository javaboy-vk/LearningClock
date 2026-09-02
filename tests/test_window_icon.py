# =============================================================================
# File Name : test_window_icon.py
# Artifact  : LearningClock - Shared Window Icon Tests
# Author    : javaboy-vk
# Date      : 2026-09-01
# Version   : v1.0.0
# Purpose:
#   Verifies title-bar icon resolution, application, graceful fallback, and
#   integration in both LauncherPad and configured LearningClock windows.
# =============================================================================

from pathlib import Path

from learningclock import window_icon


class FakeWindow:
    def __init__(self):
        self.icon_options = None

    def iconbitmap(self, **options):
        self.icon_options = options


def test_apply_window_icon_uses_resolved_multiresolution_asset(tmp_path, monkeypatch):
    icon = tmp_path / "Learning-Clock.ico"
    icon.write_bytes(b"icon")
    window = FakeWindow()
    monkeypatch.setattr(window_icon, "resolve_window_icon", lambda: icon)

    applied = window_icon.apply_window_icon(window)

    assert applied == icon
    assert window.icon_options == {"default": str(icon)}


def test_apply_window_icon_fails_softly_when_asset_is_missing(monkeypatch):
    window = FakeWindow()
    monkeypatch.setattr(window_icon, "resolve_window_icon", lambda: None)

    assert window_icon.apply_window_icon(window) is None
    assert window.icon_options is None


def test_packaged_icon_matches_launcher_icon():
    root = Path(__file__).resolve().parents[1]

    assert (root / "src" / "learningclock" / "assets" / "Learning-Clock.ico").read_bytes() == (
        root / "launcher" / "Learning-Clock.ico"
    ).read_bytes()


def test_both_primary_windows_apply_the_shared_icon():
    root = Path(__file__).resolve().parents[1]
    launcherpad_source = (root / "src" / "learningclock" / "launcherpad.py").read_text(
        encoding="utf-8"
    )
    clock_source = (root / "src" / "learningclock" / "app.py").read_text(encoding="utf-8")

    assert "apply_window_icon(self.root)" in launcherpad_source
    assert "apply_window_icon(self.root)" in clock_source
