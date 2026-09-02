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
dev launcherpad
```

Register the same source LauncherPad in the current user's Windows Start Menu:

```cmd
dev launcherpad-register
```

The registration command uses `launcher\Learning-Clock.ico` and asks Windows to
pin the shortcut. If Windows does not expose automatic pinning, find
**LearningClock LauncherPad** in Start, right-click it, and select **Pin to Start**.

Run one configured clock directly for debugging while retaining singleton protection:

```cmd
.\.venv\Scripts\pythonw.exe -m learningclock.desktop --clock launcher\dev.properties
```
