# =============================================================================
# File Name : test_observability.py
# Artifact  : LearningClock - Application Observability Tests
# Author    : javaboy-vk
# Date      : 2026-08-24
# Version   : v2.0.1
# Purpose:
#   Verifies LearningClock event-catalog integrity and native protepo.log
#   semantic file output.
# =============================================================================

from __future__ import annotations

from protepo.log import AudienceMode, EventDefinition, Log

from learningclock import telemetry
from learningclock.events import (
    ALL_EVENT_CATALOGS,
    ApplicationEvents,
    CliEvents,
    ConfigurationEvents,
    StorageEvents,
    TimerEvents,
    UiEvents,
)
from learningclock.observability import (
    REQUIRED_PROTEPO_LOG_VERSION,
    configure_observability,
    correlation_context,
    shutdown_observability,
)
from learningclock.telemetry import LAUNCH_REQUESTED


def test_event_catalog_ids_are_unique_and_within_their_declared_ranges():

    event_codes = set()
    for catalog in ALL_EVENT_CATALOGS:
        range_start, range_end = catalog.id_range
        for event in catalog.declared_events().values():
            assert range_start <= event.event_id <= range_end
            event_code = f"{catalog.module}-{event.event_id}"
            assert event_code not in event_codes
            event_codes.add(event_code)


def test_event_catalog_modules_use_the_approved_five_byte_abbreviations():

    expected_modules = {
        ApplicationEvents: "APPLC",
        UiEvents: "USRIF",
        TimerEvents: "TIMER",
        StorageEvents: "STORG",
        ConfigurationEvents: "CONFG",
        CliEvents: "CMDLN",
    }

    assert {catalog: catalog.module for catalog in ALL_EVENT_CATALOGS} == expected_modules
    assert all(len(module.encode("ascii")) == 5 for module in expected_modules.values())


def test_formal_v2_events_use_the_approved_family_abbreviations():

    events = [
        value
        for value in vars(telemetry).values()
        if isinstance(value, EventDefinition)
    ]
    prefixes = {event.code.partition("-")[0] for event in events}

    assert prefixes == {"LPLCL", "CONFG", "LPCRP", "MUTEX", "LIFCL", "CLNDR"}
    assert all(len(prefix.encode("ascii")) == 5 for prefix in prefixes)


def test_observability_writes_semantic_events_to_the_application_log(tmp_path, monkeypatch):

    monkeypatch.delenv("LEARNINGCLOCK_SEQ_URL", raising=False)
    log_file = tmp_path / "learning_clock_debug.log"
    loggers = configure_observability(log_file, console_enabled=False)
    try:
        with correlation_context("test-session"):
            loggers.timer.info(
                TimerEvents.STARTED,
                "Reading",
                "09:00:00",
            )
    finally:
        shutdown_observability()

    output = log_file.read_text(encoding="utf-8")
    assert "CONFG-5004 Observability configured" in output
    assert "TIMER-3002 Timer started for Reading at 09:00:00" in output


def test_configured_loggers_are_the_native_protepo_log_instances():

    loggers = configure_observability(None, console_enabled=False, include_seq=False)
    try:
        assert loggers.application is Log.get_logger(ApplicationEvents)
        assert loggers.ui is Log.get_logger(UiEvents)
        assert loggers.timer is Log.get_logger(TimerEvents)
        assert loggers.storage is Log.get_logger(StorageEvents)
        assert loggers.configuration is Log.get_logger(ConfigurationEvents)
        assert loggers.cli is Log.get_logger(CliEvents)
        assert Log.get_effective_mode() is AudienceMode.ENGINEERING
        assert REQUIRED_PROTEPO_LOG_VERSION == "2.0.0"
    finally:
        shutdown_observability()


def test_formal_v2_launch_event_contains_structured_properties():

    output = []
    Log.configure(
        application="LearningClock",
        mode=AudienceMode.ENGINEERING,
        console_enabled=False,
        callback=output.append,
        callback_mode=AudienceMode.ENGINEERING,
        preserve_existing_handlers=False,
    )
    try:
        with Log.context("launch-correlation"):
            Log.get_logger("protepo.learningclock.test").event(
                LAUNCH_REQUESTED,
                clock_id="magpai",
                clock_name="MAGPAI",
                configuration_path="MAGPAI.properties",
                parent_process_id=123,
                runtime_mode="source",
                launch_mode="launcherpad",
                application_version="6.0",
            )
    finally:
        Log.shutdown()

    assert len(output) == 1
    assert "LPCRP-3001" in output[0]
    assert '"clock_id":"magpai"' in output[0]
    assert '"correlation_id":"launch-correlation"' in output[0]
    assert '"schema_version":"2.0"' in output[0]
