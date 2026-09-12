# =============================================================================
# File Name : reporting.py
# Artifact  : LearningClock - Cross-Clock Category Reporting
# Author    : javaboy-vk
# Date      : 2026-09-11
# Version   : v1.2.0
# Purpose:
#   Resolves inclusive local-date periods, aggregates LearningClock CSV data,
#   and returns file/row diagnostics for every skipped or invalid input.
# =============================================================================

from __future__ import annotations

import csv
import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from learningclock.configuration import LEARNING_PATH_DIRECTORY_NAME, ConfiguredClock
from learningclock.csv_store import (
    ACTIVITIES,
    ACTIVITY_TO_FIELD,
    LEGACY_CSV_DATE_FORMATS,
    LEGACY_FIELD_MAPPINGS,
    LOG_FILE_NAME,
    format_seconds,
)
from learningclock.telemetry import REPORT_COMPLETED, REPORT_INPUT_SKIPPED

PERIOD_OPTIONS = ("This week", "Last week", "This month", "Define range")


@dataclass(frozen=True, slots=True)
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("Start date cannot be after end date.")


@dataclass(frozen=True, slots=True)
class ReportIssue:
    clock_name: str
    source_path: Path
    input_kind: str
    reason: str
    message: str
    row_number: int | None = None
    column: str | None = None
    value: str | None = None


@dataclass(frozen=True, slots=True)
class ReportResult:
    date_range: DateRange
    totals: tuple[tuple[str, int], ...]
    total_seconds: int
    clock_count: int
    row_count: int
    warning_count: int
    warnings: tuple[str, ...]
    issues: tuple[ReportIssue, ...]


def resolve_date_range(
    period: str,
    *,
    today: date | None = None,
    custom_start: date | None = None,
    custom_end: date | None = None,
) -> DateRange:
    current = today or date.today()
    if period == "This week":
        return DateRange(current - timedelta(days=current.weekday()), current)
    if period == "Last week":
        this_monday = current - timedelta(days=current.weekday())
        return DateRange(this_monday - timedelta(days=7), this_monday - timedelta(days=1))
    if period == "This month":
        return DateRange(current.replace(day=1), current)
    if period == "Define range":
        if custom_start is None or custom_end is None:
            raise ValueError("Select both a start date and an end date.")
        return DateRange(custom_start, custom_end)
    raise ValueError(f"Unknown report period: {period}")


def parse_csv_date(value: str | None) -> date | None:
    text = (value or "").strip()
    if not text or text.casefold() == "total":
        return None
    from datetime import datetime

    for date_format in LEGACY_CSV_DATE_FORMATS:
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def parse_duration_strict(value: str | None) -> int | None:
    text = (value or "").strip()
    if not text:
        return 0
    parts = text.split(":")
    if len(parts) != 3:
        return None
    try:
        hours, minutes, seconds = (int(part) for part in parts)
    except ValueError:
        return None
    if hours < 0 or not 0 <= minutes < 60 or not 0 <= seconds < 60:
        return None
    return hours * 3600 + minutes * 60 + seconds


def _legacy_fields_for(current_field: str) -> tuple[str, ...]:
    return tuple(
        legacy for legacy, current in LEGACY_FIELD_MAPPINGS.items() if current == current_field
    )


def aggregate_clock_time(
    clocks: Iterable[ConfiguredClock], date_range: DateRange, *, logger: Any | None = None
) -> ReportResult:
    totals = {activity: 0 for activity in ACTIVITIES}
    issues: list[ReportIssue] = []
    included_clock_count = 0
    included_row_count = 0
    seen_log_dirs: set[str] = set()

    def warn(
        message: str,
        clock_name: str,
        input_kind: str,
        reason: str,
        source_path: Path,
        *,
        row_number: int | None = None,
        column: str | None = None,
        value: str | None = None,
    ) -> None:
        issue = ReportIssue(
            clock_name=clock_name,
            source_path=source_path.resolve(),
            input_kind=input_kind,
            reason=reason,
            message=message,
            row_number=row_number,
            column=column,
            value=value,
        )
        issues.append(issue)
        if logger is not None:
            logger.event(
                REPORT_INPUT_SKIPPED,
                clock_name=clock_name,
                input_kind=input_kind,
                reason=reason,
                source_path=issue.source_path,
                row_number=row_number,
                column=column,
            )

    for clock in clocks:
        log_key = os.path.normcase(str(clock.log_dir.resolve()))
        if log_key in seen_log_dirs:
            warn(
                f"Skipped duplicate source for {clock.display_name}.",
                clock.display_name,
                "clock",
                "duplicate log directory",
                clock.configuration_path,
                column="logDir",
                value=str(clock.log_dir),
            )
            continue
        seen_log_dirs.add(log_key)
        learning_path_dir = clock.log_dir / LEARNING_PATH_DIRECTORY_NAME
        csv_path = learning_path_dir / LOG_FILE_NAME
        if not clock.log_dir.is_dir():
            warn(
                f"Skipped unavailable clock {clock.display_name}.",
                clock.display_name,
                "clock",
                "log directory unavailable",
                clock.configuration_path,
                column="logDir",
                value=str(clock.log_dir),
            )
            continue
        if not csv_path.is_file():
            warn(
                f"No time log yet for {clock.display_name}.",
                clock.display_name,
                "CSV",
                "time log missing",
                csv_path,
            )
            continue

        clock_rows = 0
        try:
            with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    warn(
                        f"Skipped empty time log for {clock.display_name}.",
                        clock.display_name,
                        "CSV",
                        "empty file",
                        csv_path,
                    )
                    continue
                for row_number, row in enumerate(reader, start=2):
                    raw_date = (row.get("date") or "").strip()
                    if raw_date.casefold() == "total":
                        continue
                    session_date = parse_csv_date(raw_date)
                    if session_date is None:
                        warn(
                            f"Skipped row {row_number} with an invalid date in {clock.display_name}.",
                            clock.display_name,
                            "row",
                            f"invalid date at row {row_number}",
                            csv_path,
                            row_number=row_number,
                            column="date",
                            value=raw_date,
                        )
                        continue
                    if not date_range.start <= session_date <= date_range.end:
                        continue
                    for activity, field in ACTIVITY_TO_FIELD.items():
                        field_names = (field, *_legacy_fields_for(field))
                        for field_name in field_names:
                            value = row.get(field_name)
                            if not (value or "").strip():
                                continue
                            seconds = parse_duration_strict(value)
                            if seconds is None:
                                warn(
                                    f"Ignored an invalid duration in row {row_number} of {clock.display_name}.",
                                    clock.display_name,
                                    "duration",
                                    f"invalid duration at row {row_number}",
                                    csv_path,
                                    row_number=row_number,
                                    column=field_name,
                                    value=value,
                                )
                                continue
                            totals[activity] += seconds
                    clock_rows += 1
                    included_row_count += 1
        except (OSError, csv.Error, UnicodeError) as exc:
            warn(
                f"Skipped unreadable time log for {clock.display_name}: {type(exc).__name__}.",
                clock.display_name,
                "CSV",
                type(exc).__name__,
                csv_path,
                value=str(exc),
            )
            continue
        if clock_rows:
            included_clock_count += 1

    ordered_totals = tuple((activity, totals[activity]) for activity in ACTIVITIES)
    total_seconds = sum(seconds for _, seconds in ordered_totals)
    result = ReportResult(
        date_range=date_range,
        totals=ordered_totals,
        total_seconds=total_seconds,
        clock_count=included_clock_count,
        row_count=included_row_count,
        warning_count=len(issues),
        warnings=tuple(issue.message for issue in issues),
        issues=tuple(issues),
    )
    if logger is not None:
        logger.event(
            REPORT_COMPLETED,
            clock_count=result.clock_count,
            row_count=result.row_count,
            warning_count=result.warning_count,
            total_duration=format_seconds(result.total_seconds),
        )
    return result


def format_report_duration(seconds: int) -> str:
    return format_seconds(seconds)
