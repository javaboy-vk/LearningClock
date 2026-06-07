# =============================================================================
# File Name : learning_clock_csv_test_support.py
# Artifact  : LearningClock - CSV Test Support
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Provides shared helpers for Learning Clock CSV unit and regression tests.
# =============================================================================

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from learningclock import csv_store as learning_clock
from learningclock.csv_store import ACTIVITIES, CsvStore


class TestCsvStore(CsvStore):
    def __init__(
        self,
        log_dir: Path,
        learning_path_name: str = "UnitTestPath",
        diagnostic_log_file: Path | None = None,
    ):
        super().__init__(log_dir, learning_path_name)
        if diagnostic_log_file is not None:
            self.diagnostic_log_file = Path(diagnostic_log_file)
            self.diagnostic_log_file.parent.mkdir(parents=True, exist_ok=True)
        self.session_start = datetime(2026, 6, 5, 9, 0, 0)
        self.session_saved = False
        self.totals = {activity: 0 for activity in ACTIVITIES}
        self.pages_read = 0

    def create_session_row(self, session_end):
        return super().create_session_row(
            self.session_start,
            session_end,
            self.totals,
            self.pages_read,
        )

    def save_session_summary(self, session_end):
        saved = super().save_session_summary(self.create_session_row(session_end))
        self.session_saved = saved
        return saved

    def save_emergency_session_file(self, session_end, error):
        return super().save_emergency_session_file(
            self.create_session_row(session_end),
            session_end,
            error,
        )


class LearningClockCsvHarness:
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.log_dir = Path(self.temp_dir.name)
        self.clock = self.make_clock()

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_clock(self):
        return TestCsvStore(self.log_dir)

    def read_log_rows(self):
        with self.clock.log_file.open("r", newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def write_csv(self, rows):
        with self.clock.log_file.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=learning_clock.FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

    def row(self, **overrides):
        values = {
            "date": "2026-06-05",
            "learning_path": "UnitTestPath",
            "session_start": "09:00:00",
            "session_end": "09:30:00",
            "reading": "00:00:00",
            "outlining": "00:00:00",
            "memorizing": "00:00:00",
            "experimenting": "00:00:00",
            "audiobook": "00:00:00",
            "update_diavgeia": "00:00:00",
            "promote_stable_concept": "00:00:00",
            "pages_read": "0",
            "total": "00:00:00",
        }
        values.update(overrides)
        return values
