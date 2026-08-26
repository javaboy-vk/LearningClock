# =============================================================================
# File Name : events.py
# Artifact  : LearningClock - Application Event Catalogs
# Author    : javaboy-vk
# Date      : 2026-08-24
# Version   : v0.1.1
# Purpose:
#   Defines stable, product-owned semantic event identities for every LearningClock
#   application logging boundary.
# =============================================================================

from protepo.log import Event, EventCatalog


class ApplicationEvents(EventCatalog):
    """Application-process lifecycle events."""

    module = "APPLC"
    id_range = (1000, 1099)

    STARTING = Event(1001, "LearningClock starting for {0}; log directory {1}")
    INITIALIZED = Event(
        1002,
        "LearningClock initialized for {0}; CSV {1}; diagnostics {2}; autosave {3} minutes",
    )
    CLOSE_REQUESTED = Event(
        1003,
        "Application close requested; session start {0}; session end {1}; saved {2}",
    )
    SHUTDOWN_FINALIZING = Event(1004, "Application shutdown finalization started")
    STOPPED = Event(1005, "LearningClock stopped normally")
    STARTUP_FAILED = Event(1099, "LearningClock failed during startup or execution")


class UiEvents(EventCatalog):
    """User-interface workflow and checkpoint events."""

    module = "USRIF"
    id_range = (2000, 2199)

    PROGRESS_READ_FAILED = Event(2001, "Progress chart CSV read failed")
    PROGRESS_CHECKPOINT_COMPLETED = Event(
        2002,
        "Progress checkpoint completed; saved {0}; session end {1}",
    )
    PROGRESS_CHECKPOINT_FAILED = Event(2003, "Progress checkpoint CSV write failed")
    MANUAL_TIME_VALIDATION_FAILED = Event(
        2010,
        "Manual time validation rejected {0} field(s)",
    )
    MANUAL_TIME_SAVE_FAILED = Event(2011, "Manual time CSV write failed")
    MANUAL_TIME_SAVED = Event(
        2012,
        "Manual time saved; activity {0}; date {1}; added {2}; activity total {3}",
    )
    PAGE_COUNT_VALIDATION_FAILED = Event(2020, "Page-count validation rejected value")
    PAGE_COUNT_SAVE_FAILED = Event(2021, "Manual page-count CSV write failed")
    PAGE_COUNT_SAVED = Event(
        2022,
        "Pages saved; added {0}; date {1}; session page total {2}",
    )
    AUTOSAVE_COMPLETED = Event(
        2030,
        "Autosave completed; interval {0} minutes; saved {1}; session end {2}",
    )
    AUTOSAVE_FAILED = Event(2031, "Autosave CSV write failed")
    AUTOSAVE_EMERGENCY_CREATED = Event(2032, "Autosave emergency file created at {0}")
    AUTOSAVE_EMERGENCY_FAILED = Event(2033, "Autosave emergency save failed")
    SHUTDOWN_SAVE_FAILED = Event(2040, "Normal shutdown CSV save failed")
    SHUTDOWN_EMERGENCY_FAILED = Event(2041, "Shutdown emergency save failed")
    SESSION_DATE_VALIDATION_FAILED = Event(2050, "Session date validation rejected value")
    SESSION_DATE_APPLIED = Event(2051, "Session date selection changed to {0}")


class TimerEvents(EventCatalog):
    """Learning timer state-transition events."""

    module = "TIMER"
    id_range = (3000, 3199)

    SWITCH_REQUESTED = Event(3001, "Timer switch requested for {0}")
    STARTED = Event(3002, "Timer started for {0} at {1}")
    CLOSED = Event(
        3003,
        "Timer closed for {0}; elapsed {1}; activity total {2}",
    )
    STOPPED = Event(3004, "Active timer stopped")
    RESET_REJECTED = Event(3005, "Timer reset rejected because no timer is active")
    RESET = Event(3006, "Timer reset for {0}")
    STOP_REJECTED = Event(3007, "Timer stop ignored because no timer is active")


class StorageEvents(EventCatalog):
    """CSV persistence, normalization, and recovery events."""

    module = "STORG"
    id_range = (4000, 4299)

    INITIALIZED = Event(4001, "CSV storage initialized; data {0}; diagnostics {1}")
    SAVE_STARTED = Event(4002, "CSV save started; session end {0}; target {1}")
    ROWS_LOADED = Event(
        4003,
        "CSV inputs loaded; existing rows {0}; emergency rows {1}; emergency files {2}",
    )
    SESSION_PREPARED = Event(
        4004,
        "Session row prepared; date {0}; start {1}; end {2}; total {3}; pages {4}; has data {5}",
    )
    SESSION_SKIPPED = Event(4005, "Session row skipped because it has no time or pages")
    SAVE_SKIPPED = Event(4006, "CSV save skipped because there are no rows to write")
    WRITE_STARTED = Event(
        4007,
        "Writing CSV; rows including total {0}; duration total {1}; page total {2}",
    )
    SAVE_COMPLETED = Event(4008, "CSV save completed successfully")
    MAIN_FILE_MISSING = Event(4009, "Main CSV does not exist yet at {0}")
    MAIN_FILE_READ = Event(4010, "Main CSV read completed; session rows {0}")
    EMERGENCY_FILE_READ_FAILED = Event(4011, "Emergency CSV read failed for {0}")
    EMERGENCY_SCAN_COMPLETED = Event(
        4012,
        "Emergency CSV scan completed; recovered rows {0}; files {1}",
    )
    EMERGENCY_FILES_MERGED = Event(4013, "Emergency CSV files marked merged; files {0}")
    DATE_NORMALIZED = Event(
        4014,
        "CSV date normalized from {0} to {1}; canonical format {2}",
    )
    DATE_PRESERVED = Event(
        4015,
        "CSV date could not be normalized; preserving {0}; canonical format {1}",
    )
    EMERGENCY_FILE_CREATED = Event(
        4016,
        "Emergency session file created at {0}; original error type {1}",
    )
    EMERGENCY_FILE_MARK_FAILED = Event(
        4017,
        "Emergency CSV could not be marked merged for {0}",
    )


class ConfigurationEvents(EventCatalog):
    """Runtime configuration events."""

    module = "CONFG"
    id_range = (5000, 5099)

    AUTOSAVE_LOADED = Event(5001, "Autosave interval loaded from {0}; minutes {1}")
    AUTOSAVE_FALLBACK = Event(
        5002,
        "Autosave configuration ignored; using {0} minutes; error type {1}",
    )
    FILE_SINK_FALLBACK = Event(
        5003,
        "File logging unavailable for {0}; continuing with console logging; error type {1}",
    )
    OBSERVABILITY_CONFIGURED = Event(
        5004,
        "Observability configured; environment {0}; file enabled {1}; Seq enabled {2}",
    )
    AUTOSAVE_DEFAULT = Event(5005, "Autosave interval defaulted to {0} minutes")


class CliEvents(EventCatalog):
    """Stable command-line interface events."""

    module = "CMDLN"
    id_range = (6000, 6099)

    READY_EMITTED = Event(6001, "CLI readiness response emitted")
    VERSION_EMITTED = Event(6002, "CLI version response emitted for {0}")
    ARGUMENT_PARSE_EXITED = Event(6003, "CLI argument parsing exited with status {0}")


ALL_EVENT_CATALOGS = (
    ApplicationEvents,
    UiEvents,
    TimerEvents,
    StorageEvents,
    ConfigurationEvents,
    CliEvents,
)
