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

Start the desktop app from source:

```cmd
set PYTHONPATH=src
.\.venv\Scripts\python.exe src\learningclock\app.py
```
