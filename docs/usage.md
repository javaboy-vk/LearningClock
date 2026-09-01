# Usage

LearningClock LauncherPad is the normal GUI entry point. Start it from source without a console:

```cmd
set PYTHONPATH=src
.\.venv\Scripts\pythonw.exe -m learningclock.desktop
```

LauncherPad discovers `D:\LearningPath\*.properties` by default. Override the directory for development:

```cmd
.\.venv\Scripts\pythonw.exe -m learningclock.desktop --config-dir launcher
```
There is an option to manually add time and record also the number of pages you process in each session.
There are also timers for sandbox exploration, updating documentation, and even promote any cool code to a production version. A user doesn't have to use all of the timers, but just the ones that fit his needs.

An installed package exposes `.venv\Scripts\learningclock-gui.exe`. Create one Desktop or Start Menu shortcut to that GUI executable; it requires no per-clock arguments. Old per-clock VBS shortcuts can be removed manually after LauncherPad validation.

The logDir parameter is where the application will generate 2 files: the .csv that tracks all the sessions and the debug log, which is the application level logging output.
The Learning-Clock-Dashboard.md file is designed to run inside the Obsidian runtime, and renders the .csv file into a graph.

LearningClock also saves a checkpoint of the current session at the positive number of minutes set in the `clock.properties` file beside `app.py`. The supplied value is five minutes. Change only the value and restart the app for a different interval:

```properties
autosave_minutes=5
```

Common launcher properties:

```properties
learning-path-name=LearningClock
logDir=<path where the app creates the .csv and .log files>\learning-clock-logs
clock-id=learningclock
display-name=LearningClock
order=10
```

`learning-path-name` and `logDir` remain required. `clock-id`, `display-name`, and `order` are optional. Without `clock-id`, the stable normalized properties filename is used. Legacy `pythonExe` and `pyScriptPath` values may remain in existing files but LauncherPad deliberately ignores them.

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

Use the `Add Time` menu item to enter manual time for one or more activities. Supported formats are:

```text
5
01:30
01:30:45
```

A plain number is interpreted as minutes. `HH:MM` and `HH:MM:SS` are interpreted as durations. Blank or zero-only Add Time and Add Pages submissions are accepted as no-ops.

Use `Add Page Count` to add a positive whole-number page count to the current session.

## Saved Output

LearningClock checkpoints the current session at the configured interval and replaces that checkpoint with final totals when the app closes. The CSV includes one row per session, one column for each activity, a `pages_read` value, and a recalculated final `TOTAL` row.

If the normal CSV write fails, LearningClock attempts an emergency save file in the same log area
and records semantic `USRIF-*` and `STORG-*` recovery events in `learning_clock_debug.log`.
