# =============================================================================
# File Name : configuration.py
# Artifact  : LearningClock - Configured Clock Discovery
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.0.0
# Purpose:
#   Loads, validates, identifies, and deterministically discovers LearningClock
#   properties files without coupling configuration data to launch code.
# =============================================================================

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from learningclock.telemetry import (
    CONFIG_DISCOVERED,
    CONFIG_DISCOVERY_COMPLETED,
    CONFIG_DISCOVERY_STARTED,
    CONFIG_DUPLICATE_ID,
    CONFIG_MALFORMED,
    CONFIG_VALIDATED,
)

DEFAULT_CONFIGURATION_DIR = Path(r"D:\LearningPath")
_CLOCK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class ConfigurationError(ValueError):
    """Raised when one LearningClock properties file is unusable."""


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


def load_properties(path: Path) -> dict[str, str]:
    """Load Java-style key/value properties used by existing LearningClock launchers."""

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


def stable_clock_id(value: str, *, fallback: bool = False) -> str:
    """Return a stable mutex-safe clock ID, normalizing legacy filename identities."""

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


def load_clock_configuration(path: Path) -> ConfiguredClock:
    """Load and validate one existing or v1 LauncherPad clock configuration."""

    resolved_path = path.expanduser().resolve()
    if resolved_path.suffix.lower() != ".properties":
        raise ConfigurationError("configuration must use the .properties extension")
    values = load_properties(resolved_path)
    learning_path_name = _required(values, "learning-path-name")
    log_dir_value = _required(values, "logDir")
    explicit_id = values.get("clock-id", "").strip()
    clock_id = stable_clock_id(explicit_id) if explicit_id else stable_clock_id(
        resolved_path.stem, fallback=True
    )
    display_name = values.get("display-name", "").strip() or learning_path_name
    log_dir = Path(log_dir_value)
    if not log_dir.is_absolute():
        log_dir = (resolved_path.parent / log_dir).resolve()
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


def legacy_clock_configuration(
    *, learning_path_name: str, log_dir: Path, clock_id: str | None = None
) -> ConfiguredClock:
    """Build a compatible identity for direct developer execution without a properties file."""

    identity = stable_clock_id(clock_id) if clock_id else stable_clock_id(
        learning_path_name, fallback=True
    )
    return ConfiguredClock(
        clock_id=identity,
        display_name=learning_path_name,
        learning_path_name=learning_path_name,
        configuration_path=Path("<direct>"),
        log_dir=log_dir.resolve(),
    )


def discover_clock_configurations(
    configuration_dir: Path, *, logger: Any | None = None
) -> DiscoveryResult:
    """Discover valid clocks while isolating malformed files and identity collisions."""

    resolved_dir = configuration_dir.expanduser().resolve()
    if logger is not None:
        logger.event(CONFIG_DISCOVERY_STARTED, configuration_dir=resolved_dir)
    issues: list[ConfigurationIssue] = []
    clocks: list[ConfiguredClock] = []
    by_id: dict[str, ConfiguredClock] = {}
    try:
        candidates = sorted(resolved_dir.glob("*.properties"), key=lambda item: item.name.casefold())
    except OSError as exc:
        candidates = []
        issues.append(ConfigurationIssue(resolved_dir, str(exc)))

    for path in candidates:
        if logger is not None:
            logger.event(CONFIG_DISCOVERED, configuration_path=path)
        try:
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
        by_id[clock.clock_id] = clock
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

