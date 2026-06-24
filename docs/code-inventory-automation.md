# Automated Code Inventory

The repository regenerates the README Code Inventory after every push to `main`.
The automation is implemented by:

```text
.github/workflows/code-inventory.yml
scripts/pygount_summary.py
```

The workflow:

1. Checks out the repository.
2. Installs Python and `pygount`.
3. Runs `python scripts/pygount_summary.py`.
4. Commits `README.md` and `docs/assets/pygount-summary.svg` when their contents changed.
5. Pushes the generated commit back to the branch.

The generated commit contains `[skip ci]`. GitHub also prevents events created
with the repository `GITHUB_TOKEN` from recursively starting another workflow.
The workflow exits without committing when the generated files are unchanged.

## Repository Settings

In GitHub, open:

```text
Settings -> Actions -> General -> Workflow permissions
```

Select **Read and write permissions** so `GITHUB_TOKEN` can push the generated
files. If `main` has branch protection, allow GitHub Actions to push or use a
pull-request-based update workflow instead.

## Add It to Another Repository

Each repository must own its complete Code Inventory implementation. Do not call
the LearningClock workflow from another repository.

Copy these files into the new repository:

```text
.github/workflows/code-inventory.yml
scripts/pygount_summary.py
```

Also ensure that the repository contains:

```text
README.md
docs/assets/
```

The copied workflow executes the copied generator from the same repository:

```yaml
- name: Regenerate Code Inventory
  run: python scripts/pygount_summary.py
```

Review the following project-specific settings after copying:

- Default branch name in `on.push.branches`.
- Python version.
- Paths counted by `COUNT_PATHS` in `scripts/pygount_summary.py`.
- Generated README heading and SVG path.
- Files staged by the workflow's `git add` command.

This duplication is intentional. Every repository remains operational if
LearningClock is renamed, deleted, made private, or its workflow changes.
