# Automated Code Inventory

The README Code Inventory image points to a generated GitHub Pages asset:

```text
https://javaboy-vk.github.io/LearningClock/pygount-summary.svg
```

That SVG is not committed to `main`. It is generated during the project Pages
workflow and published with the Engineering Scorecard and coverage report.

The scorecard is published at:

```text
https://javaboy-vk.github.io/LearningClock/
```

The automation is implemented by:

```text
.github/workflows/coverage-pages.yml
scripts/pygount_summary.py
```

The workflow:

1. Checks out the repository.
2. Installs the project with development dependencies.
3. Runs pytest with HTML and JSON coverage plus aggregate JUnit XML.
4. Runs `python scripts/pygount_summary.py`.
5. Generates the versioned Engineering Scorecard, overview, test, performance,
   benchmark, repository-inventory, and four project-area inventory sections.
6. Assembles the report tree under the GitHub Pages artifact, with the scorecard
   as the landing page and coverage under `coverage/`.
7. Deploys the complete Pages artifact.

The action does not push commits, so it does not create bot commits that make
local branches diverge from `main`.

## Local Generation

Run the local generator with:

```text
python scripts/pygount_summary.py
```

It writes generated scorecard and inventory output under:

```text
build/reports/
```

It also writes generated supporting landing pages under `build/tests/`,
`build/performance/`, and `build/benchmarks/`. Performance and benchmark pages
state explicitly when no dedicated workload exists; they do not invent evidence.

The `build/` directory is ignored by Git. Do not commit generated pygount output.

## Repository Settings

In GitHub, open:

```text
Settings -> Pages
```

Set the source to **GitHub Actions**.

## Add It to Another Repository

Each repository must own its complete Code Inventory implementation. Do not call
the LearningClock workflow from another repository.

Copy these files into the new repository:

```text
.github/workflows/coverage-pages.yml
scripts/pygount_summary.py
```

Review the following project-specific settings after copying:

- GitHub Pages URL in `scripts/pygount_summary.py`.
- Default branch name in `on.push.branches`.
- Python version.
- Paths counted by `scripts/pygount_summary.py`.
- Published scorecard, coverage, and inventory paths in the workflow and README.

This duplication is intentional. Every repository remains operational if
LearningClock is renamed, deleted, made private, or its workflow changes.
