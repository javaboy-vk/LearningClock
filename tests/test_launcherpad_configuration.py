# =============================================================================
# File Name : test_launcherpad_configuration.py
# Artifact  : LearningClock - LauncherPad Configuration Tests
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.0
# Purpose:
#   Verifies backward-compatible discovery, stable identity, ordering, malformed
#   file isolation, and duplicate identity handling.
# =============================================================================

from pathlib import Path

from learningclock.configuration import (
    discover_clock_configurations,
    load_clock_configuration,
    stable_clock_id,
)
from learningclock.telemetry import CONFIG_DUPLICATE_ID, CONFIG_MALFORMED


class CaptureLogger:
    def __init__(self):
        self.events = []

    def event(self, definition, **properties):
        self.events.append((definition, properties))


def write_configuration(path: Path, name: str, log_dir: str, **values: object) -> None:
    lines = [f"learning-path-name={name}", f"logDir={log_dir}"]
    lines.extend(f"{key.replace('_', '-')}={value}" for key, value in values.items())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_legacy_filename_produces_stable_clock_identity(tmp_path):
    path = tmp_path / "Python-Engineering-Lab.properties"
    write_configuration(path, "Python Engineering Lab", "logs")

    first = load_clock_configuration(path)
    second = load_clock_configuration(path)

    assert first.clock_id == second.clock_id == "python-engineering-lab"
    assert first.display_name == "Python Engineering Lab"
    assert first.log_dir == (tmp_path / "logs").resolve()
    assert stable_clock_id("MAGPAI") == "magpai"


def test_discovery_honors_order_then_display_name_and_isolates_bad_files(tmp_path):
    write_configuration(tmp_path / "z.properties", "Zulu", "z-logs")
    write_configuration(tmp_path / "a.properties", "Alpha", "a-logs", order=2)
    write_configuration(tmp_path / "b.properties", "Beta", "b-logs", order=1)
    (tmp_path / "broken.properties").write_text("learning-path-name=Broken\n", encoding="utf-8")
    logger = CaptureLogger()

    result = discover_clock_configurations(tmp_path, logger=logger)

    assert [clock.display_name for clock in result.clocks] == ["Beta", "Alpha", "Zulu"]
    assert len(result.issues) == 1
    assert any(definition is CONFIG_MALFORMED for definition, _ in logger.events)


def test_duplicate_clock_id_is_skipped_without_hiding_valid_clock(tmp_path):
    write_configuration(tmp_path / "one.properties", "One", "one", clock_id="shared")
    write_configuration(tmp_path / "two.properties", "Two", "two", clock_id="shared")
    write_configuration(tmp_path / "three.properties", "Three", "three")
    logger = CaptureLogger()

    result = discover_clock_configurations(tmp_path, logger=logger)

    assert {clock.clock_id for clock in result.clocks} == {"shared", "three"}
    assert len(result.issues) == 1
    assert any(definition is CONFIG_DUPLICATE_ID for definition, _ in logger.events)

