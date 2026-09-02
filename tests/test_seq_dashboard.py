# =============================================================================
# File Name : test_seq_dashboard.py
# Artifact  : LearningClock - Seq Dashboard Contract Tests
# Author    : javaboy-vk
# Date      : 2026-08-31
# Version   : v1.1.1
# Purpose:
#   Validates the version-controlled workspace, queries, operations dashboard,
#   and idempotent credential-free installer without requiring live Seq.
# =============================================================================

import json
from pathlib import Path

SEQ_ROOT = Path(__file__).resolve().parents[1] / "monitoring" / "seq"
SEQ_BROWSER_EXTENSION_ROOT = SEQ_ROOT / "browser-extension"


def read_json(name):
    return json.loads((SEQ_ROOT / name).read_text(encoding="utf-8"))


def test_dashboard_covers_launcher_runtime_integrity_and_diagnostics():
    dashboard = read_json("dashboard-LearningClock.template")
    by_title = {chart["Title"]: chart for chart in dashboard["Charts"]}
    recent_events = by_title["Recent LearningClock Events"]["Queries"][0]

    assert dashboard["Title"] == "LearningClock Operations"
    assert recent_events["Limit"] == 200
    assert [measurement["Label"] for measurement in recent_events["Measurements"]] == [
        "Timestamp",
        "Level",
        "EventId",
        "Message",
        "ClockId",
    ]
    assert recent_events["Measurements"][2]["Value"] == "EventCode"
    assert recent_events["Measurements"][-2]["Value"] == "@Message"
    assert recent_events["Measurements"][-1]["Value"] == "properties.clock_id"
    assert {measurement["Value"] for measurement in recent_events["Measurements"]}.isdisjoint(
        {"@Id", "ProcessId", "Environment", "CorrelationId"}
    )
    assert recent_events["DisplayStyle"]["Type"] == "Table"
    assert by_title["Recent LearningClock Events"]["DisplayStyle"]["WidthColumns"] == 12
    assert {
        "Application Health",
        "Recently Active Clocks",
        "Launch Activity",
        "Duplicate-Instance Protection",
        "Configuration Health",
        "Persistence Health",
        "Warnings and Errors",
        "Events by Component",
    }.issubset(by_title)
    dashboard_text = json.dumps(dashboard)
    assert "properties.clock_id" in dashboard_text
    assert "MUTEX-4004" in dashboard_text
    assert "STORG-" in dashboard_text


def test_browser_extension_keeps_dashboard_rows_on_one_line_with_horizontal_overflow():
    manifest = json.loads(
        (SEQ_BROWSER_EXTENSION_ROOT / "manifest.json").read_text(encoding="utf-8")
    )
    stylesheet = (SEQ_BROWSER_EXTENSION_ROOT / "seq-dashboard.css").read_text(encoding="utf-8")
    script = (SEQ_BROWSER_EXTENSION_ROOT / "seq-dashboard.js").read_text(encoding="utf-8")

    assert manifest["manifest_version"] == 3
    assert manifest["content_scripts"][0]["css"] == ["seq-dashboard.css"]
    assert manifest["content_scripts"][0]["js"] == ["seq-dashboard.js"]
    assert {"http://localhost/*", "https://localhost/*"}.issubset(
        manifest["content_scripts"][0]["matches"]
    )
    assert ".learningclock-recent-events .chart-table" in stylesheet
    assert "overflow-x: auto !important" in stylesheet
    assert "white-space: nowrap !important" in stylesheet
    assert "width: max-content !important" in stylesheet
    assert 'TARGET_CHART_TITLE = "Recent LearningClock Events"' in script
    assert 'TARGET_CHART_CLASS = "learningclock-recent-events"' in script


def test_signal_saved_query_and_workspace_support_tailing_and_filters():
    signal = read_json("signal-LearningClock - All Events.template")
    query = read_json("sqlquery-LearningClock Events - Log Format.template")
    workspace = (SEQ_ROOT / "workspace-LearningClock.template").read_text(encoding="utf-8")

    assert signal["Filters"][0]["Filter"] == "Application = 'LearningClock'"
    assert {column["Expression"] for column in signal["Columns"]} >= {
        "EventCode",
        "Module",
        "properties.clock_id",
        "ProcessId",
        "CorrelationId",
    }
    assert "order by Timestamp desc" in query["Sql"]
    assert "limit 200" in query["Sql"]
    assert 'ref("signal-LearningClock - All Events.template")' in workspace
    assert 'ref("dashboard-LearningClock.template")' in workspace


def test_installer_merges_without_persisting_credentials():
    installer = (SEQ_ROOT / "Install-LearningClockSeqDashboard.ps1").read_text(encoding="utf-8")
    ignored = (SEQ_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert '"template"' in installer
    assert '"import"' in installer
    assert '"--merge"' in installer
    assert "$env:SEQ_ADMIN_API_KEY" in installer
    assert "$env:SEQ_API_KEY" in installer
    assert "import.state" in ignored
    assert "<session-only administrative key>" not in installer
