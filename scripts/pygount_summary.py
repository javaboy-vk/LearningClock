# =============================================================================
# File Name : pygount_summary.py
# Artifact  : LearningClock - Pygount Summary Generator
# Author    : javaboy-vk
# Date      : 2026-06-09
# Version   : v0.1.1
# Purpose:
#   Generates a GitHub Pages-only code inventory SVG without changing tracked
#   documentation files.
# =============================================================================

from __future__ import annotations

import html
import json
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BUILD_REPORT_DIR = ROOT / "build" / "reports"
SUMMARY_TEXT = BUILD_REPORT_DIR / "pygount-summary.txt"
SUMMARY_SVG = BUILD_REPORT_DIR / "pygount-summary.svg"
EXCLUDED_FILENAMES = {".gitignore", ".gitkeep"}
HIDDEN_LANGUAGE_BUCKETS = {"__binary__", "__duplicate__", "__generated__"}
DISPLAY_LANGUAGE_NAMES = {"__unknown__": "Env Config"}
TABLE_COLUMNS = ["Language", "Files", "Lines", "Code", "Comment", "Blank"]


# Source documentation:
#   What it does: Resolves the project or PATH pygount executable.
#   Why it exists: Inventory generation needs the venv and a clear bootstrap error elsewhere.
#   Designed use: run_pygount calls it once; dependencies are never installed implicitly.
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


# Source documentation:
#   What it does: Returns the deterministic Git-tracked file set used for inventory.
#   Why it exists: Totals must not vary with untracked files or ignored build output.
#   Designed use: main passes it to pygount/fallback counters; an empty set is a failure.
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


# Source documentation:
#   What it does: Runs pygount once and decodes its JSON report.
#   Why it exists: Collection must stay separate from repository-specific presentation.
#   Designed use: Pass tracked paths; subprocess or JSON failures stop partial generation.
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


# Source documentation:
#   What it does: Normalizes pygount data into repository display rows.
#   Why it exists: Internal buckets and unknown text require project-specific classification.
#   Designed use: Supply the report and discovery list; output feeds text and SVG renderers.
def build_summary_rows(report: dict[str, Any], paths: list[str]) -> list[list[str]]:
    report_files = {
        str(item.get("path", "")).replace("\\", "/"): item for item in report.get("files", [])
    }
    totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"files": 0, "lines": 0, "code": 0, "comment": 0, "blank": 0}
    )

    for raw_path in paths:
        normalized_path = raw_path.replace("\\", "/")
        item = report_files.get(normalized_path, {})
        language = str(item.get("language", "__unknown__"))
        if language.startswith("__"):
            if language in HIDDEN_LANGUAGE_BUCKETS:
                continue
            if language == "__unknown__":
                try:
                    unknown_lines = (
                        (ROOT / normalized_path).read_text(encoding="utf-8").splitlines()
                    )
                except UnicodeDecodeError:
                    unknown_lines = []
                line_count = len(unknown_lines)
                blank_count = sum(not line.strip() for line in unknown_lines)
                code_count = line_count - blank_count
                comment_count = 0
            else:
                line_count = int(item.get("lineCount", 0) or 0)
                code_count = int(item.get("sourceCount", 0) or 0)
                comment_count = int(item.get("documentationCount", 0) or 0)
                blank_count = int(item.get("emptyCount", 0) or 0)
            language = DISPLAY_LANGUAGE_NAMES.get(language)
            if language is None:
                continue
        else:
            line_count = int(item.get("lineCount", 0) or 0)
            code_count = int(item.get("sourceCount", 0) or 0)
            comment_count = int(item.get("documentationCount", 0) or 0)
            blank_count = int(item.get("emptyCount", 0) or 0)

        values = totals[language]
        values["files"] += 1
        values["lines"] += line_count
        values["code"] += code_count
        values["comment"] += comment_count
        values["blank"] += blank_count

    rows = [
        [
            language,
            str(values["files"]),
            str(values["lines"]),
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
            str(sum(values["files"] for values in totals.values())),
            str(sum(values["lines"] for values in totals.values())),
            str(sum(values["code"] for values in totals.values())),
            str(sum(values["comment"] for values in totals.values())),
            str(sum(values["blank"] for values in totals.values())),
        ]
    )
    return rows


# Source documentation:
#   What it does: Renders aligned plain-text inventory rows.
#   Why it exists: Text is human-readable evidence and the canonical SVG input.
#   Designed use: Pass normalized rows including totals; widths derive from the full table.
def render_summary_text(rows: list[list[str]]) -> str:
    widths = [
        max(len(row[index]) for row in [TABLE_COLUMNS, *rows])
        for index in range(len(TABLE_COLUMNS))
    ]

    def format_row(row: list[str]) -> str:

        return "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))

    divider = "  ".join("-" * width for width in widths)
    return (
        "\n".join([format_row(TABLE_COLUMNS), divider, *(format_row(row) for row in rows)]) + "\n"
    )


# Source documentation:
#   What it does: Wraps inventory text in a terminal-style documentation SVG.
#   Why it exists: GitHub Pages needs a portable visual with fixed geometry and escaped content.
#   Designed use: Pass render_summary_text output; main persists XML under the report directory.
def render_svg(summary_text: str) -> str:
    lines = summary_text.rstrip().splitlines() or ["No pygount output."]
    font_size = 15
    line_height = 18
    padding_x = 14
    padding_y = 12
    char_width = 8.7
    width = int(max(len(line) for line in lines) * char_width + padding_x * 2)
    height = int(len(lines) * line_height + padding_y * 2)
    text_lines = [
        f'<text x="{padding_x}" y="{padding_y + font_size + index * line_height}" xml:space="preserve">{html.escape(line)}</text>'
        for index, line in enumerate(lines)
    ]
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Pygount code inventory">',
            f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0b3bdc"/>',
            f'<rect x="4" y="4" width="{width - 8}" height="{height - 8}" fill="none" stroke="#ffffff" stroke-width="2"/>',
            f'<g fill="#ffffff" font-family="Consolas, Cascadia Mono, Courier New, monospace" font-size="{font_size}">',
            *text_lines,
            "</g>",
            "</svg>",
            "",
        ]
    )


# Source documentation:
#   What it does: Generates synchronized text and SVG source-inventory evidence.
#   Why it exists: One command keeps discovery, counting, and both presentations aligned.
#   Designed use: Run dev pygount-summary; outputs go under build/reports.
def main() -> int:
    paths = source_controlled_files()
    rows = build_summary_rows(run_pygount(paths), paths)
    summary_text = render_summary_text(rows)
    BUILD_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_TEXT.write_text(summary_text, encoding="utf-8")
    SUMMARY_SVG.write_text(render_svg(summary_text), encoding="utf-8")
    print(f"[pygount] scanned source-controlled files: {len(paths)}")
    print(f"[pygount] wrote {SUMMARY_TEXT.relative_to(ROOT)}")
    print(f"[pygount] wrote {SUMMARY_SVG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
