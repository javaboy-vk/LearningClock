# =============================================================================
# File Name : test_learning_clock_csv_regression.py
# Artifact  : LearningClock - External CSV Regression Tests
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Tests a supplied real CSV file without modifying the original file.
# =============================================================================

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import unittest
from datetime import datetime
from pathlib import Path

from learning_clock_csv_test_support import LearningClockCsvHarness, learning_clock

EXTERNAL_CSV_PATH = None
DURATION_PATTERN = r"^\d{1,}:\d{2}:\d{2}$"
CANONICAL_DURATION_PATTERN = r"^\d{2,}:\d{2}:\d{2}$"


# Regression fixture that copies a real CSV into a temporary log directory before each test.
class LearningClockCsvRegressionTestCase(LearningClockCsvHarness, unittest.TestCase):

    # Prepare an isolated copy of the supplied CSV so regression tests never edit the source file.
    def setUp(self):
        if not EXTERNAL_CSV_PATH:
            self.skipTest("No external CSV supplied. Use --csv path\\to\\learning_time_log.csv.")

        super().setUp()
        self.source_csv = Path(EXTERNAL_CSV_PATH)
        if not self.source_csv.exists():
            self.fail(f"External CSV file does not exist: {self.source_csv}")

        shutil.copy2(self.source_csv, self.clock.log_file)

    # Read the rewritten temporary CSV exactly as downstream dashboard/report code would see it.
    def read_rows(self):
        with self.clock.log_file.open("r", newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    # Verify the external CSV can be loaded into the current schema without losing session rows.
    def test_external_csv_can_be_read_and_normalized(self):
        rows = self.clock.read_existing_session_rows()

        self.assertGreater(len(rows), 0, f"No session rows found in {self.source_csv}")
        for index, row in enumerate(rows, start=1):
            with self.subTest(row=index, date=row.get("date")):
                self.assertEqual(set(learning_clock.FIELDNAMES), set(row.keys()))
                self.assertNotEqual("TOTAL", row["date"])
                for field_name in learning_clock.ACTIVITY_TO_FIELD.values():
                    self.assertRegex(row[field_name], DURATION_PATTERN)
                self.assertRegex(row["total"], DURATION_PATTERN)

    # Verify every stored row total still equals the sum of its activity duration columns.
    def test_external_csv_row_totals_match_activity_sums(self):
        rows = self.clock.read_existing_session_rows()

        for index, row in enumerate(rows, start=1):
            expected_total = self.clock.recalculate_row_total(row)
            with self.subTest(row=index, date=row.get("date"), start=row.get("session_start")):
                self.assertEqual(
                    self.clock.parse_duration(expected_total),
                    self.clock.parse_duration(row["total"]),
                    "Row total does not match the sum of activity columns.",
                )

    # Verify a rewrite keeps the CSV structurally clean and leaves one final TOTAL row.
    def test_external_csv_rewrite_has_no_blank_lines_and_one_total_row(self):
        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 10, 0, 0))

        self.assertTrue(saved, f"Rewrite skipped because {self.source_csv} had no data rows.")
        raw_text = self.clock.log_file.read_text(encoding="utf-8")
        self.assertNotIn("\n\n", raw_text)
        self.assertNotIn("\r\n\r\n", raw_text)

        rows = self.read_rows()
        total_rows = [row for row in rows if row.get("date") == "TOTAL"]
        self.assertEqual(
            1,
            len(total_rows),
            "CSV must contain exactly one TOTAL row after rewrite.",
        )
        self.assertEqual("TOTAL", rows[-1]["date"], "TOTAL row must be the final CSV row.")
        for index, row in enumerate(rows, start=1):
            with self.subTest(row=index, date=row.get("date")):
                for field_name in learning_clock.ACTIVITY_TO_FIELD.values():
                    self.assertRegex(row[field_name], DURATION_PATTERN)
                self.assertRegex(row["total"], DURATION_PATTERN)

        total_row = rows[-1]
        for field_name in learning_clock.ACTIVITY_TO_FIELD.values():
            with self.subTest(total_field=field_name):
                self.assertRegex(total_row[field_name], CANONICAL_DURATION_PATTERN)
        self.assertRegex(total_row["total"], CANONICAL_DURATION_PATTERN)

    # Verify the rewritten TOTAL row is recalculated from the persisted session rows.
    def test_external_csv_total_row_matches_session_rows(self):
        self.clock.save_session_summary(datetime(2026, 6, 5, 10, 0, 0))
        rows = self.read_rows()
        sessions = [row for row in rows if row.get("date") != "TOTAL"]
        actual_total = rows[-1]
        expected_total = self.clock.create_total_row(sessions)

        for field_name in learning_clock.ACTIVITY_TO_FIELD.values():
            with self.subTest(field=field_name):
                self.assertEqual(expected_total[field_name], actual_total[field_name])
        self.assertEqual(expected_total["pages_read"], actual_total["pages_read"])
        self.assertEqual(expected_total["total"], actual_total["total"])


# Split the custom --csv argument from unittest arguments before starting the test runner.
def parse_test_args(argv):
    parser = argparse.ArgumentParser(description="Learning Clock external CSV regression suite")
    parser.add_argument("--csv", required=True, help="Problem CSV file to copy and test.")
    args, unittest_args = parser.parse_known_args(argv)
    return args, unittest_args


if __name__ == "__main__":
    parsed_args, remaining_args = parse_test_args(sys.argv[1:])
    EXTERNAL_CSV_PATH = parsed_args.csv
    unittest.main(argv=[sys.argv[0], *remaining_args])
