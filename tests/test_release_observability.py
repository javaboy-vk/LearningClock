# =============================================================================
# File Name : test_release_observability.py
# Artifact  : LearningClock - Observability Release Tests
# Author    : javaboy-vk
# Date      : 2026-08-24
# Version   : v0.1.2
# Purpose:
#   Verifies production release planning includes every runtime module required
#   by the protepo.log and FastAPI integrations.
# =============================================================================

from scripts import dev


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
    assert "src\\learningclock\\api.py" in output
    assert "src\\learningclock\\events.py" in output
    assert "src\\learningclock\\observability.py" in output
    assert "src\\learningclock\\window_icon.py" in output
    assert "launcher\\Learning-Clock.ico" in output
