# LearningClock LauncherPad and Observability

LearningClock v6.0 uses one GUI entry point, `learningclock-gui.exe`, to open LauncherPad. LauncherPad discovers `D:\LearningPath\*.properties`, presents each valid clock, observes running state through `OpenMutexW`, and launches independent GUI processes. LearningClock—not LauncherPad—owns `Local\Protepo.LearningClock.<clock-id>` before creating CSV persistence, making singleton enforcement a data-integrity boundary.

Normal execution contains no VBS, WScript, CScript, CMD, PowerShell, or Python console. Source mode uses the active environment's `pythonw.exe`; installed/frozen mode launches the GUI executable directly. LauncherPad can close without affecting clocks and reconstructs their state after restart from the kernel mutexes.

`protepo.log` 2.0 is the canonical observability path. Formal `LPLCL-*`, `CONFG-*`, `LPCRP-*`, `MUTEX-*`, `LIFCL-*`, and `CLNDR-*` events include structured clock identity, configuration, process, runtime mode, operation, error, and correlation properties. A launch correlation passes from LauncherPad into the selected clock process.

The version-controlled **LearningClock Operations** Seq dashboard is installed with:

```cmd
dev seq-dashboard
```

It provides recent events, application/launch/configuration/persistence health, duplicate rejection, active-clock telemetry, warnings/errors, and component grouping. Seq is operational evidence only; mutex inspection remains the runtime ownership authority.

The Set Date action now opens its calendar immediately after revealing the date field. The transient popup is deiconified, raised, visibility-synchronized, focused, and grabbed in that order so it cannot remain hidden behind the LearningClock window.
