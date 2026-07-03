# =============================================================================
# File Name : migrate_learningpath_csv_categories.py
# Artifact  : LearningClock - External CSV Category Migration Utility
# Author    : javaboy-vk
# Date      : 2026-07-03
# Version   : v0.1.0
# Purpose:
#   Migrates LearningClock CSV files selected by launcher-style .properties files
#   to the current category schema.
#
# Migration call tree:
#   main(argv)
#   |-- parse --properties-root
#   |-- find *.properties under the properties root
#   |-- load_properties(properties_path)
#   |   `-- parse key=value launcher settings
#   |-- resolve_path(logDir, properties_path.parent)
#   |-- migrate_csv(csv_path, learning_path_name, backup_suffix)
#   |   |-- CsvStore(csv_path.parent, learning_path_name)
#   |   |-- read_existing_session_rows()
#   |   |   |-- normalize legacy dates
#   |   |   |-- map memorizing into active_recall
#   |   |   |-- map experimenting into sandbox
#   |   |   |-- fill new engineering category fields with 00:00:00
#   |   |   `-- drop stale TOTAL rows
#   |   |-- create_total_row(rows)
#   |   |-- copy original CSV to a timestamped .bak file
#   |   `-- rewrite CSV with current FIELDNAMES plus one recalculated TOTAL row
#   `-- print one SKIP or MIGRATED line per properties file
#
# Safety contract:
#   - The script never guesses CSV locations from folder names alone. It reads
#     logDir from each .properties file and appends learning_time_log.csv.
#   - The original CSV is copied beside the source file before any rewrite.
#   - Existing user rows are normalized through CsvStore so legacy compatibility
#     stays identical to the app's normal read/write behavior.
# =============================================================================

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from learningclock.csv_store import FIELDNAMES, LOG_FILE_NAME, CsvStore  # noqa: E402


# Configuration parsing:
#   What this function does:
#     Reads one Java/VBS-style launcher .properties file.
#   Success:
#     Returns trimmed key/value pairs and ignores comments or blank lines.
#   Error handling:
#     File read errors propagate because a requested migration source must be
#     readable before any CSV target can be trusted.
def load_properties(path: Path) -> dict[str, str]:

    values: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", ";")):
                continue
            key, separator, value = stripped.partition("=")
            if separator:
                values[key.strip()] = value.strip().strip('"')
    return values


# Path resolution:
#   What this function does:
#     Resolves launcher paths the same way the regression tests do.
#   Success:
#     Absolute paths stay unchanged; relative paths resolve against the
#     .properties file directory.
#   Error handling:
#     Existence checks belong to the caller because some paths are optional
#     launcher settings while logDir is mandatory for this migration.
def resolve_path(value: str, base_dir: Path) -> Path:

    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


# CSV migration:
#   What this function does:
#     Rewrites one existing LearningClock CSV into the current production schema.
#   Success:
#     The CSV contains normalized session rows and exactly one recalculated final
#     TOTAL row using FIELDNAMES from learningclock.csv_store.
#   Error handling:
#     Backup, read, normalize, or write failures propagate so the caller sees the
#     original filesystem/CSV error and does not report a false migration.
def migrate_csv(csv_path: Path, learning_path_name: str, backup_suffix: str) -> tuple[int, Path]:

    store = CsvStore(csv_path.parent, learning_path_name)
    store.log_file = csv_path  # Point CsvStore at the externally configured CSV.

    rows = store.read_existing_session_rows()  # Normalize legacy columns and remove stale TOTAL rows.
    total_row = store.create_total_row(rows)   # Recalculate summary from normalized session rows.
    backup_path = csv_path.with_name(f"{csv_path.name}.{backup_suffix}.bak")
    shutil.copy2(csv_path, backup_path)        # Preserve user data before opening the CSV for rewrite.

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(total_row)

    return len(rows), backup_path


# Command-line entry point:
#   What this function does:
#     Discovers launcher .properties files and migrates each configured CSV.
#   Success:
#     Every properties file produces a machine-readable SKIP or MIGRATED line.
#   Error handling:
#     Missing properties roots or empty property sets fail early; per-file missing
#     logDir/CSV paths are skipped so other learning paths can still migrate.
def main(argv: list[str] | None = None) -> int:

    parser = argparse.ArgumentParser(description="Migrate LearningClock CSV files to the current category schema.")
    parser.add_argument(
        "--properties-root",
        default=r"D:\LearningPath",
        help="Directory containing LearningClock .properties files.",
    )
    args = parser.parse_args(argv)

    properties_root = Path(args.properties_root)
    backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    properties_files = sorted(properties_root.glob("*.properties"))

    if not properties_files:
        raise SystemExit(f"No .properties files found under {properties_root}")

    for properties_path in properties_files:
        properties = load_properties(properties_path)                          # Read one launcher config.
        learning_path_name = properties.get("learning-path-name", properties_path.stem)  # Prefer explicit app label.
        log_dir_value = properties.get("logDir")                               # CSV directory is configured here.
        if not log_dir_value:
            print(f"SKIP\t{properties_path}\tmissing logDir")
            continue

        log_dir = resolve_path(log_dir_value, properties_path.parent)           # Match launcher relative-path behavior.
        csv_path = log_dir / LOG_FILE_NAME                                     # LearningClock always uses this CSV name.
        if not csv_path.exists():
            print(f"SKIP\t{properties_path}\tmissing CSV\t{csv_path}")
            continue

        row_count, backup_path = migrate_csv(csv_path, learning_path_name, backup_suffix)
        print(f"MIGRATED\t{learning_path_name}\trows={row_count}\tcsv={csv_path}\tbackup={backup_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
