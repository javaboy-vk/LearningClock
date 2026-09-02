# LearningClock 6.0 Implementation

**Product Release:** 6.0  
**Document Revision:** R1  
**Document Version:** 6.0.R1

The v6.0 implementation is a `src`-layout Python package with a Tkinter desktop
runtime, Windows process and mutex adapters, CSV persistence, semantic logging,
and a small FastAPI readiness surface.

## Primary workflows

### LauncherPad startup

1. `desktop.main()` selects LauncherPad mode when `--clock` is absent.
2. `launcherpad.main()` configures diagnostics and creates the Tkinter root.
3. `discover_clock_configurations()` validates every discovered properties file
   while isolating malformed files and duplicate identities.
4. LauncherPad maps each valid clock to a control and observes its mutex every
   1.5 seconds.

### Clock launch and startup

1. A launch creates a correlation ID and emits `LPCRP-3001`.
2. `process_launcher.launch_clock()` creates a detached list-form command.
3. The child re-enters `desktop.main()` with `--clock` and dispatches to
   `app.main()`.
4. The clock loads its immutable configuration and acquires
   `Local\Protepo.LearningClock.<clock-id>`.
5. Only the successful mutex owner initializes `CsvStore`, timer state, and UI.

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
- File/Seq sink configuration falls back to visible console diagnostics.
- Seq delivery failure does not block UI startup or CSV operations.
- Normal CSV write failure attempts a timestamped emergency CSV.
- Closing LauncherPad cancels observation only; it does not signal clocks.

See [Python Source Code](Python%20Source%20Code.md) for the complete module,
script, and test responsibility map.
