# =============================================================================
# File Name : test_learning_clock_csv_unit.py
# Artifact  : LearningClock - CSV Unit Tests
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v5.4
# Purpose:
#   Verifies CSV save, normalization, emergency recovery, and total calculations.
# =============================================================================

from __future__ import annotations

import csv
import unittest
from datetime import date, datetime

from learning_clock_csv_test_support import LearningClockCsvHarness, learning_clock
from learningclock.app import (
    LearningClock,
    build_progress_summary,
    load_autosave_minutes,
    parse_session_date,
)


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
    #     The public category list and CSV schema use the current user-facing activity names.
    #   Success:
    #     The UI-facing activity list contains Book Listening and Sandbox, and future CSV writes use their current fields.
    #   Error checks:
    #     Assertions catch accidental reintroduction of old display labels or CSV columns.
    def test_schema_uses_current_activity_categories_and_columns(self):

        self.assertIn("Book Listening", learning_clock.ACTIVITIES)             # UI label is current.
        self.assertNotIn("Audiobook", learning_clock.ACTIVITIES)               # Old display label is legacy only.
        self.assertIn("book_listening", learning_clock.FIELDNAMES)             # CSV column is current.
        self.assertNotIn("audiobook", learning_clock.FIELDNAMES)               # Old CSV column is legacy only.
        self.assertIn("Sandbox", learning_clock.ACTIVITIES)                    # UI label is current.
        self.assertNotIn("Experimenting", learning_clock.ACTIVITIES)           # Old display label is legacy only.
        self.assertIn("sandbox", learning_clock.FIELDNAMES)                    # CSV column is current.
        self.assertNotIn("experimenting", learning_clock.FIELDNAMES)           # Old CSV column is legacy only.

    def test_legacy_audiobook_column_merges_into_book_listening(self):

        legacy_row = self.row(book_listening="00:02:00", audiobook="00:01:30")

        normalized = self.clock.normalize_existing_row(legacy_row)

        self.assertEqual("00:03:30", normalized["book_listening"])

    # Testing algorithm:
    #   What we test:
    #     CsvStore builds one session row from fixed app state and a supplied session end.
    #   Success:
    #     Date, learning path, start/end times, activity fields, page count, and total are formatted.
    #   Error checks:
    #     Field-by-field assertions catch date, duration, page, and total formatting drift.
    def test_create_session_row_formats_fields_and_total(self):

        self.clock.totals["Reading"] = 60                                      # Seed one minute of reading.
        self.clock.totals["Sandbox"] = 3600                                    # Seed one hour of sandbox time.
        self.clock.totals["AI-Assisted Engineering"] = 120                     # Seed AI-assisted engineering time.
        self.clock.totals["AI-Assisted Architecture & Design"] = 240          # Seed AI architecture/design time.
        self.clock.totals["Classical Software Engineering"] = 180              # Seed classical engineering time.
        self.clock.totals["Update Diavgeia"] = 30                              # Seed thirty seconds in a mapped activity.
        self.clock.pages_read = 7                                              # Seed session page count.

        row = self.clock.create_session_row(datetime(2026, 6, 5, 10, 15, 30))  # Build the persisted row.

        self.assertEqual("2026-06-05", row["date"])                            # Date uses ISO CSV format.
        self.assertEqual("UnitTestPath", row["learning_path"])                 # Harness learning path is preserved.
        self.assertEqual("09:00:00", row["session_start"])                     # Harness session start is fixed.
        self.assertEqual("10:15:30", row["session_end"])                       # Provided session end is formatted.
        self.assertEqual("00:01:00", row["reading"])                           # Reading seconds become HH:MM:SS.
        self.assertEqual("01:00:00", row["sandbox"])                           # Sandbox seconds become HH:MM:SS.
        self.assertEqual("00:02:00", row["ai_assisted_engineering"])           # New AI-assisted field is written.
        self.assertEqual("00:04:00", row["ai_assisted_architecture_design"])  # AI architecture/design field is written.
        self.assertEqual("00:03:00", row["classical_software_engineering"])    # New classical field is written.
        self.assertEqual("00:00:30", row["update_diavgeia"])                   # Mapped activity field is written.
        self.assertEqual("7", row["pages_read"])                               # Page count is persisted as text.
        self.assertEqual("01:10:30", row["total"])                             # Total sums all activity seconds.

    def test_create_session_row_uses_selected_backdate(self):

        row = learning_clock.CsvStore.create_session_row(
            self.clock,
            datetime(2026, 6, 5, 9, 0, 0),
            datetime(2026, 6, 5, 10, 0, 0),
            {activity: 0 for activity in learning_clock.ACTIVITIES},
            1,
            session_date=date(2026, 6, 1),
        )

        self.assertEqual("2026-06-01", row["date"])
        self.assertEqual(date(2026, 6, 1), parse_session_date("06/01/2026"))

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
                active_recall="00:01:00",                                      # First row active recall duration.
                sandbox="00:05:00",                                           # First row sandbox duration.
                ai_assisted_engineering="00:02:00",                            # First row AI-assisted duration.
                ai_assisted_architecture_design="00:03:00",                   # First row AI architecture/design duration.
                pages_read="3",                                                # First row page count.
                total="00:21:00",                                              # First row total duration.
            ),
            self.row(
                reading="00:20:00",
                book_listening="00:07:30",
                classical_software_engineering="00:04:00",
                pages_read="4",
                total="00:31:30",
            ),                                                                  # Second row.
        ]

        total = self.clock.create_total_row(rows)                              # Calculate summary from rows.

        self.assertEqual("TOTAL", total["date"])                               # Summary row marker.
        self.assertEqual("00:30:00", total["reading"])                         # Reading values are summed.
        self.assertEqual("00:01:00", total["active_recall"])                   # Active Recall values are summed.
        self.assertEqual("00:05:00", total["sandbox"])                         # Sandbox value carries forward.
        self.assertEqual("00:02:00", total["ai_assisted_engineering"])         # AI-assisted value carries forward.
        self.assertEqual("00:03:00", total["ai_assisted_architecture_design"])  # AI architecture/design value carries forward.
        self.assertEqual("00:04:00", total["classical_software_engineering"])  # Classical engineering value carries forward.
        self.assertEqual("00:07:30", total["book_listening"])                       # Book Listening value carries forward.
        self.assertEqual("7", total["pages_read"])                             # Page counts are summed.
        self.assertEqual("00:52:30", total["total"])                           # Grand total sums activity totals.

    # Operational algorithm:
    #   What we test:
    #     The in-app progress chart uses the same activity, total, page, and date aggregation as CSV reporting.
    #   Success:
    #     A normalized CSV row set becomes chart-ready totals without starting Tkinter.
    #   Error checks:
    #     Assertions catch missing activity fields or mismatched chart footer totals.
    def test_build_progress_summary_aggregates_csv_sessions(self):

        rows = [
            self.row(
                date="2026-06-05",
                reading="00:10:00",
                ai_assisted_architecture_design="00:03:00",
                pages_read="2",
                total="00:13:00",
            ),
            self.row(
                date="2026-06-06",
                ai_assisted_engineering="00:04:00",
                pages_read="5",
                total="00:04:00",
            ),
        ]

        summary = build_progress_summary(rows)

        self.assertEqual(600, summary["totals"]["Reading"])
        self.assertEqual(180, summary["totals"]["AI-Assisted Architecture & Design"])
        self.assertEqual(240, summary["totals"]["AI-Assisted Engineering"])
        self.assertEqual(1020, summary["total_seconds"])
        self.assertEqual(7, summary["pages_read"])
        self.assertEqual("2026-06-05", summary["first_date"])
        self.assertEqual("2026-06-06", summary["last_date"])

    # Testing algorithm:
    #   What we test:
    #     Pressing Add Time while its fields are open invokes the save path instead of merely
    #     hiding the values that the user entered.
    #   Success:
    #     The same menu action that closes Add Time delegates to add_all_manual_time.
    #   Error checks:
    #     The assertion catches a regression to the old unsaved exit_add_time_mode behavior.
    def test_add_time_toggle_submits_open_manual_entries(self):

        clock = LearningClock.__new__(LearningClock)
        clock.add_time_mode = True
        calls = []
        clock.add_all_manual_time = lambda: calls.append("submitted")

        clock.toggle_add_time_mode()

        self.assertEqual(["submitted"], calls)

    def test_add_page_count_toggle_submits_open_page_entry(self):

        clock = LearningClock.__new__(LearningClock)
        clock.add_page_count_mode = True
        calls = []
        clock.add_page_count = lambda: calls.append("submitted")

        clock.toggle_add_page_count_mode()

        self.assertEqual(["submitted"], calls)

    # Testing algorithm:
    #   What we test:
    #     A backdated Add Time submission is written immediately as one CSV row, including all
    #     activities submitted together, and remains in the CSV total after a later checkpoint.
    #   Success:
    #     The saved backdated row and the progress aggregate contain the submitted manual time
    #     exactly once, so a View Progress checkpoint cannot lose or duplicate it.
    #   Error checks:
    #     Assertions catch deferred persistence, a current-date row, missing activity values,
    #     and manual-time duplication during a normal session save.
    def test_add_manual_time_persists_backdated_activities_immediately_without_duplicate_checkpoint(self):

        class Entry:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

            def delete(self, _start, _end):
                self.value = ""

        clock = LearningClock.__new__(LearningClock)
        clock.store = learning_clock.CsvStore(self.log_dir, "UnitTestPath")
        clock.session_start = datetime(2026, 6, 5, 9, 0, 0)
        clock.active_activity = None
        clock.active_start = None
        clock.selected_session_date = date(2026, 6, 1)
        clock.date_entry = None
        clock.totals = {activity: 0 for activity in learning_clock.ACTIVITIES}
        clock.persisted_manual_totals = {activity: 0 for activity in learning_clock.ACTIVITIES}
        clock.manual_totals_by_date = {}
        clock.manual_pages_by_date = {}
        clock.manual_session_starts = {}
        clock.pages_read = 0
        clock.persisted_manual_pages = 0
        clock.session_saved = False
        clock.manual_entries = {
            activity: Entry("15" if activity == "Reading" else "00:02:30" if activity == "Sandbox" else "")
            for activity in learning_clock.ACTIVITIES
        }
        clock.update_display = lambda: None
        clock.exit_add_time_mode = lambda: None

        clock.add_all_manual_time()

        rows = self.read_log_rows()
        self.assertEqual(["2026-06-01", "TOTAL"], [row["date"] for row in rows])
        self.assertEqual("00:15:00", rows[0]["reading"])
        self.assertEqual("00:02:30", rows[0]["sandbox"])
        self.assertEqual("00:17:30", rows[-1]["total"])

        clock.manual_entries["Reading"].value = "5"
        clock.add_all_manual_time()

        rows = self.read_log_rows()
        self.assertEqual(["2026-06-01", "TOTAL"], [row["date"] for row in rows])
        self.assertEqual("00:20:00", rows[0]["reading"])
        self.assertEqual("00:02:30", rows[0]["sandbox"])
        self.assertEqual("00:22:30", rows[-1]["total"])

        class Status:
            def config(self, **_kwargs):
                pass

        clock.page_count_entry = Entry("4")
        clock.status = Status()
        clock.exit_add_page_count_mode = lambda: None
        clock.add_page_count()

        rows = self.read_log_rows()
        self.assertEqual(["2026-06-01", "TOTAL"], [row["date"] for row in rows])
        self.assertEqual("4", rows[0]["pages_read"])
        self.assertEqual("4", rows[-1]["pages_read"])

        self.assertTrue(clock.persist_session_for_progress())

        rows = self.read_log_rows()
        summary = build_progress_summary(rows[:-1])
        self.assertEqual(1200, summary["totals"]["Reading"])
        self.assertEqual(150, summary["totals"]["Sandbox"])
        self.assertEqual(1350, summary["total_seconds"])

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
        self.clock.totals["Active Recall"] = 17                               # Seed small active recall duration.
        self.clock.totals["Sandbox"] = 600                                    # Seed ten minutes of sandbox time.

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
        self.clock.totals["Sandbox"] = 120                                    # New session sandbox duration.
        self.clock.pages_read = 3                                             # New session pages.

        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 10, 0, 0))  # Append new session and rewrite TOTAL.

        self.assertTrue(saved)                                                # Non-empty save should write.
        rows = self.read_log_rows()                                           # Read rewritten CSV.
        self.assertEqual(3, len(rows))                                        # Existing, new, TOTAL.
        self.assertEqual("2026-06-04", rows[0]["date"])                       # Existing row remains first.
        self.assertEqual("2026-06-05", rows[1]["date"])                       # New row is appended.
        self.assertEqual("TOTAL", rows[2]["date"])                            # TOTAL row is final.
        self.assertEqual("00:20:00", rows[2]["reading"])                      # Reading total includes both rows.
        self.assertEqual("00:02:00", rows[2]["sandbox"])                      # Sandbox total includes new row.
        self.assertEqual("5", rows[2]["pages_read"])                          # Page total includes both rows.
        self.assertEqual("00:22:00", rows[2]["total"])                        # Grand total includes all activities.

    def test_save_session_summary_sorts_backdated_session_chronologically(self):

        self.write_csv([self.row(date="2026-06-05", reading="00:01:00", total="00:01:00")])
        self.clock.totals["Reading"] = 60
        backdated_row = learning_clock.CsvStore.create_session_row(
            self.clock,
            self.clock.session_start,
            datetime(2026, 6, 5, 10, 0, 0),
            self.clock.totals,
            0,
            session_date=date(2026, 6, 1),
        )

        learning_clock.CsvStore.save_session_summary(self.clock, backdated_row)

        rows = self.read_log_rows()
        self.assertEqual(["2026-06-01", "2026-06-05", "TOTAL"], [row["date"] for row in rows])

    # Operational algorithm:
    #   What we test:
    #     Re-saving a current application session replaces its earlier autosave checkpoint.
    #   Success:
    #     The CSV retains one updated session row and one recalculated TOTAL row.
    #   Error checks:
    #     Assertions catch duplicated interval totals after an autosave or final close.
    def test_save_session_summary_replaces_matching_autosave_checkpoint(self):

        self.clock.totals["Reading"] = 60                                    # Seed the first checkpoint.
        first_row = self.clock.create_session_row(datetime(2026, 6, 5, 9, 5, 0))
        learning_clock.CsvStore.save_session_summary(
            self.clock,
            first_row,
            replace_session=True,
        )

        self.clock.totals["Reading"] = 120                                   # Advance time before the next checkpoint.
        second_row = self.clock.create_session_row(datetime(2026, 6, 5, 9, 10, 0))
        saved = learning_clock.CsvStore.save_session_summary(
            self.clock,
            second_row,
            replace_session=True,
        )

        self.assertTrue(saved)                                                # Updated checkpoint should save.
        rows = self.read_log_rows()                                           # Read checkpoint and TOTAL rows.
        self.assertEqual(2, len(rows))                                        # One session row plus TOTAL only.
        self.assertEqual("09:10:00", rows[0]["session_end"])                 # New checkpoint replaces the old end time.
        self.assertEqual("00:02:00", rows[0]["reading"])                    # New checkpoint replaces old totals.
        self.assertEqual("00:02:00", rows[1]["total"])                      # TOTAL does not double count checkpoints.

    # Operational algorithm:
    #   What we test:
    #     The app-local properties file accepts a positive autosave interval and rejects zero.
    #   Success:
    #     Valid configuration is used and invalid configuration falls back to the safe default.
    #   Error checks:
    #     Assertions catch missing validation for values that would disable autosave scheduling.
    def test_load_autosave_minutes_reads_positive_properties_value(self):

        properties_file = self.log_dir / "clock.properties"                  # Isolate properties from the source tree.
        properties_file.write_text("autosave_minutes=12\n", encoding="utf-8")
        self.assertEqual(12, load_autosave_minutes(properties_file))          # Positive configured interval is accepted.

        properties_file.write_text("autosave_minutes=0\n", encoding="utf-8")
        self.assertEqual(5, load_autosave_minutes(properties_file))           # Zero falls back to the default interval.

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
            "memorizing": "00:04:00",                                         # Legacy Active Recall column name.
            "experimenting": "00:05:00",                                      # Legacy Sandbox column name.
            "sandbox": "00:01:00",                                            # Current Sandbox column name.
            "reading": "00:02:00",                                            # Current column with duration.
        }

        normalized = self.clock.normalize_existing_row(row)                   # Convert to current row schema.

        self.assertEqual("2026-06-05", normalized["date"])                    # Date becomes ISO format.
        self.assertEqual("00:03:00", normalized["update_diavgeia"])           # Legacy field maps to current field.
        self.assertEqual("00:04:00", normalized["active_recall"])             # Legacy memorizing maps to Active Recall.
        self.assertEqual("00:06:00", normalized["sandbox"])                   # Legacy experimenting combines with Sandbox.
        self.assertEqual("00:00:00", normalized["ai_assisted_architecture_design"])  # The current field defaults when absent.
        self.assertEqual("00:00:00", normalized["outlining"])                 # Missing duration defaults to zero.
        self.assertEqual("0", normalized["pages_read"])                       # Missing pages default to zero.
        self.assertEqual("00:15:00", normalized["total"])                     # Total is recalculated from activity fields.

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
        self.assertEqual("2026-06-04", rows[0]["date"])                     # Older emergency row is first chronologically.
        self.assertEqual("2026-06-05", rows[1]["date"])                     # Current row follows the older session.
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

        self.clock.totals["Book Listening"] = 90                                # Seed book_listening duration.
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
        self.assertEqual("00:01:30", rows[0]["book_listening"])                  # Book Listening duration is persisted.
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

        self.assertEqual(3723, learning_clock.parse_duration("01:02:03"))   # Valid duration parses to seconds.
        self.assertEqual(0, learning_clock.parse_duration(""))              # Blank duration safely becomes zero.
        self.assertEqual(0, learning_clock.parse_duration("not-a-duration"))  # Malformed duration safely becomes zero.
        self.assertEqual("01:02:03", learning_clock.format_seconds(3723))   # Seconds format back to HH:MM:SS.

    # Testing algorithm:
    #   What we test:
    #     Manual time entry accepts supported input shapes and rejects invalid values.
    #   Success:
    #     Minutes, HH:MM, and HH:MM:SS convert to seconds; blank and malformed values raise ValueError.
    #   Error checks:
    #     Assertions catch accepted-format drift and missing validation errors.
    def test_manual_input_accepts_supported_formats_and_rejects_bad_values(self):

        self.assertEqual(300, LearningClock.parse_manual_input("5"))        # Plain number means minutes.
        self.assertEqual(0, LearningClock.parse_manual_input("0"))          # Zero is a valid no-op duration.
        self.assertEqual(5400, LearningClock.parse_manual_input("01:30"))   # HH:MM converts to seconds.
        self.assertEqual(5445, LearningClock.parse_manual_input("01:30:45"))  # HH:MM:SS converts to seconds.

        with self.assertRaises(ValueError):                                 # Blank input should be rejected.
            LearningClock.parse_manual_input("")
        with self.assertRaises(ValueError):                                 # Non-numeric time part should be rejected.
            LearningClock.parse_manual_input("1:xx")


if __name__ == "__main__":
    unittest.main()
