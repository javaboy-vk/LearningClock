# =============================================================================
# File Name : test_app_ui.py
# Artifact  : LearningClock - Tkinter UI State Tests
# Author    : javaboy-vk
# Date      : 2026-08-08
# Version   : v6.0.1
# Purpose:
#   Verifies activity-button colors follow the active timer without a display.
# =============================================================================

from learningclock.app import (
    ACTIVE_TIMER_BUTTON_BACKGROUND,
    BUTTON_BACKGROUND,
    MENU_FONT,
    LearningClock,
    present_calendar_popup,
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


def test_calendar_popup_is_mapped_raised_and_visible_before_keyboard_grab():

    calls = []

    class FakePicker:
        def __getattr__(self, name):
            return lambda: calls.append(name)

    present_calendar_popup(FakePicker())

    assert calls == ["deiconify", "lift", "wait_visibility", "focus_force", "grab_set"]


def test_set_date_action_schedules_the_calendar_popup_immediately():

    calls = []

    class FakeRoot:
        def after_idle(self, callback):
            calls.append("after_idle")
            callback()

    class FakeEntry:
        def focus_set(self):
            calls.append("focus_set")

    clock = LearningClock.__new__(LearningClock)
    clock.root = FakeRoot()
    clock.set_date_mode = False
    clock.add_page_count_mode = False
    clock.selected_session_date = None
    clock.date_frame = object()
    clock.date_entry = FakeEntry()
    clock.show_control_at_timer_column = lambda control: calls.append(("show", control))
    clock.open_date_picker = lambda: calls.append("open_date_picker")

    clock.toggle_set_date_mode()

    assert clock.set_date_mode is True
    assert calls == [
        ("show", clock.date_frame),
        "focus_set",
        "after_idle",
        "open_date_picker",
    ]
