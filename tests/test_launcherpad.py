# =============================================================================
# File Name : test_launcherpad.py
# Artifact  : LearningClock - LauncherPad State Tests
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.0
# Purpose:
#   Verifies the visible available/running state mapping without a GUI display.
# =============================================================================

import tkinter as tk
from pathlib import Path

from learningclock.configuration import ConfiguredClock
from learningclock.launcherpad import (
    AVAILABLE_BACKGROUND,
    RUNNING_BACKGROUND,
    clock_control_state,
)


def test_launcherpad_maps_mutex_state_to_enabled_and_running_controls():
    clock = ConfiguredClock(
        "magpai", "MAGPAI", "MAGPAI", Path("MAGPAI.properties"), Path("logs")
    )

    available = clock_control_state(clock, False)
    running = clock_control_state(clock, True)

    assert available.text == "MAGPAI"
    assert available.widget_state == tk.NORMAL
    assert available.background == AVAILABLE_BACKGROUND
    assert running.text == "MAGPAI — Running"
    assert running.widget_state == tk.DISABLED
    assert running.background == RUNNING_BACKGROUND

