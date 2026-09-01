# Quick Start

Run from the repository root:

```cmd
python -m venv .venv
scripts\dev.cmd install
scripts\dev.cmd test
```

Start the lightweight package CLI:

```cmd
.\.venv\Scripts\python.exe -m learningclock
.\.venv\Scripts\python.exe -m learningclock --version
```

Start the primary LauncherPad GUI from source without a console:

```cmd
set PYTHONPATH=src
.\.venv\Scripts\pythonw.exe -m learningclock.desktop
```

Run one configured clock directly for debugging while retaining singleton protection:

```cmd
.\.venv\Scripts\pythonw.exe -m learningclock.desktop --clock launcher\dev.properties
```
