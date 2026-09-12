# LearningClock 6.0 Architecture

**Product Release:** 6.0  
**Document Revision:** R6
**Document Version:** 6.0.R6

LearningClock 6.0 is a local-first Windows desktop system. LauncherPad is a
discovery and launch surface; each configured clock is an independent process
that owns its timer state, singleton guard, persistence, and diagnostics.

## Architectural principles

1. **Split configuration ownership.** Central `clock.properties` owns Python runtime paths; one per-clock file owns `learning-path-name` and `logDir`.
2. **The clock owns integrity.** The clock process acquires its named mutex
   before `CsvStore` initialization. LauncherPad cannot grant ownership.
3. **Processes are independent.** LauncherPad does not retain pipes or child
   lifetime ownership and can close without stopping clocks.
4. **CSV is authoritative.** Session rows and the recalculated final `TOTAL` row
   are the durable learning record. Emergency CSV files preserve recoverability.
5. **Observability is failure-isolated.** Local logging and offline CLEF remain
   available when Seq delivery fails. Seq is evidence, not coordination.
6. **Interfaces stay separated.** Tkinter owns desktop interaction; FastAPI owns
   readiness/OpenAPI; neither directly controls the other.
7. **Provisioning is transactional.** Preflight validation precedes atomic writes and rollback never removes pre-existing content.
8. **Reporting is read-only and current-request wins.** CSV scans run off the UI thread and stale results cannot replace a newer period.

## Component boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| `desktop.py` | GUI-mode dispatch | Timer state or discovery policy |
| `configuration.py` | Central/per-clock parsing, validation, identity, ordering, migration | UI, processes, directories, CSV |
| `provisioning.py` | New-clock validation, atomic properties/CSV files, rollback | Timer state, dashboard deployment, or existing-content overwrite |
| `reporting.py` | Inclusive periods, compatible CSV reads, cross-clock totals | CSV mutation or UI widgets |
| `date_picker.py` | Reusable modal calendar selection | Period or aggregation rules |
| `launcherpad.py` | Clock controls, creation dialog, state observation, report/chart coordination | Clock mutex ownership, CSV writes, child lifetime |
| `process_launcher.py` | Safe command construction and detached process creation | Shell/VBS execution or process supervision |
| `singleton.py` | Windows mutex ownership and observation | Configuration parsing or persistence |
| `app.py` | Timer UI, session state, manual input, lifecycle | CSV normalization rules |
| `csv_store.py` | CSV schema, compatibility, totals, recovery | Tkinter presentation |
| `observability.py` | Logging composition, sinks, correlation | Product event identity definitions |
| `events.py`, `telemetry.py` | Stable semantic event contracts | Sink configuration |
| `api.py` | `/health`, OpenAPI, Swagger UI, ReDoc | Desktop lifecycle or CSV mutation |

## Runtime and data boundaries

The normal packaged path is:

```text
Desktop or Start Menu
  -> learningclock-gui.exe
  -> LauncherPad
  -> central pythonExe + pyScriptPath
  -> detached app.py --learning-path <name> --log-dir <configured-logDir>\LearningPath
  -> named mutex
  -> Tkinter timer and CsvStore
```

LauncherPad itself is started by the installed GUI entry point or repository `pythonw.exe -m learningclock.desktop`. Deployed modules live under `D:\LearningClock\Lib`; clock children use its single `learningclock\app.py`. Each configured `logDir` has a `LearningPath` child containing CSV data, while diagnostics are centralized under `D:\LearningClock\logs`. One dashboard at the vault root uses one view under `Engineering/LearningClock` to discover every clock CSV. No VBS, WScript, CScript, CMD, PowerShell, or console process belongs to normal clock launch.

See [Architecture Diagrams](Diagrams.md) for system, process, sequence, data,
and observability views.
