# =============================================================================
# File Name : csv_store.py
# Artifact  : LearningClock - CSV Persistence
# Author    : javaboy-vk
# Date      : 2026-06-06
# Version   : v0.1.0
# Purpose:
#   Provides CSV read, write, normalization, total calculation, and emergency
#   session recovery for LearningClock.
# =============================================================================

from __future__ import annotations

import csv
import traceback
from datetime import datetime
from pathlib import Path

ACTIVITIES = [
    "Reading",
    "Outlining",
    "Memorizing",
    "Experimenting",
    "Audiobook",
    "Update Diavgeia",
    "Promote stable concept",
]

LOG_FILE_NAME = "learning_time_log.csv"
EMERGENCY_FILE_PREFIX = "learning_time_log_emergency_"
DIAGNOSTIC_LOG_FILE_NAME = "learning_clock_debug.log"
CSV_DATE_FORMAT = "%Y-%m-%d"
CSV_DATE_FORMAT_DESCRIPTION = "YYYY-MM-DD"
LEGACY_CSV_DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%m-%d-%Y",
    "%m-%d-%y",
]

FIELDNAMES = [
    "date",
    "learning_path",
    "session_start",
    "session_end",
    "reading",
    "outlining",
    "memorizing",
    "experimenting",
    "audiobook",
    "update_diavgeia",
    "promote_stable_concept",
    "pages_read",
    "total",
]

ACTIVITY_TO_FIELD = {
    "Reading": "reading",
    "Outlining": "outlining",
    "Memorizing": "memorizing",
    "Experimenting": "experimenting",
    "Audiobook": "audiobook",
    "Update Diavgeia": "update_diavgeia",
    "Promote stable concept": "promote_stable_concept",
}

LEGACY_FIELD_MAPPINGS = {
    "document_in_diavgeia": "update_diavgeia",
}


class CsvStore:
    def __init__(self, log_dir: str | Path, learning_path_name: str):
        self.learning_path_name = learning_path_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / LOG_FILE_NAME
        self.diagnostic_log_file = self.log_dir / DIAGNOSTIC_LOG_FILE_NAME

    # Append a diagnostic message to the Learning Clock debug log.
    def write_diagnostic_log(self, message, exc=None):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines = [f"[{timestamp}] {message}"]
            if exc is not None:
                lines.extend(traceback.format_exception(type(exc), exc, exc.__traceback__))
            with self.diagnostic_log_file.open("a", encoding="utf-8") as log:
                log.write("\n".join(line.rstrip() for line in lines))
                log.write("\n")
        except Exception:
            # Logging must never break the timer itself.
            pass

    # Build the CSV row for the session ending at the supplied timestamp.
    def create_session_row(
        self,
        session_start: datetime,
        session_end: datetime,
        activity_seconds: dict[str, int],
        pages_read: int,
    ):
        total_seconds = sum(activity_seconds.values())

        row = {
            "date": self.format_csv_date(session_end),
            "learning_path": self.learning_path_name,
            "session_start": session_start.strftime("%H:%M:%S"),
            "session_end": session_end.strftime("%H:%M:%S"),
            "pages_read": str(pages_read),
            "total": self.format_seconds(total_seconds),
        }

        for activity, field_name in ACTIVITY_TO_FIELD.items():
            row[field_name] = self.format_seconds(activity_seconds.get(activity, 0))

        return row

    # Persist session rows and a recalculated TOTAL row when the window closes.
    def save_session_summary(self, session_row):
        self.write_diagnostic_log(
            f"Save started | session_end={session_row.get('session_end')} | "
            f"log_file={self.log_file}"
        )

        existing_rows = self.read_existing_session_rows()
        emergency_rows, emergency_files = self.read_emergency_session_rows()

        self.write_diagnostic_log(
            f"Rows loaded | existing_rows={len(existing_rows)} | "
            f"emergency_rows={len(emergency_rows)} | emergency_files={len(emergency_files)}"
        )

        has_data = self.has_session_data(session_row)
        self.write_diagnostic_log(
            "Session row created | "
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

        if has_data:
            existing_rows.append(session_row)
        else:
            self.write_diagnostic_log("Session row skipped because it had no time or pages.")

        existing_rows.extend(emergency_rows)

        if not existing_rows:
            self.write_diagnostic_log("Save skipped because there were no rows to write.")
            return False

        total_row = self.create_total_row(existing_rows)
        rows_to_write = len(existing_rows) + 1

        self.write_diagnostic_log(
            f"Writing CSV | rows_to_write_including_total={rows_to_write} | "
            f"total={total_row.get('total')} | pages_total={total_row.get('pages_read')}"
        )

        with self.log_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(existing_rows)
            writer.writerow(total_row)

        self.mark_emergency_files_merged(emergency_files)
        self.write_diagnostic_log("Save completed successfully.")
        return True

    # Return true when a row contains useful session data worth saving.
    def has_session_data(self, session_row):
        if self.parse_duration(session_row.get("total", "00:00:00")) > 0:
            return True
        try:
            return int(session_row.get("pages_read", 0)) > 0
        except (TypeError, ValueError):
            return False

    # Read the main CSV and return normalized session rows, excluding the TOTAL row.
    def read_existing_session_rows(self):
        if not self.log_file.exists():
            self.write_diagnostic_log(f"Main CSV does not exist yet | log_file={self.log_file}")
            return []

        rows = []
        with self.log_file.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("date") == "TOTAL":
                    continue
                rows.append(self.normalize_existing_row(row))
        self.write_diagnostic_log(f"Main CSV read completed | session_rows={len(rows)}")
        return rows

    # Read unmerged emergency CSV files created after failed normal saves.
    def read_emergency_session_rows(self):
        rows = []
        files = []

        for emergency_file in sorted(self.log_dir.glob(f"{EMERGENCY_FILE_PREFIX}*.csv")):
            try:
                with emergency_file.open("r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("date") == "TOTAL":
                            continue
                        normalized_row = self.normalize_existing_row(row)
                        if self.has_session_data(normalized_row):
                            rows.append(normalized_row)
                files.append(emergency_file)
            except OSError as exc:
                self.write_diagnostic_log(f"Emergency CSV read failed | file={emergency_file}", exc)
                continue

        summary = (
            f"Emergency CSV scan completed | rows={len(rows)} "
            f"| files={len(files)}"
        )
        self.write_diagnostic_log(summary)
        return rows, files

    # Rename recovered emergency files after their rows have been written to the main CSV.
    def mark_emergency_files_merged(self, emergency_files):
        for emergency_file in emergency_files:
            merged_file = emergency_file.with_suffix(emergency_file.suffix + ".merged")
            try:
                if merged_file.exists():
                    merged_file.unlink()
                emergency_file.rename(merged_file)
            except OSError:
                pass

    # Convert a row from any supported CSV version into the current schema.
    def normalize_existing_row(self, row):
        normalized_row = {field: row.get(field, "") for field in FIELDNAMES}
        normalized_row["date"] = self.normalize_csv_date_value(normalized_row.get("date", ""))

        for legacy_field, current_field in LEGACY_FIELD_MAPPINGS.items():
            legacy_value = row.get(legacy_field, "")
            current_value = normalized_row.get(current_field, "")
            if legacy_value and not current_value:
                normalized_row[current_field] = legacy_value

        for field in ACTIVITY_TO_FIELD.values():
            if not normalized_row.get(field):
                normalized_row[field] = "00:00:00"

        if not normalized_row.get("pages_read"):
            normalized_row["pages_read"] = "0"
        if not normalized_row.get("total"):
            normalized_row["total"] = self.recalculate_row_total(normalized_row)

        return normalized_row

    # Aggregate all session rows into the final synthetic TOTAL CSV row.
    def create_total_row(self, rows):
        total_seconds_by_field = {field_name: 0 for field_name in ACTIVITY_TO_FIELD.values()}
        grand_total = 0
        pages_total = 0

        for row in rows:
            for field_name in ACTIVITY_TO_FIELD.values():
                duration = row.get(field_name, "00:00:00")
                total_seconds_by_field[field_name] += self.parse_duration(duration)
            grand_total += self.parse_duration(row.get("total", "00:00:00"))
            try:
                pages_total += int(row.get("pages_read", "0") or 0)
            except ValueError:
                pages_total += 0

        total_row = {
            "date": "TOTAL",
            "learning_path": "",
            "session_start": "",
            "session_end": "",
            "pages_read": str(pages_total),
            "total": self.format_seconds(grand_total),
        }

        for field_name, seconds in total_seconds_by_field.items():
            total_row[field_name] = self.format_seconds(seconds)

        return total_row

    # Recompute a row total from activity fields when an older row has no total value.
    def recalculate_row_total(self, row):
        return self.format_seconds(
            sum(
                self.parse_duration(row.get(field_name, "00:00:00"))
                for field_name in ACTIVITY_TO_FIELD.values()
            )
        )

    # Normalize all persisted CSV session dates to one canonical format.
    def normalize_csv_date_value(self, value):
        raw_value = (value or "").strip()

        if not raw_value or raw_value == "TOTAL":
            return raw_value

        for date_format in LEGACY_CSV_DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(raw_value, date_format).date()
                normalized_value = parsed_date.strftime(CSV_DATE_FORMAT)
                if normalized_value != raw_value:
                    self.write_diagnostic_log(
                        "CSV date normalized | "
                        f"original={raw_value} | normalized={normalized_value} | "
                        f"canonical_format={CSV_DATE_FORMAT_DESCRIPTION}"
                    )
                return normalized_value
            except ValueError:
                continue

        self.write_diagnostic_log(
            "CSV date could not be normalized; preserving original value | "
            f"value={raw_value} | canonical_format={CSV_DATE_FORMAT_DESCRIPTION}"
        )
        return raw_value

    # Write a fallback one-session CSV when the normal main CSV cannot be saved.
    def save_emergency_session_file(self, session_row, session_end, error):
        emergency_file = self.log_dir / (
            EMERGENCY_FILE_PREFIX
            + session_end.strftime("%Y%m%d_%H%M%S")
            + ".csv"
        )

        with emergency_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
            writer.writerow(session_row)

        self.write_diagnostic_log(
            f"Emergency session file created | file={emergency_file} | "
            f"original_error={error}"
        )
        return emergency_file

    # Format a datetime or date-like value as the canonical CSV date string.
    @staticmethod
    def format_csv_date(value):
        if isinstance(value, datetime):
            return value.strftime(CSV_DATE_FORMAT)
        return datetime.strptime(str(value), CSV_DATE_FORMAT).strftime(CSV_DATE_FORMAT)

    # Format integer seconds as HH:MM:SS for display and CSV storage.
    @staticmethod
    def format_seconds(seconds):
        seconds = int(seconds)
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

    # Parse an HH:MM:SS value from CSV or UI state into seconds.
    @staticmethod
    def parse_duration(duration):
        try:
            hours, minutes, seconds = duration.split(":")
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        except (AttributeError, ValueError):
            return 0


format_seconds = CsvStore.format_seconds
parse_duration = CsvStore.parse_duration
