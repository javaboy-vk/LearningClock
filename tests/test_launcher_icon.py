# =============================================================================
# File Name : test_launcher_icon.py
# Artifact  : LearningClock - Windows Launcher Icon Contract Tests
# Author    : javaboy-vk
# Date      : 2026-09-01
# Version   : v1.0.0
# Purpose:
#   Verifies the LauncherPad icon contains high-resolution PNG-backed Windows
#   frames and retains its tracked transparent source artwork and build script.
# =============================================================================

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON_PATH = ROOT / "launcher" / "Learning-Clock.ico"
ICON_SOURCE_PATH = ROOT / "launcher" / "Learning-Clock-source.png"
ICON_BUILD_SCRIPT_PATH = ROOT / "scripts" / "Build-LauncherIcon.ps1"


def test_launcher_icon_contains_native_small_and_large_frames():
    icon = ICON_PATH.read_bytes()
    reserved, image_type, image_count = struct.unpack_from("<HHH", icon)
    entries = [
        struct.unpack_from("<BBBBHHII", icon, 6 + (index * 16)) for index in range(image_count)
    ]
    sizes = {256 if entry[0] == 0 else entry[0] for entry in entries}

    assert (reserved, image_type) == (0, 1)
    assert image_count == 10
    assert sizes == {16, 20, 24, 32, 40, 48, 64, 96, 128, 256}
    for entry in entries:
        byte_count, image_offset = entry[6], entry[7]
        assert icon[image_offset : image_offset + 8] == b"\x89PNG\r\n\x1a\n"
        assert image_offset + byte_count <= len(icon)


def test_launcher_icon_source_and_reproducible_builder_are_tracked():
    source = ICON_SOURCE_PATH.read_bytes()
    builder = ICON_BUILD_SCRIPT_PATH.read_text(encoding="utf-8")

    assert source.startswith(b"\x89PNG\r\n\x1a\n")
    assert b"IHDR" in source[:32]
    assert "Format32bppArgb" in builder
    assert "@(16, 20, 24, 32, 40, 48, 64, 96, 128, 256)" in builder
