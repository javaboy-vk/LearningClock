# =============================================================================
# File Name : provisioning.py
# Artifact  : LearningClock - New Clock Provisioning
# Author    : javaboy-vk
# Date      : 2026-09-11
# Version   : v1.2.0
# Purpose:
#   Validates and transactionally creates per-clock configuration and CSV data.
#   The vault-level Diavgeia dashboard is deployed once by release tooling.
# =============================================================================

from __future__ import annotations

import csv
import io
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learningclock.configuration import (
    LEARNING_PATH_DIRECTORY_NAME,
    ConfigurationError,
    discover_clock_configurations,
    stable_clock_id,
)
from learningclock.csv_store import FIELDNAMES, LOG_FILE_NAME
from learningclock.telemetry import CLOCK_PROVISION_FAILED, CLOCK_PROVISIONED

_INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}


@dataclass(frozen=True, slots=True)
class ProvisioningPlan:
    learning_path_name: str
    log_dir: Path
    learning_path_dir: Path
    properties_path: Path
    csv_path: Path


@dataclass(frozen=True, slots=True)
class ProvisioningResult:
    plan: ProvisioningPlan
    created_files: tuple[Path, ...]


def _canonical_path_key(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def validate_learning_path_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise ConfigurationError("Learning path name is required.")
    if name in {".", ".."} or ".." in Path(name).parts:
        raise ConfigurationError("Learning path name cannot contain path traversal.")
    if _INVALID_FILENAME.search(name) or name.endswith((" ", ".")):
        raise ConfigurationError("Learning path name contains invalid filename characters.")
    if name.casefold() in _WINDOWS_RESERVED_NAMES:
        raise ConfigurationError("Learning path name is reserved by Windows.")
    stable_clock_id(name, fallback=True)
    return name


def build_provisioning_plan(
    configuration_dir: Path, learning_path_name: str, log_dir: Path | str
) -> ProvisioningPlan:
    name = validate_learning_path_name(learning_path_name)
    raw_log_dir = Path(str(log_dir).strip()).expanduser()
    if not str(log_dir).strip():
        raise ConfigurationError("Diavgeia clock directory is required.")
    if not raw_log_dir.is_absolute():
        raise ConfigurationError("Diavgeia clock directory must be a complete path.")
    resolved_configuration_dir = configuration_dir.expanduser().resolve()
    resolved_log_dir = raw_log_dir.resolve()
    learning_path_dir = resolved_log_dir / LEARNING_PATH_DIRECTORY_NAME
    return ProvisioningPlan(
        learning_path_name=name,
        log_dir=resolved_log_dir,
        learning_path_dir=learning_path_dir,
        properties_path=resolved_configuration_dir / f"{name}.properties",
        csv_path=learning_path_dir / LOG_FILE_NAME,
    )


def validate_provisioning_plan(plan: ProvisioningPlan, configuration_dir: Path) -> None:
    resolved_configuration_dir = configuration_dir.expanduser().resolve()
    try:
        plan.properties_path.resolve().relative_to(resolved_configuration_dir)
    except ValueError as exc:
        raise ConfigurationError("Clock configuration would escape the configuration directory.") from exc

    discovery = discover_clock_configurations(
        resolved_configuration_dir, migrate_legacy=False
    )
    if any(
        clock.learning_path_name.casefold() == plan.learning_path_name.casefold()
        for clock in discovery.clocks
    ):
        raise ConfigurationError(f"A clock named {plan.learning_path_name!r} already exists.")
    target_log_dir = _canonical_path_key(plan.log_dir)
    if any(_canonical_path_key(clock.log_dir) == target_log_dir for clock in discovery.clocks):
        raise ConfigurationError("Another configured clock already uses this log directory.")

    conflicts = [path for path in (plan.properties_path, plan.csv_path) if path.exists()]
    if conflicts:
        rendered = "\n".join(str(path) for path in conflicts)
        raise ConfigurationError(f"Creation would overwrite existing LearningClock files:\n{rendered}")


def _csv_header() -> str:
    buffer = io.StringIO(newline="")
    csv.writer(buffer, lineterminator="\n").writerow(FIELDNAMES)
    return buffer.getvalue()


def _atomic_write(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.learningclock.tmp")
    try:
        temporary.write_text(content, encoding="utf-8", newline="")
        os.replace(temporary, path)
    except Exception:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _create_directory(path: Path, created_dirs: list[Path]) -> None:
    missing: list[Path] = []
    cursor = path
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    path.mkdir(parents=True, exist_ok=True)
    created_dirs.extend(reversed(missing))


def provision_clock(
    configuration_dir: Path,
    learning_path_name: str,
    log_dir: Path | str,
    *,
    logger: Any | None = None,
) -> ProvisioningResult:
    try:
        plan = build_provisioning_plan(configuration_dir, learning_path_name, log_dir)
        validate_provisioning_plan(plan, configuration_dir)
    except Exception as exc:
        if logger is not None:
            logger.event(
                CLOCK_PROVISION_FAILED,
                exc_info=exc,
                clock_name=learning_path_name.strip() or "unknown",
                log_dir=str(log_dir),
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        raise
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    try:
        for directory in (
            plan.properties_path.parent,
            plan.log_dir,
            plan.learning_path_dir,
        ):
            _create_directory(directory, created_dirs)
        contents = (
            f"learning-path-name={plan.learning_path_name}\n"
            f"logDir={plan.log_dir}\n"
        )
        writes = [
            (plan.properties_path, contents),
            (plan.csv_path, _csv_header()),
        ]
        for path, content in writes:
            _atomic_write(path, content)
            created_files.append(path)
    except Exception as exc:
        for path in reversed(created_files):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        if logger is not None:
            logger.event(
                CLOCK_PROVISION_FAILED,
                exc_info=exc,
                clock_name=plan.learning_path_name,
                log_dir=plan.log_dir,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        raise
    if logger is not None:
        logger.event(
            CLOCK_PROVISIONED,
            clock_name=plan.learning_path_name,
            configuration_path=plan.properties_path,
            log_dir=plan.log_dir,
        )
    return ProvisioningResult(plan, tuple(created_files))
