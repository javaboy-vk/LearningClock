# LearningClock 6.0 Architecture Diagrams

**Product Release:** 6.0  
**Document Revision:** R6
**Document Version:** 6.0.R6

## System context

```mermaid
flowchart LR
    User[User] --> LauncherPad[LearningClock LauncherPad]
    LauncherPad --> ClockA[Configured Clock A]
    LauncherPad --> ClockB[Configured Clock B]
    LauncherPad --> Provision[Transactional clock provisioning]
    LauncherPad --> Report[Cross-clock category histogram]
    ClockA --> CsvA[(Clock A CSV)]
    ClockB --> CsvB[(Clock B CSV)]
    LauncherPad --> Logs[Local semantic logs]
    ClockA --> Logs
    ClockB --> Logs
    Logs -. optional CLEF .-> Seq[Seq]
    Seq --> Dashboard[LearningClock Operations]
    HealthClient[Health or integration client] --> API[FastAPI health API]
```

## Runtime process model

```mermaid
flowchart TD
    Entry[learningclock-gui] --> Desktop[desktop.main]
    Desktop -->|no --clock| LP[LauncherPad process]
    LP --> Central[Load central runtime configuration]
    LP --> Discovery[Discover and migrate clock configurations]
    Central -->|pythonExe and pyScriptPath| Child[Detached clock process]
    Discovery -->|learning-path-name and logDir| Child
    Child --> Guard[Acquire per-clock named mutex]
    Guard -->|new owner| App[Tkinter LearningClock]
    Guard -->|already exists| Reject[Reject before persistence]
    App --> Store[CsvStore]
    LP -. OpenMutexW observation .-> Guard
```

## Launch and singleton sequence

```mermaid
sequenceDiagram
    actor User
    participant LP as LauncherPad
    participant PL as ProcessLauncher
    participant Clock as Clock process
    participant Mutex as Windows mutex
    participant CSV as CsvStore
    User->>LP: Select configured clock
    LP->>LP: Create correlation ID
    LP->>LP: Validate central executable and script
    LP->>PL: launch_clock(central, clock, correlation)
    PL-->>LP: Detached process ID
    PL->>Clock: app.py --learning-path NAME --log-dir PATH
    Clock->>Mutex: CreateMutexW(clock_id)
    alt mutex acquired
        Mutex-->>Clock: owned handle
        Clock->>CSV: initialize log directory and session state
        Clock-->>User: show timer UI
    else mutex already exists
        Mutex-->>Clock: ERROR_ALREADY_EXISTS
        Clock-->>User: reject duplicate startup
    end
```

## Provisioning and report flow

```mermaid
flowchart LR
    Form[Create New Clock form] --> Validate[Validate name, path, duplicates, conflicts]
    Validate --> Atomic[Atomic properties and LearningPath CSV writes]
    Central[One deployed vault dashboard and view] --> Scan[Discover every LearningPath CSV]
    Scan --> Select[Select a clock]
    Atomic --> Refresh[Immediate discovery refresh]
    Refresh --> Launch[Launchable clock]
    Refresh --> Worker[Background report worker]
    Worker --> Rows[Read dated non-TOTAL rows]
    Rows --> Aggregate[Canonical ordered category totals]
    Rows --> Issues[File row column value and reason]
    Aggregate --> Latest{Latest request ID?}
    Latest -->|yes| Chart[Vertical histogram]
    Latest -->|no| Discard[Discard stale result]
    Issues --> Link[Skipped invalid hyperlink]
    Link --> Popup[Read-only diagnostic popup]
    Popup --> Source[Open source file or nearest directory]
```

## Persistence flow

```mermaid
flowchart TD
    UI[Timer and manual input] --> Session[In-memory session state]
    Session --> Checkpoint[Autosave, refresh, or close checkpoint]
    Checkpoint --> Read[Read existing session rows]
    Read --> Normalize[Normalize dates and legacy fields]
    Normalize --> Merge[Merge recoverable emergency rows]
    Merge --> Sort[Sort session rows chronologically]
    Sort --> Total[Recalculate one final TOTAL row]
    Total --> CSV[(learning_time_log.csv)]
    Checkpoint -->|normal write fails| Emergency[(timestamped emergency CSV)]
```

## Observability flow

```mermaid
flowchart LR
    Components[Application components] --> Events[events.py and telemetry.py]
    Events --> Composition[observability.py]
    Composition --> File[(D:\LearningClock\logs\clock-id\learning_clock_debug.log)]
    Composition -. optional .-> SeqSink[Seq CLEF ingestion]
    SeqSink --> Seq[(Seq)]
    Seq --> Ops[LearningClock Operations dashboard]
    SeqSink -->|delivery unavailable| Spool[(D:\LearningClock\logs\clock-id\offline CLEF spool)]
```

Dashed Seq paths are optional. A dashboard event confirms received telemetry;
it does not confirm that a clock owns a mutex or that CSV persistence succeeded
unless the corresponding structured event is present.
