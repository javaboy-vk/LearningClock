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
import importlib.util
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "src" / "learningclock" / "learning-clock.py"


def load_learning_clock_module():
    spec = importlib.util.spec_from_file_location("learning_clock_app", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


learning_clock = load_learning_clock_module()


class LearningClockCsvHarness:
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.log_dir = Path(self.temp_dir.name)
        self.clock = self.make_clock()

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_clock(self):
        clock = learning_clock.LearningClock.__new__(learning_clock.LearningClock)
        clock.learning_path_name = "UnitTestPath"
        clock.log_dir = self.log_dir
        clock.log_file = self.log_dir / learning_clock.LOG_FILE_NAME
        clock.diagnostic_log_file = self.log_dir / learning_clock.DIAGNOSTIC_LOG_FILE_NAME
        clock.session_start = datetime(2026, 6, 5, 9, 0, 0)
        clock.session_saved = False
        clock.active_activity = None
        clock.active_start = None
        clock.totals = {activity: 0 for activity in learning_clock.ACTIVITIES}
        clock.pages_read = 0
        return clock

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
