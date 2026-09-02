# LearningClock Seq Operations

This directory contains the version-controlled LearningClock Seq workspace, signal, saved event-tail query, Operations dashboard, and idempotent installer. Its structure follows the Python Engineering Lab `monitoring/seq` contract.

Install or update the workspace:

```cmd
dev seq-dashboard
```

The installer defaults to `http://localhost:5341`. For another instance, keep the administrative key in the current environment only:

```powershell
$env:SEQ_URL = "https://seq.example.com"
$env:SEQ_ADMIN_API_KEY = "<session-only administrative key>"
dev seq-dashboard
```

The installer uses `seqcli template import --merge` and the ignored `import.state` mapping, so repeated runs update the existing entities. No credentials are stored in the repository.

LearningClock runtime ingestion uses `LEARNINGCLOCK_SEQ_URL` or `SEQ_URL`, and `LEARNINGCLOCK_SEQ_API_KEY` or `SEQ_API_KEY`. It defaults to local Seq and spools failed clock delivery beside that clock's diagnostics. LauncherPad uses `D:\LearningPath\Tools\LearningClock\launcherpad_seq_offline.clef` by default.

Select the **LearningClock** workspace, choose **LearningClock - All Events**, and enable **Tail**. In **LearningClock Operations**, the recent-events table intentionally shows only Timestamp, Level, EventId, Message, and ClockId, with ClockId as the rightmost column. The chart spans all 12 dashboard columns so the pane follows the available window width. Use the Seq Events workspace when complete structured-event inspection is required.

Seq 2026.1 dashboard templates do not expose table CSS or horizontal-overflow settings. To preserve the log format at every window size without modifying Seq's installed files, load the CSS-only Chromium extension from `monitoring/seq/browser-extension/`:

1. Open `chrome://extensions` in Chrome or `edge://extensions` in Edge.
2. Enable **Developer mode**.
3. Select **Load unpacked** and choose `D:\GitHub\LearningClock\monitoring\seq\browser-extension`.
4. Reload Seq.

The extension applies only to Seq pages on `localhost` or `127.0.0.1`, and it styles only **Recent LearningClock Events**. It keeps every cell in that table on one line, gives the table its natural content width, and adds a horizontal scrollbar when that width exceeds the pane.

The dashboard is operational telemetry, not a synchronization service: LauncherPad's `OpenMutexW` observation remains the authoritative running-state check.
