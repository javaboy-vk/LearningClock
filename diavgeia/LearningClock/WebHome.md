# LearningClock Engineering Knowledge

This version-independent page is the published entry point for LearningClock
engineering and operational knowledge.

## Controlled product baselines

- [LearningClock 6.0](6.0/Overview.md)
  - [Architecture](6.0/Architecture/Overview.md)
  - [Architecture diagrams](6.0/Architecture/Diagrams.md)
  - [Configuration](6.0/Configuration/Overview.md)
  - [Seq setup](6.0/Configuration/Seq%20Setup.md)
  - [Implementation](6.0/Implementation/Overview.md)
  - [Python source code](6.0/Implementation/Python%20Source%20Code.md)

See [Documentation Versioning](Documentation%20Versioning.md) for the boundary
between controlled release documentation and cross-release material.

## Version-independent operations and reference

- [Developer Commands](Developer-Commands.md)
- [How to add a new timer](How-to-add-a-new-timer.md)
- [Learning Clock Dashboard](/Learning-Clock-Dashboard.md)
- [Reference overview](Reference/Overview.md)
- [LauncherPad and Observability compatibility page](LauncherPad-and-Observability.md)

The deployable dashboard implementation remains under
`views/learning-clock-dashboard/`. Release tooling installs that component once
under `Engineering/LearningClock` and installs the dashboard note at the vault
root. The view discovers every configured clock's `LearningPath/learning_time_log.csv`
file in the vault and exposes one alphabetically sorted selector.
