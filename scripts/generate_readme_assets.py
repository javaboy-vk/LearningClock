# =============================================================================
# File Name : generate_readme_assets.py
# Artifact  : LearningClock - README Visual Asset Generator
# Author    : javaboy-vk
# Date      : 2026-06-09
# Version   : v0.1.0
# Purpose:
#   Generates stable SVG visuals used by README.md to show the app UI and
#   Obsidian dashboard output.
# =============================================================================

from __future__ import annotations

import csv
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from learningclock.csv_store import ACTIVITY_TO_FIELD, ACTIVITIES, parse_duration  # noqa: E402

ASSET_DIR = ROOT / "docs" / "assets"
UI_SVG = ASSET_DIR / "learning-clock-ui.svg"
DASHBOARD_SVG = ASSET_DIR / "learning-clock-dashboard.svg"
QA_CSV = ROOT / "build" / "Clock-QA" / "learning_time_log.csv"


def text(value: object) -> str:
    return html.escape(str(value), quote=True)


def format_duration(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


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


def generate_ui_svg() -> str:
    width = 560
    height = 500
    row_height = 43
    top = 126
    rows = []
    for index, activity in enumerate(ACTIVITIES):
        y = top + index * row_height
        status = "01:42:35" if activity == "Experimenting" else "00:00:00"
        rows.append(
            f"""
            <g>
              <rect x="38" y="{y}" width="282" height="37" fill="#eeeeee" stroke="#8c8c8c" stroke-width="1.4"/>
              <line x1="40" y1="{y + 2}" x2="318" y2="{y + 2}" stroke="#ffffff" stroke-width="1"/>
              <line x1="40" y1="{y + 35}" x2="318" y2="{y + 35}" stroke="#777777" stroke-width="1"/>
              <text x="45" y="{y + 26}" fill="#111111" font-size="21">{text(activity)}</text>
              <text x="360" y="{y + 26}" fill="#050505" font-size="24" font-family="Consolas, Cascadia Mono, Courier New, monospace">{status}</text>
            </g>"""
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="LearningClock desktop UI with seven learning timers">
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#000000" flood-opacity="0.25"/>
    </filter>
  </defs>
  <rect width="{width}" height="{height}" fill="#c8c6bd"/>
  <rect x="18" y="26" width="524" height="496" rx="9" fill="#eeeeee" stroke="#9d9d9d" filter="url(#shadow)"/>
  <rect x="18" y="26" width="524" height="41" rx="9" fill="#f8f8f8"/>
  <rect x="18" y="57" width="524" height="30" fill="#ffffff"/>
  <text x="31" y="52" fill="#174c84" font-family="Segoe UI Emoji, Segoe UI Symbol, Arial, sans-serif" font-size="19">🪶</text>
  <text x="54" y="51" fill="#8a8a8a" font-family="Segoe UI, Arial, sans-serif" font-size="15">Learning Clock - v3.3 - LearningClock</text>
  <text x="389" y="51" fill="#8a8a8a" font-family="Segoe UI, Arial, sans-serif" font-size="18">−</text>
  <rect x="448" y="40" width="10" height="10" fill="none" stroke="#d9d9d9"/>
  <text x="506" y="52" fill="#8a8a8a" font-family="Segoe UI, Arial, sans-serif" font-size="24">×</text>
  <text x="26" y="81" fill="#777777" font-family="Segoe UI, Arial, sans-serif" font-size="15">About</text>
  <text x="86" y="81" fill="#777777" font-family="Segoe UI, Arial, sans-serif" font-size="15">Add Time</text>
  <text x="168" y="81" fill="#777777" font-family="Segoe UI, Arial, sans-serif" font-size="15">Add Page Count</text>
  <text x="43" y="119" fill="#000000" font-family="Segoe UI, Arial, sans-serif" font-size="21" font-weight="700">Stopped: Experimenting</text>
  <g font-family="Segoe UI, Arial, sans-serif">
    {''.join(rows)}
  </g>
  <rect x="38" y="434" width="132" height="35" fill="#eeeeee" stroke="#8c8c8c" stroke-width="1.4"/>
  <line x1="40" y1="436" x2="168" y2="436" stroke="#ffffff" stroke-width="1"/>
  <text x="87" y="458" fill="#111111" font-family="Segoe UI, Arial, sans-serif" font-size="16">Stop</text>
  <rect x="178" y="434" width="132" height="35" fill="#eeeeee" stroke="#8c8c8c" stroke-width="1.4"/>
  <line x1="180" y1="436" x2="308" y2="436" stroke="#ffffff" stroke-width="1"/>
  <text x="211" y="458" fill="#111111" font-family="Segoe UI, Arial, sans-serif" font-size="16">Reset Timer</text>
</svg>
"""


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
    colors = ["#3279b7", "#4c8fc2", "#6aa2cc", "#2f6f9f", "#7aa9c9", "#4f86b3", "#245f8f"]
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
        label = text(activity)
        label_lines = label.split(" ")
        if len(label_lines) > 2:
            first = " ".join(label_lines[:2])
            second = " ".join(label_lines[2:])
            labels.append(
                f'<text x="{x + bar_width / 2:.1f}" y="352" fill="#111827" font-size="13" text-anchor="middle"><tspan x="{x + bar_width / 2:.1f}">{first}</tspan><tspan x="{x + bar_width / 2:.1f}" dy="16">{second}</tspan></text>'
            )
        else:
            labels.append(
                f'<text x="{x + bar_width / 2:.1f}" y="360" fill="#111827" font-size="13" text-anchor="middle">{label}</text>'
            )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="LearningClock Obsidian dashboard bar chart">
  <rect width="{width}" height="{height}" fill="#f3f7fb"/>
  <text x="38" y="44" fill="#111827" font-family="Segoe UI, Arial, sans-serif" font-size="28" font-weight="700">LearningClock Learning Time</text>
  <rect x="34" y="60" width="{width - 68}" height="404" rx="18" fill="#f8fbff" stroke="#c5d8ec" stroke-width="2"/>
  <line x1="{chart_x}" y1="{chart_y + chart_height}" x2="{chart_x + chart_width}" y2="{chart_y + chart_height}" stroke="#a9c5df" stroke-width="3"/>
  <g font-family="Segoe UI, Arial, sans-serif">
    {''.join(bars)}
    {''.join(labels)}
  </g>
  <g font-family="Segoe UI, Arial, sans-serif" font-size="17" fill="#111827">
    <text x="58" y="430">Total time: <tspan fill="#164f86" font-weight="700">{format_duration(grand_total)}</tspan></text>
    <text x="282" y="430">Total pages read: <tspan fill="#164f86" font-weight="700">{pages}</tspan></text>
    <text x="516" y="430">Start Date: <tspan fill="#164f86" font-weight="700">06-05-26</tspan></text>
    <text x="706" y="430">Last Update: <tspan fill="#164f86" font-weight="700">06-06-26</tspan></text>
  </g>
</svg>
"""


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    UI_SVG.write_text(generate_ui_svg(), encoding="utf-8")
    DASHBOARD_SVG.write_text(generate_dashboard_svg(), encoding="utf-8")
    print(f"wrote {UI_SVG.relative_to(ROOT)}")
    print(f"wrote {DASHBOARD_SVG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
