# Application Logging and Seq Operations

LearningClock requires distribution `protepo-log` 2.0.0 and imports it as `protepo.log`. The dependency is pinned to immutable release commit `115ab65d25e445876257b80a623a6d1667ac8cec`; the application refuses to configure observability if the imported runtime version differs.

## Protepo Logging Standard v2

LauncherPad and new runtime boundaries use formal `define_event(...)` definitions from `telemetry.py`, named component loggers from `Log.get_logger(...)`, and `logger.event(...)`. Engineering audience mode preserves internal operational detail while Seq receives the independently configured engineering representation. Existing timer and CSV catalogs remain supported through protepo.log's compatible semantic catalog API.

| Family | Component | Responsibility |
| --- | --- | --- |
| `LPLCL-1xxx` | `LauncherPad` | Lifecycle, running-state transitions, provisioning, report completion, and skipped report inputs. |
| `CONFG-2xxx` | `Configuration` | Discovery, validation, malformed files, and duplicate IDs. |
| `LPCRP-3xxx` | `ProcessLauncher` | Launch requests, commands, created processes, and failures. |
| `MUTEX-4xxx` | `InstanceGuard` | Mutex identity, acquisition, duplicate rejection, observation, and cleanup. |
| `LIFCL-5xxx` | `Runtime` | Configured LearningClock startup, initialization, close, and fatal failures. |
| `CLNDR-6xxx` | `Calendar` | Calendar initialization and popup failures. |
| `APPLC`, `USRIF`, `TIMER`, `STORG`, `CONFG`, `CMDLN` | Existing components | Desktop, UI, timer, persistence, configuration, and CLI behavior. |

Formal event properties use the v2 canonical `snake_case` property contract. Representative fields are `clock_id`, `clock_name`, `configuration_path`, `runtime_mode`, `launch_mode`, `parent_process_id`, `child_process_id`, `mutex_name`, `operation_id`, `error_type`, `error_message`, and `application_version`. Protepo adds `Application`, `Environment`, `Module`, `EventCode`, `ProcessId`, `CorrelationId`, severity, visibility, schema version, thread identity, and exception details to Seq's CLEF envelope.

Complete CSV contents, arbitrary environment contents, credentials, and ordinary polling observations are not logged. Migration records removed property names, never obsolete path values; report diagnostics record the affected clock/input and reason, never CSV contents.

## Correlation

Each LauncherPad button action creates a correlation ID. The same ID surrounds the launch-request events and is passed through the internal `--correlation-id` argument to the new process. LearningClock restores that protepo.log context around configuration resolution, mutex acquisition, and runtime initialization. Seq can therefore follow:

```text
LPCRP-3001 -> LPCRP-3003 -> LIFCL-5001 -> MUTEX-4002 -> LIFCL-5002
```

## Local files and Seq

Each configured clock writes `learning_clock_debug.log` and offline CLEF under `D:\LearningClock\logs\<clock-id>`. LauncherPad writes its log and offline CLEF directly under `D:\LearningClock\logs`. CSV files remain in their configured Diavgeia `LearningPath` directories.

| Variable | Purpose |
| --- | --- |
| `LEARNINGCLOCK_ENVIRONMENT` | Environment label; default `local`. |
| `LEARNINGCLOCK_LOG_CONSOLE` | Enables engineering console output. Normal GUI launch leaves it disabled. |
| `LEARNINGCLOCK_SEQ_URL` or `SEQ_URL` | Seq base URL or CLEF endpoint; default `http://localhost:5341`. |
| `LEARNINGCLOCK_SEQ_API_KEY` or `SEQ_API_KEY` | Optional ingestion key; never stored in source. |
| `SEQ_ADMIN_API_KEY` | Session-only administrative key used by the dashboard installer. |

Seq delivery is failure-isolated. When an initialized clock cannot reach Seq, protepo.log appends ingest-ready CLEF to `learning_clock_seq_offline.clef`; LauncherPad uses `launcherpad_seq_offline.clef`. A spool proves local fallback, not live receipt.

## Dashboard installation and diagnosis

The assets in `monitoring/seq` follow the Python Engineering Lab workspace/signal/saved-query/dashboard layout. Installation is repeatable through `seqcli template import --merge`:

```cmd
dev seq-dashboard
```

The **LearningClock Operations** dashboard includes recent events, application health, recently active clocks, launch activity, duplicate-instance protection, configuration health, persistence health, consolidated warnings/errors, and events by component. Filter the Events workspace with `properties.clock_id`, `properties.clock_name`, `Module`, `EventCode`, `ProcessId`, `Environment`, or `CorrelationId`.

Use `MUTEX-4003` and `MUTEX-4004` to diagnose duplicate rejection. Use `LPCRP-3004` for process failures, `CONFG-2004`/`CONFG-2005`/`CONFG-2009` for invalid discovery, `CONFG-2007` for old-file migration, `LPLCL-1031` for skipped report inputs, and `STORG-*` for persistence problems. Seq telemetry is historical evidence; direct mutex observation remains the live authority.

## Verification

```cmd
.\.venv\Scripts\python.exe -I -c "from importlib.metadata import version; import protepo.log; assert version('protepo-log') == protepo.log.__version__ == '2.0.0'; print(protepo.log.__version__)"
.\.venv\Scripts\python.exe -m pip check
dev test
dev seq-dashboard
```
