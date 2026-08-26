# Application Logging

LearningClock uses the internal `protepo-log` distribution through the `protepo.log` import
namespace. Application events are semantic: each event belongs to a product-owned catalog and has
a stable code rather than an arbitrary message-only identity.

## Event catalogs

| Catalog | Range | Responsibility |
| --- | ---: | --- |
| `APPLC` | 1000-1099 | Desktop process startup, close, shutdown, and fatal execution failures. |
| `USRIF` | 2000-2199 | Progress, manual entry, page count, autosave, and UI save failures. |
| `TIMER` | 3000-3199 | Timer switch, start, close, stop, and reset transitions. |
| `STORG` | 4000-4299 | CSV reads, writes, normalization, totals, and emergency recovery. |
| `CONFG` | 5000-5099 | Autosave and observability configuration decisions. |
| `CMDLN` | 6000-6099 | Readiness, version, and argument-parser outcomes. |

The catalog definitions are authoritative in `src/learningclock/events.py`. Event IDs are unique,
validated at startup, and tested for range compliance.

## Local file and console output

The desktop application writes semantic events to `learning_clock_debug.log` beside its configured
`learning_time_log.csv`. This preserves the existing diagnostic-file location while changing its
contents to the Protepo event format:

```text
20:14:08.123  TIMER-3002 Timer started for Reading at 20:14:08
```

Set `LEARNINGCLOCK_LOG_CONSOLE=true` to also emit desktop events to stderr. The lightweight CLI
always keeps its user response on stdout and writes its semantic events to stderr.

## Optional Seq delivery

Seq is disabled unless `LEARNINGCLOCK_SEQ_URL` is set. Supported environment settings are:

| Variable | Purpose |
| --- | --- |
| `LEARNINGCLOCK_ENVIRONMENT` | Event environment; defaults to `local`. |
| `LEARNINGCLOCK_LOG_CONSOLE` | Enables desktop stderr output with `true`, `1`, `yes`, or `on`. |
| `LEARNINGCLOCK_SEQ_URL` | Seq root URL or `/ingest/clef` endpoint. |
| `LEARNINGCLOCK_SEQ_API_KEY` | Optional Seq ingestion API key. Never store it in source. |

When Seq is enabled, failed CLEF deliveries are spooled beside the diagnostic log as
`learning_clock_seq_offline.clef`. `protepo-log` 0.1.1 sends synchronously, so Seq should be enabled
for the Tkinter application only after its endpoint latency and unavailable-server behavior have
been tested. A local spool proves fallback persistence, not live Seq receipt.

## Correlation and native API

One `protepo.log` correlation context spans each desktop run or CLI command. Native event metadata
is projected consistently to file, console, and Seq sinks. Application modules call the native
semantic loggers returned by `Log.get_logger(...)` through their `info()`, `warning()`, and
`exception()` methods; LearningClock does not wrap or dynamically dispatch those calls.

Do not place credentials, complete CSV rows, arbitrary user-entered text, or exception messages in
event templates or arguments. Exceptions are attached only at explicit error boundaries, and
emergency-file events record the error type rather than interpolating the original exception text.

## Verification

```cmd
.\.venv\Scripts\python.exe -c "import protepo.log; from importlib.metadata import version; print(protepo.log.__version__); print(version('protepo-log'))"
.\.venv\Scripts\python.exe -m pip check
.\dev.bat test
.\dev.bat all
```
