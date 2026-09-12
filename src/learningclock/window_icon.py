# =============================================================================
# File Name : window_icon.py
# Artifact  : LearningClock - Shared Tkinter Window Icon
# Author    : javaboy-vk
# Date      : 2026-09-01
# Version   : v1.1.0
# Purpose:
#   Resolves and applies the same multi-resolution Windows icon to LauncherPad
#   and configured LearningClock root windows across source and packaged modes.
# =============================================================================

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from typing import Any

ICON_FILE_NAME = "Learning-Clock.ico"


# Source documentation:
#   What it does: Lists packaged, frozen, released-source, and repository icon locations.
#   Why it exists: LauncherPad can run from a wheel, frozen executable, staged source, or checkout.
#   Designed use: resolve_window_icon checks these locations in priority order without guessing
#     from the process working directory.
def window_icon_candidates() -> tuple[Path, ...]:
    module_path = Path(__file__).resolve()
    return (
        module_path.parent / "assets" / ICON_FILE_NAME,
        module_path.parents[2] / "assets" / ICON_FILE_NAME,
        Path(sys.executable).resolve().parent / ICON_FILE_NAME,
        module_path.parent.parent / ICON_FILE_NAME,
        module_path.parents[2] / "launcher" / ICON_FILE_NAME,
    )


# Source documentation:
#   What it does: Returns the first existing icon location for the active runtime layout.
#   Why it exists: Tkinter needs a concrete filesystem path and runtime layouts differ.
#   Designed use: Window initialization calls it through apply_window_icon; missing assets return
#     None so a cosmetic failure cannot prevent timer or LauncherPad startup.
def resolve_window_icon() -> Path | None:
    return next((path for path in window_icon_candidates() if path.is_file()), None)


# Source documentation:
#   What it does: Applies the shared multi-resolution ICO to one Tkinter window title bar.
#   Why it exists: LauncherPad and every configured clock must present one visible application
#     identity instead of Tk's generic default icon.
#   Designed use: Root-window constructors call it before setting their title; unsupported Tk
#     platforms, test doubles, and missing/corrupt icon assets fail softly and return None.
def apply_window_icon(window: Any) -> Path | None:
    icon_path = resolve_window_icon()
    if icon_path is None:
        return None
    try:
        window.iconbitmap(default=str(icon_path))
    except (AttributeError, tk.TclError):
        return None
    return icon_path
