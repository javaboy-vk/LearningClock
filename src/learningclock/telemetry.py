# =============================================================================
# File Name : telemetry.py
# Artifact  : LearningClock - Protepo Log v2 Event Definitions
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v2.0.1
# Purpose:
#   Defines formal, structured Protepo Logging Standard v2 events for LauncherPad,
#   configuration, process launching, singleton protection, runtime, and calendar flows.
# =============================================================================

from protepo.log import Severity, Visibility, define_event


def _event(code: str, severity: Severity, message: str, component: str):
    """Declare one internal LearningClock operational event."""

    return define_event(
        code=code,
        severity=severity,
        visibility=Visibility.INTERNAL,
        internal_message=message,
        component=component,
    )


LAUNCHERPAD_STARTING = _event(
    "LPLCL-1001", Severity.INFO, "LauncherPad starting from {configuration_dir}.", "LauncherPad"
)
LAUNCHERPAD_INITIALIZED = _event(
    "LPLCL-1002",
    Severity.INFO,
    "LauncherPad initialized with {clock_count} valid clocks and {error_count} skipped configurations.",
    "LauncherPad",
)
LAUNCHERPAD_CLOSING = _event(
    "LPLCL-1003", Severity.INFO, "LauncherPad closing.", "LauncherPad"
)
LAUNCHERPAD_CLOSED = _event(
    "LPLCL-1004", Severity.INFO, "LauncherPad closed.", "LauncherPad"
)
RUNNING_STATE_CHANGED = _event(
    "LPLCL-1010",
    Severity.INFO,
    "Clock {clock_id} running state changed from {previous_state} to {current_state}.",
    "LauncherPad",
)
EXTERNAL_INSTANCE_DETECTED = _event(
    "LPLCL-1011",
    Severity.INFO,
    "LauncherPad detected an already-running clock {clock_id}.",
    "LauncherPad",
)

CONFIG_DISCOVERY_STARTED = _event(
    "CONFG-2001",
    Severity.INFO,
    "Configuration discovery started in {configuration_dir}.",
    "Configuration",
)
CONFIG_DISCOVERED = _event(
    "CONFG-2002",
    Severity.DEBUG,
    "Configuration discovered at {configuration_path}.",
    "Configuration",
)
CONFIG_VALIDATED = _event(
    "CONFG-2003",
    Severity.INFO,
    "Configuration {clock_id} validated for {clock_name}.",
    "Configuration",
)
CONFIG_MALFORMED = _event(
    "CONFG-2004",
    Severity.WARN,
    "Configuration {configuration_path} was skipped: {error_type}: {error_message}.",
    "Configuration",
)
CONFIG_DUPLICATE_ID = _event(
    "CONFG-2005",
    Severity.WARN,
    "Configuration {configuration_path} duplicates clock identity {clock_id} and was skipped.",
    "Configuration",
)
CONFIG_DISCOVERY_COMPLETED = _event(
    "CONFG-2006",
    Severity.INFO,
    "Configuration discovery completed with {clock_count} valid clocks and {error_count} errors.",
    "Configuration",
)

LAUNCH_REQUESTED = _event(
    "LPCRP-3001", Severity.INFO, "Launch requested for clock {clock_id}.", "ProcessLauncher"
)
LAUNCH_COMMAND_CONSTRUCTED = _event(
    "LPCRP-3002",
    Severity.DEBUG,
    "Launch command constructed for {clock_id} in {runtime_mode} mode using {executable}.",
    "ProcessLauncher",
)
PROCESS_CREATED = _event(
    "LPCRP-3003",
    Severity.INFO,
    "LearningClock process {child_process_id} created for {clock_id}.",
    "ProcessLauncher",
)
PROCESS_LAUNCH_FAILED = _event(
    "LPCRP-3004",
    Severity.ERROR,
    "LearningClock launch failed for {clock_id}: {error_type}: {error_message}.",
    "ProcessLauncher",
)

MUTEX_IDENTITY_CONSTRUCTED = _event(
    "MUTEX-4001",
    Severity.DEBUG,
    "Mutex identity {mutex_name} constructed for clock {clock_id}.",
    "InstanceGuard",
)
MUTEX_ACQUIRED = _event(
    "MUTEX-4002",
    Severity.INFO,
    "Mutex {mutex_name} acquired for clock {clock_id}.",
    "InstanceGuard",
)
DUPLICATE_MUTEX_DETECTED = _event(
    "MUTEX-4003",
    Severity.WARN,
    "Existing mutex {mutex_name} detected for clock {clock_id}.",
    "InstanceGuard",
)
DUPLICATE_CLOCK_REJECTED = _event(
    "MUTEX-4004",
    Severity.WARN,
    "Duplicate LearningClock startup rejected for {clock_id} before persistence initialization.",
    "InstanceGuard",
)
MUTEX_OBSERVATION_FAILED = _event(
    "MUTEX-4005",
    Severity.ERROR,
    "Mutex observation failed for {mutex_name}: {error_type}: {error_message}.",
    "InstanceGuard",
)
MUTEX_CLOSED = _event(
    "MUTEX-4006",
    Severity.DEBUG,
    "Mutex {mutex_name} released and handle closed for clock {clock_id}.",
    "InstanceGuard",
)
MUTEX_OPERATION_FAILED = _event(
    "MUTEX-4007",
    Severity.ERROR,
    "Mutex operation {operation_id} failed for {mutex_name}: {error_code}.",
    "InstanceGuard",
)

CLOCK_STARTING = _event(
    "LIFCL-5001",
    Severity.INFO,
    "LearningClock starting for {clock_id} from {configuration_path}.",
    "Runtime",
)
CLOCK_INITIALIZED = _event(
    "LIFCL-5002",
    Severity.INFO,
    "LearningClock initialized for {clock_id} with process {process_id}.",
    "Runtime",
)
CLOCK_CLOSED = _event(
    "LIFCL-5003", Severity.INFO, "LearningClock closed for {clock_id}.", "Runtime"
)
CLOCK_STARTUP_FAILED = _event(
    "LIFCL-5099",
    Severity.FATAL,
    "LearningClock startup failed for {clock_id}: {error_type}: {error_message}.",
    "Runtime",
)

CALENDAR_INITIALIZED = _event(
    "CLNDR-6001",
    Severity.INFO,
    "Calendar popup initialized for clock {clock_id}.",
    "Calendar",
)
CALENDAR_OPEN_FAILED = _event(
    "CLNDR-6002",
    Severity.ERROR,
    "Calendar popup failed for clock {clock_id}: {error_type}: {error_message}.",
    "Calendar",
)
