# Production Release

Use `release` to update the runnable LearningClock app. This is separate from `deploy`.

```cmd
scripts\release.cmd --dry-run
scripts\release.cmd
```

Default production directory:

```text
D:\LearningPath\Tools\LearningClock
```

Files copied by release:

- `launcher\Learning-Clock.ico`
- every `src\learningclock\*.py` module under `learningclock\`
- the default `clock.properties`, while preserving an existing deployed copy

VBS is no longer released. `D:\LearningPath\*.properties` remains the configuration-data directory; legacy `pythonExe` and `pyScriptPath` properties are ignored by LauncherPad.

The released ICO is built from `launcher\Learning-Clock-source.png` with
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

Release also reads `D:\LearningPath\*.properties` and exports the shared dashboard component beside each configured `LearningPath` CSV folder:

```text
Learning-Clock-Dashboard.md
views\
```

For a properties file with `logDir=D:\DiavgeiaVault\Engineering\MAGPAI\LearningPath`, release updates `D:\DiavgeiaVault\Engineering\MAGPAI\Learning-Clock-Dashboard.md` and `D:\DiavgeiaVault\Engineering\MAGPAI\views\`.

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

The build uses `setuptools` through `pyproject.toml`. `[project.gui-scripts]` produces `learningclock-gui.exe`; `[project.scripts]` retains the non-GUI `learningclock` health/version CLI. Package data includes the multi-resolution window ICO. PyInstaller is not part of this repository.

## Generated Output Policy

Generated outputs are written under `build\` whenever possible:

- pytest cache
- coverage data
- coverage HTML
- package artifacts
- generated Clock-QA regression CSV

`build\` is ignored by Git. The repository tracks source, tests, fixtures, scripts, launcher assets, and documentation, not generated QA/build output.
