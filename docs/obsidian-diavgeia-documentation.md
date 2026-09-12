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

- `Learning-Clock-Dashboard.md` is deployed at the vault root and uses a short `dataviewjs` loader that targets the shared view under `Engineering/LearningClock/views`.
- The dashboard implementation lives in `views/learning-clock-dashboard/view.js`. Keeping the large script outside the Markdown page prevents Diavgeia from showing hundreds of lines of source before Dataview refreshes.
- The view scans the open vault for `*/LearningPath/learning_time_log.csv` and presents an alphabetically sorted clock selector.
- Per-clock directories contain only their documentation and `LearningPath` data child; they do not contain dashboard Markdown or JavaScript copies.
- Keep file metadata as JavaScript comments inside the Dataview view script. Do not place an HTML comment or `<style>` block above the dashboard, because Diavgeia can render those as visible text.

Export Diavgeia content:

```cmd
scripts\dev.cmd deploy
```

The deploy target runs:

```powershell
scripts\export-diavgeia-vault.ps1
```

It copies the complete LearningClock documentation tree, including the one dashboard and view, to:

```text
D:\DiavgeiaVault\Engineering\LearningClock
```

The dashboard resources are:

```text
D:\DiavgeiaVault\Learning-Clock-Dashboard.md
D:\DiavgeiaVault\Engineering\LearningClock\views\learning-clock-dashboard\view.js
```

The `release` target first updates the runtime dashboard assets and then publishes those two centralized resources to the same vault directory.

No release or new-clock operation generates per-clock dashboard copies.
