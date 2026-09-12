# =============================================================================
# File Name : configuration.py
# Artifact  : LearningClock - Configured Clock Discovery
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v2.4.0
# Purpose:
#   Loads central runtime settings; validates, migrates, identifies, and
#   deterministically discovers per-clock properties files.
#
# Configuration flow:
#   load_central_configuration(clock.properties) -> pythonExe + pyScriptPath
#   discover_clock_configurations(configuration_dir)
#   |-- enumerate *.properties in case-insensitive filename order
#   |-- load_clock_configuration(path)
#   |   |-- load_properties(path)
#   |   |-- require learning-path-name and logDir
#   |   |-- validate explicit clock-id or normalize the filename fallback
#   |   `-- resolve relative logDir values beside the properties file
#   |-- isolate malformed files as ConfigurationIssue values
#   |-- atomically remove obsolete per-clock shared runtime keys
#   |-- reject duplicate IDs, names, and canonical log directories
#   `-- order valid clocks by explicit order, display name, and clock ID
#
# Boundary contract:
#   This module returns immutable configuration data. It does not create UI,
#   launch processes, acquire mutexes, create log directories, or open CSV files.
#   Per-file failures remain visible in DiscoveryResult so LauncherPad can keep
#   operating with the remaining valid configurations.
# =============================================================================

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learningclock.telemetry import (
    CONFIG_DISCOVERED,
    CONFIG_DISCOVERY_COMPLETED,
    CONFIG_DISCOVERY_STARTED,
    CONFIG_DUPLICATE_ID,
    CONFIG_DUPLICATE_SOURCE,
    CONFIG_LEGACY_MIGRATED,
    CONFIG_LEGACY_MIGRATION_FAILED,
    CONFIG_MALFORMED,
    CONFIG_VALIDATED,
)

INSTALLATION_ROOT = Path(r"D:\LearningClock")
DEFAULT_CONFIGURATION_DIR = INSTALLATION_ROOT / "props"
DEFAULT_LOG_DIRECTORY = INSTALLATION_ROOT / "logs"
DEFAULT_CENTRAL_CONFIGURATION = Path(__file__).resolve().with_name("clock.properties")
CENTRAL_CONFIGURATION_ENV = "LEARNINGCLOCK_CENTRAL_CONFIG"
LEARNING_PATH_DIRECTORY_NAME = "LearningPath"
_CLOCK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_SHARED_KEYS = frozenset({"pythonExe", "pyScriptPath"})


def logs_directory(configuration_dir: Path) -> Path:
    """Resolve centralized logs beside the standard props directory."""

    resolved = configuration_dir.expanduser().resolve()
    installation_root = resolved.parent if resolved.name.casefold() == "props" else resolved
    return installation_root / "logs"


class ConfigurationError(ValueError):
    """Raised when one LearningClock properties file is unusable."""


@dataclass(frozen=True, slots=True)
class CentralConfiguration:
    """Application-level executable and script settings shared by every clock."""

    configuration_path: Path
    python_executable: Path
    script_path: Path


@dataclass(frozen=True, slots=True)
class ConfiguredClock:
    """Validated configuration needed to identify and launch one clock."""

    clock_id: str
    display_name: str
    learning_path_name: str
    configuration_path: Path
    log_dir: Path
    order: int | None = None


@dataclass(frozen=True, slots=True)
class ConfigurationIssue:
    """One malformed or conflicting configuration skipped during discovery."""

    path: Path
    message: str


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """Valid configured clocks plus isolated per-file discovery failures."""

    clocks: tuple[ConfiguredClock, ...]
    issues: tuple[ConfigurationIssue, ...]


# Source documentation:
#   What it does: Loads Java-style key/value properties used by LearningClock launchers.
#   Why it exists: Existing learning paths already use properties files, so this preserves
#     compatibility without coupling discovery to a UI.
#   Designed use: Call with one candidate file. It returns trimmed string values and raises
#     ConfigurationError for unreadable files or malformed non-comment lines.
def load_properties(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise ConfigurationError(f"could not read properties: {exc}") from exc
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        key, separator, value = line.partition("=")
        if not separator or not key.strip():
            raise ConfigurationError(f"line {line_number} is not a key=value property")
        values[key.strip()] = value.strip().strip('"')
    return values


def central_configuration_path(override: Path | None = None) -> Path:
    """Resolve central configuration without depending on the process working directory."""

    selected = override or Path(
        os.getenv(CENTRAL_CONFIGURATION_ENV, str(DEFAULT_CENTRAL_CONFIGURATION))
    )
    if selected.is_absolute():
        return selected.resolve()
    return (DEFAULT_CENTRAL_CONFIGURATION.parent / selected).resolve()


def _resolve_property_path(value: str, properties_path: Path) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (properties_path.parent / candidate).resolve()


def load_central_configuration(
    path: Path | None = None, *, validate_paths: bool = False
) -> CentralConfiguration:
    """Load shared runtime settings and optionally prove both configured files exist."""

    resolved_path = central_configuration_path(path)
    values = load_properties(resolved_path)
    central = CentralConfiguration(
        configuration_path=resolved_path,
        python_executable=_resolve_property_path(_required(values, "pythonExe"), resolved_path),
        script_path=_resolve_property_path(_required(values, "pyScriptPath"), resolved_path),
    )
    if validate_paths:
        missing: list[str] = []
        if not central.python_executable.is_file():
            missing.append(f"Python executable does not exist: {central.python_executable}")
        if not central.script_path.is_file():
            missing.append(f"LearningClock script does not exist: {central.script_path}")
        if missing:
            raise ConfigurationError("\n".join(missing))
    return central


def migrate_legacy_clock_configuration(path: Path, *, logger: Any | None = None) -> bool:
    """Remove obsolete shared keys and normalize the former CSV-directory logDir."""

    try:
        original = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ConfigurationError(f"could not read properties for migration: {exc}") from exc
    lines = original.splitlines(keepends=True)
    kept: list[str] = []
    removed: list[str] = []
    normalized_log_dir = False
    for raw_line in lines:
        stripped = raw_line.strip()
        key = stripped.partition("=")[0].strip() if "=" in stripped else ""
        if key in _SHARED_KEYS:
            removed.append(key)
        elif key == "logDir":
            prefix, separator, raw_value = raw_line.partition("=")
            value = raw_value.strip().strip('"')
            candidate = Path(value)
            if candidate.name.casefold() == LEARNING_PATH_DIRECTORY_NAME.casefold():
                line_ending = "\r\n" if raw_line.endswith("\r\n") else "\n" if raw_line.endswith("\n") else ""
                kept.append(f"{prefix}{separator}{candidate.parent}{line_ending}")
                normalized_log_dir = True
            else:
                kept.append(raw_line)
        else:
            kept.append(raw_line)
    if not removed and not normalized_log_dir:
        return False
    temporary = path.with_name(f".{path.name}.learningclock.tmp")
    try:
        temporary.write_text("".join(kept), encoding="utf-8")
        os.replace(temporary, path)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        if logger is not None:
            logger.event(
                CONFIG_LEGACY_MIGRATION_FAILED,
                configuration_path=path,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
        raise ConfigurationError(f"could not migrate legacy properties: {exc}") from exc
    if logger is not None:
        logger.event(
            CONFIG_LEGACY_MIGRATED,
            configuration_path=path,
            removed_properties=",".join(sorted(set(removed))),
            normalized_log_dir=normalized_log_dir,
        )
    return True


# Source documentation:
#   What it does: Returns a stable, mutex-safe clock ID.
#   Why it exists: Discovery, Windows mutexes, logs, and Seq filters share this identity.
#   Designed use: Keep fallback disabled for explicit clock-id values; enable it only when
#     normalizing legacy filenames or display names before validation.
def stable_clock_id(value: str, *, fallback: bool = False) -> str:
    normalized = value.strip().lower()
    if fallback:
        normalized = re.sub(r"[^a-z0-9._-]+", "-", normalized).strip("-._")
    if not _CLOCK_ID_PATTERN.fullmatch(normalized):
        raise ConfigurationError(
            "clock-id must contain 1-64 lowercase letters, digits, dots, underscores, or hyphens"
        )
    return normalized


def _required(values: dict[str, str], key: str) -> str:
    value = values.get(key, "").strip()
    if not value:
        raise ConfigurationError(f"required property {key!r} is missing or empty")
    return value


# Source documentation:
#   What it does: Loads and validates one LauncherPad clock configuration.
#   Why it exists: Launch code needs one immutable resolved object instead of repeatedly
#     interpreting raw properties at different boundaries.
#   Designed use: Discovery and --clock startup call it before UI or storage initialization;
#     invalid extensions or values raise ConfigurationError for the caller to handle.
def load_clock_configuration(path: Path) -> ConfiguredClock:
    resolved_path = path.expanduser().resolve()
    if resolved_path.suffix.lower() != ".properties":
        raise ConfigurationError("configuration must use the .properties extension")
    values = load_properties(resolved_path)
    learning_path_name = _required(values, "learning-path-name")
    log_dir_value = _required(values, "logDir")
    explicit_id = values.get("clock-id", "").strip()
    clock_id = (
        stable_clock_id(explicit_id)
        if explicit_id
        else stable_clock_id(resolved_path.stem, fallback=True)
    )
    display_name = values.get("display-name", "").strip() or learning_path_name
    log_dir = Path(log_dir_value)
    if not log_dir.is_absolute():
        log_dir = (resolved_path.parent / log_dir).resolve()
    if log_dir.name.casefold() == LEARNING_PATH_DIRECTORY_NAME.casefold():
        log_dir = log_dir.parent
    order_value = values.get("order", "").strip()
    order: int | None = None
    if order_value:
        try:
            order = int(order_value)
        except ValueError as exc:
            raise ConfigurationError("order must be an integer") from exc
    return ConfiguredClock(
        clock_id=clock_id,
        display_name=display_name,
        learning_path_name=learning_path_name,
        configuration_path=resolved_path,
        log_dir=log_dir,
        order=order,
    )


# Source documentation:
#   What it does: Builds a compatible identity for direct execution without a properties file.
#   Why it exists: Historical developer/debugger commands pass name and log directory directly,
#     while the v6.0 runtime still requires a clock identity.
#   Designed use: Use only for app.main's legacy argument path; LauncherPad launches should load
#     a real configuration with load_clock_configuration.
def legacy_clock_configuration(
    *, learning_path_name: str, log_dir: Path, clock_id: str | None = None
) -> ConfiguredClock:
    identity = (
        stable_clock_id(clock_id)
        if clock_id
        else stable_clock_id(learning_path_name, fallback=True)
    )
    return ConfiguredClock(
        clock_id=identity,
        display_name=learning_path_name,
        learning_path_name=learning_path_name,
        configuration_path=Path("<direct>"),
        log_dir=log_dir.resolve(),
    )


# Source documentation:
#   What it does: Discovers valid clocks while isolating per-file failures.
#   Why it exists: One malformed or duplicate configuration must not hide other valid clocks.
#   Designed use: LauncherPad renders the returned clocks and reports issues; optional logging
#     records discovery without affecting deterministic validation or ordering.
def discover_clock_configurations(
    configuration_dir: Path,
    *,
    logger: Any | None = None,
    migrate_legacy: bool = True,
    excluded_paths: tuple[Path, ...] = (),
) -> DiscoveryResult:
    resolved_dir = configuration_dir.expanduser().resolve()
    if logger is not None:
        logger.event(CONFIG_DISCOVERY_STARTED, configuration_dir=resolved_dir)
    issues: list[ConfigurationIssue] = []
    clocks: list[ConfiguredClock] = []
    by_id: dict[str, ConfiguredClock] = {}
    by_name: dict[str, ConfiguredClock] = {}
    by_log_dir: dict[str, ConfiguredClock] = {}
    excluded = {os.path.normcase(str(path.resolve())) for path in excluded_paths}
    try:
        candidates = sorted(
            resolved_dir.glob("*.properties"), key=lambda item: item.name.casefold()
        )
    except OSError as exc:
        candidates = []
        issues.append(ConfigurationIssue(resolved_dir, str(exc)))

    for path in candidates:
        if os.path.normcase(str(path.resolve())) in excluded:
            continue
        if logger is not None:
            logger.event(CONFIG_DISCOVERED, configuration_path=path)
        try:
            values = load_properties(path)
            if migrate_legacy and (
                _SHARED_KEYS.intersection(values)
                or Path(values.get("logDir", "")).name.casefold()
                == LEARNING_PATH_DIRECTORY_NAME.casefold()
            ):
                migrate_legacy_clock_configuration(path, logger=logger)
            clock = load_clock_configuration(path)
        except (ConfigurationError, OSError) as exc:
            issues.append(ConfigurationIssue(path, str(exc)))
            if logger is not None:
                logger.event(
                    CONFIG_MALFORMED,
                    configuration_path=path,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
            continue
        if clock.clock_id in by_id:
            issues.append(ConfigurationIssue(path, f"duplicate clock-id {clock.clock_id!r}"))
            if logger is not None:
                logger.event(
                    CONFIG_DUPLICATE_ID,
                    configuration_path=path,
                    clock_id=clock.clock_id,
                )
            continue
        name_key = clock.learning_path_name.casefold()
        log_dir_key = os.path.normcase(str(clock.log_dir.resolve()))
        if name_key in by_name:
            message = f"duplicate learning-path-name {clock.learning_path_name!r}"
            issues.append(ConfigurationIssue(path, message))
            if logger is not None:
                logger.event(
                    CONFIG_DUPLICATE_SOURCE,
                    configuration_path=path,
                    duplicate_kind="learning_path_name",
                    duplicate_value=clock.learning_path_name,
                )
            continue
        if log_dir_key in by_log_dir:
            message = f"duplicate canonical logDir {clock.log_dir}"
            issues.append(ConfigurationIssue(path, message))
            if logger is not None:
                logger.event(
                    CONFIG_DUPLICATE_SOURCE,
                    configuration_path=path,
                    duplicate_kind="log_dir",
                    duplicate_value=clock.log_dir,
                )
            continue
        by_id[clock.clock_id] = clock
        by_name[name_key] = clock
        by_log_dir[log_dir_key] = clock
        clocks.append(clock)
        if logger is not None:
            logger.event(
                CONFIG_VALIDATED,
                clock_id=clock.clock_id,
                clock_name=clock.display_name,
                configuration_path=clock.configuration_path,
            )

    clocks.sort(
        key=lambda clock: (
            clock.order is None,
            clock.order if clock.order is not None else 0,
            clock.display_name.casefold(),
            clock.clock_id,
        )
    )
    if logger is not None:
        logger.event(
            CONFIG_DISCOVERY_COMPLETED,
            configuration_dir=resolved_dir,
            clock_count=len(clocks),
            error_count=len(issues),
        )
    return DiscoveryResult(tuple(clocks), tuple(issues))
