const TARGET_CHART_TITLE = "Recent LearningClock Events";
const TARGET_CHART_CLASS = "learningclock-recent-events";

// What it does: Marks only the LearningClock recent-events chart for layout styling.
// Why it exists: Seq uses the same table classes across every local dashboard.
// Designed use: The mutation observer calls this after Seq renders or refreshes charts.
function markRecentEventsChart() {
  document.querySelectorAll(".chart-component").forEach((chart) => {
    const heading = chart.querySelector(":scope > .chart-component-title");
    chart.classList.toggle(
      TARGET_CHART_CLASS,
      heading?.textContent.trim() === TARGET_CHART_TITLE,
    );
  });
}

const chartObserver = new MutationObserver(markRecentEventsChart);
chartObserver.observe(document.documentElement, {
  childList: true,
  subtree: true,
  characterData: true,
});
markRecentEventsChart();
