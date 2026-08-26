# =============================================================================
# File Name : test_app_ui.py
# Artifact  : LearningClock - Tkinter UI State Tests
# Author    : javaboy-vk
# Date      : 2026-08-08
# Version   : v5.3
# Purpose:
#   Verifies activity-button colors follow the active timer without a display.
# =============================================================================

from learningclock.app import (
    ACTIVE_TIMER_BUTTON_BACKGROUND,
    BUTTON_BACKGROUND,
    MENU_FONT,
    LearningClock,
)


class FakeButton:
    """Captures Tkinter-style configuration calls without requiring a GUI display."""

    def __init__(self):
        self.options = {}

    def config(self, **kwargs):
        self.options.update(kwargs)


def test_active_timer_button_is_orange_and_inactive_buttons_are_blue():

    clock = LearningClock.__new__(LearningClock)
    reading_button = FakeButton()
    sandbox_button = FakeButton()
    clock.activity_buttons = {"Reading": reading_button, "Sandbox": sandbox_button}
    clock.active_activity = "Sandbox"

    clock.refresh_activity_button_colors()

    assert ACTIVE_TIMER_BUTTON_BACKGROUND == "#FF6600"
    assert reading_button.options == {"bg": BUTTON_BACKGROUND, "activebackground": BUTTON_BACKGROUND}
    assert sandbox_button.options == {
        "bg": ACTIVE_TIMER_BUTTON_BACKGROUND,
        "activebackground": ACTIVE_TIMER_BUTTON_BACKGROUND,
    }


def test_menu_uses_a_bold_font_for_visibility():

    assert MENU_FONT[-1] == "bold"
