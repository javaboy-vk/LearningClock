# =============================================================================
# File Name : test_learning_clock_csv_regression.py
# Artifact  : LearningClock - CSV Regression Tests
# Author    : javaboy-vk
# Date      : 2026-06-05
# Version   : v0.1.0
# Purpose:
#   Tests a supplied real CSV file without modifying the original file.
#
# Test runner call tree:
#   main
#   |-- parse_test_args(sys.argv[1:])
#   |   |-- argparse.ArgumentParser(...)
#   |   |-- parser.add_argument("--properties", ...)
#   |   |-- parser.add_argument("--csv", ...)
#   |   `-- parser.parse_known_args(argv)
#   |-- REGRESSION_CONFIG = load_regression_config(parsed_args)
#   |   |-- load_properties(properties_path)
#   |   |-- resolve logDir relative to the properties file
#   |   `-- derive CSV and diagnostic log paths from logDir/csvFile/diagnosticLogFile values
#   |-- normalize_unittest_args(remaining_args)
#   |   |-- test1 -> LearningClockCsvRegressionTestCase.test1_csv_can_be_read_and_normalized
#   |   |-- test2 -> LearningClockCsvRegressionTestCase.test2_csv_row_totals_match_activity_sums
#   |   |-- test3 -> LearningClockCsvRegressionTestCase.test3_csv_rewrite_has_clean_total_row
#   |   `-- test4 -> LearningClockCsvRegressionTestCase.test4_csv_total_row_matches_session_rows
#   `-- unittest.main(argv=[sys.argv[0], *remaining_args])
#       `-- LearningClockCsvRegressionTestCase
#           |-- setUp()
#           |   |-- verify the properties-derived CSV exists
#           |   |-- LearningClockCsvHarness.setUp()
#           |   |-- verify the supplied CSV exists
#           |   |-- copy the supplied CSV into the isolated test log file
#           |   `-- write diagnostics to the configured app log directory
#           |-- test1_csv_can_be_read_and_normalized()
#           |   |-- CsvStore.read_existing_session_rows()
#           |   `-- assert schema, row type, and duration formats are valid
#           |-- test2_csv_row_totals_match_activity_sums()
#           |   |-- CsvStore.read_existing_session_rows()
#           |   |-- CsvStore.recalculate_row_total(row)
#           |   `-- assert stored totals equal recalculated totals
#           |-- test3_csv_rewrite_has_clean_total_row()
#           |   |-- CsvStore.save_session_summary(...)
#           |   |-- read the rewritten temporary CSV text
#           |   |-- read_rows()
#           |   `-- assert clean spacing, one TOTAL row, and valid duration formats
#           `-- test4_csv_total_row_matches_session_rows()
#               |-- CsvStore.save_session_summary(...)
#               |-- read_rows()
#               |-- CsvStore.create_total_row(session_rows)
#               `-- assert persisted TOTAL fields equal recalculated TOTAL fields
# =============================================================================

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import unittest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from learning_clock_csv_test_support import LearningClockCsvHarness, TestCsvStore, learning_clock

REGRESSION_CONFIG = None
DURATION_PATTERN = r"^\d{1,}:\d{2}:\d{2}$"
CANONICAL_DURATION_PATTERN = r"^\d{2,}:\d{2}:\d{2}$"
LOG_FILE_NAME = "learning_time_log.csv"
DIAGNOSTIC_LOG_FILE_NAME = "learning_clock_debug.log"
TEST_ALIASES = {
    "test1": "LearningClockCsvRegressionTestCase.test1_csv_can_be_read_and_normalized",
    "test2": "LearningClockCsvRegressionTestCase.test2_csv_row_totals_match_activity_sums",
    "test3": "LearningClockCsvRegressionTestCase.test3_csv_rewrite_has_clean_total_row",
    "test4": "LearningClockCsvRegressionTestCase.test4_csv_total_row_matches_session_rows",
}


@dataclass(frozen=True)
class RegressionConfig:
    # Testing algorithm:
    #   What we test:
    #     The regression suite must use one resolved configuration object for all path decisions.
    #   Success:
    #     Every test sees the same properties path, learning path name, CSV path, and log path.
    #   Error checks:
    #     Downstream setup fails early if the resolved CSV path does not exist.
    properties_path: Path | None       # Full path to the properties file that configured the run.
    learning_path_name: str            # App learning-path name passed into CsvStore.
    log_dir: Path                      # Directory that owns the configured CSV and log files.
    csv_path: Path                     # Full path to the real CSV used as test input.
    diagnostic_log_path: Path          # Full path to the shared diagnostic log for the run.


# Regression fixture that copies a real CSV into a temporary log directory before each test.
class LearningClockCsvRegressionTestCase(LearningClockCsvHarness, unittest.TestCase):

    # Testing algorithm:
    #   What we test:
    #     Every test must run against a properties-derived real CSV file, but the original
    #     file must never be edited by the regression suite.
    #   Success:
    #     The source CSV path exists and is copied into the harness-owned temporary log file.
    #   Error checks:
    #     Missing config skips the tests with instructions. A nonexistent path fails immediately.
    def setUp(self):
        if not REGRESSION_CONFIG:                           # Error check: the suite needs app-like configuration.
            self.skipTest("No regression config supplied. Use --properties path\\to\\file.properties.")

        super().setUp()                                     # Create the isolated CsvStore and temporary log directory.
        self.source_csv = REGRESSION_CONFIG.csv_path        # Keep the original path for diagnostics.
        if not self.source_csv.exists():                    # Error check: fail before copying a bad path.
            self.fail(f"CSV file does not exist: {self.source_csv}")

        shutil.copy2(self.source_csv, self.clock.log_file)  # Test copy protects the original CSV.

    def make_clock(self):
        # Testing algorithm:
        #   What we test:
        #     The harness-created CsvStore must use the configured learning path and log file.
        #   Success:
        #     CsvStore reads/writes the temporary CSV copy while diagnostics go to the app log.
        #   Error checks:
        #     If REGRESSION_CONFIG is missing, setUp skips before this helper is meaningfully used.
        return TestCsvStore(
            self.log_dir,                         # Temporary CSV directory protects the source CSV.
            REGRESSION_CONFIG.learning_path_name,  # Match the app learning path from properties.
            REGRESSION_CONFIG.diagnostic_log_path, # Write test and CsvStore diagnostics together.
        )

    # Testing algorithm:
    #   What we test:
    #     Helper reads the temporary CSV through csv.DictReader, matching dashboard/report code.
    #   Success:
    #     Callers receive row dictionaries keyed by the CSV header.
    #   Error checks:
    #     File and CSV parsing errors should surface naturally to the failing test.
    def read_rows(self):
        with self.clock.log_file.open(
            "r", newline="", encoding="utf-8"
        ) as handle:                              # Read temp CSV.
            return list(csv.DictReader(handle))   # Convert persisted rows into comparable dicts.

    # Testing algorithm:
    #   What we test:
    #     CsvStore can read a real historical CSV and normalize it into the current schema.
    #   Success:
    #     At least one session row is loaded, every row has exactly the current field names,
    #     no session row is mistaken for TOTAL, and every duration has h:mm:ss-like shape.
    #   Error checks:
    #     assertGreater detects an empty import. assertEqual catches missing or extra fields.
    #     assertNotEqual catches accidental TOTAL leakage. assertRegex catches bad durations.
    def test1_csv_can_be_read_and_normalized(self):
        rows = self.clock.read_existing_session_rows()                             # Load and normalize non-TOTAL session rows.

        self.assertGreater(
            len(rows), 0, f"No session rows found in {self.source_csv}"
        )                                                                          # Success requires at least one session row.
        for index, row in enumerate(rows, start=1):                                # Check every imported session independently.
            with self.subTest(row=index, date=row.get("date")):                    # Report the exact failing row.
                self.assertEqual(set(learning_clock.FIELDNAMES), set(row.keys()))  # Schema match.
                self.assertNotEqual("TOTAL", row["date"])                          # Session rows cannot be TOTAL.
                for field_name in learning_clock.ACTIVITY_TO_FIELD.values():       # Activity times.
                    self.assertRegex(row[field_name], DURATION_PATTERN)            # Parseable duration.
                self.assertRegex(row["total"], DURATION_PATTERN)                   # Total is duration-shaped.

    # Testing algorithm:
    #   What we test:
    #     Each imported row's stored total must equal the sum of the activity duration columns.
    #   Success:
    #     Recalculating each row total produces the same number of seconds as the stored total.
    #   Error checks:
    #     parse_duration compares values numerically, so formatting differences do not hide math
    #     errors, and the custom assertion message explains the broken invariant.
    def test2_csv_row_totals_match_activity_sums(self):
        rows = self.clock.read_existing_session_rows()                          # Load normalized rows from the test copy.

        for index, row in enumerate(rows, start=1):                             # Validate totals row by row.
            expected_total = self.clock.recalculate_row_total(row)              # Sum activities from the row.
            with self.subTest(row=index, date=row.get("date"), start=row.get("session_start")):
                self.assertEqual(
                    self.clock.parse_duration(expected_total),                  # Expected total in seconds.
                    self.clock.parse_duration(row["total"]),                    # Stored total in seconds.
                    "Row total does not match the sum of activity columns.",
                )

    # Testing algorithm:
    #   What we test:
    #     Rewriting a real CSV through save_session_summary keeps the file structurally clean.
    #   Success:
    #     The rewrite happens, no blank lines are introduced, exactly one TOTAL row exists, that
    #     TOTAL row is last, and all duration fields still use the expected display format.
    #   Error checks:
    #     assertTrue catches skipped saves. assertNotIn catches blank-line regressions.
    #     assertEqual catches duplicate or misplaced TOTAL rows. assertRegex catches bad times.
    def test3_csv_rewrite_has_clean_total_row(self):
        saved = self.clock.save_session_summary(datetime(2026, 6, 5, 10, 0, 0))      # Rewrite temp CSV.

        self.assertTrue(
            saved, f"Rewrite skipped because {self.source_csv} had no data rows."
        )                                                                            # Success means the save path actually wrote rows.
        raw_text = self.clock.log_file.read_text(encoding="utf-8")                   # Inspect raw file spacing.
        self.assertNotIn("\n\n", raw_text)                                           # Error check: no Unix-style blank lines.
        self.assertNotIn("\r\n\r\n", raw_text)                                       # Error check: no Windows-style blank lines.

        rows = self.read_rows()                                                      # Read the rewritten CSV as downstream consumers would.
        total_rows = [row for row in rows if row.get("date") == "TOTAL"]             # Find summary rows.
        self.assertEqual(
            1,
            len(total_rows),
            "CSV must contain exactly one TOTAL row after rewrite.",
        )
        self.assertEqual(
            "TOTAL", rows[-1]["date"], "TOTAL row must be the final CSV row."
        )                                                                            # TOTAL must be last.
        for index, row in enumerate(rows, start=1):                                  # Check duration formatting on every row.
            with self.subTest(row=index, date=row.get("date")):                      # Isolate row-format failures.
                for field_name in learning_clock.ACTIVITY_TO_FIELD.values():         # Activity columns.
                    self.assertRegex(row[field_name], DURATION_PATTERN)              # h:mm:ss or hh:mm:ss.
                self.assertRegex(row["total"], DURATION_PATTERN)                     # Row total stays duration-shaped.

        total_row = rows[-1]                                                         # The final row is the summary row asserted above.
        for field_name in learning_clock.ACTIVITY_TO_FIELD.values():                 # Summary activity totals.
            with self.subTest(total_field=field_name):                               # Identify the exact bad total column.
                self.assertRegex(total_row[field_name], CANONICAL_DURATION_PATTERN)  # Use hh:mm:ss.
        self.assertRegex(total_row["total"], CANONICAL_DURATION_PATTERN)             # Canonical grand total.

    # Testing algorithm:
    #   What we test:
    #     The persisted TOTAL row is not copied blindly; it is recalculated from session rows.
    #   Success:
    #     The rewritten TOTAL row's activity fields, page count, and grand total equal a freshly
    #     calculated total row built from the persisted session rows.
    #   Error checks:
    #     Field-by-field assertEqual calls pinpoint exactly which summary value is wrong.
    def test4_csv_total_row_matches_session_rows(self):
        self.clock.save_session_summary(
            datetime(2026, 6, 5, 10, 0, 0)
        )                                                                               # Force TOTAL recalculation.
        rows = self.read_rows()                                                         # Read the persisted result, not in-memory assumptions.
        sessions = [row for row in rows if row.get("date") != "TOTAL"]                  # Inputs to summary math.
        actual_total = rows[-1]                                                         # Persisted summary row produced by save_session_summary.
        expected_total = self.clock.create_total_row(sessions)                          # Fresh summary from session rows.

        for field_name in learning_clock.ACTIVITY_TO_FIELD.values():                    # Compare each activity total.
            with self.subTest(field=field_name):                                        # Report the exact summary column if it fails.
                self.assertEqual(expected_total[field_name], actual_total[field_name])  # Match.
        self.assertEqual(expected_total["pages_read"], actual_total["pages_read"])      # Page total.
        self.assertEqual(expected_total["total"], actual_total["total"])                # Grand duration total.


# Split custom regression-suite arguments from unittest arguments before starting the test runner.
def parse_test_args(argv):
    # Testing algorithm:
    #   What we test:
    #     Regression-specific arguments must be separated from standard unittest arguments.
    #   Success:
    #     --properties and --csv configure this suite, while test1/test2 still reach unittest.
    #   Error checks:
    #     argparse reports malformed regression arguments before unittest starts.
    parser = argparse.ArgumentParser(description="Learning Clock CSV regression suite")  # Suite parser.
    parser.add_argument(
        "--properties",                                                              # App-style config.
        default="tests/fixtures/MAGPAI-regression.properties",
        help="Properties file containing app-style learning-path-name and logDir values.",
    )
    parser.add_argument(
        "--csv",                                                                     # Optional CSV override.
        default=None,
        help="Optional CSV override. Defaults to learning_time_log.csv under properties logDir.",
    )
    args, unittest_args = parser.parse_known_args(argv)                               # Keep unittest args.
    return args, unittest_args                                                        # Return suite and unittest args.


def load_properties(path):
    # Testing algorithm:
    #   What we test:
    #     A Java/VBS-style .properties file can drive the regression suite configuration.
    #   Success:
    #     Non-comment key=value lines become a dictionary and the source path is absolute.
    #   Error checks:
    #     Missing properties file stops the run before any test can use the wrong CSV or log.
    properties_path = Path(path).resolve()                                            # Normalize for logging.
    if not properties_path.exists():                                                  # Error check: config file exists.
        raise SystemExit(f"Properties file does not exist: {properties_path}")

    values = {}                                                                       # Parsed key/value settings.
    with properties_path.open("r", encoding="utf-8") as handle:                       # Read text config.
        for line in handle:                                                           # Process one property line.
            trimmed = line.strip()                                                    # Ignore surrounding whitespace.
            if not trimmed or trimmed.startswith(("#", ";")):                         # Skip blank/comment lines.
                continue
            key, separator, value = trimmed.partition("=")                            # Split key from value.
            if separator:                                                             # Ignore malformed lines.
                values[key.strip()] = value.strip().strip('"')                        # Store unquoted value.
    return properties_path, values                                                     # Return source path and settings.


def resolve_config_path(value, base_dir):
    # Testing algorithm:
    #   What we test:
    #     Relative paths from properties resolve like launcher paths: relative to a base folder.
    #   Success:
    #     Absolute paths stay absolute; relative paths become full paths for logs and diagnostics.
    #   Error checks:
    #     Callers validate existence when the resolved path must already exist.
    path = Path(value)                         # Convert property text to a path object.
    if path.is_absolute():                     # Absolute paths are already fully specified.
        return path
    return (base_dir / path).resolve()         # Resolve relative to the properties/log base directory.


def load_regression_config(args):
    # Testing algorithm:
    #   What we test:
    #     The suite can initialize from app-style properties and produce exact resolved paths.
    #   Success:
    #     logDir, csvFile, diagnosticLogFile, and learning-path-name become one immutable config.
    #   Error checks:
    #     Missing properties file fails in load_properties; missing CSV fails in setUp.
    properties_path, properties = load_properties(args.properties)                    # Load app settings.
    log_dir = resolve_config_path(properties.get("logDir", "."), properties_path.parent)  # Resolve log dir.
    csv_path = (
        Path(args.csv).resolve()                                                      # CLI CSV override wins.
        if args.csv
        else resolve_config_path(properties.get("csvFile", LOG_FILE_NAME), log_dir)   # Otherwise use property.
    )
    diagnostic_log_file = properties.get(
        "diagnosticLogFile",                                                         # Preferred log property.
        properties.get("logFile", DIAGNOSTIC_LOG_FILE_NAME),                         # Backward-compatible name.
    )
    diagnostic_log_path = resolve_config_path(diagnostic_log_file, log_dir)           # Log beside CSV by default.
    return RegressionConfig(
        properties_path=properties_path,                                              # Proves which config was used.
        learning_path_name=properties.get("learning-path-name", "LearningClock"),     # App display name.
        log_dir=log_dir,                                                              # Source CSV/log directory.
        csv_path=csv_path,                                                            # Source CSV input path.
        diagnostic_log_path=diagnostic_log_path,                                      # Shared test/store log.
    )


def reset_regression_log(config):
    # Testing algorithm:
    #   What we test:
    #     Each regression run starts with a clean diagnostic log for unambiguous evidence.
    #   Success:
    #     The configured log directory exists and the configured log file starts empty.
    #   Error checks:
    #     Filesystem errors should stop the run because logs are part of the regression evidence.
    config.diagnostic_log_path.parent.mkdir(parents=True, exist_ok=True)       # Ensure log directory exists.
    config.diagnostic_log_path.write_text("", encoding="utf-8")                # Clear stale evidence.


def write_regression_start_log(config, unittest_args):
    # Testing algorithm:
    #   What we test:
    #     The first diagnostic log lines must prove which inputs the test actually used.
    #   Success:
    #     The log starts with full paths for properties, CSV, diagnostic log, and selected tests.
    #   Error checks:
    #     If the log cannot be opened, the run fails before CsvStore can produce ambiguous output.
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")                  # One timestamp for the header.
    lines = [
        f"[{timestamp}] Regression test started",                             # Mark the beginning of this run.
        f"[{timestamp}] properties_path={config.properties_path}",             # Full config file path.
        f"[{timestamp}] learning_path_name={config.learning_path_name}",       # Learning path passed to CsvStore.
        f"[{timestamp}] log_dir={config.log_dir}",                             # Resolved log directory.
        f"[{timestamp}] csv_path={config.csv_path}",                           # Resolved CSV input path.
        f"[{timestamp}] diagnostic_log_path={config.diagnostic_log_path}",     # Shared diagnostic log path.
        f"[{timestamp}] unittest_args={unittest_args or '<all tests>'}",       # Selected tests or full suite.
    ]
    with config.diagnostic_log_path.open("a", encoding="utf-8") as handle:     # Append to clean log.
        handle.write("\n".join(lines))                                         # Write evidence lines.
        handle.write("\n")                                                     # End with newline for CsvStore logs.


def normalize_unittest_args(unittest_args):
    # Testing algorithm:
    #   What we test:
    #     Human-friendly test indexes must become unittest-compatible method selectors.
    #   Success:
    #     test1/test2/test3/test4 map to exactly one test, while other unittest args pass through.
    #   Error checks:
    #     Unknown selectors are left to unittest so it can report the invalid test name.
    if not unittest_args:                                              # No selector means unittest should run the full regression suite.
        return unittest_args
    return [TEST_ALIASES.get(arg, arg) for arg in unittest_args]       # Let test1 focus one test.


if __name__ == "__main__":
    # Testing algorithm:
    #   What we test:
    #     Main must configure logging before unittest executes any CsvStore behavior.
    #   Success:
    #     The diagnostic log begins with resolved parameters, then CsvStore appends its own logs.
    #   Error checks:
    #     Bad properties paths or log write failures stop the run before ambiguous tests execute.
    parsed_args, remaining_args = parse_test_args(sys.argv[1:])       # Read command-line test inputs.
    REGRESSION_CONFIG = load_regression_config(parsed_args)           # Store app-like settings for setUp.
    remaining_args = normalize_unittest_args(remaining_args)          # Translate test1/test2 shortcuts.
    reset_regression_log(REGRESSION_CONFIG)                           # Start each run with current parameters.
    write_regression_start_log(REGRESSION_CONFIG, remaining_args)     # Prove which files this run uses.
    unittest.main(argv=[sys.argv[0], *remaining_args])                # Start unittest with only unittest args.
