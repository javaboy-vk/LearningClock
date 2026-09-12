# LearningClock 6.0 Python Source Code

**Product Release:** 6.0  
**Document Revision:** R10
**Document Version:** 6.0.R10

This catalog documents every tracked Python area and explicitly includes the
v6.0 modules added for configuration discovery, LauncherPad, process launching,
singleton enforcement, and formal telemetry.

## Product package

| File | Responsibility and principal interface |
| --- | --- |
| `src/learningclock/__init__.py` | Package metadata and authoritative import-level `__version__`. |
| `src/learningclock/__main__.py` | `python -m learningclock` adapter to `cli.main()`. |
| `src/learningclock/api.py` | FastAPI app, typed `HealthResponse`, `GET /health`, and generated OpenAPI surfaces. It does not control desktop state. |
| `src/learningclock/app.py` | Configured Tkinter clock, timer/manual-entry state, calendar, checkpointing, singleton acquisition, and shutdown recovery. |
| `src/learningclock/cli.py` | Non-GUI readiness/version command with stdout reserved for user output. |
| `src/learningclock/configuration.py` | Central `pythonExe`/`pyScriptPath`, immutable per-clock configuration, literal properties parsing, validation, migration, identity, de-duplication, ordering, and isolated issues. |
| `src/learningclock/csv_store.py` | CSV schema, legacy normalization, chronological rows, aggregate totals, emergency files, and storage events. |
| `src/learningclock/desktop.py` | One GUI entry that delays imports and dispatches LauncherPad or internal `--clock` mode. |
| `src/learningclock/date_picker.py` | Dependency-free modal Tkinter calendar used by custom report ranges. |
| `src/learningclock/events.py` | Stable catalog-style product events for application, UI, timer, storage, configuration, and CLI behavior. |
| `src/learningclock/launcherpad.py` | Multi-clock grid, create form, asynchronous cross-clock histogram, mutex observation, correlated launch requests, and non-owning close behavior. |
| `src/learningclock/learning-clock.py` | Compatibility adapter for historical direct script/debug launch paths. |
| `src/learningclock/observability.py` | protepo.log 2.0 composition, version enforcement, named loggers, local/Seq sinks, fallback, and correlation. |
| `src/learningclock/process_launcher.py` | Central-plus-per-clock command construction and detached, shell-free, stream-free process creation. |
| `src/learningclock/provisioning.py` | New-clock validation, exact two-key properties, canonical CSV initialization, atomic writes, and safe rollback. |
| `src/learningclock/reporting.py` | Inclusive period resolution, legacy-compatible read-only CSV parsing, category aggregation, and warning isolation. |
| `src/learningclock/singleton.py` | Injectable Windows mutex API, process-lifetime ownership guard, and non-owning observation. |
| `src/learningclock/telemetry.py` | Formal v2 `LPLCL`, `CONFG`, `LPCRP`, `MUTEX`, `LIFCL`, and `CLNDR` event definitions. |
| `src/learningclock/window_icon.py` | Resolves the shared ICO across installed, frozen, released-source, and repository layouts and applies it non-fatally to both primary Tk title bars. |

Manual-time mode expands the LearningClock window to 620 pixels and uses
eight-character entry widgets. Tk key validation permits only prefixes of the
exact `HH:MM:SS` structure, rejects a ninth character, and constrains minutes
and seconds to `00` through `59`. Submission repeats strict validation so a
programmatic or otherwise unvalidated value cannot bypass the contract.

## Developer and generation scripts

| File | Responsibility |
| --- | --- |
| `scripts/dev.py` | Command dispatcher for clean, compile, test, coverage, API, OpenAPI, Seq, LauncherPad startup/registration, package, deploy, release, and aggregate lifecycle targets. |
| `scripts/Build-LauncherIcon.ps1` | Builds high-contrast multi-resolution Windows ICO frames from the transparent LauncherPad source artwork. |
| `scripts/Register-LauncherPad.ps1` | Current-user Start Menu shortcut creation and best-effort Windows Start pin request. |
| `scripts/export_openapi.py` | Writes tracked `docs/openapi.json` from `learningclock.api.app.openapi()`. |
| `scripts/generate_readme_assets.py` | Generates the synchronized LearningClock README SVG illustrations. |
| `scripts/migrate_learningpath_csv_categories.py` | Resolves configured CSVs, creates timestamped backups, normalizes rows, and rewrites one final `TOTAL`. |
| `scripts/pygount_summary.py` | Counts Git-tracked source-controlled files and writes ignored inventory reports under `build/reports`. |

## Test support and suites

| File | Contract covered |
| --- | --- |
| `tests/learning_clock_csv_test_support.py` | Isolated CSV harness, deterministic sessions, fixture seeding, and row helpers. |
| `tests/test_api.py` | Health, Swagger UI, ReDoc, and tracked OpenAPI parity. |
| `tests/test_app_ui.py` | Activity colors, menu visibility, and calendar popup ordering. |
| `tests/test_cli.py` | Readiness and version command behavior. |
| `tests/test_dev_launcherpad.py` | Detached LauncherPad developer startup and side-effect-free Start Menu command construction. |
| `tests/test_launcherpad_configuration.py` | Legacy identity, ordering, malformed-file isolation, and duplicate IDs. |
| `tests/test_launcherpad.py` | Available/running control-state mapping without a display. |
| `tests/test_launcherpad_requirements.py` | Central configuration, migration, provisioning, rollback, date ranges, aggregation, UI contracts, and packaged resources. |
| `tests/test_launcher_icon.py` | Native icon-size inventory, PNG-backed ICO frames, source artwork, and reproducible builder contract. |
| `tests/test_learning_clock_csv_regression.py` | Fixture and configured-file CSV regression behavior. |
| `tests/test_learning_clock_csv_unit.py` | Schema, compatibility, totals, checkpoints, recovery, dates, manual time, and pages. |
| `tests/test_observability.py` | Catalog identity, event families, structured properties, local files, and native loggers. |
| `tests/test_process_launcher.py` | Central runtime command composition, no-shell/no-VBS contract, detached flags, and failures. |
| `tests/test_release_observability.py` | Production release inclusion of the observability modules. |
| `tests/test_seq_dashboard.py` | Templates, dashboard coverage, workspace references, installer merge, and credential hygiene. |
| `tests/test_singleton.py` | Fake mutex semantics plus Windows process-exit cleanup integration. |
| `tests/test_window_icon.py` | Shared icon resolution, soft failure, packaged-asset parity, and integration in both primary windows. |

## Launcher assets

| File | Responsibility |
| --- | --- |
| `launcher/Learning-Clock-source.png` | Transparent 512-pixel high-contrast master with a large blue/orange clock mark. |
| `launcher/Learning-Clock.ico` | Generated Windows icon containing ten native sizes from 16 through 256 pixels. |
| `src/learningclock/assets/Learning-Clock.ico` | Synchronized package-data copy used by installed LauncherPad and LearningClock title bars. |

## Source-commentary convention

Python file headers describe the file's purpose and revision. Complex modules
add call trees, data flows, ownership rules, or safety contracts.

Every non-trivial function or method must document:

1. **What it does** — its behavior, result, and important side effects.
2. **Why it exists** — the architectural, operational, compatibility, safety, or
   usability problem it solves.
3. **Designed use** — its intended callers, valid inputs, sequencing, ownership,
   and whether it is a callback, helper, composition boundary, or public API.
4. **Failure behavior** when it is not obvious — exceptions, fallback, no-op,
   error reporting, retry, or cleanup expectations.

Callable documentation uses Java-style `#` comment blocks immediately above the
function or method definition, outside the callable body. When a decorator is
present, the comment block goes immediately above the decorator so it describes
the complete definition. In-body function/method docstrings are not used for this
project's callable documentation. An `Operational algorithm` block may provide
step-level detail, but it must remain above the definition and include or be
paired there with the required what, why, and designed-use information.

A method that is only a couple of obvious lines, a direct property accessor, a
protocol signature, or a clearly named test/fake helper does not need redundant
comments. Length alone is not an exemption when ordering, ownership, persistence,
security, or error behavior is significant. Module and class docstrings remain
valid because this placement rule specifically governs functions and methods.

The v6.0 LauncherPad/configuration/process/singleton/observability functions and
the substantive developer/generator functions use explicit `Why` and
`Designed use` sections above their definitions. Core timer and CSV functions
extend their existing operational comments and call trees in the same location.

The header `# Version` is a file revision. Product release remains `6.0` in
`pyproject.toml`, `learningclock.__version__`, and `APP_VERSION`.
