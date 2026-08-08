# LearningClock v5.2

LearningClock is a Windows-friendly Python/Tkinter desktop timer for tracking focused learning sessions. It records time across named study activities, page counts, session metadata, recovered emergency saves, and a recalculated CSV `TOTAL` row that can feed reports and Diavgeia documentation.

It is inspired by **dual timers chess clocks**. As soon as a player makes a moove stops his timer which starts his opponent timer. Similarly that Learning Clock has timers that track the different stages of learning. For example, I can start with reading, and as soon as hit the outlining timer, the reading timer stops and the outliner starts.

The project is intentionally small and operational: the GUI owns timer behavior, `CsvStore` owns persistence, tests protect the CSV contract, and `scripts/dev.py` provides repeatable lifecycle commands for development, QA, coverage, packaging, Diavgeia export, and production release.

## Application And Dashboard

The desktop app presents learning timers that map directly to the persisted CSV activity columns. The refreshed view includes **Set Date** for backdated entries, **Add Page Count**, and the **View Progress** toggle.

### Version 5.2 interface

The v5.2 desktop interface uses bold menu and button labels for better visibility. Inactive activity controls are blue (`#069bff`); the running activity is orange (`#FF6600`). **Book Listening** is the current listening timer and persists as the `book_listening` CSV column. Existing `audiobook` data is retained through CSV normalization and migration.

![LearningClock desktop UI with learning timers](docs/assets/learning-clock-ui.svg)

**View Progress** opens the same CSV-based progress information inside the desktop app, beside the timers.

![LearningClock in-app View Progress dashboard](docs/assets/learning-clock-progress.svg)

The Obsidian/Diavgeia dashboard reads the CSV and renders the aggregate learning-time graph from `diavgeia/LearningClock/Learning-Clock-Dashboard.md`.

![LearningClock Obsidian dashboard graph](docs/assets/learning-clock-dashboard.svg)

## Categories

| Category | Purpose |
| --- | --- |
| Reading | Reading books, articles, docs. |
| Book Listening | Listening to technical learning material. |
| Outlining | Structuring notes, chapters, designs. |
| Active Recall | Recall practice, repetition, self-testing, and memory reinforcement. |
| Sandbox | Trial-and-error sandbox work, examples, prototypes, technology probes, and book/example exercises. |
| AI-Assisted Architecture & Design | Architecture, system design, modeling, tradeoff analysis, and design documentation performed through AI-assisted conversation. |
| AI-Assisted Engineering | Working with ChatGPT, CODEX, or other AI tools to generate, repair, design, document, test, or debug code. |
| Classical Software Engineering | Personally writing, modifying, refactoring, testing, debugging, and implementing code using traditional software engineering practices. |
| Update Diavgeia | Capturing stable knowledge in Obsidian/Diavgeia. |
| Promote Stable Concept | Turning stable ideas into reusable, publishable, or shareable concepts. |

“Sandbox” is for sandbox learning, trial-and-error, book examples, technology probes, prototype exploration, and trying things out before they become stable engineering work.

“AI-Assisted Engineering” is for time spent instructing ChatGPT, CODEX, or another AI assistant to generate, repair, explain, refactor, test, document, or debug code.

“AI-Assisted Architecture & Design” is for architecture, system design, modeling, tradeoff analysis, and design documentation performed through AI-assisted conversation.

“Classical Software Engineering” is for time spent directly implementing software yourself using traditional engineering practices: editing files, designing code, debugging in the IDE, running tests, refactoring, and fixing issues based on your own analysis.

## What Is Implemented

- Tkinter desktop timer with activity switching, stop/reset controls, manual time entry, and page-count entry.
- CSV persistence with a stable schema, canonical date formatting, activity-to-column mapping, page totals, and final aggregate `TOTAL` row.
- Existing CSV normalization for legacy dates and legacy field names.
- Emergency CSV save/recovery path for shutdown failures.
- Diagnostic logging beside the configured CSV output.
- Package CLI health check and version command.
- Compatibility launcher for the historical `learning-clock.py` entry path.
- Unit tests for CSV behavior and focused regression tests for real/app-style CSV inputs.
- Default `clock-QA` regression fixture under `build\Clock-QA` so the complete pytest suite runs without skipped CSV regression tests.
- HTML coverage generation through a convenience command.
- Diavgeia Markdown source pages and export tooling.
- Production release script that copies the runnable launcher/runtime files to `D:\LearningPath\Tools\LearningClock`.

## Documentation

- [Requirements](docs/requirements.md)
- [Quick Start](docs/quick-start.md)
- [Usage](docs/usage.md)
- [Source Code Structure](docs/source-code-structure.md)
- [CSV Contract](docs/csv-contract.md)
- [Tests and Default Clock-QA Regression Fixture](docs/tests.md)
- [Coverage](docs/coverage.md)
- [Coverage Report](https://javaboy-vk.github.io/LearningClock/)
- [Convenience Commands](docs/convenience-commands.md)
- [Production Release, Packaging, and Generated Output Policy](docs/production-release.md)
- [Obsidian-Diavgeia Documentation](docs/obsidian-diavgeia-documentation.md)
- [VS Code Support](docs/vscode-support.md)
- [Automated Code Inventory](docs/code-inventory-automation.md)

## Code Inventory

The GitHub Pages workflow generates this image without modifying the repository.

![Pygount summary](https://javaboy-vk.github.io/LearningClock/pygount-summary.svg)
