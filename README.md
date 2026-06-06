# LearningClock

Python project scaffold for LearningClock.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe scripts\dev.py install
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m learningclock
```

## Common Commands

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

All generated build outputs are written under `build/`. The install workflow installs dependency
packages only; it does not install the local project in editable mode, so source-tree egg metadata
is not kept in the repository.
