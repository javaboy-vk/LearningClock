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

Select the **LearningClock** workspace, choose **LearningClock - All Events**, and enable **Tail**. The dashboard is operational telemetry, not a synchronization service: LauncherPad's `OpenMutexW` observation remains the authoritative running-state check.

