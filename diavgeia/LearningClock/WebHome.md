# LearningClock v6.0

LearningClock project notes and deployment-facing content.

## Status

- Version 6.0 adds LauncherPad, per-clock Windows mutex protection, no-console GUI processes, protepo.log 2.0 structured telemetry, and the LearningClock Seq Operations dashboard.
- The v5.3 timer interface uses bold menu and button labels for visibility.
- Inactive activity buttons are blue (`#069bff`); the currently running timer is orange (`#FF6600`).
- **Book Listening** is the listening timer and uses the `book_listening` CSV column. Legacy `audiobook` data is normalized during CSV reads and migration.
- Python source lives under `src/learningclock`; generated artifacts are kept under `build/`.

## Pages

- [Developer Commands](Developer-Commands.md)
- [Learning Clock Dashboard](Learning-Clock-Dashboard.md)
- [LauncherPad and Observability](LauncherPad-and-Observability.md)
