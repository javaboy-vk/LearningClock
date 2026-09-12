# Usage

LearningClock LauncherPad is the normal GUI entry point. Start it from source without a console:

```cmd
dev launcherpad
```

LauncherPad discovers `D:\LearningClock\props\*.properties` by default. Override the directory for development:

```cmd
dev launcherpad --config-dir launcher
```

For an explicit central configuration during development:

```cmd
dev launcherpad --central-config D:\LearningClock\Lib\learningclock\clock.properties
```
There is an option to manually add time and record also the number of pages you process in each session.
There are also timers for sandbox exploration, updating documentation, and even promote any cool code to a production version. A user doesn't have to use all of the timers, but just the ones that fit his needs.

Register the source LauncherPad for the current user with `dev launcherpad-register`. The command creates **LearningClock LauncherPad** in the Windows Start Menu, synchronizes an existing taskbar-pinned shortcut, uses `launcher\Learning-Clock.ico`, and requests a Start pin when the shell permits it. Windows 11 can withhold the automatic pin verb; in that case, right-click the registered Start entry and select **Pin to Start**. Pass `--no-pin` when no new Start pin should be requested; existing Start Menu and taskbar shortcuts are still updated.

An installed package exposes `.venv\Scripts\learningclock-gui.exe`; the developer registration command deliberately targets the repository's `.venv\Scripts\pythonw.exe` and source tree. Old per-clock VBS shortcuts can be removed manually after LauncherPad validation.

The `logDir` parameter identifies the clock's Diavgeia directory. LearningClock creates a `LearningPath` child there for the session CSV. Diagnostic logs and offline telemetry are centralized under `D:\LearningClock\logs\<clock-id>`. The centralized `Learning-Clock-Dashboard.md` note at the vault root discovers those CSV files and renders the clock selected from its alphabetical list.

The central `clock.properties` file beside the installed `learningclock` package supplies the shared runtime paths and checkpoint interval:

```properties
pythonExe=P:\Python\Python314\pythonw.exe
pyScriptPath=D:\LearningClock\Lib\learningclock\app.py
autosave_minutes=5
```

Set the paths for the machine during deployment. `LEARNINGCLOCK_CENTRAL_CONFIG` can point to a different central file; a relative override resolves beside the packaged default, never against the current working directory.

Every new per-clock file contains exactly:

```properties
learning-path-name=LearningClock
logDir=D:\DiavgeiaVault\Engineering\LearningClock
```

Use **Create New Clock** in LauncherPad to enter the learning path name and choose the complete Diavgeia clock directory. LauncherPad creates its `LearningPath` child, the two-property file, and a canonical CSV header, then refreshes immediately. Dashboard Markdown and JavaScript are deployed once under `Engineering\LearningClock`; the view discovers the new CSV automatically. Provisioning refuses duplicate names/log directories and existing LearningClock properties or CSV files. Old four-property files remain readable; LauncherPad atomically removes obsolete `pythonExe` and `pyScriptPath` lines and converts their former `...\LearningPath` logDir to the parent clock directory. Central values always win.

The report period defaults to **This week** (Monday through today). **Last week** is the previous Monday through Sunday, **This month** is day one through today, and **Define range** uses calendar-only start/end selection. All boundaries are inclusive and use the local date. The report reads dated session rows, ignores `TOTAL`, and supports current and legacy date/category columns. When inputs are unavailable or malformed, the skipped/invalid count is a hyperlink that opens a read-only diagnostic popup showing each source file, CSV row, column, rejected value, and reason; click an item to open the file or nearest existing directory.

## Timer Workflow

- Click an activity button to start timing that activity.
- Click a different activity to stop the previous timer and start the new one.
- Use `Stop Timer` to pause the active timer.
- Use `Reset Timer` to clear only the currently running activity.
- Use `Set Date` to show the unlabeled `MM/DD/YYYY` session-date field and immediately open its calendar. The embedded calendar icon, `Alt+Down`, and `F4` reopen the popup; it is raised above the LearningClock window and accepts mouse or keyboard selection.
- Use `Add Time` or `Add Page Count` again to hide its fields; press Enter in a visible field to submit, without an extra action button.
- Use `View Progress` to toggle the saved CSV bar chart open or closed. Use `Refresh` after a new autosave.

Tracked activities are `Reading`, `Book Listening`, `Outlining`, `Active Recall`, `Sandbox`, `AI-Assisted Architecture & Design`, `AI-Assisted Engineering`, `Classical Software Engineering`, `Update Diavgeia`, and `Promote Stable Concept`.

`Sandbox` is for sandbox learning, trial-and-error, book examples, technology probes, prototype exploration, and trying things out before they become stable engineering work. `AI-Assisted Engineering` is for work done by instructing ChatGPT, CODEX, or another AI assistant to generate, repair, explain, refactor, test, document, or debug code. `AI-Assisted Architecture & Design` is for architecture, system design, modeling, tradeoff analysis, and design documentation performed through AI-assisted conversation. `Classical Software Engineering` is for directly implementing software yourself with traditional engineering practices.

## Manual Time And Pages

Use the `Add Time` menu item to enter manual time for one or more activities. Each field accepts exactly:

```text
01:30:45
```

The required format is `HH:MM:SS`, with exactly two digits per component and minute/second values from `00` through `59`. The field rejects a ninth character, malformed separators, and out-of-range minute or second values. Add Time widens the LearningClock window so the complete value remains visible without clipping. Blank or `00:00:00` Add Time submissions and zero-only Add Pages submissions are accepted as no-ops.

Use `Add Page Count` to add a positive whole-number page count to the current session.

## Saved Output

LearningClock checkpoints the current session at the configured interval and replaces that checkpoint with final totals when the app closes. The CSV includes one row per session, one column for each activity, a `pages_read` value, and a recalculated final `TOTAL` row.

If the normal CSV write fails, LearningClock attempts an emergency save file beside the CSV
and records semantic `USRIF-*` and `STORG-*` recovery events in `D:\LearningClock\logs\<clock-id>\learning_clock_debug.log`.
