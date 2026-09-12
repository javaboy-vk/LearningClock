# =============================================================================
# File Name : test_readme_assets.py
# Artifact  : LearningClock - README Visual Asset Tests
# Author    : javaboy-vk
# Date      : 2026-09-02
# Version   : v0.3.0
# Purpose:
#   Verifies generated LauncherPad feature screenshots and README references.
# =============================================================================

import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.generate_readme_assets import (
    generate_launcherpad_svg,
    generate_report_diagnostics_svg,
)

ROOT = Path(__file__).resolve().parents[1]


def test_launcherpad_svg_shows_available_and_running_clocks() -> None:
    svg = generate_launcherpad_svg()
    root = ET.fromstring(svg)
    assert root.attrib["width"] == "900"
    assert root.attrib["height"] == "620"
    assert "LearningClock LauncherPad 2.0" in svg
    assert "Create New Clock" in svg
    assert "Time by category across all clocks" in svg
    assert "6 configured clocks" in svg
    assert "4 skipped/invalid inputs" in svg
    assert 'text-decoration="underline"' in svg
    assert "Northstar Lab — Running" in svg
    assert "Atlas Study" in svg
    assert svg.count('fill="#069bff"') >= 6
    assert svg.count('fill="#FF6600"') >= 2


def test_readme_embeds_generated_launcherpad_asset() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/assets/learning-clock-launcherpad.svg" in readme
    asset = ROOT / "docs" / "assets" / "learning-clock-launcherpad.svg"
    assert asset.read_text(encoding="utf-8") == generate_launcherpad_svg()


def test_report_diagnostics_svg_shows_linked_file_and_row_details() -> None:
    svg = generate_report_diagnostics_svg()
    root = ET.fromstring(svg)
    visible_text = "".join(root.itertext())
    assert root.attrib["width"] == "900"
    assert root.attrib["height"] == "560"
    assert "Skipped and Invalid Report Inputs" in svg
    assert "read-only and does not rewrite CSV data" in svg
    assert "learning_time_log.csv — row 29" in svg
    assert "Column: date" in svg
    assert "Value: ''" in visible_text
    assert "time log missing" in svg
    assert svg.count('text-decoration="underline"') == 4


def test_readme_embeds_generated_report_diagnostics_asset() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/assets/learning-clock-report-diagnostics.svg" in readme
    asset = ROOT / "docs" / "assets" / "learning-clock-report-diagnostics.svg"
    assert asset.read_text(encoding="utf-8") == generate_report_diagnostics_svg()


def test_readme_and_generated_ui_images_do_not_disclose_private_project_names() -> None:
    public_files = [
        ROOT / "README.md",
        ROOT / "docs" / "assets" / "learning-clock-launcherpad.svg",
        ROOT / "docs" / "assets" / "learning-clock-report-diagnostics.svg",
        ROOT / "docs" / "assets" / "learning-clock-ui.svg",
        ROOT / "docs" / "assets" / "learning-clock-progress.svg",
        ROOT / "docs" / "assets" / "learning-clock-dashboard.svg",
        ROOT
        / "docs"
        / "assets"
        / "mockups"
        / "learning-clock-current-ui-blue-buttons.svg",
    ]
    private_names = (
        "aixtreme",
        "dias",
        "magpai",
        "performance engineering",
        "python engineering lab",
        "protepo",
        "diavgeia",
    )
    for path in public_files:
        content = path.read_text(encoding="utf-8").casefold()
        for private_name in private_names:
            assert private_name not in content, f"{private_name!r} leaked into {path.name}"
