# =============================================================================
# File Name : csv_store.py
# Artifact  : LearningClock - CSV Persistence
# Author    : javaboy-vk
# Date      : 2026-06-06
# Version   : v0.1.0
# Purpose:
#   Provides CSV read, write, normalization, total calculation, and emergency
#   session recovery for LearningClock.
#
# Persistence call tree:
#   CsvStore.__init__(log_dir, learning_path_name)
#   |-- create log directory
#   |-- set main CSV path: learning_time_log.csv
#   `-- set diagnostic log path: learning_clock_debug.log
#
#   LearningClock shutdown / regression test save path
#   `-- CsvStore.save_session_summary(session_row)
#       |-- write_diagnostic_log("Save started ...")
#       |-- read_existing_session_rows()
#       |   |-- open learning_time_log.csv when it exists
#       |   |-- skip stale TOTAL rows
#       |   |-- normalize_existing_row(row)
#       |   |   |-- normalize_csv_date_value(row["date"])
#       |   |   |-- copy legacy document_in_diavgeia into update_diavgeia
#       |   |   |-- fill missing activity durations with 00:00:00
#       |   |   |-- fill missing pages_read with 0
#       |   |   `-- recalculate_row_total(row) when total is missing
#       |   `-- write_diagnostic_log("Main CSV read completed ...")
#       |-- read_emergency_session_rows()
#       |   |-- find learning_time_log_emergency_*.csv files
#       |   |-- normalize_existing_row(row)
#       |   |-- has_session_data(normalized_row)
#       |   `-- write_diagnostic_log("Emergency CSV scan completed ...")
#       |-- has_session_data(session_row)
#       |   |-- parse_duration(session_row["total"])
#       |   `-- check pages_read when total duration is zero
#       |-- append current session row when it has data
#       |-- merge recovered emergency rows
#       |-- create_total_row(existing_rows)
#       |   |-- parse_duration(activity_duration)
#       |   |-- parse_duration(row["total"])
#       |   |-- sum pages_read
#       |   `-- format_seconds(total_seconds)
#       |-- rewrite learning_time_log.csv
#       |   |-- csv.DictWriter(... FIELDNAMES ...)
#       |   |-- writer.writeheader()
#       |   |-- writer.writerows(session rows)
#       |   `-- writer.writerow(TOTAL row)
#       |-- mark_emergency_files_merged(emergency_files)
#       `-- write_diagnostic_log("Save completed successfully.")
#
#   LearningClock emergency save path
#   `-- CsvStore.save_emergency_session_file(session_row, session_end, error)
#       |-- build learning_time_log_emergency_YYYYMMDD_HHMMSS.csv path
#       |-- csv.DictWriter(... FIELDNAMES ...)
#       |-- writer.writeheader()
#       |-- writer.writerow(session_row)
#       `-- write_diagnostic_log("Emergency session file created ...")
#
#   Row construction path
#   `-- CsvStore.create_session_row(session_start, session_end, activity_seconds, pages_read)
#       |-- format_csv_date(session_end)
#       |-- format_seconds(sum(activity_seconds.values()))
#       |-- map ACTIVITIES through ACTIVITY_TO_FIELD
#       `-- format_seconds(activity_seconds.get(activity, 0))
# =============================================================================

from __future__ import annotations

import csv
import traceback
from datetime import datetime
from pathlib import Path

# Data model:
#   What this defines:
#     The user-facing activity names tracked by the timer and persisted into the CSV.
#   Success:
#     Every activity has a matching CSV field in ACTIVITY_TO_FIELD.
#   Error checks:
#     Tests should fail if a new activity is added without a matching field mapping.
ACTIVITIES = [
    "Reading",                  # Time spent reading source material.
    "Outlining",                # Time spent structuring notes or plans.
    "Memorizing",               # Time spent memorizing or drilling.
    "Experimenting",            # Time spent testing ideas in practice.
    "Audiobook",                # Time spent listening to study material.
    "Update Diavgeia",          # Time spent documenting the learning path.
    "Promote stable concept",   # Time spent promoting stable concepts.
]

# File and formatting contract:
#   What this defines:
#     The stable filenames and date formats shared by the app, tests, launcher, and reports.
#   Success:
#     The main CSV, emergency CSVs, diagnostic log, and date values use predictable names/formats.
#   Error checks:
#     Regression tests catch accidental CSV format drift and date-normalization regressions.
LOG_FILE_NAME = "learning_time_log.csv"                         # Main persisted session CSV.
EMERGENCY_FILE_PREFIX = "learning_time_log_emergency_"           # Prefix for fallback one-session CSVs.
DIAGNOSTIC_LOG_FILE_NAME = "learning_clock_debug.log"            # Diagnostic log beside the CSV.
CSV_DATE_FORMAT = "%Y-%m-%d"                                     # Canonical persisted date format.
CSV_DATE_FORMAT_DESCRIPTION = "YYYY-MM-DD"                       # Human-readable date format label.
LEGACY_CSV_DATE_FORMATS = [
    "%Y-%m-%d",                                                   # Current canonical format.
    "%m/%d/%Y",                                                   # Legacy US format with four-digit year.
    "%m/%d/%y",                                                   # Legacy US format with two-digit year.
    "%m-%d-%Y",                                                   # Legacy dashed US format.
    "%m-%d-%y",                                                   # Legacy dashed US format with two-digit year.
]

FIELDNAMES = [
    "date",                                                       # Session date or TOTAL marker.
    "learning_path",                                              # Learning path displayed in the app.
    "session_start",                                              # Session start time.
    "session_end",                                                # Session end time.
    "reading",                                                    # Reading duration.
    "outlining",                                                  # Outlining duration.
    "memorizing",                                                 # Memorizing duration.
    "experimenting",                                              # Experimenting duration.
    "audiobook",                                                  # Audiobook duration.
    "update_diavgeia",                                            # Documentation duration.
    "promote_stable_concept",                                     # Stable-concept promotion duration.
    "pages_read",                                                 # Pages read during the session.
    "total",                                                      # Session or aggregate total duration.
]

ACTIVITY_TO_FIELD = {
    "Reading": "reading",                                         # Map UI activity to CSV column.
    "Outlining": "outlining",                                     # Map UI activity to CSV column.
    "Memorizing": "memorizing",                                   # Map UI activity to CSV column.
    "Experimenting": "experimenting",                             # Map UI activity to CSV column.
    "Audiobook": "audiobook",                                     # Map UI activity to CSV column.
    "Update Diavgeia": "update_diavgeia",                         # Map UI activity to CSV column.
    "Promote stable concept": "promote_stable_concept",           # Map UI activity to CSV column.
}

LEGACY_FIELD_MAPPINGS = {
    "document_in_diavgeia": "update_diavgeia",                    # Preserve older CSV column name.
}

# Data conversion:
#   What these functions do:
#     Convert between integer seconds and HH:MM:SS duration text used by the UI and CSV.
#   Success:
#     Seconds format consistently, and malformed persisted duration values safely parse as zero.
#   Error handling:
#     format_seconds rejects non-integer-like values; parse_duration treats unreadable values as zero.
def format_seconds(seconds):

    seconds = int(seconds)                                                # Normalize integer-like input.
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"  # Render HH:MM:SS.


def parse_duration(duration):

    try:
        hours, minutes, seconds = duration.split(":")                     # Split duration components.
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)       # Convert to total seconds.
    except (AttributeError, ValueError):
        return 0                                                          # Bad duration values count as zero.

# Operational algorithm:
#   What this class does:
#     Owns all CSV persistence, CSV normalization, total-row math, and diagnostic logging.
#   Success:
#     The app can read existing rows, append valid sessions, recover emergency rows, and write
#     one clean CSV with a final recalculated TOTAL row.
#   Error handling:
#     Diagnostic logging records recoverable conditions, and emergency-save helpers provide a
#     fallback when normal persistence fails.
class CsvStore:

    learning_path_name: str
    log_dir: Path
    log_file: Path
    diagnostic_log_file: Path

    # Operational algorithm:
    #   What this method does:
    #     Builds the file paths used by the store for one LearningClock run.
    #   Success:
    #     The log directory exists and the store knows the main CSV and diagnostic log paths.
    #   Error handling:
    #     Directory creation errors propagate because the app cannot persist without the log folder.
    def __init__(self, log_dir: str | Path, learning_path_name: str):

        self.learning_path_name = learning_path_name                         # Persisted learning path label.
        self.log_dir = Path(log_dir)                                         # Directory for CSV and diagnostic logs.
        self.log_dir.mkdir(parents=True, exist_ok=True)                      # Ensure persistence directory exists.
        self.log_file = self.log_dir / LOG_FILE_NAME                         # Main CSV file path.
        self.diagnostic_log_file = self.log_dir / DIAGNOSTIC_LOG_FILE_NAME   # Diagnostic log file path.

    # Operational algorithm:
    #   What this method does:
    #     Appends one diagnostic entry, plus an optional exception traceback, to the debug log.
    #   Success:
    #     The log contains timestamped evidence for app/test troubleshooting.
    #   Error handling:
    #     Logging failures are swallowed so diagnostic output never breaks timer operation.
    def write_diagnostic_log(self, message, exc=None):

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")              # Timestamp this diagnostic event.
            lines = [f"[{timestamp}] {message}"]                                  # Start with the caller's message.
            if exc is not None:                                                   # Include traceback when supplied.
                lines.extend(traceback.format_exception(type(exc), exc, exc.__traceback__))
            with self.diagnostic_log_file.open("a", encoding="utf-8") as log:     # Append to the diagnostic log.
                log.write("\n".join(line.rstrip() for line in lines))             # Strip traceback line endings.
                log.write("\n")                                                   # End each event cleanly.
        except Exception:
            pass                                                                  # Logging must never break the timer.

    # Operational algorithm:
    #   What this method does:
    #     Converts the current session state into one persisted CSV session row.
    #   Success:
    #     The returned row contains every current CSV field and a total equal to activity seconds.
    #   Error handling:
    #     Missing activity keys default to zero so incomplete activity dictionaries remain safe.
    def create_session_row(
        self,
        session_start: datetime,
        session_end: datetime,
        activity_seconds: dict[str, int],
        pages_read: int,
    ):

        total_seconds = sum(activity_seconds.values())                            # Sum all tracked activity time.

        row = {
            "date": self.format_csv_date(session_end),                            # Persist canonical session date.
            "learning_path": self.learning_path_name,                             # Persist the current learning path.
            "session_start": session_start.strftime("%H:%M:%S"),                  # Persist start time.
            "session_end": session_end.strftime("%H:%M:%S"),                      # Persist end time.
            "pages_read": str(pages_read),                                        # CSV stores pages as text.
            "total": format_seconds(total_seconds),                               # Persist total duration.
        }

        for activity, field_name in ACTIVITY_TO_FIELD.items():                    # Fill each activity column.
            row[field_name] = format_seconds(activity_seconds.get(activity, 0))   # Missing activity means zero.

        return row                                                                # Return a complete session row.

    # Operational algorithm:
    #   What this method does:
    #     Persists the current session plus any recovered emergency rows into the main CSV.
    #   Success:
    #     The main CSV contains all session rows, no duplicate old TOTAL row, and one final
    #     recalculated TOTAL row.
    #   Error handling:
    #     Empty sessions are skipped, empty files are not written, and emergency files are marked
    #     merged only after the main CSV write succeeds.
    def save_session_summary(self, session_row):

        self.write_diagnostic_log(
            f"Save started | session_end={session_row.get('session_end')} | "
            f"log_file={self.log_file}"                                      # Record target CSV path.
        )

        existing_rows = self.read_existing_session_rows()                     # Load normalized main CSV rows.
        emergency_rows, emergency_files = self.read_emergency_session_rows()  # Load recoverable emergency rows.

        self.write_diagnostic_log(
            f"Rows loaded | existing_rows={len(existing_rows)} | "
            f"emergency_rows={len(emergency_rows)} | emergency_files={len(emergency_files)}"  # Record input counts.
        )

        has_data = self.has_session_data(session_row)                         # Decide whether current row is useful.
        self.write_diagnostic_log(
            "Session row created | "                                          # Record the row about to be considered.
            f"date={session_row.get('date')} | "
            f"start={session_row.get('session_start')} | "
            f"end={session_row.get('session_end')} | "
            f"reading={session_row.get('reading')} | "
            f"outlining={session_row.get('outlining')} | "
            f"memorizing={session_row.get('memorizing')} | "
            f"experimenting={session_row.get('experimenting')} | "
            f"audiobook={session_row.get('audiobook')} | "
            f"update_diavgeia={session_row.get('update_diavgeia')} | "
            f"promote_stable_concept={session_row.get('promote_stable_concept')} | "
            f"pages_read={session_row.get('pages_read')} | "
            f"total={session_row.get('total')} | "
            f"has_data={has_data}"
        )

        if has_data:                                                           # Only persist meaningful sessions.
            existing_rows.append(session_row)                                  # Add current session to existing rows.
        else:
            self.write_diagnostic_log("Session row skipped because it had no time or pages.")  # Explain skipped row.

        existing_rows.extend(emergency_rows)                                   # Merge recovered emergency rows.

        if not existing_rows:                                                  # Avoid creating an empty CSV file.
            self.write_diagnostic_log("Save skipped because there were no rows to write.")  # Explain skipped save.
            return False                                                       # Caller can tell nothing was written.

        total_row = self.create_total_row(existing_rows)                       # Recalculate aggregate from sessions.
        rows_to_write = len(existing_rows) + 1                                 # Include final TOTAL row.

        self.write_diagnostic_log(
            f"Writing CSV | rows_to_write_including_total={rows_to_write} | "
            f"total={total_row.get('total')} | pages_total={total_row.get('pages_read')}"  # Record output summary.
        )

        with self.log_file.open("w", newline="", encoding="utf-8") as f:       # Rewrite the main CSV atomically enough for this app.
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")  # Enforce current schema.
            writer.writeheader()                                               # Write one header row.
            writer.writerows(existing_rows)                                    # Write session rows only.
            writer.writerow(total_row)                                         # Write exactly one final TOTAL row.

        self.mark_emergency_files_merged(emergency_files)                      # Mark emergency files after successful rewrite.
        self.write_diagnostic_log("Save completed successfully.")              # Record success.
        return True                                                            # Caller can tell rows were written.

    # Operational algorithm:
    #   What this method does:
    #     Decides whether a session row contains useful persisted data.
    #   Success:
    #     Rows with time or pages are saved; completely empty rows are skipped.
    #   Error handling:
    #     Bad page values are treated as zero so malformed input does not crash shutdown.
    def has_session_data(self, session_row):

        if parse_duration(session_row.get("total", "00:00:00")) > 0:           # Any positive time is useful data.
            return True                                                        # Save time-bearing rows.
        try:
            return int(session_row.get("pages_read", 0)) > 0                   # Pages also make a row worth saving.
        except (TypeError, ValueError):
            return False                                                       # Non-numeric pages count as no pages.

    # Operational algorithm:
    #   What this method does:
    #     Reads existing main CSV rows and normalizes them into the current schema.
    #   Success:
    #     Returns session rows only; old TOTAL rows are ignored and recalculated later.
    #   Error handling:
    #     Missing CSV is normal for first run and returns an empty row list.
    def read_existing_session_rows(self):

        if not self.log_file.exists():                                        # First run may not have a CSV yet.
            self.write_diagnostic_log(f"Main CSV does not exist yet | log_file={self.log_file}")  # Record empty source.
            return []                                                         # No rows to merge.

        rows = []                                                             # Accumulate normalized session rows.
        with self.log_file.open("r", newline="", encoding="utf-8") as f:      # Read CSV with newline-safe mode.
            reader = csv.DictReader(f)                                        # Parse rows by header name.
            for row in reader:                                                # Inspect each persisted row.
                if row.get("date") == "TOTAL":                                # Ignore stale summary rows.
                    continue
                rows.append(self.normalize_existing_row(row))                 # Normalize legacy/current row.
        self.write_diagnostic_log(f"Main CSV read completed | session_rows={len(rows)}")  # Record read result.
        return rows                                                           # Return session rows only.

    # Operational algorithm:
    #   What this method does:
    #     Reads emergency CSV files created when normal shutdown persistence failed.
    #   Success:
    #     Valid emergency rows are normalized and returned with the files that supplied them.
    #   Error handling:
    #     A bad emergency file is logged and skipped so other recoverable files can still merge.
    def read_emergency_session_rows(self):

        rows = []                                                             # Recovered emergency session rows.
        files = []                                                            # Emergency files that should be marked merged.

        for emergency_file in sorted(self.log_dir.glob(f"{EMERGENCY_FILE_PREFIX}*.csv")):  # Process deterministic order.
            try:
                with emergency_file.open("r", newline="", encoding="utf-8") as f:  # Open one emergency CSV.
                    reader = csv.DictReader(f)                                     # Parse by header name.
                    for row in reader:                                             # Inspect each emergency row.
                        if row.get("date") == "TOTAL":                             # Emergency TOTAL rows are not inputs.
                            continue
                        normalized_row = self.normalize_existing_row(row)          # Convert to current schema.
                        if self.has_session_data(normalized_row):                  # Keep only useful rows.
                            rows.append(normalized_row)
                files.append(emergency_file)                                      # Mark this source file as consumed.
            except OSError as exc:
                self.write_diagnostic_log(f"Emergency CSV read failed | file={emergency_file}", exc)  # Preserve failure evidence.
                continue                                                          # Continue with other emergency files.

        summary = (
            f"Emergency CSV scan completed | rows={len(rows)} "
            f"| files={len(files)}"                                               # Summarize recovery result.
        )
        self.write_diagnostic_log(summary)                                        # Record recovery summary.
        return rows, files                                                        # Return rows and source files.

    # Operational algorithm:
    #   What this method does:
    #     Marks emergency files as merged after their rows have been persisted to the main CSV.
    #   Success:
    #     Each consumed emergency file receives a .merged suffix.
    #   Error handling:
    #     Rename/delete failures are ignored because the main CSV write has already succeeded.
    def mark_emergency_files_merged(self, emergency_files):

        for emergency_file in emergency_files:                                  # Process each consumed emergency file.
            merged_file = emergency_file.with_suffix(emergency_file.suffix + ".merged")  # Build marker filename.
            try:
                if merged_file.exists():                                        # Remove stale marker before rename.
                    merged_file.unlink()
                emergency_file.rename(merged_file)                              # Mark source as merged.
            except OSError:
                pass                                                            # Do not fail after successful CSV write.

    # Operational algorithm:
    #   What this method does:
    #     Converts a persisted row from any supported CSV version into the current schema.
    #   Success:
    #     The returned row contains every current field, canonical date text, and complete duration columns.
    #   Error handling:
    #     Missing fields are filled with safe defaults; missing totals are recalculated from activity columns.
    def normalize_existing_row(self, row):

        normalized_row = {field: row.get(field, "") for field in FIELDNAMES}   # Copy only current schema fields.
        normalized_row["date"] = self.normalize_csv_date_value(normalized_row.get("date", ""))  # Canonicalize date.

        for legacy_field, current_field in LEGACY_FIELD_MAPPINGS.items():      # Preserve known old column names.
            legacy_value = row.get(legacy_field, "")                           # Read old column value.
            current_value = normalized_row.get(current_field, "")              # Check whether current column is empty.
            if legacy_value and not current_value:                             # Use legacy value only when needed.
                normalized_row[current_field] = legacy_value                   # Move old value into current field.

        for field in ACTIVITY_TO_FIELD.values():                               # Ensure each activity field exists.
            if not normalized_row.get(field):                                  # Missing/blank duration should be zero.
                normalized_row[field] = "00:00:00"

        if not normalized_row.get("pages_read"):                               # Missing pages should not break totals.
            normalized_row["pages_read"] = "0"
        if not normalized_row.get("total"):                                    # Older rows may not have total column.
            normalized_row["total"] = self.recalculate_row_total(normalized_row)  # Rebuild total from activities.

        return normalized_row                                                  # Return current-schema row.

    # Operational algorithm:
    #   What this method does:
    #     Aggregates session rows into the synthetic final TOTAL row.
    #   Success:
    #     Activity totals, page totals, and grand duration total equal the sum of persisted sessions.
    #   Error handling:
    #     Bad page values count as zero; bad durations parse as zero through parse_duration.
    def create_total_row(self, rows):

        total_seconds_by_field = {field_name: 0 for field_name in ACTIVITY_TO_FIELD.values()}  # Accumulate per activity.
        grand_total = 0                                                                        # Accumulate row totals.
        pages_total = 0                                                                        # Accumulate pages.

        for row in rows:                                                                       # Aggregate each session row.
            for field_name in ACTIVITY_TO_FIELD.values():                                      # Sum each activity column.
                duration = row.get(field_name, "00:00:00")                                     # Missing duration is zero.
                total_seconds_by_field[field_name] += parse_duration(duration)                 # Add parsed seconds.
            grand_total += parse_duration(row.get("total", "00:00:00"))                        # Add row total seconds.
            try:
                pages_total += int(row.get("pages_read", "0") or 0)                            # Add numeric page count.
            except ValueError:
                pages_total += 0                                                               # Bad page count contributes zero.

        total_row = {
            "date": "TOTAL",                                                                   # Mark synthetic summary row.
            "learning_path": "",                                                               # Summary row has no path label.
            "session_start": "",                                                               # Summary row has no start time.
            "session_end": "",                                                                 # Summary row has no end time.
            "pages_read": str(pages_total),                                                     # Persist aggregate pages.
            "total": format_seconds(grand_total),                                              # Persist aggregate duration.
        }

        for field_name, seconds in total_seconds_by_field.items():                              # Write activity totals.
            total_row[field_name] = format_seconds(seconds)

        return total_row                                                                        # Return complete TOTAL row.

    # Operational algorithm:
    #   What this method does:
    #     Recomputes a row total from all activity duration fields.
    #   Success:
    #     The result is an HH:MM:SS duration equal to the sum of activity durations.
    #   Error handling:
    #     Missing or malformed activity durations parse as zero.
    def recalculate_row_total(self, row):

        return format_seconds(
            sum(
                parse_duration(row.get(field_name, "00:00:00"))                  # Convert each activity to seconds.
                for field_name in ACTIVITY_TO_FIELD.values()                    # Include every current activity column.
            )
        )                                                                        # Return formatted duration text.

    # Operational algorithm:
    #   What this method does:
    #     Converts supported persisted date strings to the canonical CSV date format.
    #   Success:
    #     Valid legacy/current dates return as YYYY-MM-DD, while TOTAL and blank values pass through.
    #   Error handling:
    #     Unsupported date text is preserved and logged instead of crashing CSV reads.
    def normalize_csv_date_value(self, value):

        raw_value = (value or "").strip()                                      # Normalize empty/None and whitespace.

        if not raw_value or raw_value == "TOTAL":                              # Blank and summary markers are not dates.
            return raw_value                                                   # Preserve special values unchanged.

        for date_format in LEGACY_CSV_DATE_FORMATS:                            # Try current and supported legacy formats.
            try:
                parsed_date = datetime.strptime(raw_value, date_format).date()  # Parse raw date text.
                normalized_value = parsed_date.strftime(CSV_DATE_FORMAT)       # Convert to canonical format.
                if normalized_value != raw_value:                              # Log only actual changes.
                    self.write_diagnostic_log(
                        "CSV date normalized | "
                        f"original={raw_value} | normalized={normalized_value} | "
                        f"canonical_format={CSV_DATE_FORMAT_DESCRIPTION}"
                    )
                return normalized_value                                        # Return canonical date.
            except ValueError:
                continue                                                       # Try the next supported date format.

        self.write_diagnostic_log(
            "CSV date could not be normalized; preserving original value | "
            f"value={raw_value} | canonical_format={CSV_DATE_FORMAT_DESCRIPTION}"
        )                                                                      # Preserve evidence for manual cleanup.
        return raw_value                                                       # Do not destroy unknown date text.

    # Operational algorithm:
    #   What this method does:
    #     Writes one fallback emergency CSV when normal main CSV persistence fails.
    #   Success:
    #     The current session row is preserved in a timestamped emergency file for later merge.
    #   Error handling:
    #     Write errors propagate to the caller, which can log or surface the emergency-save failure.
    def save_emergency_session_file(self, session_row, session_end, error):

        emergency_file = self.log_dir / (
            EMERGENCY_FILE_PREFIX                                              # Prefix identifies recovery files.
            + session_end.strftime("%Y%m%d_%H%M%S")                            # Timestamp keeps emergency files unique.
            + ".csv"                                                           # Emergency files are still CSVs.
        )

        with emergency_file.open("w", newline="", encoding="utf-8") as f:      # Write the fallback CSV.
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")  # Use current schema.
            writer.writeheader()                                               # Include header for recovery reader.
            writer.writerow(session_row)                                       # Preserve only this session row.

        self.write_diagnostic_log(
            f"Emergency session file created | file={emergency_file} | "
            f"original_error={error}"                                          # Keep the original save failure visible.
        )
        return emergency_file                                                  # Return file path for caller/tests.

    # Operational algorithm:
    #   What this method does:
    #     Formats datetime/date-like values into the canonical CSV date string.
    #   Success:
    #     Datetime values and YYYY-MM-DD strings return as YYYY-MM-DD.
    #   Error handling:
    #     Unsupported values raise ValueError so callers/tests notice invalid date input.
    @staticmethod
    def format_csv_date(value):

        if isinstance(value, datetime):                                       # Datetime is already structured.
            return value.strftime(CSV_DATE_FORMAT)                            # Format directly.
        return datetime.strptime(str(value), CSV_DATE_FORMAT).strftime(CSV_DATE_FORMAT)  # Validate and normalize text.
