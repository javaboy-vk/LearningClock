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
scripts\dev.cmd test
scripts\dev.cmd unittest-csv
scripts\dev.cmd package
scripts\dev.cmd install
scripts\dev.cmd deploy
```

Run the CSV test suite against a specific problem CSV without modifying the original file:

```cmd
scripts\dev.cmd unittest-csv-file --csv "D:\DiavgeiaVault\Engineering\LearningClock\LearningPath\learning_time_log.csv"
```

Equivalent interpreter-explicit commands:

```cmd
.\.venv\Scripts\python.exe scripts\dev.py clean
.\.venv\Scripts\python.exe scripts\dev.py compile
.\.venv\Scripts\python.exe scripts\dev.py test
.\.venv\Scripts\python.exe scripts\dev.py unittest-csv
.\.venv\Scripts\python.exe scripts\dev.py unittest-csv-file --csv "D:\DiavgeiaVault\Engineering\LearningClock\LearningPath\learning_time_log.csv"
.\.venv\Scripts\python.exe scripts\dev.py package
.\.venv\Scripts\python.exe scripts\dev.py install
.\.venv\Scripts\python.exe scripts\dev.py deploy
```

Lifecycle mapping:

- `clean`: remove generated build, cache, coverage, and bytecode artifacts.
- `compile`: byte-compile `src` and `tests`.
- `test`: run `pytest`.
- `package`: build package artifacts into `build\dist` and remove source-tree package metadata.
- `install`: install runtime and development requirements into `.venv` without installing the local project in editable mode.
- `deploy`: export Diavgeia content to the local vault.
