```dataviewjs
const dashboardPath = dv.current().file.path;
const dashboardFolder = dashboardPath.includes("/") ? dashboardPath.slice(0, dashboardPath.lastIndexOf("/")) : "";
const viewPath = [dashboardFolder, "views/learning-clock-dashboard"].filter(Boolean).join("/");

await dv.view(viewPath);
```
