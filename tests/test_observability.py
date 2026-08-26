# =============================================================================
# File Name : test_observability.py
# Artifact  : LearningClock - Application Observability Tests
# Author    : javaboy-vk
# Date      : 2026-08-24
# Version   : v0.1.2
# Purpose:
#   Verifies LearningClock event-catalog integrity and native protepo.log
#   semantic file output.
# =============================================================================

from __future__ import annotations

from protepo.log import Log

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
    configure_observability,
    correlation_context,
    shutdown_observability,
)


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
    finally:
        shutdown_observability()
