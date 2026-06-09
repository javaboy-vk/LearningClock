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
- `launcher\Learning-clock.vbs`
- `src\learningclock\__init__.py`
- `src\learningclock\app.py`
- `src\learningclock\csv_store.py`

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

The build uses `setuptools` through `pyproject.toml`.

## Generated Output Policy

Generated outputs are written under `build\` whenever possible:

- pytest cache
- coverage data
- coverage HTML
- package artifacts
- generated Clock-QA regression CSV

`build\` is ignored by Git. The repository tracks source, tests, fixtures, scripts, launcher assets, and documentation, not generated QA/build output.
