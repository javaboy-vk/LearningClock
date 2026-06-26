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
  const dashboardPath = currentPage.file.path || "";
  const dashboardFolder = currentPage.file.folder
    || (dashboardPath.includes("/") ? dashboardPath.slice(0, dashboardPath.lastIndexOf("/")) : "");
  await dv.view([dashboardFolder, "views/learning-clock-dashboard"].filter(Boolean).join("/"));
}
```
