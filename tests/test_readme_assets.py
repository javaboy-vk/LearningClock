# =============================================================================
# File Name : test_readme_assets.py
# Artifact  : LearningClock - README Visual Asset Tests
# Author    : javaboy-vk
# Date      : 2026-09-02
# Version   : v0.1.0
# Purpose:
#   Verifies the generated LauncherPad illustration and its README reference.
# =============================================================================

import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.generate_readme_assets import generate_launcherpad_svg

ROOT = Path(__file__).resolve().parents[1]


def test_launcherpad_svg_shows_available_and_running_clocks() -> None:
    svg = generate_launcherpad_svg()
    root = ET.fromstring(svg)
    assert root.attrib["width"] == "900"
    assert root.attrib["height"] == "330"
    assert "LearningClock LauncherPad 1.0" in svg
    assert "6 configured clocks" in svg
    assert "Performance Engineering — Running" in svg
    assert svg.count('fill="#069bff"') >= 6
    assert svg.count('fill="#FF6600"') >= 2


def test_readme_embeds_generated_launcherpad_asset() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/assets/learning-clock-launcherpad.svg" in readme
    asset = ROOT / "docs" / "assets" / "learning-clock-launcherpad.svg"
    assert asset.read_text(encoding="utf-8") == generate_launcherpad_svg()
