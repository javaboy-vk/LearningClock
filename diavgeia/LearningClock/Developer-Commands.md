# Developer Commands

This page tracks CLI commands executed while building and maintaining LearningClock.

## Python Environment

### Create project virtual environment

Run from the repository root in Command Prompt:

```cmd
python -m venv .venv
```

Purpose: create the project-owned Python virtual environment at `.venv`.

Status: pending manual execution.

## Maven-Style Python Lifecycle

Run these from the repository root after `.venv` exists:

```cmd
scripts\dev.cmd clean
scripts\dev.cmd compile
scripts\dev.cmd validate-config
scripts\dev.cmd test
scripts\coverage.cmd
scripts\pygount-summary.cmd
scripts\readme-assets.cmd
scripts\dev.cmd unittest-csv
scripts\dev.cmd csv-test test1
scripts\dev.cmd package
scripts\dev.cmd install
scripts\dev.cmd deploy
scripts\release.cmd --dry-run
scripts\release.cmd
```

Run the CSV regression suite against app-style properties without modifying the original CSV:

```cmd
scripts\dev.cmd unittest-csv-file --properties "tests\fixtures\clock-QA.properties"
```

Run one CSV regression test repeatedly by passing its index alias:

```cmd
scripts\dev.cmd unittest-csv-file --properties "tests\fixtures\clock-QA.properties" test1
```

Short local-fixture commands for focused CSV regression work:

```cmd
scripts\csv-test.cmd test1
scripts\test1.cmd
```

Equivalent interpreter-explicit commands:

```cmd
.\.venv\Scripts\python.exe scripts\dev.py clean
.\.venv\Scripts\python.exe scripts\dev.py compile
.\.venv\Scripts\python.exe scripts\dev.py validate-config
.\.venv\Scripts\python.exe scripts\dev.py test
.\.venv\Scripts\python.exe scripts\dev.py coverage
.\.venv\Scripts\python.exe scripts\dev.py pygount-summary
.\.venv\Scripts\python.exe scripts\dev.py readme-assets
.\.venv\Scripts\python.exe scripts\dev.py unittest-csv
.\.venv\Scripts\python.exe scripts\dev.py unittest-csv-file --properties "tests\fixtures\clock-QA.properties"
.\.venv\Scripts\python.exe scripts\dev.py unittest-csv-file --properties "tests\fixtures\clock-QA.properties" test1
.\.venv\Scripts\python.exe scripts\dev.py csv-test test1
.\.venv\Scripts\python.exe scripts\dev.py package
.\.venv\Scripts\python.exe scripts\dev.py install
.\.venv\Scripts\python.exe scripts\dev.py deploy
.\.venv\Scripts\python.exe scripts\dev.py release --dry-run
.\.venv\Scripts\python.exe scripts\dev.py release
```

Lifecycle mapping:

- `clean`: remove generated build, cache, coverage, and bytecode artifacts.
- `compile`: byte-compile `src` and `tests`.
- `validate-config`: validate `.vscode\launch.json`, `.vscode\tasks.json`, and `LearningClock.code-workspace`.
- `test`: run `pytest`.
- `coverage`: run the complete pytest suite with terminal coverage and write HTML coverage to `build\coverage\html`.
- `pygount-summary`: run pygount summary reporting, generate `docs\assets\pygount-summary.svg`, and keep the README code inventory at the bottom.
- `readme-assets`: generate README SVG visuals for the desktop UI and Obsidian dashboard.
- `unittest-csv`: run the isolated CSV unit test file.
- `unittest-csv-file`: run the CSV regression suite against a properties-selected or explicitly supplied CSV.
- `csv-test`: run a focused CSV regression selector through the local fixture properties.
- `package`: build package artifacts into `build\dist` and remove source-tree package metadata.
- `install`: install runtime and development requirements into `.venv` without installing the local project in editable mode.
- `deploy`: export Diavgeia content to the local vault.
- `release`: copy the production launcher and runtime Python files to `D:\LearningPath\Tools\LearningClock`.

## Production Release

Use `release`, not `deploy`, when updating the runnable LearningClock app.

Recommended release sequence from the repository root:

```cmd
scripts\dev.cmd clean
scripts\dev.cmd install
scripts\dev.cmd compile
scripts\dev.cmd validate-config
scripts\dev.cmd test
scripts\release.cmd --dry-run
scripts\release.cmd
```

The release target copies these files:

- `launcher\Learning-Clock.ico` -> `D:\LearningPath\Tools\LearningClock\Learning-Clock.ico`
- `launcher\Learning-clock.vbs` -> `D:\LearningPath\Tools\LearningClock\Learning-clock.vbs`
- `src\learningclock\__init__.py` -> `D:\LearningPath\Tools\LearningClock\__init__.py`
- `src\learningclock\app.py` -> `D:\LearningPath\Tools\LearningClock\app.py`
- `src\learningclock\csv_store.py` -> `D:\LearningPath\Tools\LearningClock\csv_store.py`

To release to a different folder:

```cmd
scripts\release.cmd --production-dir "D:\Some\Other\LearningClock"
```
