# LearningClock 6.0 Documentation Baseline

**Product Release:** 6.0  
**Document Revision:** R1  
**Document Version:** 6.0.R1

This directory is the controlled documentation baseline for LearningClock 6.0.
It covers the multi-clock LauncherPad, independently running timer processes,
per-clock Windows singleton enforcement, CSV persistence, the FastAPI readiness
surface, protepo.log 2.0 telemetry, and Seq operations.

- [Architecture](Architecture/Overview.md)
- [Architecture diagrams](Architecture/Diagrams.md)
- [Configuration](Configuration/Overview.md)
- [Seq setup](Configuration/Seq%20Setup.md)
- [Implementation](Implementation/Overview.md)
- [Python source code](Implementation/Python%20Source%20Code.md)

Cross-release command, dashboard, and maintenance pages remain at the
LearningClock root. See
[Documentation Versioning](../Documentation%20Versioning.md).

## Baseline summary

- One `learningclock-gui` entry opens LauncherPad without a console.
- LauncherPad discovers multiple `.properties` files and launches one detached
  process per selected clock.
- Each clock owns `Local\Protepo.LearningClock.<clock-id>` before initializing
  CSV persistence; LauncherPad only observes that mutex.
- CSV files remain the authoritative learning-session store and retain legacy
  field normalization.
- Local semantic logs remain available when Seq is disabled or unreachable.
- Seq provides correlated operational evidence and a version-controlled
  dashboard; it does not control process ownership or persistence.
