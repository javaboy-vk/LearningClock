/*
File Name : view.js
Artifact  : LearningClock - Learning Clock Dashboard Dataview View
Author    : javaboy-vk
Date      : 2026-06-05
Version   : v6.3
Purpose:
  Discovers every LearningClock CSV in the vault and renders the selected clock.
*/

const csvFileName = "learning_time_log.csv";
const legacyCsvFolderName = "LearningPath";
const viewInput = typeof input === "object" && input ? input : {};

const activityFields = [
  ["Reading", "reading"],
  ["Book Listening", "book_listening", ["audiobook"]],
  ["Outlining", "outlining"],
  ["Active Recall", "active_recall", ["memorizing"]],
  ["Sandbox", "sandbox", ["experimenting"]],
  ["AI-Assisted Architecture & Design", "ai_assisted_architecture_design"],
  ["AI-Assisted Engineering", "ai_assisted_engineering"],
  ["Classical Software Engineering", "classical_software_engineering"],
  ["Update Diavgeia", "update_diavgeia"],
  ["Promote Stable Concept", "promote_stable_concept"],
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

function appendDashboardTitle(parent, learningPathName) {
  const title = document.createElement("h1");
  const name = document.createElement("span");
  name.className = "lc-title-name";
  name.textContent = learningPathName;

  title.appendChild(name);
  title.appendChild(document.createTextNode(" Learning Time"));
  parent.appendChild(title);
  return title;
}

function joinVaultPath(...parts) {
  return parts.filter(Boolean).join("/");
}

function getCurrentFolderPath() {
  const currentPath = dv.current()?.file?.path;
  if (!currentPath) {
    throw new Error("Could not resolve the current dashboard page path.");
  }

  const lastSlash = currentPath.lastIndexOf("/");
  return lastSlash >= 0 ? currentPath.slice(0, lastSlash) : "";
}

function getLearningPathName(rows, fallbackName) {
  if (viewInput.learningPathName) {
    return String(viewInput.learningPathName);
  }
  const rowWithPath = rows.find((row) => row.learning_path && row.learning_path.trim());
  if (rowWithPath) {
    return rowWithPath.learning_path.trim();
  }

  return fallbackName || "LearningClock";
}

function resolveConfiguredCsvFile() {
  if (!viewInput.csvPath) {
    return null;
  }

  const currentFolder = getCurrentFolderPath();
  const candidatePaths = [
    String(viewInput.csvPath),
    joinVaultPath(currentFolder, String(viewInput.csvPath)),
  ].filter(Boolean);

  for (const candidatePath of candidatePaths) {
    const candidateFile = app.vault.getAbstractFileByPath(candidatePath);
    if (candidateFile) {
      return { file: candidateFile, path: candidatePath, name: String(viewInput.learningPathName || "LearningClock") };
    }
  }

  throw new Error(`CSV file not found in dashboard component: ${candidatePaths.join(" or ")}`);
}

function discoverClockSources() {
  const configured = resolveConfiguredCsvFile();
  if (configured) {
    return [configured];
  }

  const suffix = `/${legacyCsvFolderName}/${csvFileName}`.toLowerCase();
  const sources = app.vault.getFiles()
    .filter((file) => `/${file.path}`.toLowerCase().endsWith(suffix))
    .map((file) => {
      const folderPath = file.path.slice(0, -suffix.length);
      const folderParts = folderPath.split("/").filter(Boolean);
      return {
        file,
        path: file.path,
        name: folderParts[folderParts.length - 1] || "LearningClock",
        folderPath,
      };
    });

  const duplicateNames = new Set(
    sources
      .filter((source, index) => sources.some((other, otherIndex) => (
        otherIndex !== index && other.name.localeCompare(source.name, undefined, { sensitivity: "accent" }) === 0
      )))
      .map((source) => source.name)
  );
  for (const source of sources) {
    source.label = duplicateNames.has(source.name) ? source.folderPath : source.name;
  }
  return sources.sort((left, right) => (
    (left.label || left.name).localeCompare(
      right.label || right.name,
      undefined,
      { sensitivity: "base", numeric: true }
    )
  ));
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
    .lc-title-name {
      color: #3279b7;
    }
    .lc-clock-picker {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 18px 0 8px;
    }
    .lc-clock-picker label {
      color: #164f86;
      font-weight: 700;
    }
    .lc-clock-picker select {
      min-width: 260px;
      max-width: 100%;
    }
    .lc-bars {
      display: grid;
      grid-template-columns: repeat(10, minmax(0, 1fr));
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
      background: #007ACC;
      color: #fff;
      display: flex;
      align-items: flex-start;
      justify-content: center;
      padding-top: 8px;
      font-weight: 400;
      font-size: 13px;
      line-height: 1;
      box-sizing: border-box;
      text-shadow: 0 1px 1px rgba(0, 0, 0, 0.35);
    }
    .lc-labels {
      display: grid;
      grid-template-columns: repeat(10, minmax(0, 1fr));
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
    .lc-sessions {
      width: 100%;
      border-collapse: collapse;
    }
    .lc-sessions th,
    .lc-sessions td {
      border-bottom: 1px solid var(--background-modifier-border);
      padding: 7px 10px;
      text-align: left;
    }
  `;
  root.appendChild(style);
}

function appendRecentSessions(parent, sessions) {
  appendText(parent, "h2", "Recent Sessions");
  const table = document.createElement("table");
  table.className = "lc-sessions";
  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const heading of ["Date", "Start", "End", "Total", "Pages"]) {
    appendText(headRow, "th", heading);
  }
  head.appendChild(headRow);
  table.appendChild(head);

  const body = document.createElement("tbody");
  for (const row of sessions.slice(-10).reverse()) {
    const tableRow = document.createElement("tr");
    for (const value of [row.date, row.session_start, row.session_end, row.total, row.pages_read || "0"]) {
      appendText(tableRow, "td", value || "");
    }
    body.appendChild(tableRow);
  }
  table.appendChild(body);
  parent.appendChild(table);
}

async function renderDashboard(parent, source) {
  parent.replaceChildren();
  const text = await app.vault.read(source.file);
  const rows = parseCsv(text);
  const sessions = rows.filter((row) => row.date && row.date !== "TOTAL");
  const totalRow = rows.find((row) => row.date === "TOTAL");
  const learningPathName = getLearningPathName(rows, source.name);

  const totals = Object.fromEntries(activityFields.map(([, field]) => [field, 0]));
  let totalSeconds = 0;
  let pagesRead = 0;

  for (const row of sessions) {
    for (const [, field, legacyFields = []] of activityFields) {
      const currentSeconds = parseDuration(row[field]);
      const legacySeconds = legacyFields.reduce((sum, legacyField) => sum + parseDuration(row[legacyField]), 0);
      totals[field] += currentSeconds || legacySeconds;
    }
    totalSeconds += parseDuration(row.total);
    pagesRead += Number.parseInt(row.pages_read || "0", 10) || 0;
  }

  const grandTotal = totalRow ? parseDuration(totalRow.total) : totalSeconds;
  const totalPages = Number.parseInt(totalRow?.pages_read || pagesRead || "0", 10) || 0;
  const maxSeconds = Math.max(...activityFields.map(([, field]) => totals[field]), 1);
  const firstSession = sessions[0];
  const lastSession = sessions[sessions.length - 1];

  appendDashboardTitle(parent, learningPathName);

  const card = document.createElement("section");
  card.className = "lc-card";
  parent.appendChild(card);

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
    if (["Sandbox", "Active Recall"].includes(label)) {
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

  appendRecentSessions(parent, sessions);
  appendText(parent, "h2", "CSV File");
  appendText(parent, "div", source.path, "lc-source");
}

try {
  const root = dv.container;
  applyStyles(root);
  const sources = discoverClockSources();
  if (sources.length === 0) {
    throw new Error(`No */${legacyCsvFolderName}/${csvFileName} files were found in this vault.`);
  }

  const picker = document.createElement("div");
  picker.className = "lc-clock-picker";
  const pickerLabel = appendText(picker, "label", "Learning clock:");
  const selector = document.createElement("select");
  pickerLabel.htmlFor = "lc-clock-selector";
  selector.id = "lc-clock-selector";
  for (const source of sources) {
    const option = document.createElement("option");
    option.value = source.path;
    option.textContent = source.label || source.name;
    selector.appendChild(option);
  }
  picker.appendChild(selector);
  root.appendChild(picker);

  const dashboard = document.createElement("div");
  root.appendChild(dashboard);
  const showSelectedClock = async () => {
    const source = sources.find((candidate) => candidate.path === selector.value) || sources[0];
    try {
      await renderDashboard(dashboard, source);
    } catch (error) {
      dashboard.replaceChildren();
      appendText(dashboard, "p", `Dashboard error: ${error.message}`);
    }
  };
  selector.addEventListener("change", showSelectedClock);
  await showSelectedClock();
} catch (error) {
  dv.paragraph(`Dashboard error: ${error.message}`);
}
