# LearningClock LauncherPad and Observability

> This compatibility page preserves the established link. The controlled v6.0
> sources are [Architecture](6.0/Architecture/Overview.md),
> [Implementation](6.0/Implementation/Overview.md), and
> [Seq Setup](6.0/Configuration/Seq%20Setup.md).

LearningClock v6.0 uses one GUI entry point, `learningclock-gui.exe`, to open LauncherPad. LauncherPad discovers `D:\LearningClock\props\*.properties`, can transactionally create complete clocks, observes running state through `OpenMutexW`, and launches `D:\LearningClock\Lib\learningclock\app.py` with each clock's name and its `logDir\LearningPath` data directory. Application logs are centralized under `D:\LearningClock\logs`. One vault-level dashboard and one `LearningClock/views` implementation discover every clock CSV and provide a selector. LauncherPad also renders a read-only cross-clock category report for four inclusive date-period choices. LearningClock—not LauncherPad—owns `Local\Protepo.LearningClock.<clock-id>` before creating CSV persistence, making singleton enforcement a data-integrity boundary.

Normal execution contains no VBS, WScript, CScript, CMD, PowerShell, or Python console. LauncherPad starts each clock with the Python executable and application script from central `clock.properties`. LauncherPad can close without affecting clocks and reconstructs their state after restart from the kernel mutexes.

Start and register the source LauncherPad with the root developer commands:

```cmd
dev launcherpad
dev launcherpad-register
```

Registration creates the current user's **LearningClock LauncherPad** Start Menu
entry with the product icon. It requests **Pin to Start** when Windows exposes
that shell action; otherwise the registered entry can be pinned manually.

`protepo.log` 2.0 is the canonical observability path. Formal `LPLCL-*`, `CONFG-*`, `LPCRP-*`, `MUTEX-*`, `LIFCL-*`, and `CLNDR-*` events include structured clock identity, configuration, process, runtime mode, operation, error, and correlation properties. A launch correlation passes from LauncherPad into the selected clock process.

The version-controlled **LearningClock Operations** Seq dashboard is installed with:

```cmd
dev seq-dashboard
```

It provides recent events, application/launch/configuration/persistence health, duplicate rejection, active-clock telemetry, warnings/errors, and component grouping. Seq is operational evidence only; mutex inspection remains the runtime ownership authority.

The Set Date action now opens its calendar immediately after revealing the date field. The transient popup is deiconified, raised, visibility-synchronized, focused, and grabbed in that order so it cannot remain hidden behind the LearningClock window.
