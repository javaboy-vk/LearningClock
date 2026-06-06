# =============================================================================
# File Name : test_learning_clock_csv_unit.py
# Artifact  : LearningClock - CSV Unit Tests
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Verifies CSV save, normalization, emergency recovery, and total calculations.
# =============================================================================

from __future__ import annotations

import csv
import unittest
from datetime import datetime

from learning_clock_csv_test_support import LearningClockCsvHarness, learning_clock


class LearningClockCsvUnitTestCase(LearningClockCsvHarness, unittest.TestCase):
    def test_create_session_row_formats_fields_and_total(self):
        self.clock.totals["Reading"] = 60
        self.clock.totals["Experimenting"] = 3600
        self.clock.totals["Update Diavgeia"] = 30
        self.clock.pages_read = 7

        row = self.clock.create_session_row(datetime(2026, 6, 5, 10, 15, 30))

        self.assertEqual("2026-06-05", row["date"])
        self.assertEqual("UnitTestPath", row["learning_path"])
        self.assertEqual("09:00:00", row["session_start"])
        self.assertEqual("10:15:30", row["session_end"])
        self.assertEqual("00:01:00", row["reading"])
        self.assertEqual("01:00:00", row["experimenting"])
        self.assertEqual("00:00:30", row["update_diavgeia"])
        self.assertEqual("7", row["pages_read"])
        self.assertEqual("01:01:30", row["total"])

    def test_create_total_row_sums_activities_pages_and_total(self):
        rows = [
            self.row(reading="00:10:00", experimenting="00:05:00", pages_read="3", total="00:15:00"),
            self.row(reading="00:20:00", audiobook="00:07:30", pages_read="4", total="00:27:30"),
        ]

        total = self.clock.create_total_row(rows)

        self.assertEqual("TOTAL", total["date"])
        self.assertEqual("00:30:00", total["reading"])
        self.assertEqual("00:05:00", total["experimenting"])
        self.assertEqual("00:07:30", total["audiobook"])
        self.assertEqual("7", total["pages_read"])
        self.assertEqual("00:42:30", total["total"])

    def test_save_session_summary_writes_one_session_and_total_without_blank_lines(self):
        self.clock.totals["Reading"] = 5
        self.clock.totals["Outlining"] = 8
        self.clock.totals["Memorizing"] = 17
        self.clock.totals["Experimenting"] = 600

        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 18, 48, 22))

        self.assertTrue(saved)
        raw_text = self.clock.log_file.read_text(encoding="utf-8")
        self.assertNotIn("\n\n", raw_text)
        self.assertNotIn("\r\n\r\n", raw_text)

        rows = self.read_log_rows()
        self.assertEqual(2, len(rows))
        self.assertEqual("2026-06-05", rows[0]["date"])
        self.assertEqual("00:10:30", rows[0]["total"])
        self.assertEqual("TOTAL", rows[1]["date"])
        self.assertEqual("00:10:30", rows[1]["total"])

    def test_save_session_summary_does_not_create_empty_csv_for_empty_session(self):
        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 18, 48, 22))

        self.assertFalse(saved)
        self.assertFalse(self.clock.log_file.exists())
        self.assertFalse(self.clock.session_saved)

    def test_save_session_summary_preserves_existing_rows_and_recalculates_total(self):
        existing = self.row(
            date="2026-06-04",
            reading="00:10:00",
            pages_read="2",
            total="00:10:00",
        )
        self.write_csv([existing])

        self.clock.totals["Reading"] = 600
        self.clock.totals["Experimenting"] = 120
        self.clock.pages_read = 3

        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 10, 0, 0))

        self.assertTrue(saved)
        rows = self.read_log_rows()
        self.assertEqual(3, len(rows))
        self.assertEqual("2026-06-04", rows[0]["date"])
        self.assertEqual("2026-06-05", rows[1]["date"])
        self.assertEqual("TOTAL", rows[2]["date"])
        self.assertEqual("00:20:00", rows[2]["reading"])
        self.assertEqual("00:02:00", rows[2]["experimenting"])
        self.assertEqual("5", rows[2]["pages_read"])
        self.assertEqual("00:22:00", rows[2]["total"])

    def test_normalize_existing_row_maps_legacy_fields_and_missing_values(self):
        row = {
            "date": "06/05/26",
            "document_in_diavgeia": "00:03:00",
            "reading": "00:02:00",
        }

        normalized = self.clock.normalize_existing_row(row)

        self.assertEqual("2026-06-05", normalized["date"])
        self.assertEqual("00:03:00", normalized["update_diavgeia"])
        self.assertEqual("00:00:00", normalized["outlining"])
        self.assertEqual("0", normalized["pages_read"])
        self.assertEqual("00:05:00", normalized["total"])

    def test_read_existing_session_rows_removes_total_row(self):
        self.write_csv([
            self.row(reading="00:02:00", total="00:02:00"),
            self.row(date="TOTAL", reading="99:00:00", total="99:00:00"),
        ])

        rows = self.clock.read_existing_session_rows()

        self.assertEqual(1, len(rows))
        self.assertEqual("2026-06-05", rows[0]["date"])
        self.assertEqual("00:02:00", rows[0]["total"])

    def test_emergency_rows_are_merged_and_files_marked_after_successful_save(self):
        emergency_file = self.log_dir / "learning_time_log_emergency_20260605_100000.csv"
        with emergency_file.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=learning_clock.FIELDNAMES)
            writer.writeheader()
            writer.writerow(self.row(date="2026-06-04", reading="00:04:00", total="00:04:00"))

        self.clock.totals["Reading"] = 60
        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 10, 0, 0))

        self.assertTrue(saved)
        self.assertFalse(emergency_file.exists())
        self.assertTrue((self.log_dir / "learning_time_log_emergency_20260605_100000.csv.merged").exists())

        rows = self.read_log_rows()
        self.assertEqual(3, len(rows))
        self.assertEqual("2026-06-05", rows[0]["date"])
        self.assertEqual("2026-06-04", rows[1]["date"])
        self.assertEqual("TOTAL", rows[2]["date"])
        self.assertEqual("00:05:00", rows[2]["reading"])
        self.assertEqual("00:05:00", rows[2]["total"])

    def test_save_emergency_session_file_uses_main_csv_schema(self):
        self.clock.totals["Audiobook"] = 90
        self.clock.pages_read = 1

        emergency_file = self.clock.save_emergency_session_file(
            datetime(2026, 6, 5, 11, 0, 0),
            RuntimeError("locked"),
        )

        self.assertTrue(emergency_file.exists())
        with emergency_file.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(learning_clock.FIELDNAMES, reader.fieldnames)
            rows = list(reader)

        self.assertEqual(1, len(rows))
        self.assertEqual("00:01:30", rows[0]["audiobook"])
        self.assertEqual("1", rows[0]["pages_read"])
        self.assertEqual("00:01:30", rows[0]["total"])

    def test_duration_parsing_and_formatting_are_stable_for_bad_values(self):
        self.assertEqual(3723, self.clock.parse_duration("01:02:03"))
        self.assertEqual(0, self.clock.parse_duration(""))
        self.assertEqual(0, self.clock.parse_duration("not-a-duration"))
        self.assertEqual("01:02:03", self.clock.format_seconds(3723))

    def test_manual_input_accepts_supported_formats_and_rejects_bad_values(self):
        self.assertEqual(300, self.clock.parse_manual_input("5"))
        self.assertEqual(5400, self.clock.parse_manual_input("01:30"))
        self.assertEqual(5445, self.clock.parse_manual_input("01:30:45"))

        with self.assertRaises(ValueError):
            self.clock.parse_manual_input("")
        with self.assertRaises(ValueError):
            self.clock.parse_manual_input("1:xx")


if __name__ == "__main__":
    unittest.main()
