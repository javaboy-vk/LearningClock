import csv
import os
from datetime import date
from pathlib import Path

import pytest

from learningclock.configuration import (
    ConfigurationError,
    ConfiguredClock,
    discover_clock_configurations,
    load_central_configuration,
    load_properties,
    logs_directory,
    migrate_legacy_clock_configuration,
)
from learningclock.csv_store import ACTIVITIES, FIELDNAMES
from learningclock.provisioning import provision_clock, validate_learning_path_name
from learningclock.reporting import (
    PERIOD_OPTIONS,
    DateRange,
    ReportIssue,
    ReportResult,
    aggregate_clock_time,
    resolve_date_range,
)


def write_properties(path: Path, name: str, log_dir: Path | str, extra: str = "") -> None:
    path.write_text(
        f"# retained comment\nlearning-path-name={name}\nlogDir={log_dir}\n{extra}",
        encoding="utf-8",
    )


def configured_clock(path: Path, name: str, log_dir: Path) -> ConfiguredClock:
    return ConfiguredClock(name.casefold(), name, name, path, log_dir)


def test_standard_props_directory_resolves_sibling_logs_directory():
    assert logs_directory(Path(r"D:\LearningClock\props")) == Path(
        r"D:\LearningClock\logs"
    )


def test_custom_configuration_directory_keeps_logs_within_custom_root(tmp_path):
    assert logs_directory(tmp_path / "config") == (tmp_path / "config" / "logs").resolve()


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def test_central_configuration_loads_literal_windows_paths_and_spaces(tmp_path):
    properties = tmp_path / "clock.properties"
    properties.write_text(
        "pythonExe=P:\\Python Tools\\Python314\\pythonw.exe\n"
        "pyScriptPath=D:\\Learning Path\\LearningClock\\app.py\n",
        encoding="utf-8",
    )
    values = load_properties(properties)
    assert values["pythonExe"] == r"P:\Python Tools\Python314\pythonw.exe"
    assert values["pyScriptPath"] == r"D:\Learning Path\LearningClock\app.py"
    central = load_central_configuration(properties)
    if os.name == "nt":
        assert str(central.python_executable) == r"P:\Python Tools\Python314\pythonw.exe"
        assert str(central.script_path) == r"D:\Learning Path\LearningClock\app.py"


@pytest.mark.parametrize(
    "content, message",
    [
        ("pyScriptPath=app.py\n", "pythonExe"),
        ("pythonExe=   \npyScriptPath=app.py\n", "pythonExe"),
        ("pythonExe=pythonw.exe\n", "pyScriptPath"),
    ],
)
def test_central_configuration_rejects_missing_or_blank_values(tmp_path, content, message):
    properties = tmp_path / "clock.properties"
    properties.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigurationError, match=message):
        load_central_configuration(properties)


def test_central_configuration_missing_and_runtime_paths_are_actionable(tmp_path):
    with pytest.raises(ConfigurationError, match="could not read"):
        load_central_configuration(tmp_path / "missing.properties")
    properties = tmp_path / "clock.properties"
    properties.write_text("pythonExe=missing.exe\npyScriptPath=missing.py\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Python executable does not exist"):
        load_central_configuration(properties, validate_paths=True)


def test_central_configuration_resolution_is_independent_of_cwd(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    elsewhere = tmp_path / "elsewhere"
    runtime.mkdir()
    elsewhere.mkdir()
    (runtime / "pythonw.exe").write_bytes(b"")
    (runtime / "app.py").write_text("", encoding="utf-8")
    properties = runtime / "clock.properties"
    properties.write_text("pythonExe=pythonw.exe\npyScriptPath=app.py\n", encoding="utf-8")
    monkeypatch.chdir(elsewhere)
    central = load_central_configuration(properties, validate_paths=True)
    assert central.python_executable == (runtime / "pythonw.exe").resolve()
    assert central.script_path == (runtime / "app.py").resolve()


def test_old_four_property_file_is_loaded_then_migrated_without_using_shared_values(tmp_path):
    path = tmp_path / "Alpha.properties"
    write_properties(
        path,
        "Alpha",
        tmp_path / "logs",
        "pythonExe=obsolete.exe\npyScriptPath=obsolete.py\ncustom=value\n",
    )
    result = discover_clock_configurations(tmp_path)
    assert [clock.learning_path_name for clock in result.clocks] == ["Alpha"]
    migrated = path.read_text(encoding="utf-8")
    assert "# retained comment" in migrated
    assert "learning-path-name=Alpha" in migrated
    assert "custom=value" in migrated
    assert "pythonExe" not in migrated and "pyScriptPath" not in migrated
    assert migrate_legacy_clock_configuration(path) is False


def test_old_four_property_file_migrates_legacy_learningpath_log_dir_to_clock_root(tmp_path):
    path = tmp_path / "Alpha.properties"
    clock_root = tmp_path / "Alpha"
    write_properties(
        path,
        "Alpha",
        clock_root / "LearningPath",
        "pythonExe=obsolete.exe\npyScriptPath=obsolete.py\n",
    )
    result = discover_clock_configurations(tmp_path)
    assert result.clocks[0].log_dir == clock_root
    assert f"logDir={clock_root}" in path.read_text(encoding="utf-8")


def test_two_property_file_migrates_legacy_learningpath_log_dir_to_clock_root(tmp_path):
    path = tmp_path / "Alpha.properties"
    clock_root = tmp_path / "Alpha"
    write_properties(path, "Alpha", clock_root / "LearningPath")
    result = discover_clock_configurations(tmp_path)
    assert result.clocks[0].log_dir == clock_root
    migrated = path.read_text(encoding="utf-8")
    assert f"logDir={clock_root}" in migrated
    assert "learning-path-name=Alpha" in migrated


def test_duplicate_names_and_canonical_log_directories_are_isolated(tmp_path):
    write_properties(tmp_path / "a.properties", "Alpha", tmp_path / "one")
    write_properties(tmp_path / "b.properties", "alpha", tmp_path / "two")
    write_properties(tmp_path / "c.properties", "Charlie", tmp_path / "one" / ".")
    result = discover_clock_configurations(tmp_path)
    assert [clock.learning_path_name for clock in result.clocks] == ["Alpha"]
    assert len(result.issues) == 2


@pytest.mark.parametrize(
    "name", ["", "..", "../escape", "bad/name", "bad:name", "NUL", "trail.", "Ελληνικά"]
)
def test_new_clock_rejects_unsafe_names(name):
    with pytest.raises(ConfigurationError):
        validate_learning_path_name(name)


def test_provisioning_creates_exact_config_csv_and_immediate_discovery(tmp_path):
    config_dir = tmp_path / "config"
    log_dir = tmp_path / "Diavgeia Vault" / "Engineering" / "Alpha"
    result = provision_clock(config_dir, "Alpha Clock", log_dir)
    assert result.plan.properties_path.read_text(encoding="utf-8") == (
        f"learning-path-name=Alpha Clock\nlogDir={log_dir.resolve()}\n"
    )
    assert "pythonExe" not in result.plan.properties_path.read_text(encoding="utf-8")
    assert result.plan.csv_path.read_text(encoding="utf-8").splitlines()[0] == ",".join(FIELDNAMES)
    assert result.plan.csv_path == log_dir / "LearningPath" / "learning_time_log.csv"
    assert not (log_dir / "Learning-Clock-Dashboard.md").exists()
    assert not (log_dir / "views").exists()
    discovery = discover_clock_configurations(config_dir)
    assert [clock.learning_path_name for clock in discovery.clocks] == ["Alpha Clock"]


def test_provisioning_conflicts_do_not_overwrite_existing_files(tmp_path):
    config_dir = tmp_path / "config"
    log_dir = tmp_path / "Alpha"
    (log_dir / "LearningPath").mkdir(parents=True)
    existing = log_dir / "LearningPath" / "learning_time_log.csv"
    existing.write_text("user data", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="overwrite"):
        provision_clock(config_dir, "Alpha", log_dir)
    assert existing.read_text(encoding="utf-8") == "user data"


def test_provisioning_reuses_existing_directory_without_touching_unrelated_files(tmp_path):
    config_dir = tmp_path / "config"
    log_dir = tmp_path / "Alpha"
    log_dir.mkdir(parents=True)
    marker = log_dir / "notes.md"
    marker.write_text("user notes", encoding="utf-8")
    result = provision_clock(config_dir, "Alpha", log_dir)
    assert marker.read_text(encoding="utf-8") == "user notes"
    assert result.plan.csv_path.is_file()


def test_provisioning_never_copies_dashboard_resources_to_clock_directories(tmp_path):
    config_dir = tmp_path / "config"
    engineering = tmp_path / "vault" / "Engineering"
    provision_clock(config_dir, "Alpha", engineering / "Alpha")
    provision_clock(config_dir, "Beta", engineering / "Beta")
    assert not (engineering / "Alpha" / "Learning-Clock-Dashboard.md").exists()
    assert not (engineering / "Beta" / "Learning-Clock-Dashboard.md").exists()
    assert not (engineering / "Alpha" / "views").exists()
    assert not (engineering / "Beta" / "views").exists()


def test_dashboard_export_writes_one_central_markdown_and_view(tmp_path):
    from scripts import dev

    vault_root = tmp_path / "vault"
    central = vault_root / "Engineering" / "LearningClock"
    central.mkdir(parents=True)
    obsolete_dashboard = central / "Learning-Clock-Dashboard.md"
    obsolete_dashboard.write_text("obsolete generated dashboard", encoding="utf-8")

    dev.export_dashboard_components(
        dashboard_target_dir=vault_root,
        views_target_dir=central / "views",
    )

    shared_view = central / "views" / "learning-clock-dashboard" / "view.js"
    assert shared_view.is_file()
    dashboard = vault_root / "Learning-Clock-Dashboard.md"
    assert "single LearningClock dashboard" in dashboard.read_text(encoding="utf-8")
    assert not obsolete_dashboard.exists()
    view = shared_view.read_text(encoding="utf-8")
    assert "discoverClockSources" in view
    assert "lc-clock-selector" in view
    assert '(left.label || left.name).localeCompare(' in view
    assert 'sensitivity: "base", numeric: true' in view
    assert '"Engineering/LearningClock/views/learning-clock-dashboard"' in (
        dashboard.read_text(encoding="utf-8")
    )


def test_partial_provisioning_failure_removes_only_created_content(tmp_path, monkeypatch):
    from learningclock import provisioning

    config_dir = tmp_path / "config"
    clock_parent = tmp_path / "existing"
    clock_parent.mkdir()
    marker = clock_parent / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    log_dir = clock_parent / "Alpha"
    real_write = provisioning._atomic_write
    calls = 0

    def fail_second(path, content):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated failure")
        real_write(path, content)

    monkeypatch.setattr(provisioning, "_atomic_write", fail_second)
    with pytest.raises(OSError, match="simulated"):
        provision_clock(config_dir, "Alpha", log_dir)
    assert marker.read_text(encoding="utf-8") == "keep"
    assert not (config_dir / "Alpha.properties").exists()
    assert not log_dir.exists()


def test_date_range_presets_cover_week_month_year_and_leap_boundaries():
    assert resolve_date_range("This week", today=date(2026, 9, 11)) == DateRange(
        date(2026, 9, 7), date(2026, 9, 11)
    )
    assert resolve_date_range("Last week", today=date(2026, 1, 1)) == DateRange(
        date(2025, 12, 22), date(2025, 12, 28)
    )
    assert resolve_date_range("This month", today=date(2024, 2, 29)) == DateRange(
        date(2024, 2, 1), date(2024, 2, 29)
    )
    assert PERIOD_OPTIONS == ("This week", "Last week", "This month", "Define range")
    with pytest.raises(ValueError, match="after"):
        DateRange(date(2026, 2, 2), date(2026, 2, 1))


def test_aggregation_uses_inclusive_session_rows_all_categories_and_legacy_columns(tmp_path):
    alpha_dir = tmp_path / "alpha"
    beta_dir = tmp_path / "beta"
    alpha = configured_clock(tmp_path / "a.properties", "Alpha", alpha_dir)
    beta = configured_clock(tmp_path / "b.properties", "Beta", beta_dir)
    row = {field: "" for field in FIELDNAMES}
    row.update(date="2026-09-07", reading="30:00:00", book_listening="01:00:00")
    total = {field: "99:00:00" for field in FIELDNAMES}
    total["date"] = "TOTAL"
    write_csv(alpha_dir / "LearningPath" / "learning_time_log.csv", [row, total])
    legacy_fields = ["date", "audiobook", "memorizing", "experimenting"]
    write_csv(
        beta_dir / "LearningPath" / "learning_time_log.csv",
        [
            {"date": "09/08/2026", "audiobook": "00:30:00", "memorizing": "00:20:00", "experimenting": "00:10:00"},
            {"date": "09/12/2026", "audiobook": "10:00:00"},
        ],
        legacy_fields,
    )
    result = aggregate_clock_time(
        [alpha, beta], DateRange(date(2026, 9, 7), date(2026, 9, 11))
    )
    totals = dict(result.totals)
    assert tuple(totals) == tuple(ACTIVITIES)
    assert totals["Reading"] == 30 * 3600
    assert totals["Book Listening"] == 90 * 60
    assert totals["Active Recall"] == 20 * 60
    assert totals["Sandbox"] == 10 * 60
    assert result.total_seconds == 32 * 3600
    assert result.clock_count == 2
    assert result.row_count == 2


def test_aggregation_isolates_missing_duplicate_and_malformed_sources(tmp_path):
    valid_dir = tmp_path / "valid"
    valid = configured_clock(tmp_path / "valid.properties", "Valid", valid_dir)
    duplicate = configured_clock(tmp_path / "duplicate.properties", "Duplicate", valid_dir / ".")
    missing = configured_clock(tmp_path / "missing.properties", "Missing", tmp_path / "missing")
    fields = ["date", "reading"]
    write_csv(
        valid_dir / "LearningPath" / "learning_time_log.csv",
        [
            {"date": "2026-09-11", "reading": "00:10:00"},
            {"date": "2026-09-11", "reading": "bad"},
            {"date": "bad", "reading": "01:00:00"},
        ],
        fields,
    )
    result = aggregate_clock_time(
        [valid, duplicate, missing], DateRange(date(2026, 9, 11), date(2026, 9, 11))
    )
    assert dict(result.totals)["Reading"] == 600
    assert result.clock_count == 1
    assert result.row_count == 2
    assert result.warning_count == 4
    assert result.warnings == tuple(issue.message for issue in result.issues)

    duration_issue, date_issue, duplicate_issue, unavailable_issue = result.issues
    assert duration_issue.source_path == (
        valid_dir / "LearningPath" / "learning_time_log.csv"
    ).resolve()
    assert duration_issue.row_number == 3
    assert duration_issue.column == "reading"
    assert duration_issue.value == "bad"
    assert duration_issue.reason == "invalid duration at row 3"
    assert date_issue.row_number == 4
    assert date_issue.column == "date"
    assert date_issue.value == "bad"
    assert duplicate_issue.source_path == duplicate.configuration_path.resolve()
    assert duplicate_issue.column == "logDir"
    assert unavailable_issue.source_path == missing.configuration_path.resolve()
    assert unavailable_issue.column == "logDir"


def test_launcherpad_source_exposes_required_ui_and_stale_result_guard():
    source = (Path(__file__).resolve().parents[1] / "src/learningclock/launcherpad.py").read_text(
        encoding="utf-8"
    )
    assert "Create New Clock" in source
    assert "filedialog.askdirectory" in source
    assert "show_date_picker" in source
    assert "request_id != self.report_request_id" in source
    assert 'state="readonly"' in source
    assert 'cursor="hand2"' in source
    assert "show_report_issues" in source
    assert "open_report_issue_source" in source
    assert "This report scan is read-only" in source


def test_stale_report_result_is_not_rendered():
    from learningclock.launcherpad import LauncherPad

    launcher = LauncherPad.__new__(LauncherPad)
    launcher.report_request_id = 2
    launcher.closed = False
    rendered = []
    launcher.render_histogram = rendered.append
    launcher.report_summary = type("Label", (), {"config": lambda *_args, **_kwargs: None})()
    result = aggregate_clock_time([], DateRange(date(2026, 9, 1), date(2026, 9, 1)))
    launcher.apply_report_result(1, result)
    assert rendered == []


def test_current_report_renders_skipped_input_as_diagnostic_link(tmp_path):
    from learningclock.launcherpad import LauncherPad

    class FakeLabel:
        def __init__(self):
            self.values = {}

        def config(self, **values):
            self.values.update(values)

    source = tmp_path / "learning_time_log.csv"
    issue = ReportIssue(
        clock_name="Broken Clock",
        source_path=source,
        input_kind="duration",
        reason="invalid duration at row 7",
        message="Ignored an invalid duration in row 7 of Broken Clock.",
        row_number=7,
        column="reading",
        value="bad",
    )
    result = ReportResult(
        date_range=DateRange(date(2026, 9, 1), date(2026, 9, 11)),
        totals=(),
        total_seconds=0,
        clock_count=0,
        row_count=0,
        warning_count=1,
        warnings=(issue.message,),
        issues=(issue,),
    )
    launcher = LauncherPad.__new__(LauncherPad)
    launcher.report_request_id = 1
    launcher.closed = False
    launcher.report_summary = FakeLabel()
    launcher.report_issue_link = FakeLabel()
    launcher.report_issues = ()
    launcher.render_histogram = lambda _result: None

    launcher.apply_report_result(1, result)

    assert "skipped/invalid" not in launcher.report_summary.values["text"]
    assert launcher.report_issue_link.values["text"] == " · 1 skipped/invalid inputs"
    assert launcher.report_issues == (issue,)


def test_packaging_includes_central_configuration_and_dashboard_resources():
    root = Path(__file__).resolve().parents[1]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert '"clock.properties"' in pyproject
    assert "Learning-Clock-Dashboard.md" in pyproject
    assert "learning-clock-dashboard/view.js" in pyproject.replace("\\", "/")
    release = (root / "scripts/dev.py").read_text(encoding="utf-8")
    assert 'lib_dir / "learningclock" / source.name' in release
    assert 'production_root / "app.py"' not in release
    assert 'lib_dir / "learningclock" / "dashboard_assets"' in release
