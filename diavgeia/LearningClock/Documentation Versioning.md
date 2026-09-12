# LearningClock Documentation Versioning

## Purpose

LearningClock product releases establish controlled documentation baselines.
Release-specific material belongs beneath the first-level release directory that
describes it; for example, `LearningClock/6.0/Architecture/`.

The current controlled baseline is **LearningClock 6.0**. A later release folder
must be created from an authoritative product-version change, not inferred from
a source-file revision, documentation edit, Git branch, or build artifact.

## Product releases and document revisions

A controlled document uses this version format:

```text
<major>.<minor>.R<revision>
```

For example, `6.0.R1` is the first revision of a document for product release
6.0. The `R` value is a documentation revision; it is not a product patch,
package version, build number, Git commit, or Python file-header revision.

Controlled documents place these fields directly below their title:

```text
Product Release: 6.0
Document Revision: R1
Document Version: 6.0.R1
```

When a controlled document is carried into a later product-release baseline,
its document revision restarts at `R1`.

## Classification rules

Release-specific material belongs under `LearningClock/<release>/`:

- `Architecture/` for system boundaries, runtime/process design, persistence,
  observability, and controlled diagrams.
- `Configuration/` for release-specific properties, environment variables,
  runtime paths, and Seq setup.
- `Implementation/` for module responsibilities, algorithms, source-code maps,
  and implementation-specific operating behavior.

Version-independent material remains directly under `LearningClock/`:

- `WebHome.md` is the cross-release entry point.
- `Documentation Versioning.md` defines this policy.
- `Reference/` contains cross-release reference and navigation.
- `Developer-Commands.md` documents the current repository command surface.
- `How-to-add-a-new-timer.md` is a maintenance workflow that links to the
  applicable release contract.
- `Learning-Clock-Dashboard.md` is published once at the vault root, while its
  centralized `views/` implementation remains under `Engineering/LearningClock`.
- `LauncherPad-and-Observability.md` remains a compatibility link for the
  previously published path.

## Python version distinction

The authoritative product version is `6.0` in `pyproject.toml`,
`src/learningclock/__init__.py`, and `APP_VERSION` in
`src/learningclock/app.py`. The `# Version` field in an individual Python file
tracks that file's own revision and does not create a new product release or
documentation baseline.
