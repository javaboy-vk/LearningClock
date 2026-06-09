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


# Testing algorithm:
#   What we test:
#     CsvStoreTtestHarness adapts CsvStore for deterministic unit and regression test sessions.
#   Success:
#     Tests get fixed session start data, isolated totals, and optional shared diagnostic logging.
#   Error checks:
#     CsvStore path setup errors still propagate so broken test storage fails immediately.
class CsvStoreTtestHarness(CsvStore):

    # Testing algorithm:
    #   What we test:
    #     CsvStoreTtestHarness initializes production CsvStore behavior with deterministic test state.
    #   Success:
    #     The store uses a test log directory, fixed session start, empty totals, and optional diagnostic path.
    #   Error checks:
    #     CsvStore directory errors and diagnostic path creation failures surface immediately.
    def __init__(
        self,
        log_dir: Path,
        learning_path_name: str = "UnitTestPath",
        diagnostic_log_file: Path | None = None,
    ):

        super().__init__(log_dir, learning_path_name)                         # Reuse production CsvStore setup.
        if diagnostic_log_file is not None:                                   # Optional shared diagnostic log for regression tests.
            self.diagnostic_log_file = Path(diagnostic_log_file)              # Store resolved diagnostic log path.
            self.diagnostic_log_file.parent.mkdir(parents=True, exist_ok=True)  # Ensure diagnostic directory exists.
        self.session_start = datetime(2026, 6, 5, 9, 0, 0)                    # Fixed start keeps expected rows stable.
        self.session_saved = False                                            # Mirror app save state for tests.
        self.totals = {activity: 0 for activity in ACTIVITIES}                # Start every activity at zero seconds.
        self.pages_read = 0                                                   # Start page count at zero.

    # Testing algorithm:
    #   What we test:
    #     Helper builds a production session row from deterministic test state.
    #   Success:
    #     CsvStore receives fixed start time, provided end time, current totals, and page count.
    #   Error checks:
    #     Production create_session_row validation and formatting errors surface to the test.
    def create_session_row(self, session_end):

        return super().create_session_row(
            self.session_start,                                               # Fixed harness session start.
            session_end,                                                       # Test-provided session end.
            self.totals,                                                       # Current seeded activity totals.
            self.pages_read,                                                   # Current seeded page count.
        )                                                                      # Return production-formatted row.

    # Testing algorithm:
    #   What we test:
    #     Helper saves the current deterministic session through the production save path.
    #   Success:
    #     CsvStore persists the generated row and the helper mirrors the returned save state.
    #   Error checks:
    #     Production save errors propagate so unit tests fail with the original persistence error.
    def save_session_summary(self, session_end):

        saved = super().save_session_summary(self.create_session_row(session_end))  # Save generated session row.
        self.session_saved = saved                                            # Mirror app session_saved state.
        return saved                                                          # Return production save result.

    # Testing algorithm:
    #   What we test:
    #     Helper writes the current deterministic session through the production emergency-save path.
    #   Success:
    #     CsvStore creates an emergency CSV using the same generated session row format.
    #   Error checks:
    #     Production emergency-save errors propagate to the failing test.
    def save_emergency_session_file(self, session_end, error):

        return super().save_emergency_session_file(
            self.create_session_row(session_end),                              # Generated row for fallback persistence.
            session_end,                                                       # Timestamp used in emergency filename/content.
            error,                                                             # Original save error recorded by CsvStore.
        )                                                                      # Return emergency file path.


# Testing algorithm:
#   What we test:
#     The harness creates and cleans an isolated CSV workspace for every test case.
#   Success:
#     Test cases receive a fresh CsvStoreTtestHarness plus helpers for reading and seeding CSV rows.
#   Error checks:
#     Temporary-directory and CSV parsing failures surface directly to the failing test.
class LearningClockCsvHarness:

    # Testing algorithm:
    #   What we test:
    #     Each test gets a clean temporary directory and fresh store instance.
    #   Success:
    #     Test methods can read and write CSV files without touching real application data.
    #   Error checks:
    #     Temporary directory creation or store initialization errors fail the test setup.
    def setUp(self):

        self.temp_dir = TemporaryDirectory()                                   # Create isolated filesystem workspace.
        self.log_dir = Path(self.temp_dir.name)                                # Convert temp path to Path for CsvStore.
        self.clock = self.make_clock()                                         # Build the test store/app adapter.

    # Testing algorithm:
    #   What we test:
    #     Test cleanup removes the temporary CSV workspace.
    #   Success:
    #     Per-test files do not leak into later tests or the repository.
    #   Error checks:
    #     TemporaryDirectory cleanup errors surface through unittest teardown.
    def tearDown(self):

        self.temp_dir.cleanup()                                                # Remove isolated workspace.

    # Testing algorithm:
    #   What we test:
    #     Harness subclasses can override store construction while the default uses CsvStoreTtestHarness.
    #   Success:
    #     Unit tests get a deterministic CsvStoreTtestHarness rooted in the temporary directory.
    #   Error checks:
    #     CsvStoreTtestHarness initialization errors fail setup before assertions run.
    def make_clock(self):

        return CsvStoreTtestHarness(self.log_dir)                              # Create default deterministic store.

    # Testing algorithm:
    #   What we test:
    #     Helper reads persisted CSV output using the production header row.
    #   Success:
    #     Callers receive dictionaries for each persisted row.
    #   Error checks:
    #     Missing files, invalid encodings, and CSV parsing problems surface to the test.
    def read_log_rows(self):

        with self.clock.log_file.open("r", newline="", encoding="utf-8") as handle:  # Open main CSV output.
            return list(csv.DictReader(handle))                                # Return rows keyed by CSV header.

    # Testing algorithm:
    #   What we test:
    #     Helper seeds the main CSV file with caller-provided rows.
    #   Success:
    #     Tests can create existing-history fixtures with the production field order.
    #   Error checks:
    #     File write errors and invalid row shapes surface during fixture setup.
    def write_csv(self, rows):

        with self.clock.log_file.open("w", newline="", encoding="utf-8") as handle:  # Open main CSV for fixture data.
            writer = csv.DictWriter(handle, fieldnames=learning_clock.FIELDNAMES)    # Use production schema.
            writer.writeheader()                                               # Write header before rows.
            writer.writerows(rows)                                             # Write supplied fixture rows.

    # Testing algorithm:
    #   What we test:
    #     Helper creates a complete default CSV row that tests can override field by field.
    #   Success:
    #     Callers get a schema-complete row with stable defaults and requested overrides applied.
    #   Error checks:
    #     Invalid override keys are preserved so production normalization/schema assertions can catch them.
    def row(self, **overrides):

        values = {                                                            # Start with one complete CSV row.
            "date": "2026-06-05",                                             # Default session date.
            "learning_path": "UnitTestPath",                                  # Default harness learning path.
            "session_start": "09:00:00",                                      # Default session start time.
            "session_end": "09:30:00",                                        # Default session end time.
            "reading": "00:00:00",                                            # Default reading duration.
            "outlining": "00:00:00",                                          # Default outlining duration.
            "memorizing": "00:00:00",                                         # Default memorizing duration.
            "experimenting": "00:00:00",                                      # Default experimenting duration.
            "audiobook": "00:00:00",                                          # Default audiobook duration.
            "update_diavgeia": "00:00:00",                                    # Default Diavgeia update duration.
            "promote_stable_concept": "00:00:00",                             # Default promotion duration.
            "pages_read": "0",                                                # Default page count.
            "total": "00:00:00",                                              # Default row total.
        }
        values.update(overrides)                                              # Apply test-specific field values.
        return values                                                         # Return complete fixture row.
