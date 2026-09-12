# Production Release

Use `release` to update the runnable LearningClock app. This is separate from `deploy`.

```cmd
scripts\release.cmd --dry-run
scripts\release.cmd
```

Default installation root:

```text
D:\LearningClock
```

Release layout:

- `Lib\learningclock\`: every application module, the single `app.py`, central `clock.properties`, and packaged dashboard assets
- `Lib\protepo\`: the required pure-Python logging dependency
- `props\`: all per-clock `.properties` files
- `logs\`: LauncherPad logs and one subdirectory per clock
- `assets\Learning-Clock.ico`: the released application icon

VBS is no longer released. Every per-clock `.properties` file remains under `D:\LearningClock\props`; release neither relocates nor deletes those files. Configure `pythonExe` and `pyScriptPath` once in `D:\LearningClock\Lib\learningclock\clock.properties`; later releases preserve that machine-specific file. `pyScriptPath` targets the only deployed application module, `D:\LearningClock\Lib\learningclock\app.py`. Release removes the superseded `runtime` tree only after the `Lib` deployment and dashboard export succeed.

The released ICO under `D:\LearningClock\assets` is built from `launcher\Learning-Clock-source.png` with
`scripts\Build-LauncherIcon.ps1`. It contains native 16, 20, 24, 32, 40, 48,
64, 96, 128, and 256 pixel frames for Start Menu, shortcut, desktop, and window
title-bar display. The builder also synchronizes
`src\learningclock\assets\Learning-Clock.ico`; setuptools includes that copy in
the wheel so both LauncherPad and configured LearningClock windows use the same
top-left icon after installation.

The production environment must contain FastAPI, Uvicorn, and pinned `protepo-log` 2.0.0. Build and install the wheel to create the no-console GUI entry executable:

```cmd
dev package
path\to\python.exe -m pip install --upgrade --no-deps "D:\LocalPackages\protepo-log\2.0.0\protepo_log-2.0.0-py3-none-any.whl"
path\to\python.exe -m pip install --upgrade build\dist\learningclock-6.0-py3-none-any.whl
path\to\python.exe -I -c "import protepo.log; print(protepo.log.__version__)"
path\to\python.exe -m pip check
```

Create one Desktop/Start Menu shortcut to that environment's `Scripts\learningclock-gui.exe`. The generated GUI entry point opens LauncherPad without a console or arguments. Do not create per-clock shortcuts.

Release exports one centralized dashboard and one Dataview implementation:

```text
D:\DiavgeiaVault\Learning-Clock-Dashboard.md
D:\DiavgeiaVault\Engineering\LearningClock\views\learning-clock-dashboard\view.js
```

The central view scans the open Obsidian vault for `*/LearningPath/learning_time_log.csv`. For `logDir=D:\DiavgeiaVault\Engineering\MAGPAI`, the CSV remains under `MAGPAI\LearningPath` and appears in the dashboard's clock selector without a Markdown or JavaScript copy under `MAGPAI`.

Release to a different folder:

```cmd
scripts\release.cmd --production-dir "D:\Some\Other\LearningClock"
```

## Packaging

Build package artifacts:

```cmd
scripts\dev.cmd package
```

Output:

```text
build\dist
```

The build uses `setuptools` through `pyproject.toml`. `[project.gui-scripts]` produces `learningclock-gui.exe`; `[project.scripts]` retains the non-GUI `learningclock` health/version CLI. Package data includes the multi-resolution ICO and central properties; wheel data includes the canonical dashboard resources. PyInstaller is not part of this repository.

## Generated Output Policy

Generated outputs are written under `build\` whenever possible:

- pytest cache
- coverage data
- coverage HTML
- package artifacts
- generated Clock-QA regression CSV

`build\` is ignored by Git. The repository tracks source, tests, fixtures, scripts, launcher assets, and documentation, not generated QA/build output.
