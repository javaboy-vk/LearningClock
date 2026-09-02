# =============================================================================
# File Name : observability.py
# Artifact  : LearningClock - Application Observability Composition
# Author    : javaboy-vk
# Date      : 2026-08-24
# Version   : v2.0.1
# Purpose:
#   Configures protepo.log once for LearningClock and exposes native semantic
#   loggers to the application, CLI, and persistence boundaries.
#
# Composition flow:
#   configure_observability(diagnostic_log_file)
#   |-- verify the required protepo.log runtime version
#   |-- resolve environment, console, file, Seq, and spool settings
#   |-- configure the engineering-audience logging pipeline
#   |-- fall back to console-only logging if sink configuration fails
#   `-- register legacy catalogs and named v2 component loggers
#
# Reliability contract:
#   Local file output is selected per configured clock, Seq is optional and
#   failure-isolated, and correlation_context() carries one workflow identity
#   across LauncherPad and clock-process events. shutdown_observability() owns
#   deterministic handler flushing and reset between tests or application runs.
# =============================================================================

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from protepo.log import AudienceMode, Log
from protepo.log import __version__ as protepo_log_version

from learningclock.events import (
    ALL_EVENT_CATALOGS,
    ApplicationEvents,
    CliEvents,
    ConfigurationEvents,
    StorageEvents,
    TimerEvents,
    UiEvents,
)

DEFAULT_ENVIRONMENT = "local"
DEFAULT_SEQ_TIMEOUT_SECONDS = 0.25
DEFAULT_SEQ_URL = "http://localhost:5341"
REQUIRED_PROTEPO_LOG_VERSION = "2.0.0"


@dataclass(frozen=True, slots=True)
class LearningClockLoggers:
    """Semantic loggers bound to the registered LearningClock event catalogs."""

    application: Any
    ui: Any
    timer: Any
    storage: Any
    configuration: Any
    cli: Any
    launcherpad: Any
    configuration_v2: Any
    process_launcher: Any
    instance_guard: Any
    runtime: Any
    calendar: Any


_active_loggers: LearningClockLoggers | None = None


# Source documentation: Reads a tolerant boolean environment setting for optional runtime sinks.
def _environment_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Source documentation:
#   What it does: Registers event catalogs and assembles all component loggers.
#   Why it exists: Application code should receive one typed bundle rather than repeat catalog
#     registration and logger-name strings throughout the product.
#   Designed use: configure_observability calls it only after Log.configure and returns the
#     resulting bundle to the CLI or GUI composition root.
def _register_loggers() -> LearningClockLoggers:
    Log.register_catalogs(*ALL_EVENT_CATALOGS)
    return LearningClockLoggers(
        application=Log.get_logger(ApplicationEvents),
        ui=Log.get_logger(UiEvents),
        timer=Log.get_logger(TimerEvents),
        storage=Log.get_logger(StorageEvents),
        configuration=Log.get_logger(ConfigurationEvents),
        cli=Log.get_logger(CliEvents),
        launcherpad=Log.get_logger("protepo.learningclock.launcherpad"),
        configuration_v2=Log.get_logger("protepo.learningclock.configuration"),
        process_launcher=Log.get_logger("protepo.learningclock.process_launcher"),
        instance_guard=Log.get_logger("protepo.learningclock.instance_guard"),
        runtime=Log.get_logger("protepo.learningclock.runtime"),
        calendar=Log.get_logger("protepo.learningclock.calendar"),
    )


# Source documentation:
#   What it does: Configures LearningClock-owned logging and returns its semantic logger set.
#   Why it exists: Every entry point needs the same identity, catalogs, correlation behavior,
#     local diagnostics, and failure-isolated Seq policy.
#   Designed use: Call once at a composition root and inject the returned bundle. Reconfiguration
#     closes older handlers; sink failures fall back to console, while incompatible protepo.log
#     versions raise because the event contract cannot be guaranteed.
def configure_observability(
    diagnostic_log_file: Path | str | None,
    *,
    console_enabled: bool | None = None,
    include_seq: bool = True,
    seq_spool_path: Path | str | None = None,
) -> LearningClockLoggers:
    global _active_loggers

    if _active_loggers is not None:
        Log.shutdown()
        _active_loggers = None

    log_path = Path(diagnostic_log_file) if diagnostic_log_file is not None else None
    environment = os.getenv("LEARNINGCLOCK_ENVIRONMENT", DEFAULT_ENVIRONMENT).strip()
    if not environment:
        environment = DEFAULT_ENVIRONMENT
    if console_enabled is None:
        console_enabled = _environment_flag("LEARNINGCLOCK_LOG_CONSOLE", False)
    if protepo_log_version != REQUIRED_PROTEPO_LOG_VERSION:
        raise RuntimeError(
            f"LearningClock requires protepo-log {REQUIRED_PROTEPO_LOG_VERSION}; "
            f"found {protepo_log_version}"
        )
    seq_endpoint = (
        os.getenv("LEARNINGCLOCK_SEQ_URL") or os.getenv("SEQ_URL") or DEFAULT_SEQ_URL
        if include_seq
        else None
    )
    if seq_endpoint is not None:
        seq_endpoint = seq_endpoint.strip() or None
    seq_enabled = seq_endpoint is not None
    selected_spool_path = (
        Path(seq_spool_path)
        if seq_spool_path is not None
        else (log_path.parent / "learning_clock_seq_offline.clef" if log_path is not None else None)
    )

    configuration_error: Exception | None = None
    try:
        Log.configure(
            application="LearningClock",
            environment=environment,
            mode=AudienceMode.ENGINEERING,
            console_enabled=console_enabled,
            file_enabled=log_path is not None,
            file_path=log_path,
            seq_enabled=seq_enabled,
            seq_endpoint=seq_endpoint,
            seq_api_key=os.getenv("LEARNINGCLOCK_SEQ_API_KEY") or os.getenv("SEQ_API_KEY"),
            seq_mode=AudienceMode.ENGINEERING,
            seq_timeout_seconds=DEFAULT_SEQ_TIMEOUT_SECONDS,
            seq_spool_path=selected_spool_path,
            preserve_existing_handlers=True,
            logger_namespace="protepo.learningclock",
        )
    except Exception as exc:
        configuration_error = exc
        Log.shutdown()
        Log.configure(
            application="LearningClock",
            environment=environment,
            mode=AudienceMode.ENGINEERING,
            console_enabled=True,
            file_enabled=False,
            seq_enabled=False,
            preserve_existing_handlers=True,
            logger_namespace="protepo.learningclock",
        )

    _active_loggers = _register_loggers()
    if configuration_error is not None and log_path is not None:
        _active_loggers.configuration.warning(
            ConfigurationEvents.FILE_SINK_FALLBACK,
            str(log_path),
            type(configuration_error).__name__,
            exc_info=(
                type(configuration_error),
                configuration_error,
                configuration_error.__traceback__,
            ),
        )
    _active_loggers.configuration.info(
        ConfigurationEvents.OBSERVABILITY_CONFIGURED,
        environment,
        log_path is not None and configuration_error is None,
        seq_enabled and configuration_error is None,
    )
    return _active_loggers


# Source documentation:
#   What it does: Returns a correlation scope for one cross-component workflow.
#   Why it exists: Parent launch and child startup events need a shared identity without passing
#     it to every log call.
#   Designed use: Wrap one launch/startup operation; None delegates identifier handling to
#     protepo.log.
def correlation_context(correlation_id: str | None = None):
    return Log.context(correlation_id)


# Source documentation:
#   What it does: Flushes and resets LearningClock-owned logging handlers.
#   Why it exists: GUI shutdown and repeated tests must not retain files, Seq workers, or stale
#     global logger state.
#   Designed use: Call from entry-point finally blocks; it is safe after partial startup.
def shutdown_observability() -> None:
    global _active_loggers

    Log.shutdown()
    _active_loggers = None
