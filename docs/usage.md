# Usage

LearningClock tracks one learning session at a time. Start it from source during development:

```cmd
set PYTHONPATH=src
.\.venv\Scripts\python.exe src\learningclock\app.py --learning-path LearningClock --log-dir build\learning-clock-logs
```

The desktop launcher reads a `.properties` file and passes the configured learning path and log directory to the app:

```cmd
wscript.exe //nologo launcher\Learning-clock.vbs launcher\dev.properties
```
There is an option to manually add time and record also the number of pages you process in each session.
There are also timers for  experimenting, updating documentation, and even promote any cool code to a production version. A user doesn't have to use all of the timers, but just the ones that fit his needs.

I typically create a shortcut on my desktop, pointing to the "...\LearningClock\Learning-clock.vbs" and pass as a single parameter the location of the <learning path>.properties file.

The logDir parameter is where the application will generate 2 files: the .csv that tracks all the sessions and the debug log, which is the application level logging output.
The Learning-Clock-Dashboard.md file is designed to run inside the Obsidian runtime, and renders the .csv file into a graph.

Common launcher properties:

```properties
learning-path-name=LearningClock
pythonExe=<path of the python runtime>pythonw.exe
pyScriptPath=< path where you install the runtime>\learningclock\app.py
logDir=<path where the app creates the .csv and .log files>\learning-clock-logs.
```

## Timer Workflow

- Click an activity button to start timing that activity.
- Click a different activity to stop the previous timer and start the new one.
- Use `Stop Timer` to pause the active timer.
- Use `Reset Timer` to clear only the currently running activity.

Tracked activities are `Reading`, `Outlining`, `Memorizing`, `Experimenting`, `Audiobook`, `Update Diavgeia`, and `Promote Stable Concept`.

## Manual Time And Pages

Use the `Add Time` menu item to enter manual time for one or more activities. Supported formats are:

```text
5
01:30
01:30:45
```

A plain number is interpreted as minutes. `HH:MM` and `HH:MM:SS` are interpreted as durations.

Use `Add Page Count` to add a positive whole-number page count to the current session.

## Saved Output

When the app closes, it writes a session row to `learning_time_log.csv` under the configured log directory. The CSV includes one column for each activity, a `pages_read` value, and a recalculated final `TOTAL` row.

If the normal CSV write fails, LearningClock attempts an emergency save file in the same log area and records diagnostics in `learning_clock_debug.log`.
