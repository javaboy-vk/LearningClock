# Source Code Structure

```text
src\learningclock\
  __init__.py          Package metadata and version.
  __main__.py          Implements python -m learningclock.
  cli.py               Lightweight non-GUI CLI and version/readiness checks.
  app.py               Tkinter application, timer state, UI workflow, shutdown flow.
  csv_store.py         CSV schema, normalization, persistence, totals, emergency recovery.
  learning-clock.py    Compatibility launcher for older script/debug paths.
```

## `learningclock.app`

`app.py` owns the desktop experience. It builds the Tkinter window, menu, timer rows, manual-entry controls, page-count controls, and shutdown lifecycle.

Main responsibilities:

- Parse desktop launch arguments such as `--learning-path`, `--log-dir`, and debug-break flags.
- Track active activity, active start time, accumulated activity totals, and page count.
- Switch, stop, and reset timers.
- Validate and apply manual time entries.
- Validate and apply page-count entries.
- Create a session row at shutdown and hand persistence to `CsvStore`.
- Attempt emergency save when normal CSV persistence fails.
- Keep diagnostic events in the same log used by CSV persistence.

## `learningclock.csv_store`

`csv_store.py` owns the persistence contract. It centralizes CSV structure and historical compatibility rules so the GUI does not need to know how to normalize or repair stored data.

Main responsibilities:

- Define activities, CSV field names, filename constants, date formats, and legacy field mappings.
- Convert duration values with `format_seconds()` and `parse_duration()`.
- Create complete session rows from activity seconds and pages.
- Read existing CSV rows while removing stale `TOTAL` rows.
- Normalize legacy dates and legacy columns.
- Read and merge emergency CSV files.
- Recalculate per-row totals when old data is incomplete.
- Recalculate the final aggregate `TOTAL` row.
- Write one clean CSV with session rows plus exactly one final `TOTAL` row.
- Write diagnostic log entries without allowing logging failures to break timer operation.

## `learningclock.cli`

`cli.py` provides a fast, non-GUI command surface for automation and health checks.

```cmd
.\.venv\Scripts\python.exe -m learningclock
.\.venv\Scripts\python.exe -m learningclock --version
```

## Compatibility Launcher

`src\learningclock\learning-clock.py` is a thin compatibility wrapper. It exists so older launchers and debugging workflows can keep calling the historical filename while the real implementation lives in importable package modules.
