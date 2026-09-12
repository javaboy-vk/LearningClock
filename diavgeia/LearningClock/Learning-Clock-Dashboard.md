# Learning Clock Dashboard v6.0

This is the single LearningClock dashboard for the Diavgeia vault. Choose any discovered clock to render its `LearningPath/learning_time_log.csv` data.

```dataviewjs
const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
let currentPage = null;

for (let attempt = 0; attempt < 20; attempt++) {
  currentPage = dv.current();
  if (currentPage?.file) {
    break;
  }
  await wait(250);
}

if (!currentPage?.file) {
  dv.paragraph("Dashboard is waiting for Obsidian to finish loading. Refresh this note if it does not appear.");
} else {
  await dv.view(
    "Engineering/LearningClock/views/learning-clock-dashboard",
    { discoverClocks: true }
  );
}
```
