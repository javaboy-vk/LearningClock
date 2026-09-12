# LauncherPad Architecture and Operations

LearningClock LauncherPad 2.0 is the normal Windows entry point. It owns configuration discovery, new-clock provisioning, runtime launch validation, mutex observation, and read-only cross-clock reporting. Each timer remains an independent process and the sole writer of its CSV.

## Configuration ownership and resolution

The central `clock.properties` is resolved from `learningclock/configuration.py`, beside the deployed package modules. In source it is `src\learningclock\clock.properties`; `dev release` places it at `D:\LearningClock\Lib\learningclock\clock.properties`; a wheel installation places it in that environment's `site-packages\learningclock`. This makes lookup independent of the shortcut or process working directory. `LEARNINGCLOCK_CENTRAL_CONFIG` and desktop `--central-config` are supported overrides; an absolute value is used directly and a relative value resolves beside the packaged default.

```properties
pythonExe=P:\Python\Python314\pythonw.exe
pyScriptPath=D:\LearningClock\Lib\learningclock\app.py
autosave_minutes=5
```

`pythonExe` and `pyScriptPath` are shared and authoritative. `autosave_minutes` remains the optional timer checkpoint setting. Values shown above are deployment examples, not code constants. The parser treats backslashes literally and supports spaces without Java `Properties` escaping.

Per-clock files are discovered from `D:\LearningClock\props` by default and newly created files contain only:

```properties
learning-path-name=Polyglot-Lab
logDir=D:\DiavgeiaVault\Engineering\Polyglot-Lab
```

On launch, `load_central_configuration(..., validate_paths=True)` proves the Python executable and script exist. `process_launcher.py` then builds a list-form, shell-free command using `--learning-path`, `--log-dir`, `--clock-id`, and `--correlation-id`. A missing/unreadable central file, blank setting, or missing runtime path produces an actionable dialog and no process attempt.

Old per-clock files containing `pythonExe` or `pyScriptPath` remain loadable. Discovery ignores those values, atomically removes only those lines, and converts an old `logDir` ending in `LearningPath` to its parent clock directory. It retains comments and other supported properties where possible and emits `CONFG-2007`. Migration failure is isolated and logged; it never updates central configuration.

## Create New Clock

**Create New Clock** opens a modal form with a learning path name, complete Diavgeia clock directory, Browse, Create, and Cancel. Enter submits and Escape cancels.

Before writing, `provisioning.py` rejects blanks, path traversal, control/invalid Windows filename characters, reserved names, relative log paths, duplicate names, duplicate canonical log directories, and any existing LearningClock properties or CSV file.

Successful creation performs one transactional workflow:

1. Create `logDir`, its `LearningPath` child, and missing configuration/Diavgeia parents without touching existing unrelated content.
2. Atomically write `<learning-path-name>.properties` with only the two per-clock keys.
3. Initialize `logDir\LearningPath\learning_time_log.csv` with the complete `csv_store.FIELDNAMES` header.
4. Leave dashboard resources untouched; release tooling owns the single vault-level dashboard and view.
5. Rediscover clock configurations and refresh the LauncherPad report immediately.

If a write fails, only files created by the operation are removed. Newly created directories are removed only when empty; pre-existing directories and unrelated files are never deleted. Existing LearningClock files are not overwritten.

## Cross-clock report

`reporting.py` uses `csv_store.ACTIVITIES`, `ACTIVITY_TO_FIELD`, legacy field mappings, date formats, and `learning_time_log.csv` filename as the canonical contract. Categories retain timer order. A single-worker executor keeps filesystem scanning off Tk's UI thread, and a monotonically increasing request ID prevents an older result replacing a newer selection.

| Option | Inclusive local-date definition |
| --- | --- |
| `This week` | Monday through today |
| `Last week` | Previous Monday through Sunday |
| `This month` | First day of this month through today |
| `Define range` | Calendar-selected start through end |

Custom fields are read-only and appear only for `Define range`; clicking either opens the reusable Tkinter calendar. Start after end is rejected.

The aggregator enumerates valid configurations, de-duplicates canonical log directories, reads dated session rows, excludes `TOTAL`, understands all current/legacy date formats and category aliases, and sums integer seconds. Missing columns contribute zero. Missing/unavailable/empty files and malformed dates or durations are isolated and logged as `LPLCL-1031`. The skipped/invalid count below the chart is a hyperlink; its read-only popup lists the clock, source path, CSV row, column, rejected value, and reason for every issue. Each path is itself a link that opens the source file, or the nearest existing directory for a missing source. The chart still renders all categories and zero totals when no rows match. Durations use unbounded hours, so values beyond 24 hours remain correct.

## Source and deployment boundaries

| Source | Responsibility |
| --- | --- |
| `configuration.py` | Central/per-clock parsing, validation, discovery, de-duplication, migration |
| `provisioning.py` | Name/path validation, atomic properties/CSV creation, rollback |
| `reporting.py` | Period resolution, CSV compatibility, aggregation |
| `date_picker.py` | Reusable modal calendar |
| `launcherpad.py` | Tkinter controls, refresh, background request ordering, chart |
| `process_launcher.py` | Central+clock command construction and detached launch |
| `csv_store.py` | Canonical filenames, activities, fields, aliases, duration format |

`pyproject.toml` includes central configuration and dashboard resources in packages. `dev release` stages the complete package under `Lib`, keeps only `Lib\learningclock\app.py`, places the icon under `assets`, and preserves `Lib\learningclock\clock.properties`. It then publishes the dashboard at `D:\DiavgeiaVault\Learning-Clock-Dashboard.md` and the view under `D:\DiavgeiaVault\Engineering\LearningClock\views`.

## Troubleshooting

- **Central configuration unavailable:** edit the reported `clock.properties` and set nonblank existing `pythonExe` and `pyScriptPath` files.
- **Invalid log directory:** select a complete Windows path. LauncherPad creates missing parents.
- **Creation conflict:** move/rename the existing properties or CSV after reviewing it; LauncherPad does not overwrite user content.
- **Missing CSV:** the report shows a skipped source; opening a newly provisioned clock uses its initialized canonical CSV.
- **Skipped report sources:** click the skipped/invalid hyperlink below the chart to inspect and open each exact file/row. The scan is read-only. `launcherpad_debug.log` retains the corresponding `LPLCL-1031` events.
- **Dashboard cannot find CSV:** confirm the CSV is in the configured clock's `LearningPath` child, the dashboard is at the vault root, and the view exists under `Engineering/LearningClock/views`.

Start and register from the repository with:

```cmd
dev launcherpad
dev launcherpad --config-dir D:\LearningClock\props
dev launcherpad --central-config D:\LearningClock\Lib\learningclock\clock.properties
dev launcherpad-register
```
