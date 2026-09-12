# LearningClock 6.0 Implementation

**Product Release:** 6.0  
**Document Revision:** R6
**Document Version:** 6.0.R6

The v6.0 implementation is a `src`-layout Python package with a Tkinter desktop
runtime, Windows process and mutex adapters, CSV persistence, semantic logging,
and a small FastAPI readiness surface.

## Primary workflows

### LauncherPad startup

1. `desktop.main()` selects LauncherPad mode when `--clock` is absent.
2. `launcherpad.main()` configures diagnostics and creates the Tkinter root.
3. `load_central_configuration()` loads package-local `pythonExe` and `pyScriptPath` without using the current working directory.
4. `discover_clock_configurations()` validates and migrates per-clock files while isolating malformed files, duplicate identities, names, and log directories.
5. LauncherPad maps each valid clock to a control and observes its mutex every
   1.5 seconds.

### Clock launch and startup

1. A launch creates a correlation ID and emits `LPCRP-3001`.
2. LauncherPad revalidates central runtime paths.
3. `process_launcher.launch_clock()` combines central and clock configuration into a detached list-form `pythonExe pyScriptPath --learning-path ... --log-dir <configured-logDir>\LearningPath ...` command.
4. `app.main()` builds the compatible immutable clock identity and acquires
   `Local\Protepo.LearningClock.<clock-id>`.
5. Only the successful mutex owner initializes `CsvStore`, timer state, and UI.

### Provisioning and reporting

`provisioning.provision_clock()` preflights duplicates/conflicts, atomically writes the exact two-key configuration, and initializes the canonical CSV under `logDir\LearningPath`. Dashboard resources are not part of per-clock provisioning: the central vault page scans for those CSV files. Provisioning rolls back only newly created content on failure.

`reporting.resolve_date_range()` provides the four inclusive local-date periods. `aggregate_clock_time()` reads non-`TOTAL` session rows across valid clocks using the canonical activity order and legacy date/field mappings. Every skipped input becomes an immutable `ReportIssue` with its clock, source path, CSV row, column, rejected value, and reason. LauncherPad performs that read in a single background worker, accepts only the latest request ID, renders the vertical chart, and exposes the issues through a linked read-only popup.

### Persistence

Timer switches close the prior activity interval and accumulate integer seconds.
Manual time and pages update the selected session date. Autosave, progress
refresh, and close use replacement/checkpoint semantics so the same session is
not duplicated. A rewrite removes stale `TOTAL` rows, normalizes legacy fields,
merges recoverable emergency rows, sorts sessions, and appends one recalculated
final `TOTAL` row.

### Observability

`events.py` retains catalog-based semantic events for the existing application,
UI, timer, CSV, configuration, and CLI boundaries. `telemetry.py` defines v2
events for LauncherPad, configuration discovery, process launch, mutex handling,
runtime, and calendar behavior. `observability.py` composes both forms into
named loggers, correlation contexts, local files, optional Seq, and offline
spooling.

## Failure behavior

- One malformed configuration is skipped without blocking other clocks.
- A duplicate mutex rejects startup before persistence initialization.
- Process launch errors remain in LauncherPad and produce structured telemetry.
- Missing central runtime settings or files prevent launch and produce an actionable dialog.
- Provisioning conflicts never overwrite existing CSV, configuration, or user content.
- Invalid report sources/rows are skipped individually; valid clocks still contribute, and the linked diagnostics identify the exact source without rewriting it.
- File/Seq sink configuration falls back to visible console diagnostics.
- Seq delivery failure does not block UI startup or CSV operations.
- Normal CSV write failure attempts a timestamped emergency CSV.
- Closing LauncherPad cancels observation only; it does not signal clocks.

See [Python Source Code](Python%20Source%20Code.md) for the complete module,
script, and test responsibility map.
