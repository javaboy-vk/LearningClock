# LearningClock 6.0 Configuration

**Product Release:** 6.0  
**Document Revision:** R1  
**Document Version:** 6.0.R1

LearningClock configuration has three distinct scopes: per-clock properties,
application environment variables, and repository/developer commands. Secrets
must remain in the process environment and must not be written to source files.

## Per-clock properties

LauncherPad discovers `*.properties` under `D:\LearningPath` by default.

```properties
learning-path-name=LearningClock
logDir=D:\DiavgeiaVault\Engineering\LearningClock\LearningPath
clock-id=learningclock
display-name=LearningClock
order=10
```

| Property | Required | Meaning |
| --- | --- | --- |
| `learning-path-name` | Yes | Label persisted with session rows. |
| `logDir` | Yes | Directory containing CSV, diagnostic log, and offline CLEF. Relative values resolve beside the properties file. |
| `clock-id` | No | Stable lowercase mutex identity. Without it, the normalized properties filename is used. |
| `display-name` | No | LauncherPad button label. Defaults to `learning-path-name`. |
| `order` | No | Integer sort priority before display name and clock ID. |

Malformed files and duplicate clock IDs are reported and skipped independently.
Legacy `pythonExe` and `pyScriptPath` entries may remain in old files but are not
used by the v6.0 LauncherPad.

## Timer-local properties

`src/learningclock/clock.properties` supplies the default checkpoint interval:

```properties
autosave_minutes=5
```

Only positive integer values are accepted; missing or invalid values fall back
to five minutes. A deployed existing file is preserved during release.

## Runtime environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `LEARNINGCLOCK_CONFIG_DIR` | `D:\LearningPath` | Default LauncherPad discovery directory. |
| `LEARNINGCLOCK_ENVIRONMENT` | `local` | Structured logging environment label. |
| `LEARNINGCLOCK_LOG_CONSOLE` | disabled | Enables engineering console output for diagnostic runs. |
| `LEARNINGCLOCK_SEQ_URL` or `SEQ_URL` | `http://localhost:5341` | Seq base URL or CLEF endpoint. |
| `LEARNINGCLOCK_SEQ_API_KEY` or `SEQ_API_KEY` | unset | Optional runtime ingestion key. |
| `SEQ_ADMIN_API_KEY` | unset | Session-only administrative key for template installation. |

The LearningClock-specific variable takes precedence over the generic Seq
variable. Empty environment labels fall back to `local`; absent or blank Seq
URL variables fall back to the local default when Seq is included by the caller.

## Runtime paths

| Data | Default location |
| --- | --- |
| Configuration discovery | `D:\LearningPath\*.properties` |
| Packaged source staging | `D:\LearningPath\Tools\LearningClock` |
| LauncherPad diagnostics | `D:\LearningPath\Tools\LearningClock\launcherpad_debug.log` |
| LauncherPad Seq spool | `D:\LearningPath\Tools\LearningClock\launcherpad_seq_offline.clef` |
| Clock CSV and diagnostics | Configured `logDir` |
| Build, test, coverage, packages | Repository `build\` |

## API configuration

The development API defaults to `127.0.0.1:8000`:

```cmd
dev api --reload
dev api --host 127.0.0.1 --port 8000
dev openapi
```

`dev openapi` refreshes the tracked `docs/openapi.json` from the same FastAPI
application that serves `/docs`, `/redoc`, and `/openapi.json`.

See [Seq Setup](Seq%20Setup.md) for installation, runtime ingestion, validation,
and troubleshooting.
