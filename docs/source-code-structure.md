# Source Code Structure

```text
src\learningclock\
  __init__.py          Package metadata and version.
  __main__.py          Implements python -m learningclock.
  cli.py               Lightweight non-GUI CLI and version/readiness checks.
  api.py               FastAPI health endpoint and automatic OpenAPI documentation.
  app.py               Tkinter application, timer state, UI workflow, shutdown flow.
  configuration.py     Properties discovery, validation, ordering, and stable clock identity.
  desktop.py           Primary no-console GUI dispatcher; LauncherPad default and --clock mode.
  launcherpad.py       Dynamic configured-clock grid and mutex-based running-state UI.
  process_launcher.py  Detached source/packaged GUI process construction and launch.
  singleton.py         Windows named-mutex ownership and observation.
  telemetry.py         Formal protepo.log 2.0 event definitions for new runtime boundaries.
  window_icon.py       Shared multi-layout icon resolution and Tk title-bar application.
  csv_store.py         CSV schema, normalization, persistence, totals, emergency recovery.
  events.py            Product-owned semantic event catalogs and stable event IDs.
  observability.py     protepo.log configuration, logger composition, and correlation.
  learning-clock.py    Compatibility launcher for older script/debug paths.
```

## `learningclock.app`

`desktop.py` is the primary GUI entry. It opens LauncherPad by default and dispatches `--clock <properties>` to `app.py`. `app.py` owns one configured timer experience and acquires its process-level singleton guard before persistence initialization.

Main responsibilities:

- Parse desktop launch arguments such as `--learning-path`, `--log-dir`, and debug-break flags.
- Resolve `--config`, acquire `Local\Protepo.LearningClock.<clock-id>`, and reject duplicates before `CsvStore` creation.
- Track active activity, active start time, accumulated activity totals, and page count.
- Switch, stop, and reset timers.
- Validate and apply manual time entries.
- Validate and apply page-count entries.
- Create a session row at shutdown and hand persistence to `CsvStore`.
- Attempt emergency save when normal CSV persistence fails.
- Call the native application, UI, and timer loggers supplied by `protepo.log`.

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
- Call the native `protepo.log` storage logger for semantic persistence events.

## `learningclock.cli`

`cli.py` provides a fast, non-GUI command surface for automation and health checks.
Its user-facing response remains on stdout; semantic `CMDLN-*` events use stderr.

```cmd
.\.venv\Scripts\python.exe -m learningclock
.\.venv\Scripts\python.exe -m learningclock --version
```

## `learningclock.api`

`api.py` owns the HTTP contract. FastAPI publishes `GET /health`, the OpenAPI schema at
`/openapi.json`, Swagger UI at `/docs`, and ReDoc at `/redoc`. `scripts/export_openapi.py`
generates the tracked `docs/openapi.json` contract from the same application object.

## `learningclock.events` and `learningclock.observability`

`events.py` owns stable event codes for application lifecycle, UI workflows, timers, storage,
configuration, and CLI behavior. `observability.py` configures console, file, and optional Seq
sinks, registers every LearningClock event catalog with `Log`, creates one native logger per
catalog through `Log.get_logger(...)`, and supplies correlation contexts.

`telemetry.py` defines the formal v2 event families used by the newest runtime
boundaries: LauncherPad (`LPLCL`), discovery (`CONFG`), process launch (`LPCRP`),
singleton protection (`MUTEX`), clock lifecycle (`LIFCL`), and calendar behavior
(`CLNDR`). Event codes and placeholders are contracts consumed by local logs,
Seq queries, dashboards, and tests.

## LauncherPad and Process Boundaries

- `configuration.py` returns immutable configurations and isolated issues; it
  does not create UI, processes, log directories, mutexes, or CSV files.
- `desktop.py` is the single GUI dispatcher. Delayed imports select LauncherPad
  or one internal `--clock` process without initializing both applications.
- `launcherpad.py` owns controls, observation, and launch requests. It never owns
  a selected clock's mutex, persistence, or lifetime.
- `process_launcher.py` builds list-form packaged/source commands and starts
  detached processes without shells, VBS, pipes, or retained supervision.
- `singleton.py` separates mutex ownership from observation. A clock acquires its
  guard before persistence; LauncherPad opens and immediately closes an
  observation handle.
- `window_icon.py` resolves one packaged, released, or repository ICO and applies
  it to both primary Tk root windows without making cosmetic failure fatal.

## Developer Python

```text
scripts\
  dev.py                                  Lifecycle command dispatcher.
  export_openapi.py                       Tracked OpenAPI schema exporter.
  generate_readme_assets.py               README SVG generator.
  migrate_learningpath_csv_categories.py  Backup-first CSV migration.
  pygount_summary.py                      Git-tracked inventory generator.
```

`scripts/dev.py` keeps generated outputs under `build\` where possible and
refuses cleanup outside the repository. `deploy` and `release` are explicit
external-write targets; tests, compilation, and local report generation do not
publish or release content.

## Test Python

The test suite covers API/OpenAPI parity, UI state, CLI behavior, configuration
discovery, LauncherPad state, CSV unit/regression behavior, observability,
detached process launching, release inclusion, Seq template contracts, and both
fake and real Windows mutex behavior. Shared CSV setup lives in
`tests/learning_clock_csv_test_support.py`.

The controlled Diavgeia catalog at
`diavgeia\LearningClock\6.0\Implementation\Python Source Code.md` lists every
tracked Python module, script, support file, and suite.

## Function and Method Documentation Standard

Every substantive function and method documents what it does, why the callable
exists, and how it is designed to be used. Failure, fallback, ownership, and
sequencing behavior are included where they are not obvious. This documentation
is a Java-style `#` comment block immediately above the definition and outside
the callable body. For decorated callables, the block is immediately above the
decorator. In-body function and method docstrings are not used for this purpose.

Redundant commentary is intentionally omitted for obvious one- or two-line
accessors, protocol declarations, direct command wrappers, and clearly named
test/fake helpers. Short length does not exempt code whose order or side effects
affect persistence, process ownership, security, or cleanup.

## Compatibility Launcher

`src\learningclock\learning-clock.py` is a thin compatibility wrapper. It exists so older launchers and debugging workflows can keep calling the historical filename while the real implementation lives in importable package modules.
