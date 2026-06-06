<!--
File Name : Learning-Clock-Dashboard.md
Artifact  : LearningClock - Learning Clock Dashboard
Author    : javaboy-vk
Date      : 2026-06-05
Version   : v0.5.0
Purpose:
  Renders the LearningClock learning-time dashboard from the vault CSV.
-->

# LearningClock Learning Time

```dataviewjs
const csvPath = "Engineering/LearningClock/LearningPath/learning_time_log.csv";

const activityFields = [
  ["Reading", "reading"],
  ["Outlining", "outlining"],
  ["Memorizing", "memorizing"],
  ["Experimenting", "experimenting"],
  ["Audiobook", "audiobook"],
  ["Update Diavgeia", "update_diavgeia"],
  ["Promote stable concept", "promote_stable_concept"],
];

function parseDuration(value) {
  if (!value || typeof value !== "string") {
    return 0;
  }

  const parts = value.trim().split(":").map(Number);
  if (parts.length !== 3 || parts.some(Number.isNaN)) {
    return 0;
  }

  return (parts[0] * 3600) + (parts[1] * 60) + parts[2];
}

function formatDuration(seconds) {
  const safeSeconds = Math.max(0, Math.round(seconds || 0));
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const remainingSeconds = safeSeconds % 60;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function formatShortDate(value) {
  if (!value || value === "TOTAL") {
    return "N/A";
  }

  const parts = value.split("-");
  if (parts.length === 3) {
    return `${parts[1]}-${parts[2]}-${parts[0].slice(-2)}`;
  }

  return value;
}

function parseCsv(text) {
  const rows = [];
  let current = "";
  let row = [];
  let quoted = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const next = text[i + 1];

    if (ch === '"' && quoted && next === '"') {
      current += '"';
      i++;
    } else if (ch === '"') {
      quoted = !quoted;
    } else if (ch === "," && !quoted) {
      row.push(current);
      current = "";
    } else if ((ch === "\n" || ch === "\r") && !quoted) {
      if (ch === "\r" && next === "\n") {
        i++;
      }
      row.push(current);
      rows.push(row);
      row = [];
      current = "";
    } else {
      current += ch;
    }
  }

  if (current.length > 0 || row.length > 0) {
    row.push(current);
    rows.push(row);
  }

  if (rows.length === 0) {
    return [];
  }

  const headers = rows[0].map((header) => header.trim());
  return rows.slice(1)
    .filter((values) => values.some((value) => value.trim().length > 0))
    .map((values) => Object.fromEntries(headers.map((header, index) => [header, (values[index] || "").trim()])));
}

function appendText(parent, tag, text, className) {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) {
    element.className = className;
  }
  parent.appendChild(element);
  return element;
}

function applyStyles(root) {
  const style = document.createElement("style");
  style.textContent = `
    .lc-card {
      border: 1px solid #c5d8ec;
      border-radius: 18px;
      background: #f8fbff;
      padding: 22px 25px 26px;
      box-shadow: 0 1px 3px rgba(21, 76, 130, 0.08);
      margin: 18px 0 24px;
      overflow: hidden;
    }
    .lc-bars {
      display: grid;
      grid-template-columns: repeat(7, minmax(0, 1fr));
      gap: 10px;
      align-items: end;
      height: 238px;
      border-bottom: 2px solid #a9c5df;
      padding: 0;
    }
    .lc-bar-cell {
      min-width: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-end;
      height: 238px;
    }
    .lc-bar {
      width: min(118px, 100%);
      min-height: 34px;
      border-radius: 8px 8px 0 0;
      background: #3279b7;
      color: #fff;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding-top: 8px;
      font-weight: 700;
      font-size: 14px;
      line-height: 1;
      box-sizing: border-box;
      text-shadow: 0 1px 1px rgba(0, 0, 0, 0.35);
    }
    .lc-labels {
      display: grid;
      grid-template-columns: repeat(7, minmax(0, 1fr));
      gap: 10px;
      margin-top: 12px;
      text-align: center;
      font-size: 12px;
      line-height: 1.25;
      color: #111;
    }
    .lc-labels > div {
      min-height: 34px;
      overflow-wrap: normal;
      word-break: normal;
    }
    .lc-label-nowrap {
      white-space: nowrap;
    }
    .lc-footer {
      display: grid;
      grid-template-columns: max-content max-content max-content max-content;
      gap: 26px;
      align-items: center;
      margin-top: 24px;
      font-size: 16px;
      color: #111;
      white-space: nowrap;
    }
    .lc-footer strong {
      color: #164f86;
      font-weight: 700;
    }
    @media (max-width: 760px) {
      .lc-footer {
        grid-template-columns: 1fr 1fr;
        white-space: normal;
      }
    }
    @media (max-width: 520px) {
      .lc-footer {
        grid-template-columns: 1fr;
      }
    }
    .lc-source {
      font-family: var(--font-monospace);
      background: #f4f7fb;
      border-left: 4px solid #2684ff;
      border-radius: 6px;
      padding: 12px 16px;
      margin: 18px 0 0;
      white-space: pre-wrap;
    }
  `;
  root.appendChild(style);
}

try {
  const root = dv.container;
  applyStyles(root);

  const file = app.vault.getAbstractFileByPath(csvPath);
  if (!file) {
    appendText(root, "p", `CSV file not found: ${csvPath}`, "lc-source");
    return;
  }

  const text = await app.vault.read(file);
  const rows = parseCsv(text);
  const sessions = rows.filter((row) => row.date && row.date !== "TOTAL");
  const totalRow = rows.find((row) => row.date === "TOTAL");

  const totals = Object.fromEntries(activityFields.map(([, field]) => [field, 0]));
  let totalSeconds = 0;
  let pagesRead = 0;

  for (const row of sessions) {
    for (const [, field] of activityFields) {
      totals[field] += parseDuration(row[field]);
    }
    totalSeconds += parseDuration(row.total);
    pagesRead += Number.parseInt(row.pages_read || "0", 10) || 0;
  }

  const grandTotal = totalRow ? parseDuration(totalRow.total) : totalSeconds;
  const totalPages = Number.parseInt(totalRow?.pages_read || pagesRead || "0", 10) || 0;
  const maxSeconds = Math.max(...activityFields.map(([, field]) => totals[field]), 1);
  const firstSession = sessions[0];
  const lastSession = sessions[sessions.length - 1];

  const card = document.createElement("section");
  card.className = "lc-card";
  root.appendChild(card);

  const bars = document.createElement("div");
  bars.className = "lc-bars";
  card.appendChild(bars);

  for (const [, field] of activityFields) {
    const seconds = totals[field];
    const cell = document.createElement("div");
    cell.className = "lc-bar-cell";

    const bar = document.createElement("div");
    bar.className = "lc-bar";
    bar.style.height = `${Math.max(34, Math.round((seconds / maxSeconds) * 228))}px`;
    bar.textContent = formatDuration(seconds);

    cell.appendChild(bar);
    bars.appendChild(cell);
  }

  const labels = document.createElement("div");
  labels.className = "lc-labels";
  card.appendChild(labels);
  for (const [label] of activityFields) {
    const labelElement = appendText(labels, "div", label);
    if (label === "Experimenting") {
      labelElement.className = "lc-label-nowrap";
    }
  }

  const footer = document.createElement("div");
  footer.className = "lc-footer";
  footer.innerHTML = `
    <span>Total time: <strong>${formatDuration(grandTotal)}</strong></span>
    <span>Total pages read: <strong>${totalPages}</strong></span>
    <span>Start Date: <strong>${formatShortDate(firstSession?.date)}</strong></span>
    <span>Last Update: <strong>${formatShortDate(lastSession?.date)}</strong></span>
  `;
  card.appendChild(footer);

  dv.header(2, "Recent Sessions");
  dv.table(
    ["Date", "Start", "End", "Total", "Pages"],
    sessions.slice(-10).reverse().map((row) => [
      row.date,
      row.session_start,
      row.session_end,
      row.total,
      row.pages_read || "0",
    ])
  );

  dv.header(2, "CSV File");
  appendText(root, "div", csvPath, "lc-source");
} catch (error) {
  dv.paragraph(`Dashboard error: ${error.message}`);
}
```
