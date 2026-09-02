# LearningClock 6.0 Seq Setup

**Product Release:** 6.0  
**Document Revision:** R5
**Document Version:** 6.0.R5

Seq is optional operational telemetry for LearningClock. Local diagnostic files
and CSV persistence continue when Seq is unavailable. Never commit an API key,
an `import.state` file, or copied credentials.

## Repository assets

`monitoring/seq/` contains:

| File | Role |
| --- | --- |
| `signal-LearningClock - All Events.template` | Application signal and event columns. |
| `sqlquery-LearningClock Events - Log Format.template` | Saved chronological event-tail query. |
| `dashboard-LearningClock.template` | LearningClock Operations dashboard. |
| `workspace-LearningClock.template` | Workspace references tying the assets together. |
| `Install-LearningClockSeqDashboard.ps1` | Idempotent `seqcli` importer. |
| `browser-extension/` | Local Chromium layout extension for fixed rows and horizontal overflow. |

The ignored `monitoring/seq/import.state` stores local template identity mappings
so `seqcli template import --merge` updates existing entities.

## Install or update the workspace

Prerequisites are a reachable Seq instance, `seqcli` on `PATH`, and an API key
with permission to create or update shared entities when the server requires it.

For local Seq without authentication:

```cmd
dev seq-dashboard
```

For an authenticated or non-default server, set session-only variables:

```powershell
$env:SEQ_URL = "https://seq.example.com"
$env:SEQ_ADMIN_API_KEY = "<session-only administrative key>"
dev seq-dashboard
```

The installer validates all four templates, imports them with `--merge`, and
prints the dashboard URL. It does not persist the key.

## Configure runtime ingestion

Use LearningClock-specific variables when multiple applications share a shell:

```powershell
$env:LEARNINGCLOCK_SEQ_URL = "http://localhost:5341"
$env:LEARNINGCLOCK_SEQ_API_KEY = "<session-only ingestion key>"
```

If no specific values exist, LearningClock falls back to `SEQ_URL` and
`SEQ_API_KEY`. Clock delivery failures spool to
`learning_clock_seq_offline.clef` beside that clock's diagnostic log;
LauncherPad uses `launcherpad_seq_offline.clef` in its diagnostics directory.

## Verify

1. Run `dev seq-dashboard` and require a successful template import.
2. Open the **LearningClock** workspace and select **LearningClock - All Events**.
3. Enable **Tail**, start LauncherPad, and launch a configured clock.
4. Confirm correlated `LPCRP-3001`, `LPCRP-3003`, `LIFCL-5001`, `MUTEX-4002`,
   and `LIFCL-5002` events for the same `CorrelationId`.
5. Open **LearningClock Operations** and filter by `properties.clock_id`.
6. Load the unpacked `monitoring/seq/browser-extension/` extension in Chrome or
   Edge and reload Seq.
7. In **Recent LearningClock Events**, confirm the dashboard shows Timestamp,
   Level, EventId, Message, and ClockId only, with ClockId as the rightmost
   column. Timestamp and the remaining cells must stay on one line. The chart
   spans the full 12-column dashboard width; when its content is wider, scroll
   horizontally within the event pane.
8. Use the Seq Events workspace to inspect complete structured events.
9. Inspect the local diagnostic log and offline spool separately.

Seq 2026.1 dashboard templates do not expose table CSS or horizontal-overflow
settings. The version-controlled, CSS-only Chromium extension supplies this
layout without changing Seq's installed web client. Load it unpacked from
`D:\GitHub\LearningClock\monitoring\seq\browser-extension`, then reload Seq.

Template tests and a successful import prove only the checked-in contract and
installation. Live receipt requires an event visible in the target Seq instance.
An offline CLEF record proves fallback behavior, not live delivery.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `seqcli was not found on PATH` | Install `seqcli`, reopen PowerShell, and rerun. |
| Unauthorized or forbidden import | Use a valid session-only administrative key with shared-entity permissions. |
| Dashboard exists but has no events | Verify runtime URL/key variables, start a clock, and inspect the offline spool. |
| Dashboard rows wrap or have no horizontal scrollbar | Load or reload the unpacked `monitoring/seq/browser-extension/` extension, then refresh Seq. |
| Duplicate clock diagnosis | Filter `MUTEX-4003` and `MUTEX-4004` by `properties.clock_id`. |
| Launch failure | Inspect `LPCRP-3004`, `error_type`, and `error_message`. |
| Configuration skipped | Inspect `CONFG-2004` and `CONFG-2005`. |
| Persistence concern | Inspect `STORG-*` events and the authoritative CSV/emergency files. |

LauncherPad's direct `OpenMutexW` observation remains the live running-state
authority; Seq must not be used as a process-lock or synchronization mechanism.
