# LearningClock 6.0 Architecture

**Product Release:** 6.0  
**Document Revision:** R1  
**Document Version:** 6.0.R1

LearningClock 6.0 is a local-first Windows desktop system. LauncherPad is a
discovery and launch surface; each configured clock is an independent process
that owns its timer state, singleton guard, persistence, and diagnostics.

## Architectural principles

1. **One configuration, one identity.** A valid `.properties` file resolves to
   one immutable `ConfiguredClock` and one stable `clock_id`.
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

## Component boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| `desktop.py` | GUI-mode dispatch | Timer state or discovery policy |
| `configuration.py` | Properties parsing, validation, identity, ordering | UI, processes, directories, CSV |
| `launcherpad.py` | Clock controls, state observation, launch requests | Clock mutex ownership, CSV, child lifetime |
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
  -> detached learningclock-gui.exe --clock <properties>
  -> named mutex
  -> Tkinter timer and CsvStore
```

Source mode replaces the packaged executable with the active environment's
adjacent `pythonw.exe -m learningclock.desktop`. No VBS, WScript, CScript, CMD,
PowerShell, or console process belongs to the normal GUI path.

See [Architecture Diagrams](Diagrams.md) for system, process, sequence, data,
and observability views.
