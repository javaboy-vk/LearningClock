# Automated Code Inventory

The README Code Inventory image points to a generated GitHub Pages asset:

```text
https://javaboy-vk.github.io/LearningClock/assets/pygount-summary.svg
```

That SVG is not committed to `main`. It is generated during the project Pages
workflow and published with the coverage report.

The automation is implemented by:

```text
.github/workflows/coverage-pages.yml
scripts/pygount_summary.py
```

The workflow:

1. Checks out the repository.
2. Installs the project with development dependencies.
3. Runs the HTML coverage report.
4. Runs `python scripts/pygount_summary.py`.
5. Copies `build/reports/pygount-summary.svg` into the GitHub Pages artifact at
   `assets/pygount-summary.svg`.
6. Deploys the complete Pages artifact.

The action does not push commits, so it does not create bot commits that make
local branches diverge from `main`.

## Local Generation

Run the local generator with:

```text
python scripts/pygount_summary.py
```

It writes generated output under:

```text
build/reports/
```

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
- Published asset path in the workflow and README.

This duplication is intentional. Every repository remains operational if
LearningClock is renamed, deleted, made private, or its workflow changes.
