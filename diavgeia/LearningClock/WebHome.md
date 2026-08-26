# LearningClock v5.3

LearningClock project notes and deployment-facing content.

## Status

- Version 5.3 uses bold menu and button labels for visibility.
- Inactive activity buttons are blue (`#069bff`); the currently running timer is orange (`#FF6600`).
- **Book Listening** is the listening timer and uses the `book_listening` CSV column. Legacy `audiobook` data is normalized during CSV reads and migration.
- Python source lives under `src/learningclock`; generated artifacts are kept under `build/`.

## Pages

- [Developer Commands](Developer-Commands.md)
- [Learning Clock Dashboard](Learning-Clock-Dashboard.md)
