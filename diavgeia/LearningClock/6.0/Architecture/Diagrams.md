# LearningClock 6.0 Architecture Diagrams

**Product Release:** 6.0  
**Document Revision:** R1  
**Document Version:** 6.0.R1

## System context

```mermaid
flowchart LR
    User[User] --> LauncherPad[LearningClock LauncherPad]
    LauncherPad --> ClockA[Configured Clock A]
    LauncherPad --> ClockB[Configured Clock B]
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
    LP --> Discovery[Discover configurations]
    LP -->|selected properties and correlation ID| Child[Detached clock process]
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
    LP->>PL: launch_clock(configuration, correlation)
    PL-->>LP: Detached process ID
    PL->>Clock: --clock PATH --correlation-id ID
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
    Composition --> File[(learning_clock_debug.log)]
    Composition -. optional .-> SeqSink[Seq CLEF ingestion]
    SeqSink --> Seq[(Seq)]
    Seq --> Ops[LearningClock Operations dashboard]
    SeqSink -->|delivery unavailable| Spool[(offline CLEF spool)]
```

Dashed Seq paths are optional. A dashboard event confirms received telemetry;
it does not confirm that a clock owns a mutex or that CSV persistence succeeded
unless the corresponding structured event is present.
