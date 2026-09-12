# =============================================================================
# File Name : generate_readme_assets.py
# Artifact  : LearningClock - README Visual Asset Generator
# Author    : javaboy-vk
# Date      : 2026-06-09
# Version   : v6.3.0
# Purpose:
#   Generates stable SVG visuals used by README.md to show LauncherPad, its
#   report diagnostics, the app UI, progress, and Obsidian dashboard output.
#
# Generation call tree:
#   main()
#   |-- generate_launcherpad_svg()
#   |   `-- render representative configured-clock controls
#   |-- generate_report_diagnostics_svg()
#   |   `-- render linked source-file and CSV-row diagnostics
#   |-- generate_ui_svg()
#   |   |-- read ACTIVITIES from learningclock.csv_store
#   |   |-- render one representative timer row per activity
#   |   `-- return a complete desktop UI SVG string
#   |-- generate_dashboard_svg()
#   |   |-- read_dashboard_totals()
#   |   |   |-- read build\Clock-QA\learning_time_log.csv when present
#   |   |   |-- aggregate activity totals through ACTIVITY_TO_FIELD
#   |   |   `-- fall back to deterministic sample totals when QA CSV is absent
#   |   |-- render bars and labels for every activity
#   |   `-- return a complete dashboard SVG string
#   |-- generate_progress_svg()
#   |   `-- return the in-app View Progress dashboard visual
#   `-- write all LauncherPad, UI, Progress, and Obsidian dashboard SVG assets
#
# Import note:
#   This script is a direct repo utility, not an installed console entry point.
#   It prepends src\ to sys.path before importing learningclock so it can run
#   from a clean checkout. That intentional dynamic import shape conflicts with
#   Ruff's sorted-import rule, so the import-order warning is disabled here.
# =============================================================================
# ruff: noqa: E402,I001

from __future__ import annotations

import csv
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))  # Let direct script execution import the local package.

from learningclock.app import APP_VERSION  # noqa: E402
from learningclock.csv_store import ACTIVITY_TO_FIELD, ACTIVITIES, parse_duration  # noqa: E402

ASSET_DIR = ROOT / "docs" / "assets"
LAUNCHERPAD_SVG = ASSET_DIR / "learning-clock-launcherpad.svg"
REPORT_DIAGNOSTICS_SVG = ASSET_DIR / "learning-clock-report-diagnostics.svg"
UI_SVG = ASSET_DIR / "learning-clock-ui.svg"
DASHBOARD_SVG = ASSET_DIR / "learning-clock-dashboard.svg"
PROGRESS_SVG = ASSET_DIR / "learning-clock-progress.svg"
QA_CSV = ROOT / "build" / "Clock-QA" / "learning_time_log.csv"


# Text rendering:
#   What this function does:
#     Escapes values before embedding them into SVG text nodes.
#   Success:
#     Activity labels and totals remain valid XML even if labels contain special characters.
#   Error handling:
#     Conversion uses str() so non-string values can still be rendered safely.
def text(value: object) -> str:

    return html.escape(str(value), quote=True)


# Duration formatting:
#   What this function does:
#     Converts integer seconds into the HH:MM:SS format used by the dashboard mock.
#   Success:
#     README assets visually match the app and dashboard duration convention.
#   Error handling:
#     Callers provide integer-like totals derived from test CSV data or deterministic samples.
def format_duration(seconds: int) -> str:

    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def public_activity_label(activity: str) -> str:
    """Return a neutral public label for documentation screenshots."""

    if ACTIVITY_TO_FIELD.get(activity) == "update_diavgeia":
        return "Update Documentation"
    return activity


# Source documentation:
#   What it does: Renders the LauncherPad window and representative configured clocks.
#   Why it exists: README readers need to see creation, launch, and reporting in the primary UI.
#   Designed use: main writes this deterministic SVG beside the other README visuals.
def generate_launcherpad_svg() -> str:
    controls = [
        ("Atlas Study", "#069bff"),
        ("Bluebird Research", "#069bff"),
        ("Cedar Notes", "#069bff"),
        ("Northstar Lab — Running", "#FF6600"),
        ("Orchard Learning", "#069bff"),
        ("Summit Skills", "#069bff"),
    ]
    buttons = []
    for index, (label, background) in enumerate(controls):
        column = index % 3
        row = index // 3
        x = 38 + column * 274
        y = 118 + row * 62
        buttons.append(
            f'<rect x="{x}" y="{y}" width="252" height="46" rx="3" '
            f'fill="{background}" stroke="#8c8c8c"/>'
            f'<line x1="{x + 2}" y1="{y + 2}" x2="{x + 250}" y2="{y + 2}" '
            f'stroke="#ffffff" stroke-opacity=".8"/>'
            f'<text x="{x + 126}" y="{y + 29}" fill="#ffffff" font-size="14" '
            f'font-weight="700" text-anchor="middle">{text(label)}</text>'
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="620" viewBox="0 0 900 620" role="img" aria-label="LearningClock LauncherPad with clock creation and category report">
  <rect width="900" height="620" rx="8" fill="#d7d7d7" stroke="#8c8c8c" stroke-width="2"/>
  <rect x="1" y="1" width="898" height="42" rx="7" fill="#fafafa"/>
  <rect x="1" y="34" width="898" height="9" fill="#fafafa"/>
  <circle cx="23" cy="22" r="13" fill="#069bff"/>
  <path d="M23 11 A11 11 0 0 1 34 22 H23 Z" fill="#FF6600"/>
  <line x1="23" y1="22" x2="23" y2="14" stroke="#ffffff" stroke-width="2"/>
  <line x1="23" y1="22" x2="29" y2="25" stroke="#ffffff" stroke-width="2"/>
  <text x="45" y="27" fill="#333333" font-family="Segoe UI, Arial, sans-serif" font-size="14">LearningClock LauncherPad 2.0</text>
  <text x="865" y="27" fill="#555555" font-family="Segoe UI, Arial, sans-serif" font-size="20">×</text>
  <text x="30" y="82" fill="#111111" font-family="Segoe UI, Arial, sans-serif" font-size="23" font-weight="700">LearningClock LauncherPad 2.0</text>
  <rect x="700" y="58" width="166" height="38" rx="4" fill="#069bff"/>
  <text x="783" y="82" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" font-size="14" font-weight="700" text-anchor="middle">Create New Clock</text>
  <g font-family="Segoe UI, Arial, sans-serif">{"".join(buttons)}</g>
  <rect x="28" y="246" width="844" height="320" rx="8" fill="#f8fbff" stroke="#a9c5df"/>
  <text x="45" y="276" fill="#111111" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">Time by category across all clocks</text>
  <text x="45" y="308" fill="#333333" font-family="Segoe UI, Arial, sans-serif" font-size="13">Period:  This week   Inclusive range: 2026-09-07 through 2026-09-11</text>
  <line x1="50" y1="494" x2="850" y2="494" stroke="#8aa9c4"/>
  <g fill="#007ACC">
    <rect x="62" y="390" width="46" height="104"/><rect x="142" y="430" width="46" height="64"/>
    <rect x="222" y="410" width="46" height="84"/><rect x="302" y="450" width="46" height="44"/>
    <rect x="382" y="440" width="46" height="54"/><rect x="462" y="360" width="46" height="134"/>
    <rect x="542" y="330" width="46" height="164"/><rect x="622" y="375" width="46" height="119"/>
    <rect x="702" y="425" width="46" height="69"/><rect x="782" y="455" width="46" height="39"/>
  </g>
  <g fill="#222222" font-family="Segoe UI, Arial, sans-serif" font-size="10" text-anchor="middle">
    <text x="85" y="512">Reading</text><text x="165" y="512">Book Listening</text>
    <text x="245" y="512">Outlining</text><text x="325" y="512">Active Recall</text>
    <text x="405" y="512">Sandbox</text><text x="485" y="512">AI Architecture</text>
    <text x="565" y="512">AI Engineering</text><text x="645" y="512">Classical Eng.</text>
    <text x="725" y="512">Documentation</text><text x="805" y="512">Promote</text>
  </g>
  <text x="45" y="548" fill="#333333" font-family="Segoe UI, Arial, sans-serif" font-size="13">Total: 18:45:00 · 6 clocks · 24 session rows · </text>
  <text x="385" y="548" fill="#0067c0" font-family="Segoe UI, Arial, sans-serif" font-size="13" text-decoration="underline">4 skipped/invalid inputs</text>
  <text x="30" y="598" fill="#333333" font-family="Segoe UI, Arial, sans-serif" font-size="14">6 configured clocks</text>
</svg>
"""


# Report diagnostics screenshot:
#   What it does: Renders the popup opened from LauncherPad's skipped/invalid link.
#   Why it exists: README readers need to see the exact file, row, column, value, and reason.
#   Designed use: main writes this deterministic SVG beside the LauncherPad overview.
def generate_report_diagnostics_svg() -> str:
    issues = [
        (
            "1. Atlas Study: Skipped row 29 with an invalid date in Atlas Study.",
            r"D:\SampleVault\Learning\Atlas Study\LearningPath\learning_time_log.csv — row 29",
            "Type: row · Reason: invalid date at row 29 · Column: date · Value: ''",
        ),
        (
            "2. Atlas Study: Skipped row 30 with an invalid date in Atlas Study.",
            r"D:\SampleVault\Learning\Atlas Study\LearningPath\learning_time_log.csv — row 30",
            "Type: row · Reason: invalid date at row 30 · Column: date · Value: ''",
        ),
        (
            "3. Atlas Study: Skipped row 31 with an invalid date in Atlas Study.",
            r"D:\SampleVault\Learning\Atlas Study\LearningPath\learning_time_log.csv — row 31",
            "Type: row · Reason: invalid date at row 31 · Column: date · Value: ''",
        ),
        (
            "4. Archived Course: No time log yet for Archived Course.",
            r"D:\SampleVault\Learning\Archived Course\LearningPath\learning_time_log.csv",
            "Type: CSV · Reason: time log missing",
        ),
    ]
    cards: list[str] = []
    for index, (title, path, details) in enumerate(issues):
        y = 126 + index * 91
        cards.append(
            f'<rect x="32" y="{y}" width="812" height="78" rx="3" '
            f'fill="#ffffff" stroke="#b8c8d8"/>'
            f'<text x="45" y="{y + 22}" fill="#111111" font-size="13" '
            f'font-weight="700">{text(title)}</text>'
            f'<text x="45" y="{y + 44}" fill="#0067c0" font-size="12" '
            f'text-decoration="underline">{text(path)}</text>'
            f'<text x="45" y="{y + 64}" fill="#4f5f6f" font-size="11">'
            f'{text(details)}</text>'
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="560" viewBox="0 0 900 560" role="img" aria-label="LearningClock skipped and invalid report inputs popup with linked files and CSV rows">
  <rect width="900" height="560" rx="8" fill="#f2f2f2" stroke="#8c8c8c" stroke-width="2"/>
  <rect x="1" y="1" width="898" height="42" rx="7" fill="#fafafa"/>
  <rect x="1" y="34" width="898" height="9" fill="#fafafa"/>
  <circle cx="23" cy="22" r="13" fill="#069bff"/>
  <path d="M23 11 A11 11 0 0 1 34 22 H23 Z" fill="#FF6600"/>
  <line x1="23" y1="22" x2="23" y2="14" stroke="#ffffff" stroke-width="2"/>
  <line x1="23" y1="22" x2="29" y2="25" stroke="#ffffff" stroke-width="2"/>
  <text x="45" y="27" fill="#333333" font-family="Segoe UI, Arial, sans-serif" font-size="14">Skipped and Invalid Report Inputs</text>
  <text x="865" y="27" fill="#555555" font-family="Segoe UI, Arial, sans-serif" font-size="20">×</text>
  <g font-family="Segoe UI, Arial, sans-serif">
    <text x="32" y="73" fill="#111111" font-size="18" font-weight="700">4 skipped or invalid inputs</text>
    <text x="32" y="96" fill="#333333" font-size="12">This report scan is read-only and does not rewrite CSV data.</text>
    <text x="32" y="113" fill="#333333" font-size="12">Each blue link identifies the source file and CSV row used by the scan.</text>
    {"".join(cards)}
  </g>
  <rect x="802" y="507" width="66" height="30" rx="3" fill="#eeeeee" stroke="#8c8c8c"/>
  <text x="835" y="527" fill="#111111" font-family="Segoe UI, Arial, sans-serif" font-size="12" text-anchor="middle">Close</text>
</svg>
"""


# Dashboard label wrapping:
#   What this function does:
#     Splits chart labels into short lines that fit under one bar cell.
#   Why it exists:
#     Long labels otherwise overflow narrow chart columns inconsistently across SVG renderers.
#   Designed use:
#     Dashboard generation calls it for every label and receives stable lines.
#   Success:
#     Dense labels do not overlap adjacent labels in the README dashboard image.
#   Error handling:
#     Unknown labels fall back to conservative word wrapping.
def dashboard_label_lines(label: str) -> list[str]:
    explicit_breaks = {
        "Active Recall": ["Active", "Recall"],
        "AI-Assisted Engineering": ["AI-Assisted", "Engineering"],
        "AI-Assisted Architecture & Design": ["AI-Assisted", "Architecture", "& Design"],
        "Classical Software Engineering": ["Classical", "Software", "Engineering"],
        "Update Diavgeia": ["Update", "Diavgeia"],
        "Promote Stable Concept": ["Promote", "Stable", "Concept"],
    }
    if label in explicit_breaks:
        return explicit_breaks[label]

    words = label.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= 12:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# Dashboard label rendering:
#   What this function does:
#     Renders a wrapped label as one centered SVG text element with tspans.
#   Why it exists:
#     SVG has no portable automatic wrapping for the generated chart geometry.
#   Designed use:
#     Pass chart coordinates and append the escaped markup to the dashboard SVG.
#   Success:
#     Every line stays centered under its own bar.
#   Error handling:
#     Escaping is delegated to text() before content enters the SVG.
def dashboard_label_svg(label: str, x: float, y: int) -> str:
    lines = dashboard_label_lines(label)
    tspans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else 15
        dy_attribute = "" if index == 0 else f' dy="{dy}"'
        tspans.append(f'<tspan x="{x:.1f}"{dy_attribute}>{text(line)}</tspan>')
    return (
        f'<text x="{x:.1f}" y="{y}" fill="#111827" font-size="12" '
        f'text-anchor="middle">{"".join(tspans)}</text>'
    )


# Dashboard data source:
#   What this function does:
#     Reads generated QA CSV totals when available, otherwise produces stable sample values.
#   Why it exists:
#     Visuals should reflect real totals but remain reproducible when no local CSV exists.
#   Designed use:
#     Dashboard generators consume activity totals, page count, and aggregate seconds.
#   Success:
#     README dashboard art reflects real CSV categories and stays deterministic in clean checkouts.
#   Error handling:
#     CSV parsing errors surface directly because broken generated CSV should be fixed, not hidden.
def read_dashboard_totals() -> tuple[dict[str, int], int, int]:
    totals = {activity: 0 for activity in ACTIVITIES}
    pages = 0
    grand_total = 0

    if not QA_CSV.exists():
        return {activity: (index + 1) * 120 for index, activity in enumerate(ACTIVITIES)}, 0, 0

    with QA_CSV.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    sessions = [row for row in rows if row.get("date") != "TOTAL"]
    total_row = next((row for row in rows if row.get("date") == "TOTAL"), None)

    for row in sessions:
        for activity, field_name in ACTIVITY_TO_FIELD.items():
            totals[activity] += parse_duration(row.get(field_name, "00:00:00"))
        pages += int(row.get("pages_read") or 0)
        grand_total += parse_duration(row.get("total", "00:00:00"))

    if total_row:
        pages = int(total_row.get("pages_read") or pages)
        grand_total = parse_duration(total_row.get("total", "00:00:00"))

    return totals, pages, grand_total


# UI SVG generation:
#   What this function does:
#     Builds the static desktop screenshot used by README.md.
#   Why it exists:
#     Repository readers need a reviewable preview aligned with current UI contracts.
#   Designed use:
#     main writes the returned SVG to the canonical timer UI asset.
#   Success:
#     Every current activity appears exactly once, and layout height follows the activity count.
#   Error handling:
#     No filesystem writes happen here; generation failures surface before main writes assets.
def generate_ui_svg() -> str:
    width = 700
    height = 165 + (len(ACTIVITIES) * 43)
    window_width = width - 36
    button_width = 365
    timer_x = 470
    row_height = 43
    top = 126
    controls_y = top + (len(ACTIVITIES) * row_height) + 7
    active_activity = "Sandbox"
    rows = []
    for index, activity in enumerate(ACTIVITIES):
        y = top + index * row_height
        status = "01:42:35" if activity == active_activity else "00:00:00"
        button_background = "#FF6600" if activity == active_activity else "#069bff"
        rows.append(
            f"""
            <g>
              <rect x="38" y="{y}" width="{button_width}" height="37" fill="{button_background}" stroke="#8c8c8c" stroke-width="1.4"/>
              <line x1="40" y1="{y + 2}" x2="{38 + button_width - 2}" y2="{y + 2}" stroke="#ffffff" stroke-width="1"/>
              <line x1="40" y1="{y + 35}" x2="{38 + button_width - 2}" y2="{y + 35}" stroke="#777777" stroke-width="1"/>
              <text x="45" y="{y + 26}" fill="#ffffff" font-size="18" font-weight="700">{text(public_activity_label(activity))}</text>
              <text x="{timer_x}" y="{y + 26}" fill="#050505" font-size="24" font-family="Consolas, Cascadia Mono, Courier New, monospace">{status}</text>
            </g>"""
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="LearningClock desktop UI with learning timers">
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#000000" flood-opacity="0.25"/>
    </filter>
  </defs>
  <rect width="{width}" height="{height}" fill="#c8c6bd"/>
  <rect x="18" y="26" width="{window_width}" height="{height - 4}" rx="9" fill="#eeeeee" stroke="#9d9d9d" filter="url(#shadow)"/>
  <rect x="18" y="26" width="{window_width}" height="41" rx="9" fill="#f8f8f8"/>
  <rect x="18" y="57" width="{window_width}" height="30" fill="#ffffff"/>
  <text x="31" y="52" fill="#174c84" font-family="Segoe UI Emoji, Segoe UI Symbol, Arial, sans-serif" font-size="19">🪶</text>
  <text x="54" y="51" fill="#8a8a8a" font-family="Segoe UI, Arial, sans-serif" font-size="15">Learning Clock - {APP_VERSION} - LearningClock</text>
  <text x="529" y="51" fill="#8a8a8a" font-family="Segoe UI, Arial, sans-serif" font-size="18">−</text>
  <rect x="588" y="40" width="10" height="10" fill="none" stroke="#d9d9d9"/>
  <text x="646" y="52" fill="#8a8a8a" font-family="Segoe UI, Arial, sans-serif" font-size="24">×</text>
  <text x="26" y="81" fill="#777777" font-family="Segoe UI, Arial, sans-serif" font-size="15" font-weight="700">About</text>
  <text x="86" y="81" fill="#777777" font-family="Segoe UI, Arial, sans-serif" font-size="15" font-weight="700">Add Time</text>
  <text x="168" y="81" fill="#777777" font-family="Segoe UI, Arial, sans-serif" font-size="15" font-weight="700">Set Date</text>
  <text x="235" y="81" fill="#777777" font-family="Segoe UI, Arial, sans-serif" font-size="15" font-weight="700">Add Page Count</text>
  <text x="347" y="81" fill="#777777" font-family="Segoe UI, Arial, sans-serif" font-size="15" font-weight="700">View Progress</text>
  <text x="43" y="119" fill="#000000" font-family="Segoe UI, Arial, sans-serif" font-size="21" font-weight="700">Running: {active_activity}</text>
  <g font-family="Segoe UI, Arial, sans-serif">
    {"".join(rows)}
  </g>
  <rect x="38" y="{controls_y}" width="132" height="35" fill="#069bff" stroke="#8c8c8c" stroke-width="1.4"/>
  <line x1="40" y1="{controls_y + 2}" x2="168" y2="{controls_y + 2}" stroke="#ffffff" stroke-width="1"/>
  <text x="87" y="{controls_y + 24}" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">Stop</text>
  <rect x="178" y="{controls_y}" width="132" height="35" fill="#069bff" stroke="#8c8c8c" stroke-width="1.4"/>
  <line x1="180" y1="{controls_y + 2}" x2="308" y2="{controls_y + 2}" stroke="#ffffff" stroke-width="1"/>
  <text x="211" y="{controls_y + 24}" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" font-size="16" font-weight="700">Reset Timer</text>
</svg>
"""


# Dashboard SVG generation:
#   What this function does:
#     Builds the static Obsidian/Diavgeia dashboard chart used by README.md.
#   Why it exists:
#     Readers need a stable chart preview without running Obsidian.
#   Designed use:
#     main writes the returned SVG after resolving totals; source CSV is never modified.
#   Success:
#     Bars and labels follow ACTIVITIES and ACTIVITY_TO_FIELD from the production CSV contract.
#   Error handling:
#     Bad CSV values parse through production parse_duration; structural errors surface naturally.
def generate_dashboard_svg() -> str:
    totals, pages, grand_total = read_dashboard_totals()
    width = 920
    height = 500
    chart_x = 58
    chart_y = 76
    chart_width = 804
    chart_height = 246
    gap = 12
    bar_width = (chart_width - gap * (len(ACTIVITIES) - 1)) / len(ACTIVITIES)
    max_seconds = max(totals.values()) or 1

    bars = []
    labels = []
    colors = ["#007ACC"] * len(ACTIVITIES)
    for index, activity in enumerate(ACTIVITIES):
        seconds = totals[activity]
        bar_height = max(34, int((seconds / max_seconds) * 228))
        x = chart_x + index * (bar_width + gap)
        y = chart_y + chart_height - bar_height
        bars.append(
            f"""
            <rect x="{x:.1f}" y="{y}" width="{bar_width:.1f}" height="{bar_height}" rx="8" fill="{colors[index]}"/>
            <text x="{x + bar_width / 2:.1f}" y="{y + 24}" fill="#ffffff" font-size="14" font-weight="700" text-anchor="middle">{format_duration(seconds)}</text>"""
        )
        labels.append(dashboard_label_svg(public_activity_label(activity), x + bar_width / 2, 350))

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="LearningClock Obsidian dashboard bar chart">
  <rect width="{width}" height="{height}" fill="#f3f7fb"/>
  <text x="38" y="44" fill="#111827" font-family="Segoe UI, Arial, sans-serif" font-size="28" font-weight="700">LearningClock Learning Time</text>
  <rect x="34" y="60" width="{width - 68}" height="404" rx="18" fill="#f8fbff" stroke="#c5d8ec" stroke-width="2"/>
  <line x1="{chart_x}" y1="{chart_y + chart_height}" x2="{chart_x + chart_width}" y2="{chart_y + chart_height}" stroke="#a9c5df" stroke-width="3"/>
  <g font-family="Segoe UI, Arial, sans-serif">
    {"".join(bars)}
    {"".join(labels)}
  </g>
  <g font-family="Segoe UI, Arial, sans-serif" font-size="17" fill="#111827">
    <text x="58" y="430">Total time: <tspan fill="#164f86" font-weight="700">{format_duration(grand_total)}</tspan></text>
    <text x="282" y="430">Total pages read: <tspan fill="#164f86" font-weight="700">{pages}</tspan></text>
    <text x="516" y="430">Start Date: <tspan fill="#164f86" font-weight="700">06-05-26</tspan></text>
    <text x="706" y="430">Last Update: <tspan fill="#164f86" font-weight="700">06-06-26</tspan></text>
  </g>
</svg>
"""


# Source documentation:
#   What it does: Builds the in-application progress-panel documentation illustration.
#   Why it exists: Docs must distinguish the embedded view from the Obsidian dashboard.
#   Designed use: main regenerates it with UI/dashboard assets to keep visuals synchronized.
def generate_progress_svg() -> str:
    totals, pages, grand_total = read_dashboard_totals()
    width = 1320
    height = 520
    panel_x = 446
    panel_width = 850
    chart_left = panel_x + 22
    chart_width = panel_width - 44
    baseline = 335
    chart_top = 151
    gap = 9
    bar_width = (chart_width - gap * (len(ACTIVITIES) - 1)) / len(ACTIVITIES)
    max_seconds = max(totals.values()) or 1
    active_activity = "Sandbox"

    timer_rows = []
    for index, activity in enumerate(ACTIVITIES):
        y = 85 + index * 34
        button_background = "#FF6600" if activity == active_activity else "#069bff"
        timer_rows.append(
            f'<rect x="12" y="{y}" width="278" height="31" fill="{button_background}" stroke="#8c8c8c"/>'
            f'<text x="18" y="{y + 21}" fill="#ffffff" font-size="16" font-weight="700">{text(public_activity_label(activity))}</text>'
            f'<text x="322" y="{y + 21}" fill="#050505" font-family="Consolas, Cascadia Mono, Courier New, monospace" font-size="16">00:00:00</text>'
        )

    bars = []
    labels = []
    for index, activity in enumerate(ACTIVITIES):
        seconds = totals[activity]
        bar_height = max(20, int((seconds / max_seconds) * (baseline - chart_top)))
        x = chart_left + index * (bar_width + gap)
        y = baseline - bar_height
        bars.append(
            f'<rect x="{x:.1f}" y="{y}" width="{bar_width:.1f}" height="{bar_height}" fill="#007ACC"/>'
            f'<text x="{x + bar_width / 2:.1f}" y="{y + 5}" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" font-size="10" font-weight="700" text-anchor="middle" dominant-baseline="hanging">{format_duration(seconds)}</text>'
        )
        labels.append(
            dashboard_label_svg(public_activity_label(activity), x + bar_width / 2, baseline + 18)
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="LearningClock in-app View Progress dashboard">
  <rect width="{width}" height="{height}" fill="#c8c6bd"/>
  <rect x="0" y="0" width="{width}" height="44" fill="#f8f8f8"/>
  <rect x="0" y="44" width="{width}" height="27" fill="#ffffff"/>
  <text x="16" y="28" fill="#8a8a8a" font-family="Segoe UI, Arial, sans-serif" font-size="15">Learning Clock - {APP_VERSION} - LearningClock</text>
  <text x="5" y="63" fill="#555555" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="700">About</text>
  <text x="47" y="63" fill="#555555" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="700">Add Time</text>
  <text x="108" y="63" fill="#555555" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="700">Set Date</text>
  <text x="166" y="63" fill="#555555" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="700">Add Page Count</text>
  <text x="257" y="63" fill="#555555" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="700">View Progress</text>
  <text x="12" y="80" fill="#000000" font-family="Segoe UI, Arial, sans-serif" font-size="17" font-weight="700">Viewing CSV progress</text>
  <g font-family="Segoe UI, Arial, sans-serif">{"".join(timer_rows)}</g>
  <rect x="12" y="430" width="104" height="28" fill="#069bff" stroke="#8c8c8c"/>
  <text x="53" y="449" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="700">Stop</text>
  <rect x="122" y="430" width="106" height="28" fill="#069bff" stroke="#8c8c8c"/>
  <text x="141" y="449" fill="#ffffff" font-family="Segoe UI, Arial, sans-serif" font-size="13" font-weight="700">Reset Timer</text>
  <rect x="{panel_x}" y="85" width="{panel_width}" height="398" fill="#f4f8fc" stroke="#c5d8ec"/>
  <text x="{panel_x + 14}" y="115" fill="#000000" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="700">Progress</text>
  <rect x="{panel_x + panel_width - 59}" y="96" width="45" height="26" fill="#eeeeee" stroke="#8c8c8c"/>
  <text x="{panel_x + panel_width - 53}" y="114" fill="#111111" font-family="Segoe UI, Arial, sans-serif" font-size="12">Refresh</text>
  <line x1="{chart_left}" y1="{baseline}" x2="{chart_left + chart_width}" y2="{baseline}" stroke="#a9c5df" stroke-width="2"/>
  <g font-family="Segoe UI, Arial, sans-serif">{"".join(bars)}{"".join(labels)}</g>
  <g font-family="Segoe UI, Arial, sans-serif" font-size="14" fill="#111827">
    <text x="{panel_x + 14}" y="463">Total time: <tspan fill="#164f86" font-weight="700">{format_duration(grand_total)}</tspan></text>
    <text x="{panel_x + 174}" y="463">Total pages read: <tspan fill="#164f86" font-weight="700">{pages}</tspan></text>
    <text x="{panel_x + 338}" y="463">Start Date: <tspan fill="#164f86" font-weight="700">06-05-26</tspan></text>
    <text x="{panel_x + 510}" y="463">Last Update: <tspan fill="#164f86" font-weight="700">06-06-26</tspan></text>
  </g>
</svg>
"""


# Command-line entry point:
#   What this function does:
#     Ensures the asset folder exists and writes both generated SVG files.
#   Why it exists:
#     One entry point prevents partial visual-documentation refreshes.
#   Designed use:
#     Run dev readme-assets after visual or activity-contract changes.
#   Success:
#     README image references point at fresh assets matching the current category schema.
#   Error handling:
#     Write failures propagate so release/deploy workflows fail visibly.
def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    LAUNCHERPAD_SVG.write_text(generate_launcherpad_svg(), encoding="utf-8")
    REPORT_DIAGNOSTICS_SVG.write_text(generate_report_diagnostics_svg(), encoding="utf-8")
    UI_SVG.write_text(generate_ui_svg(), encoding="utf-8")
    DASHBOARD_SVG.write_text(generate_dashboard_svg(), encoding="utf-8")
    PROGRESS_SVG.write_text(generate_progress_svg(), encoding="utf-8")
    print(f"wrote {LAUNCHERPAD_SVG.relative_to(ROOT)}")
    print(f"wrote {REPORT_DIAGNOSTICS_SVG.relative_to(ROOT)}")
    print(f"wrote {UI_SVG.relative_to(ROOT)}")
    print(f"wrote {DASHBOARD_SVG.relative_to(ROOT)}")
    print(f"wrote {PROGRESS_SVG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
