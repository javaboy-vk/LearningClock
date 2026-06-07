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
scripts\dev.cmd validate-config
scripts\dev.cmd test
scripts\dev.cmd unittest-csv
scripts\csv-test.cmd test1
scripts\test1.cmd
scripts\dev.cmd package
scripts\dev.cmd install
scripts\dev.cmd deploy
```

Run the CSV test suite against app-style properties without modifying the original CSV:

```cmd
scripts\dev.cmd unittest-csv-file --properties "tests\fixtures\MAGPAI-regression.properties"
```

Run one CSV regression test repeatedly by passing its index alias:

```cmd
scripts\dev.cmd unittest-csv-file --properties "tests\fixtures\MAGPAI-regression.properties" test1
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
.\.venv\Scripts\python.exe scripts\dev.py unittest-csv
.\.venv\Scripts\python.exe scripts\dev.py unittest-csv-file --properties "tests\fixtures\MAGPAI-regression.properties"
.\.venv\Scripts\python.exe scripts\dev.py unittest-csv-file --properties "tests\fixtures\MAGPAI-regression.properties" test1
.\.venv\Scripts\python.exe scripts\dev.py csv-test test1
.\.venv\Scripts\python.exe scripts\dev.py package
.\.venv\Scripts\python.exe scripts\dev.py install
.\.venv\Scripts\python.exe scripts\dev.py deploy
```

All generated build outputs are written under `build/`. The install workflow installs dependency
packages only; it does not install the local project in editable mode, so source-tree egg metadata
is not kept in the repository.
