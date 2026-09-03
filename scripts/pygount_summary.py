# =============================================================================
# File Name : pygount_summary.py
# Artifact  : LearningClock - Engineering Scorecard and Pygount Inventory
# Author    : javaboy-vk
# Date      : 2026-06-09
# Version   : v0.2.3
# Purpose:
#   Generates a repository-wide Pygount inventory, a LearningClock-specific
#   breakdown, and the local/GitHub Pages Engineering Scorecard.
# =============================================================================

from __future__ import annotations

import ast
import html
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BUILD_REPORT_DIR = ROOT / "build" / "reports"
SUMMARY_TEXT = BUILD_REPORT_DIR / "pygount-summary.txt"
SUMMARY_SVG = BUILD_REPORT_DIR / "pygount-summary.svg"
SCORECARD_HTML = BUILD_REPORT_DIR / "index.html"
OVERVIEW_HTML = BUILD_REPORT_DIR / "overview.html"
ROOT_INDEX_HTML = BUILD_REPORT_DIR / "root-index.html"
TEST_REPORT_DIR = ROOT / "build" / "tests"
JUNIT_XML = TEST_REPORT_DIR / "junit" / "pytest-results.xml"
COVERAGE_JSON = ROOT / "build" / "coverage" / "coverage.json"
COVERAGE_INDEX_HTML = ROOT / "build" / "coverage" / "index.html"
PERFORMANCE_REPORT_DIR = ROOT / "build" / "performance"
BENCHMARK_REPORT_DIR = ROOT / "build" / "benchmarks"
EXCLUDED_FILENAMES = {".gitignore", ".gitkeep"}
HIDDEN_LANGUAGE_BUCKETS = {"__binary__", "__duplicate__", "__generated__"}
DISPLAY_LANGUAGE_NAMES = {"__unknown__": "Env Config"}
TABLE_COLUMNS = ["Language", "Files", "%", "Lines", "%", "Code", "Comment", "Blank"]
SCORECARD_CATEGORY_NAMES = (
    "Application Source",
    "Tests and Benchmarks",
    "Documentation",
    "DevOps",
)
INVENTORY_DESCRIPTIONS = {
    "Repository Inventory": (
        "Entire LearningClock repository across application source, assurance, "
        "documentation, and build infrastructure."
    ),
    "Application Source": (
        "LearningClock package modules, packaged assets, and LauncherPad runtime resources."
    ),
    "Tests and Benchmarks": (
        "Unit, regression, UI, integration, performance, and benchmark assurance code."
    ),
    "Documentation": (
        "README, authored guides, API contracts, and versioned Diavgeia material."
    ),
    "DevOps": (
        "Developer commands, packaging configuration, editor support, and CI workflows."
    ),
}
TERMINAL_BLUE = "#0b43d9"
TERMINAL_WHITE = "#ffffff"
GITHUB_REPOSITORY = "https://github.com/javaboy-vk/LearningClock"


def project_version() -> str:
    version_file = ROOT / "src" / "learningclock" / "__init__.py"
    tree = ast.parse(version_file.read_text(encoding="utf-8"), filename=str(version_file))
    versions = [
        node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if len(versions) != 1:
        raise RuntimeError(
            f"Expected one static __version__ string assignment in {version_file}; "
            f"found {len(versions)}."
        )
    return versions[0]


def pygount_executable() -> Path:
    executable = ROOT / ".venv" / "Scripts" / "pygount.exe"
    if executable.exists():
        return executable
    found = shutil.which("pygount")
    if found:
        return Path(found)
    raise SystemExit(
        "pygount is not installed. Run scripts\\dev.cmd install, then rerun "
        "scripts\\pygount-summary.cmd."
    )


def source_controlled_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = []
    for raw_path in result.stdout.decode("utf-8").split("\0"):
        if not raw_path:
            continue
        normalized = raw_path.replace("\\", "/")
        if Path(normalized).name in EXCLUDED_FILENAMES:
            continue
        if (ROOT / normalized).is_file():
            paths.append(normalized)
    if not paths:
        raise SystemExit("No Git-tracked files were found for the pygount summary.")
    return paths


def run_pygount(paths: list[str]) -> dict[str, Any]:
    command = [str(pygount_executable()), "--duplicates", "--format=json", *paths]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise SystemExit(f"Unable to parse pygount JSON output: {error}") from error


def scorecard_category(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith(("src/", "launcher/")):
        return "Application Source"
    if normalized.startswith(("tests/", "benchmarks/")):
        return "Tests and Benchmarks"
    if normalized == "README.md" or normalized.startswith(("docs/", "diavgeia/")):
        return "Documentation"
    return "DevOps"


def scorecard_categories(paths: list[str]) -> dict[str, list[str]]:
    categories = {name: [] for name in SCORECARD_CATEGORY_NAMES}
    for path in paths:
        categories[scorecard_category(path)].append(path)
    return categories


def percentage(value: int, total: int) -> str:
    return f"{value * 100 / total:.1f}" if total else "0.0"


def build_summary_rows(report: dict[str, Any], paths: list[str]) -> list[list[str]]:
    report_files = {
        str(item.get("path", "")).replace("\\", "/"): item
        for item in report.get("files", [])
    }
    totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"files": 0, "lines": 0, "code": 0, "comment": 0, "blank": 0}
    )
    for raw_path in paths:
        normalized_path = raw_path.replace("\\", "/")
        item = report_files.get(normalized_path, {})
        language = str(item.get("language", "__unknown__"))
        if language in HIDDEN_LANGUAGE_BUCKETS:
            continue
        line_count = int(item.get("lineCount", 0) or 0)
        code_count = int(item.get("sourceCount", 0) or 0)
        comment_count = int(item.get("documentationCount", 0) or 0)
        blank_count = int(item.get("emptyCount", 0) or 0)
        if language == "__unknown__":
            try:
                unknown_lines = (ROOT / normalized_path).read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                unknown_lines = []
            if unknown_lines:
                line_count = len(unknown_lines)
                blank_count = sum(not line.strip() for line in unknown_lines)
                code_count = line_count - blank_count
                comment_count = 0
        language = DISPLAY_LANGUAGE_NAMES.get(language, language)
        if language.startswith("__"):
            continue
        values = totals[language]
        values["files"] += 1
        values["lines"] += line_count
        values["code"] += code_count
        values["comment"] += comment_count
        values["blank"] += blank_count

    total_files = sum(values["files"] for values in totals.values())
    total_lines = sum(values["lines"] for values in totals.values())
    rows = [
        [
            language,
            str(values["files"]),
            percentage(values["files"], total_files),
            str(values["lines"]),
            percentage(values["lines"], total_lines),
            str(values["code"]),
            str(values["comment"]),
            str(values["blank"]),
        ]
        for language, values in sorted(
            totals.items(), key=lambda entry: (-entry[1]["lines"], entry[0].lower())
        )
    ]
    rows.append(
        [
            "Sum",
            str(total_files),
            "100.0" if total_files else "0.0",
            str(total_lines),
            "100.0" if total_lines else "0.0",
            str(sum(values["code"] for values in totals.values())),
            str(sum(values["comment"] for values in totals.values())),
            str(sum(values["blank"] for values in totals.values())),
        ]
    )
    return rows


def render_summary_text(rows: list[list[str]]) -> str:
    widths = [
        max(len(row[index]) for row in [TABLE_COLUMNS, *rows])
        for index in range(len(TABLE_COLUMNS))
    ]

    def format_row(row: list[str]) -> str:
        return "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))

    divider = "  ".join("-" * width for width in widths)
    return "\n".join([format_row(TABLE_COLUMNS), divider, *(format_row(row) for row in rows)]) + "\n"


def render_svg(
    report: dict[str, Any],
    paths: list[str],
    title: str = "Repository Inventory",
    description: str = INVENTORY_DESCRIPTIONS["Repository Inventory"],
) -> str:
    rows = build_summary_rows(report, paths)
    detail_rows = rows[:-1]
    display_rows = detail_rows if len(detail_rows) == 1 else rows
    all_rows = [TABLE_COLUMNS, *display_rows]
    char_width = 17
    row_height = 38
    top_padding = 26
    side_padding = 26
    table_top = 76
    cell_padding = 30
    border_width = 4
    minimum_widths = [390, 135, 110, 155, 110, 155, 175, 155]
    column_widths = []
    for column_index, minimum_width in enumerate(minimum_widths):
        longest = max(len(row[column_index]) for row in all_rows)
        column_widths.append(max(minimum_width, longest * char_width + cell_padding * 2))
    width = sum(column_widths) + side_padding * 2
    table_height = row_height * (len(display_rows) + 1)
    height = table_top + table_height + top_padding
    description_x = side_padding + len(title) * char_width + 18
    description_width = width - description_x - side_padding
    description_fit = (
        f' textLength="{description_width}" lengthAdjust="spacingAndGlyphs"'
        if (len(description) + 2) * 15 > description_width
        else ""
    )
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(title)} pygount code inventory"',
        f'     viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f'  <rect width="100%" height="100%" fill="{TERMINAL_BLUE}"/>',
        "  <style>",
        "    text{font-family:Consolas,'Courier New',monospace;fill:#fff;font-size:30px;letter-spacing:0}",
        "    .header{font-size:30px}",
        "    .title{font-size:30px;font-weight:700}",
        "    .description{font-size:26px;font-style:italic;font-weight:400}",
        "  </style>",
        f'  <text class="title" x="{side_padding}" y="46">{html.escape(title)}</text>',
        f'  <text class="description" x="{description_x}" y="46"{description_fit}>({html.escape(description)})</text>',
    ]
    x_positions = [side_padding]
    for column_width in column_widths[:-1]:
        x_positions.append(x_positions[-1] + column_width)

    def draw_row(row: list[str], row_index: int, y: int) -> None:
        for column_index, value in enumerate(row):
            x = x_positions[column_index]
            cell_width = column_widths[column_index]
            svg_parts.append(
                f'  <rect x="{x}" y="{y}" width="{cell_width}" height="{row_height}" '
                f'fill="{TERMINAL_BLUE}" stroke="{TERMINAL_WHITE}" stroke-width="{border_width}"/>'
            )
            is_numeric = column_index > 0
            text_anchor = "end" if is_numeric else "start"
            text_x = x + cell_width - cell_padding if is_numeric else x + cell_padding
            css_class = "header" if row_index == 0 else ""
            svg_parts.append(
                f'  <text class="{css_class}" x="{text_x}" y="{y + 28}" '
                f'text-anchor="{text_anchor}">{html.escape(value)}</text>'
            )
    draw_row(TABLE_COLUMNS, 0, table_top)
    for row_index, row in enumerate(display_rows, start=1):
        draw_row(row, row_index, table_top + row_height * row_index)
    svg_parts.extend(["</svg>", ""])
    return "\n".join(svg_parts)


def html_page(title: str, body: str) -> str:
    escaped_title = html.escape(title)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{escaped_title}</title><style>
:root{{--engineering-blue:#069bff;--engineering-header-text:#fff;--engineering-content-bg:#e7e5df;
--engineering-content-text:#1e1e1e;--engineering-panel-blue:#0588df;--engineering-sidebar-blue:#057ed0;
--engineering-soft-border:rgba(255,255,255,.45);--engineering-selection:rgba(110,135,154,.35);
--engineering-yellow:#f8c52a;--engineering-orange:#ff6600}}
*{{box-sizing:border-box}} body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Ubuntu,
Cantarell,"Helvetica Neue",sans-serif;margin:0;background:var(--engineering-content-bg);
color:var(--engineering-content-text);font-weight:700}}
header{{background:var(--engineering-blue);border-bottom:1px solid var(--engineering-sidebar-blue);
color:var(--engineering-header-text)}} header .content,main{{max-width:1100px;margin:0 auto;padding:1rem 2rem}}
h1{{font-size:1.5rem;margin:0}} h2{{color:var(--engineering-sidebar-blue)}}
table{{border-collapse:collapse;width:100%;margin:1rem 0}} th,td{{border:1px solid
var(--engineering-soft-border);padding:.55rem;text-align:left}} th{{background:var(--engineering-blue);
color:var(--engineering-header-text)}} tbody tr:nth-child(even) td{{background:#dddcd6}}
tbody tr:hover td{{background:var(--engineering-selection)}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}}
.card{{border:1px solid var(--engineering-soft-border);border-radius:6px;padding:1rem;background:#dddcd6}}
.card h2{{margin-top:0}} code{{background:#dddcd6;padding:.1rem .25rem}} a{{color:#075985}}
a.button{{display:inline-block;background:var(--engineering-yellow);border:1px solid #d39b00;border-radius:3px;
color:#fff;text-decoration:none;padding:.3rem .65rem;text-shadow:0 1px 2px rgba(0,0,0,.45)}}
a.button:hover,a.button:focus{{background:var(--engineering-orange);border-color:#c94f00}}
footer{{background:var(--engineering-sidebar-blue);color:rgba(255,255,255,.78);margin-top:2rem}}
footer .content{{max-width:1100px;margin:0 auto;padding:.75rem 2rem}}
tfoot td{{background:var(--engineering-panel-blue);color:var(--engineering-header-text)}}
.pygount-panel{{background:#0b43d9;color:#fff;border-radius:6px;margin:1rem 0 2rem;padding:1rem;
box-shadow:0 2px 5px rgba(0,0,0,.18)}}
.pygount-panel h3{{color:#fff;margin:.15rem 0 1rem}}
.pygount-description{{font-size:.86em;font-weight:400}}
.pygount-table-wrap{{overflow-x:auto}} .pygount-table{{min-width:850px;margin:.5rem 0 0}}
.pygount-table th,.pygount-table td{{background:#0b43d9;color:#fff;border:2px solid #fff;
font-family:Consolas,"Courier New",monospace;font-weight:700}}
.pygount-table th:not(:first-child),.pygount-table td:not(:first-child){{text-align:right}}
.pygount-table tbody tr:nth-child(even) td,.pygount-table tbody tr:hover td,
.pygount-table tfoot td{{background:#0b43d9;color:#fff}}
</style></head><body><header><div class="content"><h1>{escaped_title}</h1></div></header>
<main>{body}</main><footer><div class="content">LearningClock engineering evidence</div></footer>
</body></html>"""


def html_table(
    headers: list[str],
    rows: list[list[str]],
    total_row: list[str] | None = None,
    *,
    css_class: str | None = None,
) -> str:
    heading = "".join(f"<th>{html.escape(value)}</th>" for value in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(value)}</td>" for value in row) + "</tr>"
        for row in rows
    )
    footer = ""
    if total_row is not None:
        footer = "<tfoot><tr>" + "".join(
            f"<td>{html.escape(value)}</td>" for value in total_row
        ) + "</tr></tfoot>"
    class_attribute = f' class="{html.escape(css_class)}"' if css_class else ""
    return f"<table{class_attribute}><thead><tr>{heading}</tr></thead><tbody>{body}</tbody>{footer}</table>"


def pygount_panel(title: str, report: dict[str, Any], paths: list[str]) -> str:
    rows = build_summary_rows(report, paths)
    detail_rows = rows[:-1]
    total_row = rows[-1] if len(detail_rows) > 1 else None
    description = INVENTORY_DESCRIPTIONS[title]
    return (
        '<section class="pygount-panel">'
        f"<h3>{html.escape(title)} "
        f'<span class="pygount-description"><em>({html.escape(description)})</em></span></h3>'
        '<div class="pygount-table-wrap">'
        + html_table(TABLE_COLUMNS, detail_rows, total_row, css_class="pygount-table")
        + "</div></section>"
    )


def coverage_label() -> str:
    if not COVERAGE_JSON.exists():
        return "Generate coverage to populate this result"
    payload = json.loads(COVERAGE_JSON.read_text(encoding="utf-8"))
    percent = payload.get("totals", {}).get("percent_covered")
    return f"{float(percent):.2f}% line coverage" if percent is not None else "Unavailable"


def junit_totals() -> dict[str, int] | None:
    if not JUNIT_XML.exists():
        return None
    root = ET.parse(JUNIT_XML).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    return {
        name: sum(int(float(suite.attrib.get(name, 0))) for suite in suites)
        for name in ("tests", "failures", "errors", "skipped")
    }


def inventory_totals(report: dict[str, Any], paths: list[str]) -> dict[str, int]:
    total = build_summary_rows(report, paths)[-1]
    return {
        "files": int(total[1]),
        "lines": int(total[3]),
        "code": int(total[5]),
        "comment": int(total[6]),
        "blank": int(total[7]),
    }


def generate_overview_page(report: dict[str, Any], categories: dict[str, list[str]]) -> None:
    rows = []
    for name in SCORECARD_CATEGORY_NAMES:
        totals = inventory_totals(report, categories[name])
        rows.append(
            [
                name,
                str(totals["files"]),
                str(totals["lines"]),
                str(totals["code"]),
                str(totals["comment"]),
                str(totals["blank"]),
            ]
        )
    body = (
        '<p><a class="button" href="index.html">Back to report portal</a></p>'
        "<p>This overview uses Pygount physical-line classifications and the same four "
        "LearningClock ownership scopes shown on the Engineering Scorecard.</p>"
        + html_table(["Area", "Files", "Lines", "Code", "Comment", "Blank"], rows)
    )
    OVERVIEW_HTML.write_text(
        html_page(f"LearningClock {project_version()} assurance overview", body), encoding="utf-8"
    )


def generate_supporting_reports(paths: list[str]) -> None:
    totals = junit_totals()
    if totals is None:
        test_body = "<p>No JUnit result is present. Run the coverage workflow to populate test totals.</p>"
    else:
        test_body = html_table(
            ["JUnit metric", "Count"],
            [[name.title(), str(value)] for name, value in totals.items()],
        )
    TEST_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (TEST_REPORT_DIR / "index.html").write_text(
        html_page("LearningClock test results", test_body), encoding="utf-8"
    )

    COVERAGE_INDEX_HTML.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_INDEX_HTML.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=html/index.html">'
        '<title>LearningClock Coverage</title></head><body>'
        '<a href="html/index.html">Open the LearningClock coverage report</a>'
        "</body></html>\n",
        encoding="utf-8",
    )

    performance_paths = [path for path in paths if path.startswith("tests/performance/")]
    benchmark_paths = [path for path in paths if path.startswith("benchmarks/")]
    PERFORMANCE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    BENCHMARK_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    performance_body = (
        f"<p>{len(performance_paths)} dedicated performance-test files are tracked.</p>"
        if performance_paths
        else "<p>No dedicated performance-test workload is configured yet. This status is explicit so the scorecard does not imply unmeasured performance evidence.</p>"
    )
    benchmark_body = (
        f"<p>{len(benchmark_paths)} dedicated benchmark files are tracked.</p>"
        if benchmark_paths
        else "<p>No dedicated benchmark workload is configured yet. This status is explicit so the scorecard does not fabricate benchmark evidence.</p>"
    )
    (PERFORMANCE_REPORT_DIR / "index.html").write_text(
        html_page("LearningClock performance tests", performance_body), encoding="utf-8"
    )
    (BENCHMARK_REPORT_DIR / "index.html").write_text(
        html_page("LearningClock benchmarks", benchmark_body), encoding="utf-8"
    )


def generate_landing_page(
    report: dict[str, Any], paths: list[str], categories: dict[str, list[str]]
) -> None:
    totals = junit_totals()
    test_label = (
        f"{totals['tests']} executions; {totals['failures']} failures; {totals['errors']} errors"
        if totals is not None
        else "Generate the JUnit report to populate totals"
    )
    performance_count = sum(path.startswith("tests/performance/") for path in paths)
    benchmark_count = sum(path.startswith("benchmarks/") for path in paths)
    cards = [
        ("Overview", "Application, assurance, documentation, and DevOps inventory", "overview.html"),
        ("Tests", test_label, "../tests/index.html"),
        ("LearningClock coverage", coverage_label(), "../coverage/index.html"),
        (
            "Performance tests",
            f"{performance_count} dedicated workload files" if performance_count else "Not configured",
            "../performance/index.html",
        ),
        (
            "Benchmarks",
            f"{benchmark_count} dedicated benchmark files" if benchmark_count else "Not configured",
            "../benchmarks/index.html",
        ),
        (
            "Diavgeia",
            "Architecture, configuration, implementation, and operational evidence",
            f"{GITHUB_REPOSITORY}/tree/main/diavgeia/LearningClock",
        ),
    ]
    card_html = "".join(
        f'<article class="card"><h2>{html.escape(title)}</h2><p>{html.escape(detail)}</p>'
        f'<a class="button" href="{target}">Open report</a></article>'
        for title, detail, target in cards
    )
    inventory_html = (
        '<h2 id="inventory">LearningClock</h2>'
        "<p>The repository table covers the entire LearningClock workspace. It is deliberately "
        "separate from the four project-area inventories below.</p>"
        + pygount_panel("Repository Inventory", report, paths)
        + f"<h2>LearningClock {project_version()} inventory</h2>"
        + "<p>These four tables partition the LearningClock application, assurance, documentation, "
        "and delivery surfaces.</p>"
        + "".join(pygount_panel(name, report, categories[name]) for name in SCORECARD_CATEGORY_NAMES)
    )
    scorecard_title = f"LearningClock {project_version()} Engineering Scorecard"
    SCORECARD_HTML.write_text(
        html_page(scorecard_title, f'<div class="cards">{card_html}</div>{inventory_html}'),
        encoding="utf-8",
    )
    ROOT_INDEX_HTML.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=reports/index.html">'
        '<title>LearningClock Engineering Scorecard</title></head><body>'
        '<a href="reports/index.html">Open the LearningClock Engineering Scorecard</a>'
        "</body></html>\n",
        encoding="utf-8",
    )


def main() -> int:
    paths = source_controlled_files()
    report = run_pygount(paths)
    categories = scorecard_categories(paths)
    rows = build_summary_rows(report, paths)
    BUILD_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_TEXT.write_text(render_summary_text(rows), encoding="utf-8")
    SUMMARY_SVG.write_text(render_svg(report, paths), encoding="utf-8")
    generate_overview_page(report, categories)
    generate_supporting_reports(paths)
    generate_landing_page(report, paths, categories)
    print(f"[pygount] scanned source-controlled files: {len(paths)}")
    print(f"[pygount] wrote {SUMMARY_TEXT.relative_to(ROOT)}")
    print(f"[pygount] wrote {SUMMARY_SVG.relative_to(ROOT)}")
    print(f"[scorecard] wrote {SCORECARD_HTML.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
