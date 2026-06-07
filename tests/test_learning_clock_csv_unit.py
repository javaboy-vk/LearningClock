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
from learningclock.app import LearningClock


# Testing algorithm:
#   What we test:
#     Unit tests exercise CsvStore and LearningClock CSV behavior with an isolated temporary harness.
#   Success:
#     Session rows, total rows, normalization, emergency recovery, and manual input rules stay stable.
#   Error checks:
#     Assertions catch schema drift, bad totals, unsafe empty saves, bad duration parsing, and recovery failures.
class LearningClockCsvUnitTestCase(LearningClockCsvHarness, unittest.TestCase):
    # Testing algorithm:
    #   What we test:
    #     CsvStore builds one session row from fixed app state and a supplied session end.
    #   Success:
    #     Date, learning path, start/end times, activity fields, page count, and total are formatted.
    #   Error checks:
    #     Field-by-field assertions catch date, duration, page, and total formatting drift.
    def test_create_session_row_formats_fields_and_total(self):
        self.clock.totals["Reading"] = 60                                      # Seed one minute of reading.
        self.clock.totals["Experimenting"] = 3600                              # Seed one hour of experimenting.
        self.clock.totals["Update Diavgeia"] = 30                              # Seed thirty seconds in a mapped activity.
        self.clock.pages_read = 7                                              # Seed session page count.

        row = self.clock.create_session_row(datetime(2026, 6, 5, 10, 15, 30))  # Build the persisted row.

        self.assertEqual("2026-06-05", row["date"])                            # Date uses ISO CSV format.
        self.assertEqual("UnitTestPath", row["learning_path"])                 # Harness learning path is preserved.
        self.assertEqual("09:00:00", row["session_start"])                     # Harness session start is fixed.
        self.assertEqual("10:15:30", row["session_end"])                       # Provided session end is formatted.
        self.assertEqual("00:01:00", row["reading"])                           # Reading seconds become HH:MM:SS.
        self.assertEqual("01:00:00", row["experimenting"])                     # Experimenting seconds become HH:MM:SS.
        self.assertEqual("00:00:30", row["update_diavgeia"])                   # Mapped activity field is written.
        self.assertEqual("7", row["pages_read"])                               # Page count is persisted as text.
        self.assertEqual("01:01:30", row["total"])                             # Total sums all activity seconds.

    # Testing algorithm:
    #   What we test:
    #     CsvStore calculates a TOTAL row from multiple existing session rows.
    #   Success:
    #     Activity durations, pages, and grand total are summed into one TOTAL row.
    #   Error checks:
    #     Assertions catch per-column summing errors and page-count conversion drift.
    def test_create_total_row_sums_activities_pages_and_total(self):
        rows = [                                                               # Build representative persisted session rows.
            self.row(
                reading="00:10:00",                                            # First row reading duration.
                experimenting="00:05:00",                                      # First row experimenting duration.
                pages_read="3",                                                # First row page count.
                total="00:15:00",                                              # First row total duration.
            ),
            self.row(reading="00:20:00", audiobook="00:07:30", pages_read="4", total="00:27:30"),  # Second row.
        ]

        total = self.clock.create_total_row(rows)                              # Calculate summary from rows.

        self.assertEqual("TOTAL", total["date"])                               # Summary row marker.
        self.assertEqual("00:30:00", total["reading"])                         # Reading values are summed.
        self.assertEqual("00:05:00", total["experimenting"])                   # Experimenting value carries forward.
        self.assertEqual("00:07:30", total["audiobook"])                       # Audiobook value carries forward.
        self.assertEqual("7", total["pages_read"])                             # Page counts are summed.
        self.assertEqual("00:42:30", total["total"])                           # Grand total sums activity totals.

    # Testing algorithm:
    #   What we test:
    #     Saving a non-empty session writes one session row and one final TOTAL row cleanly.
    #   Success:
    #     The CSV has no blank lines, contains exactly two rows, and both totals match session time.
    #   Error checks:
    #     Assertions catch skipped saves, extra blank lines, row-count drift, and wrong TOTAL placement.
    def test_save_session_summary_writes_one_session_and_total_without_blank_lines(self):
        self.clock.totals["Reading"] = 5                                      # Seed small reading duration.
        self.clock.totals["Outlining"] = 8                                    # Seed small outlining duration.
        self.clock.totals["Memorizing"] = 17                                  # Seed small memorizing duration.
        self.clock.totals["Experimenting"] = 600                              # Seed ten minutes of experimenting.

        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 18, 48, 22))  # Persist session and TOTAL row.

        self.assertTrue(saved)                                                # Save path should write data.
        raw_text = self.clock.log_file.read_text(encoding="utf-8")            # Inspect raw CSV spacing.
        self.assertNotIn("\n\n", raw_text)                                    # No Unix-style blank lines.
        self.assertNotIn("\r\n\r\n", raw_text)                                # No Windows-style blank lines.

        rows = self.read_log_rows()                                           # Read persisted CSV rows.
        self.assertEqual(2, len(rows))                                        # Session row plus TOTAL row.
        self.assertEqual("2026-06-05", rows[0]["date"])                       # First row is the session.
        self.assertEqual("00:10:30", rows[0]["total"])                        # Session total matches seeded seconds.
        self.assertEqual("TOTAL", rows[1]["date"])                            # Final row is TOTAL.
        self.assertEqual("00:10:30", rows[1]["total"])                        # TOTAL matches only session row.

    # Testing algorithm:
    #   What we test:
    #     Saving an empty session should not create a CSV or mark the session saved.
    #   Success:
    #     CsvStore returns false, no log file exists, and session_saved stays false.
    #   Error checks:
    #     Assertions catch accidental empty-file creation and incorrect save-state updates.
    def test_save_session_summary_does_not_create_empty_csv_for_empty_session(self):
        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 18, 48, 22))  # Attempt to save zero data.

        self.assertFalse(saved)                                               # Empty session should be skipped.
        self.assertFalse(self.clock.log_file.exists())                        # Skipped save should not create CSV.
        self.assertFalse(self.clock.session_saved)                            # App save flag should remain false.

    # Testing algorithm:
    #   What we test:
    #     Saving with existing rows preserves sessions and recalculates the final TOTAL row.
    #   Success:
    #     Existing row, new row, and recalculated TOTAL row are persisted in order.
    #   Error checks:
    #     Assertions catch lost history, misplaced rows, bad activity sums, and bad page totals.
    def test_save_session_summary_preserves_existing_rows_and_recalculates_total(self):
        existing = self.row(
            date="2026-06-04",                                                # Prior session date.
            reading="00:10:00",                                               # Prior session reading duration.
            pages_read="2",                                                   # Prior session pages.
            total="00:10:00",                                                 # Prior session total.
        )
        self.write_csv([existing])                                            # Seed existing CSV history.

        self.clock.totals["Reading"] = 600                                    # New session reading duration.
        self.clock.totals["Experimenting"] = 120                              # New session experimenting duration.
        self.clock.pages_read = 3                                             # New session pages.

        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 10, 0, 0))  # Append new session and rewrite TOTAL.

        self.assertTrue(saved)                                                # Non-empty save should write.
        rows = self.read_log_rows()                                           # Read rewritten CSV.
        self.assertEqual(3, len(rows))                                        # Existing, new, TOTAL.
        self.assertEqual("2026-06-04", rows[0]["date"])                       # Existing row remains first.
        self.assertEqual("2026-06-05", rows[1]["date"])                       # New row is appended.
        self.assertEqual("TOTAL", rows[2]["date"])                            # TOTAL row is final.
        self.assertEqual("00:20:00", rows[2]["reading"])                      # Reading total includes both rows.
        self.assertEqual("00:02:00", rows[2]["experimenting"])                # Experimenting total includes new row.
        self.assertEqual("5", rows[2]["pages_read"])                          # Page total includes both rows.
        self.assertEqual("00:22:00", rows[2]["total"])                        # Grand total includes all activities.

    # Testing algorithm:
    #   What we test:
    #     Existing CSV rows are normalized across legacy field names and missing values.
    #   Success:
    #     Legacy date/field values map to current schema and missing numeric/duration fields default safely.
    #   Error checks:
    #     Assertions catch date normalization, legacy-column mapping, defaulting, and recalculated total drift.
    def test_normalize_existing_row_maps_legacy_fields_and_missing_values(self):
        row = {                                                               # Simulate a legacy partial CSV row.
            "date": "06/05/26",                                               # Legacy short date format.
            "document_in_diavgeia": "00:03:00",                               # Legacy column name.
            "reading": "00:02:00",                                            # Current column with duration.
        }

        normalized = self.clock.normalize_existing_row(row)                   # Convert to current row schema.

        self.assertEqual("2026-06-05", normalized["date"])                    # Date becomes ISO format.
        self.assertEqual("00:03:00", normalized["update_diavgeia"])           # Legacy field maps to current field.
        self.assertEqual("00:00:00", normalized["outlining"])                 # Missing duration defaults to zero.
        self.assertEqual("0", normalized["pages_read"])                       # Missing pages default to zero.
        self.assertEqual("00:05:00", normalized["total"])                     # Total is recalculated from activity fields.

    # Testing algorithm:
    #   What we test:
    #     Reading existing session rows excludes the persisted TOTAL summary row.
    #   Success:
    #     Only real session rows are returned for future append/recalculate work.
    #   Error checks:
    #     Assertions catch accidental TOTAL leakage and incorrect row normalization.
    def test_read_existing_session_rows_removes_total_row(self):
        self.write_csv([
            self.row(reading="00:02:00", total="00:02:00"),                  # Real session row.
            self.row(date="TOTAL", reading="99:00:00", total="99:00:00"),    # Existing summary row.
        ])                                                                    # Seed CSV with session and TOTAL.

        rows = self.clock.read_existing_session_rows()                       # Load only non-TOTAL rows.

        self.assertEqual(1, len(rows))                                       # TOTAL row should be removed.
        self.assertEqual("2026-06-05", rows[0]["date"])                      # Remaining row is normalized session.
        self.assertEqual("00:02:00", rows[0]["total"])                       # Session total is preserved.

    # Testing algorithm:
    #   What we test:
    #     Emergency session CSV files are merged on the next successful normal save.
    #   Success:
    #     Emergency file is renamed as merged, session rows are combined, and TOTAL reflects both rows.
    #   Error checks:
    #     Assertions catch unmerged emergency files, lost emergency rows, wrong order, and bad totals.
    def test_emergency_rows_are_merged_and_files_marked_after_successful_save(self):
        emergency_file = self.log_dir / "learning_time_log_emergency_20260605_100000.csv"  # Expected emergency filename.
        with emergency_file.open("w", newline="", encoding="utf-8") as handle:             # Create emergency CSV fixture.
            writer = csv.DictWriter(handle, fieldnames=learning_clock.FIELDNAMES)          # Use production schema.
            writer.writeheader()                                                          # Write CSV header.
            writer.writerow(self.row(date="2026-06-04", reading="00:04:00", total="00:04:00"))  # Emergency row.

        self.clock.totals["Reading"] = 60                                  # Seed current session reading time.
        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 10, 0, 0))  # Save current session and merge emergency.

        self.assertTrue(saved)                                              # Normal save succeeds.
        self.assertFalse(emergency_file.exists())                           # Original emergency file is consumed.
        self.assertTrue(
            (self.log_dir / "learning_time_log_emergency_20260605_100000.csv.merged").exists()
        )                                                                   # Merged marker file proves recovery completed.

        rows = self.read_log_rows()                                         # Read merged CSV output.
        self.assertEqual(3, len(rows))                                      # Current, emergency, TOTAL.
        self.assertEqual("2026-06-05", rows[0]["date"])                     # Current session row is first.
        self.assertEqual("2026-06-04", rows[1]["date"])                     # Emergency row is merged.
        self.assertEqual("TOTAL", rows[2]["date"])                          # TOTAL row remains final.
        self.assertEqual("00:05:00", rows[2]["reading"])                    # Reading total includes both rows.
        self.assertEqual("00:05:00", rows[2]["total"])                      # Grand total includes both rows.

    # Testing algorithm:
    #   What we test:
    #     Emergency save writes a standalone CSV using the same schema as the main log.
    #   Success:
    #     Emergency file exists, has production fieldnames, and contains the current session values.
    #   Error checks:
    #     Assertions catch missing fallback files, schema drift, bad page values, and wrong totals.
    def test_save_emergency_session_file_uses_main_csv_schema(self):
        self.clock.totals["Audiobook"] = 90                                # Seed audiobook duration.
        self.clock.pages_read = 1                                           # Seed page count.

        emergency_file = self.clock.save_emergency_session_file(
            datetime(2026, 6, 5, 11, 0, 0),                                 # Session end for fallback row.
            RuntimeError("locked"),                                         # Simulated normal-save failure.
        )                                                                   # Create emergency CSV.

        self.assertTrue(emergency_file.exists())                            # Fallback file should be present.
        with emergency_file.open("r", newline="", encoding="utf-8") as handle:  # Read fallback CSV.
            reader = csv.DictReader(handle)                                 # Parse by header.
            self.assertEqual(learning_clock.FIELDNAMES, reader.fieldnames)  # Schema matches main CSV.
            rows = list(reader)                                             # Materialize fallback rows.

        self.assertEqual(1, len(rows))                                      # One emergency session row.
        self.assertEqual("00:01:30", rows[0]["audiobook"])                  # Audiobook duration is persisted.
        self.assertEqual("1", rows[0]["pages_read"])                        # Page count is persisted.
        self.assertEqual("00:01:30", rows[0]["total"])                      # Total matches activity duration.

    # Testing algorithm:
    #   What we test:
    #     Duration parsing and formatting stay stable for valid, blank, and malformed values.
    #   Success:
    #     Valid HH:MM:SS parses to seconds, bad values parse to zero, and seconds format canonically.
    #   Error checks:
    #     Assertions catch parser exceptions, bad fallback values, and formatting drift.
    def test_duration_parsing_and_formatting_are_stable_for_bad_values(self):
        self.assertEqual(3723, self.clock.parse_duration("01:02:03"))       # Valid duration parses to seconds.
        self.assertEqual(0, self.clock.parse_duration(""))                  # Blank duration safely becomes zero.
        self.assertEqual(0, self.clock.parse_duration("not-a-duration"))    # Malformed duration safely becomes zero.
        self.assertEqual("01:02:03", self.clock.format_seconds(3723))       # Seconds format back to HH:MM:SS.

    # Testing algorithm:
    #   What we test:
    #     Manual time entry accepts supported input shapes and rejects invalid values.
    #   Success:
    #     Minutes, HH:MM, and HH:MM:SS convert to seconds; blank and malformed values raise ValueError.
    #   Error checks:
    #     Assertions catch accepted-format drift and missing validation errors.
    def test_manual_input_accepts_supported_formats_and_rejects_bad_values(self):
        self.assertEqual(300, LearningClock.parse_manual_input("5"))        # Plain number means minutes.
        self.assertEqual(5400, LearningClock.parse_manual_input("01:30"))   # HH:MM converts to seconds.
        self.assertEqual(5445, LearningClock.parse_manual_input("01:30:45"))  # HH:MM:SS converts to seconds.

        with self.assertRaises(ValueError):                                 # Blank input should be rejected.
            LearningClock.parse_manual_input("")
        with self.assertRaises(ValueError):                                 # Non-numeric time part should be rejected.
            LearningClock.parse_manual_input("1:xx")


if __name__ == "__main__":
    unittest.main()
