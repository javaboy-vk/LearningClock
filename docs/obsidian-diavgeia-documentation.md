# Obsidian-Diavgeia Documentation

Diavgeia source pages live under:

```text
diavgeia\LearningClock
```

The root separates version-independent material from controlled product
baselines. The current structure is:

```text
diavgeia\LearningClock\
  WebHome.md
  Documentation Versioning.md
  Developer-Commands.md
  How-to-add-a-new-timer.md
  Learning-Clock-Dashboard.md
  LauncherPad-and-Observability.md
  Reference\
    Overview.md
  6.0\
    Overview.md
    Architecture\
      Overview.md
      Diagrams.md
    Configuration\
      Overview.md
      Seq Setup.md
    Implementation\
      Overview.md
      Python Source Code.md
  views\
    learning-clock-dashboard\
      view.js
```

`WebHome.md`, documentation policy, reference, developer commands, maintenance
guidance, and the deployable dashboard are version-independent. Architecture,
configuration, implementation, controlled diagrams, and Seq setup for the
current product live under `6.0\` and carry `6.0.R<n>` document metadata.

Dashboard viewing:

- `Learning-Clock-Dashboard.md` uses a short `dataviewjs` loader so it can read the vault CSV and render the chart.
- The dashboard implementation lives in `views/learning-clock-dashboard/view.js`. Keeping the large script outside the Markdown page prevents Diavgeia from showing hundreds of lines of source before Dataview refreshes.
- The view resolves `learning_time_log.csv` from the dashboard component folder first, then from `LearningPath/learning_time_log.csv` under that same folder. It does not scan the whole vault, so multiple learning clocks can coexist.
- Keep the deployable component self-contained: `Learning-Clock-Dashboard.md`, `views/`, and the CSV/log files should live under the same `LearningClock` directory.
- Keep file metadata as JavaScript comments inside the Dataview view script. Do not place an HTML comment or `<style>` block above the dashboard, because Diavgeia can render those as visible text.

Export Diavgeia content:

```cmd
scripts\dev.cmd deploy
```

The deploy target runs:

```powershell
scripts\export-diavgeia-vault.ps1
```

It also reads `D:\LearningPath\*.properties`, resolves each `logDir`, and copies the shared dashboard component into the parent Diavgeia folder for that learning path. For example, a `logDir` of:

```text
D:\DiavgeiaVault\Engineering\MAGPAI\LearningPath
```

receives:

```text
D:\DiavgeiaVault\Engineering\MAGPAI\Learning-Clock-Dashboard.md
D:\DiavgeiaVault\Engineering\MAGPAI\views\
```

The `release` target performs the same dashboard export after updating the runnable desktop application files.

The export command copies the complete `diavgeia\LearningClock` source tree to
the vault. The per-learning-path dashboard copy is a separate deployment step
that preserves the root `Learning-Clock-Dashboard.md` and `views\` locations
expected by the Dataview loader.
