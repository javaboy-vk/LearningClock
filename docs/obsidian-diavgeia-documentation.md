# Obsidian-Diavgeia Documentation

Diavgeia source pages live under:

```text
diavgeia\LearningClock
```

Current pages:

- `WebHome.md`
- `Learning-Clock-Dashboard.md`
- `Developer-Commands.md`

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
