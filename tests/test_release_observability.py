# =============================================================================
# File Name : test_release_observability.py
# Artifact  : LearningClock - Observability Release Tests
# Author    : javaboy-vk
# Date      : 2026-08-24
# Version   : v0.5.0
# Purpose:
#   Verifies production release planning includes every runtime module required
#   by the protepo.log and FastAPI integrations.
# =============================================================================

from pathlib import Path, PureWindowsPath

from scripts import dev


def test_private_runtime_dependency_uses_published_immutable_commit():
    project = (dev.ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "@115ab65d25e445876257b80a623a6d1667ac8cec#subdirectory=" in project
    assert "@protepo-log-v2.0.0#subdirectory=" not in project


def test_default_release_layout_uses_standard_application_directories():
    assert PureWindowsPath(dev.PRODUCTION_ROOT) == PureWindowsPath(r"D:\LearningClock")
    assert PureWindowsPath(dev.PRODUCTION_LIB_DIR) == PureWindowsPath(r"D:\LearningClock\Lib")
    assert PureWindowsPath(dev.LEARNINGCLOCK_PROPERTIES_DIR) == PureWindowsPath(
        r"D:\LearningClock\props"
    )
    assert PureWindowsPath(dev.LEARNINGCLOCK_LOG_DIR) == PureWindowsPath(
        r"D:\LearningClock\logs"
    )
    assert PureWindowsPath(dev.LEARNINGCLOCK_ASSETS_DIR) == PureWindowsPath(
        r"D:\LearningClock\assets"
    )
    central = (dev.ROOT / "src" / "learningclock" / "clock.properties").read_text(
        encoding="utf-8"
    )
    assert r"pyScriptPath=D:\LearningClock\Lib\learningclock\app.py" in central


def test_release_dry_run_includes_observability_runtime_modules(tmp_path, monkeypatch, capsys):

    monkeypatch.setattr(dev, "export_dashboard_components", lambda *_args, **_kwargs: None)

    dev.release(
        [
            "--dry-run",
            "--production-dir",
            str(tmp_path / "production"),
        ]
    )

    output = capsys.readouterr().out
    assert str(Path("src") / "learningclock" / "api.py") in output
    assert str(Path("src") / "learningclock" / "events.py") in output
    assert str(Path("src") / "learningclock" / "observability.py") in output
    assert str(Path("src") / "learningclock" / "window_icon.py") in output
    assert str(Path("launcher") / "Learning-Clock.ico") in output
    assert "would release runtime dependency:" in output
    assert str(tmp_path / "production" / "Lib" / "learningclock" / "app.py") in output
    assert str(tmp_path / "production" / "app.py") not in output
    assert str(tmp_path / "production" / "assets" / "Learning-Clock.ico") in output
    assert f"would ensure directory: {tmp_path / 'production' / 'props'}" in output
    assert f"would ensure directory: {tmp_path / 'production' / 'logs'}" in output


def test_obsolete_runtime_cleanup_is_scoped_to_installation_root(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "app.py").write_text("obsolete", encoding="utf-8")
    marker = tmp_path / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    dev.remove_obsolete_runtime_directory(tmp_path)

    assert not runtime.exists()
    assert marker.read_text(encoding="utf-8") == "keep"
