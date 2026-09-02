# =============================================================================
# File Name : test_app_ui.py
# Artifact  : LearningClock - Tkinter UI State Tests
# Author    : javaboy-vk
# Date      : 2026-08-08
# Version   : v6.0.4
# Purpose:
#   Verifies activity-button colors and fixed UI sizing without a display.
# =============================================================================

from learningclock.app import (
    ACTIVE_TIMER_BUTTON_BACKGROUND,
    ADD_TIME_GEOMETRY,
    BUTTON_BACKGROUND,
    CALENDAR_WEEKDAYS,
    MANUAL_TIME_ENTRY_WIDTH,
    MANUAL_TIME_INPUT_LENGTH,
    MENU_FONT,
    LearningClock,
    calendar_month_weeks,
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


def test_manual_time_mode_fits_a_complete_hh_mm_ss_value():

    add_time_width = int(ADD_TIME_GEOMETRY.partition("x")[0])

    assert add_time_width >= 620
    assert MANUAL_TIME_INPUT_LENGTH == len("00:00:00")
    assert MANUAL_TIME_ENTRY_WIDTH == len("00:00:00")


def test_manual_time_field_rejects_text_beyond_hh_mm_ss():

    accepted_edits = ["", "0", "00", "00:", "00:00", "00:00:", "00:00:00"]
    rejected_edits = ["000", "0:", "00:60", "00:00:60", "00:00:001", "00:00:00x"]

    assert all(LearningClock.validate_manual_time_edit(value) for value in accepted_edits)
    assert not any(LearningClock.validate_manual_time_edit(value) for value in rejected_edits)


def test_calendar_popup_is_mapped_raised_and_visible_before_keyboard_grab():

    calls = []

    class FakePicker:
        def __getattr__(self, name):
            return lambda: calls.append(name)

    present_calendar_popup(FakePicker())

    assert calls == ["deiconify", "lift", "wait_visibility", "focus_force", "grab_set"]


def test_calendar_dates_align_with_sunday_first_weekday_headings():

    september_2026 = calendar_month_weeks(2026, 9)
    weekday_column = next(
        column
        for week in september_2026
        for column, day_number in enumerate(week)
        if day_number == 2
    )

    assert CALENDAR_WEEKDAYS[weekday_column] == "Wed"


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
