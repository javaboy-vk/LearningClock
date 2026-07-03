# Automated Code Inventory

The repository verifies the README Code Inventory after every push to `main`.
The automation is implemented by:

```text
.github/workflows/code-inventory.yml
scripts/pygount_summary.py
```

The workflow:

1. Checks out the repository.
2. Installs Python and `pygount`.
3. Runs `python scripts/pygount_summary.py`.
4. Fails if `README.md` or `docs/assets/pygount-summary.svg` changed during regeneration.

The workflow exits successfully when the generated files are already current.
When it fails, run the generator locally and commit the updated files:

```text
python scripts/pygount_summary.py
git add README.md docs/assets/pygount-summary.svg
git commit
```

## Repository Settings

The workflow only needs read access to repository contents:

```text
Settings -> Actions -> General -> Workflow permissions
```

Select **Read repository contents permission**. The action does not push commits,
so it will not create bot commits that make local branches diverge from `main`.

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
- Files checked by the workflow's `git diff` command.

This duplication is intentional. Every repository remains operational if
LearningClock is renamed, deleted, made private, or its workflow changes.
