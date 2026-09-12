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
scripts\dev.cmd api --reload
scripts\dev.cmd openapi
scripts\dev.cmd seq-dashboard
scripts\dev.cmd launcherpad
scripts\dev.cmd launcherpad-register
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
.\.venv\Scripts\python.exe scripts\dev.py api --reload
.\.venv\Scripts\python.exe scripts\dev.py openapi
.\.venv\Scripts\python.exe scripts\dev.py seq-dashboard
.\.venv\Scripts\python.exe scripts\dev.py launcherpad
.\.venv\Scripts\python.exe scripts\dev.py launcherpad-register
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
- `pygount-summary`: count Git-tracked files and generate ignored text/SVG inventory reports under `build\reports`.
- `readme-assets`: generate README SVG visuals for the desktop UI and Obsidian dashboard.
- `api`: run the FastAPI readiness surface, Swagger UI, ReDoc, and runtime OpenAPI schema.
- `openapi`: regenerate tracked `docs\openapi.json` from the FastAPI application.
- `launcherpad`: start the source LauncherPad as an independent no-console process using the project `.venv` and `D:\LearningClock\props` by default.
- `launcherpad-register`: create or update the current user's Start Menu shortcut, synchronize an existing taskbar pin with the same paths, and request **Pin to Start**. Windows may require the pin to be completed manually; `--no-pin` skips only the new pin request.
- `unittest-csv`: run the isolated CSV unit test file.
- `unittest-csv-file`: run the CSV regression suite against a properties-selected or explicitly supplied CSV.
- `csv-test`: run a focused CSV regression selector through the local fixture properties.
- `package`: build package artifacts into `build\dist` and remove source-tree package metadata.
- `install`: install runtime and development requirements into `.venv` without installing the local project in editable mode.
- `deploy`: export Diavgeia content to the local vault.
- `release`: deploy modules to `D:\LearningClock\Lib`, the icon to `assets`, and ensure `props` and `logs` exist.
- `seq-dashboard`: install or update the LearningClock Seq workspace and Operations dashboard.

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

- `launcher\Learning-Clock.ico` -> `D:\LearningClock\assets\Learning-Clock.ico`
- every `src\learningclock\*.py` -> `D:\LearningClock\Lib\learningclock\`
- the pure-Python logging dependency -> `D:\LearningClock\Lib\protepo\`
- the default `clock.properties` only when the deployed copy does not already exist

The v6.0 release no longer deploys VBS. Install the built wheel to obtain the
single no-console `learningclock-gui.exe` entry point. Release exports the central
dashboard to `D:\DiavgeiaVault\Learning-Clock-Dashboard.md` and the Dataview
implementation under `D:\DiavgeiaVault\Engineering\LearningClock\views`; clock
directories receive no copies.

To release to a different folder:

```cmd
scripts\release.cmd --production-dir "D:\Some\Other\LearningClock"
```

## Controlled v6.0 documentation

- [Architecture](6.0/Architecture/Overview.md)
- [Architecture diagrams](6.0/Architecture/Diagrams.md)
- [Configuration](6.0/Configuration/Overview.md)
- [Seq setup](6.0/Configuration/Seq%20Setup.md)
- [Implementation](6.0/Implementation/Overview.md)
- [Python source code](6.0/Implementation/Python%20Source%20Code.md)
