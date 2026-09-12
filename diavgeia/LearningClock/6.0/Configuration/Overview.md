# LearningClock 6.0 Configuration

**Product Release:** 6.0  
**Document Revision:** R8
**Document Version:** 6.0.R8

LearningClock configuration has three distinct scopes: per-clock properties,
application environment variables, and repository/developer commands. Secrets
must remain in the process environment and must not be written to source files.

## Central application properties

`src\learningclock\clock.properties` is the source file. Release deploys it as `D:\LearningClock\Lib\learningclock\clock.properties`, beside the LauncherPad modules, and it is the sole authority for shared runtime paths:

```properties
pythonExe=P:\Python\Python314\pythonw.exe
pyScriptPath=D:\LearningClock\Lib\learningclock\app.py
autosave_minutes=5
```

The paths are deployment examples. LearningClock preserves backslashes literally. `LEARNINGCLOCK_CENTRAL_CONFIG` overrides the central file; relative overrides resolve beside the packaged default rather than the current directory. LauncherPad validates that both files exist before launch.

## Per-clock properties

LauncherPad discovers `*.properties` under `D:\LearningClock\props` by default.

```properties
learning-path-name=LearningClock
logDir=D:\DiavgeiaVault\Engineering\LearningClock
```

New LauncherPad-created files contain only `learning-path-name` and `logDir`. Existing `clock-id`, `display-name`, and `order` metadata remains readable for backward compatibility but is not written for new clocks. Obsolete `pythonExe` and `pyScriptPath` lines are ignored in favor of central values and atomically removed during discovery. When such an old file points `logDir` at a `LearningPath` directory, migration changes it to the parent clock directory while leaving the existing data in place.

| Property | Required | Meaning |
| --- | --- | --- |
| `learning-path-name` | Yes | Label persisted with session rows. |
| `logDir` | Yes | Clock's Diavgeia directory. CSV data lives in its `LearningPath` child; diagnostic logs and offline CLEF live under `D:\LearningClock\logs\<clock-id>`. Relative values resolve beside the properties file. |

Malformed files and duplicate clock IDs are reported and skipped independently.
Duplicate learning-path names and canonical log directories are also skipped so one physical CSV cannot be counted or launched twice.

## New-clock provisioning

**Create New Clock** validates the name and complete `logDir`, creates `logDir\LearningPath` and missing parents, writes the two-property clock file, and initializes the canonical CSV header under `LearningPath`. The centralized dashboard discovers that CSV automatically; provisioning never copies dashboard Markdown or JavaScript into clock directories. Existing LearningClock properties or CSV files are conflicts and are never overwritten. Partial failures remove only known files and empty directories created by that attempt.

The same central file supplies the optional checkpoint interval:

```properties
autosave_minutes=5
```

Only positive integer values are accepted; missing or invalid values fall back
to five minutes. A deployed existing file is preserved during release.

## Runtime environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `LEARNINGCLOCK_CONFIG_DIR` | `D:\LearningClock\props` | Default LauncherPad discovery directory. |
| `LEARNINGCLOCK_CENTRAL_CONFIG` | Package-local `clock.properties` | Central configuration override. |
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
| Configuration discovery | `D:\LearningClock\props\*.properties` |
| Application modules and dependencies | `D:\LearningClock\Lib` |
| Application icon | `D:\LearningClock\assets\Learning-Clock.ico` |
| LauncherPad diagnostics | `D:\LearningClock\logs\launcherpad_debug.log` |
| LauncherPad Seq spool | `D:\LearningClock\logs\launcherpad_seq_offline.clef` |
| Per-clock diagnostics and Seq spool | `D:\LearningClock\logs\<clock-id>` |
| Central clock dashboard | `D:\DiavgeiaVault\Learning-Clock-Dashboard.md` |
| Clock CSV data | Configured `logDir\LearningPath` |
| Build, test, coverage, packages | Repository `build\` |

## LauncherPad commands and Start registration

Start LauncherPad from the repository `.venv` without a console:

```cmd
dev launcherpad
dev launcherpad --config-dir D:\LearningClock\props
```

Create or update the current user's Windows Start Menu entry:

```cmd
dev launcherpad-register
dev launcherpad-register --no-pin
```

The shortcut is named **LearningClock LauncherPad**, targets the repository
`.venv\Scripts\pythonw.exe`, supplies the source module and configuration
directory arguments, and uses `launcher\Learning-Clock.ico`. The default command
requests **Pin to Start**, but Windows can require the user to complete pinning
from the registered Start entry. `--no-pin` skips that request.

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
