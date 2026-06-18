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
- Keep file metadata as JavaScript comments inside the Dataview view script. Do not place an HTML comment or `<style>` block above the dashboard, because Diavgeia can render those as visible text.

Export Diavgeia content:

```cmd
scripts\dev.cmd deploy
```

The deploy target runs:

```powershell
scripts\export-diavgeia-vault.ps1
```
