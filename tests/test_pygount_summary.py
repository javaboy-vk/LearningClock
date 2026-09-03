# =============================================================================
# File Name : test_pygount_summary.py
# Artifact  : LearningClock - Engineering Scorecard Generator Tests
# Author    : javaboy-vk
# Date      : 2026-09-02
# Version   : v0.1.0
# Purpose:
#   Verifies repository inventory classification, Pygount presentation, and the
#   generated LearningClock Engineering Scorecard contract.
# =============================================================================

from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from scripts import pygount_summary


def sample_report(paths: list[str]) -> dict[str, object]:
    return {
        "files": [
            {
                "path": path,
                "language": (
                    "Markdown"
                    if path.endswith(".md")
                    else "YAML"
                    if path.endswith((".yml", ".yaml"))
                    else "Python"
                ),
                "lineCount": 10,
                "sourceCount": 6,
                "documentationCount": 3,
                "emptyCount": 1,
            }
            for path in paths
        ]
    }


def test_scorecard_categories_partition_learningclock_workspace() -> None:
    paths = [
        "src/learningclock/app.py",
        "launcher/dev.properties",
        "tests/test_app_ui.py",
        "benchmarks/benchmark_csv.py",
        "README.md",
        "docs/usage.md",
        "diavgeia/LearningClock/6.0/Overview.md",
        ".github/workflows/coverage-pages.yml",
        "scripts/dev.py",
        "pyproject.toml",
    ]
    categories = pygount_summary.scorecard_categories(paths)
    assert categories == {
        "Application Source": [
            "src/learningclock/app.py",
            "launcher/dev.properties",
        ],
        "Tests and Benchmarks": [
            "tests/test_app_ui.py",
            "benchmarks/benchmark_csv.py",
        ],
        "Documentation": [
            "README.md",
            "docs/usage.md",
            "diavgeia/LearningClock/6.0/Overview.md",
        ],
        "DevOps": [
            ".github/workflows/coverage-pages.yml",
            "scripts/dev.py",
            "pyproject.toml",
        ],
    }
    categorized = [path for values in categories.values() for path in values]
    assert sorted(categorized) == sorted(paths)
    assert len(categorized) == len(set(categorized))


def test_pygount_rows_and_svg_use_scorecard_table_format() -> None:
    paths = ["src/learningclock/app.py", "README.md", ".github/workflows/pages.yml"]
    report = sample_report(paths)
    rows = pygount_summary.build_summary_rows(report, paths)
    assert rows[-1] == ["Sum", "3", "100.0", "30", "100.0", "18", "9", "3"]
    svg = pygount_summary.render_svg(report, paths)
    assert 'fill="#0b43d9"' in svg
    assert "Repository Inventory" in svg
    assert "Entire LearningClock repository" in svg
    assert ">Files</text>" in svg
    assert ">%</text>" in svg
    assert ">Sum</text>" in svg


def test_landing_page_matches_protepo_scorecard_sections(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    paths = [
        "src/learningclock/app.py",
        "tests/test_app_ui.py",
        "benchmarks/benchmark_csv.py",
        "README.md",
        ".github/workflows/coverage-pages.yml",
    ]
    report = sample_report(paths)
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(pygount_summary, "SCORECARD_HTML", reports / "index.html")
    monkeypatch.setattr(pygount_summary, "ROOT_INDEX_HTML", reports / "root-index.html")
    monkeypatch.setattr(pygount_summary, "project_version", lambda: "9.8")
    monkeypatch.setattr(pygount_summary, "coverage_label", lambda: "97.25% line coverage")
    monkeypatch.setattr(
        pygount_summary,
        "junit_totals",
        lambda: {"tests": 12, "failures": 0, "errors": 0, "skipped": 1},
    )
    pygount_summary.generate_landing_page(
        report,
        paths,
        pygount_summary.scorecard_categories(paths),
    )
    portal = (reports / "index.html").read_text(encoding="utf-8")
    assert "<title>LearningClock 9.8 Engineering Scorecard</title>" in portal
    assert "<h1>LearningClock 9.8 Engineering Scorecard</h1>" in portal
    assert "--engineering-blue:#069bff" in portal
    assert "background:#0b43d9" in portal
    for card in (
        "Overview",
        "Tests",
        "LearningClock coverage",
        "Performance tests",
        "Benchmarks",
        "Diavgeia",
    ):
        assert f"<h2>{card}</h2>" in portal
    for inventory in (
        "Repository Inventory",
        "Application Source",
        "Tests and Benchmarks",
        "Documentation",
        "DevOps",
    ):
        assert f"<h3>{inventory} " in portal
    assert portal.count('class="pygount-table"') == 5
    assert "entire LearningClock workspace" in portal
    assert "97.25% line coverage" in portal
    assert 'href="../coverage/index.html"' in portal
    assert "12 executions; 0 failures; 0 errors" in portal
    assert "tree/main/diavgeia/LearningClock" in portal
    assert "reports/index.html" in (reports / "root-index.html").read_text(encoding="utf-8")


def test_junit_totals_reads_pytest_testsuites_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    junit = tmp_path / "pytest-results.xml"
    root = ET.Element("testsuites", {"name": "pytest tests"})
    ET.SubElement(
        root,
        "testsuite",
        {"tests": "107", "failures": "0", "errors": "0", "skipped": "2"},
    )
    ET.ElementTree(root).write(junit, encoding="utf-8", xml_declaration=True)
    monkeypatch.setattr(pygount_summary, "JUNIT_XML", junit)
    assert pygount_summary.junit_totals() == {
        "tests": 107,
        "failures": 0,
        "errors": 0,
        "skipped": 2,
    }


def test_supporting_reports_are_explicit_when_workloads_are_absent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tests_dir = tmp_path / "tests"
    performance_dir = tmp_path / "performance"
    benchmark_dir = tmp_path / "benchmarks"
    coverage_index = tmp_path / "coverage" / "index.html"
    monkeypatch.setattr(pygount_summary, "TEST_REPORT_DIR", tests_dir)
    monkeypatch.setattr(pygount_summary, "PERFORMANCE_REPORT_DIR", performance_dir)
    monkeypatch.setattr(pygount_summary, "BENCHMARK_REPORT_DIR", benchmark_dir)
    monkeypatch.setattr(pygount_summary, "COVERAGE_INDEX_HTML", coverage_index)
    monkeypatch.setattr(pygount_summary, "junit_totals", lambda: None)
    pygount_summary.generate_supporting_reports(["tests/test_app_ui.py"])
    assert "No JUnit result is present" in (tests_dir / "index.html").read_text(encoding="utf-8")
    assert "html/index.html" in coverage_index.read_text(encoding="utf-8")
    assert "does not imply unmeasured performance evidence" in (
        performance_dir / "index.html"
    ).read_text(encoding="utf-8")
    assert "does not fabricate benchmark evidence" in (
        benchmark_dir / "index.html"
    ).read_text(encoding="utf-8")
