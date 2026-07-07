# QUANTAURA-Core v0.4 Architecture

## Overview

QUANTAURA-Core is a unified research operating system that integrates:

- **Orchestration Engine**: Schedules and coordinates complex experiment pipelines with dependency resolution
- **Telemetry System**: Real-time event streaming and observability
- **Resource Management**: CPU/memory allocation and enforcement
- **Validation Framework**: Configuration validation and dependency graph analysis
- **Retry Mechanisms**: Automatic failure recovery with configurable backoff strategies

## Core Components

### 1. Scheduler (`scheduler.py`)

The experiment orchestration engine manages:

- **Experiment Registration**: Define tasks, dependencies, timeouts, and priorities
- **Dependency Resolution**: Topological sorting of experiment DAG (directed acyclic graph)
- **Concurrent Execution**: Manages up to N parallel experiments (configurable)
- **State Machine**: PENDING → QUEUED → RUNNING → COMPLETED/FAILED
- **Pause/Resume**: Live control of experiment execution

**Key Classes:**
- `Experiment`: Individual task definition
- `ExperimentScheduler`: Main orchestration engine
- `DependencyGraph`: Manages experiment dependencies
- `ExperimentState`: Execution state enum

**Usage:**
```python
scheduler = ExperimentScheduler(max_concurrent=4)
exp_id = scheduler.register_experiment(experiment)
await scheduler.run()
```

### 2. Retry Policy (`retry_policy.py`)

Handles automatic failure recovery:

**Strategies:**
- `EXPONENTIAL_BACKOFF`: Delay grows exponentially (default)
- `LINEAR_BACKOFF`: Delay grows linearly
- `FIXED_DELAY`: Same delay between retries
- `IMMEDIATE`: Retry immediately

**Configuration:**
```python
policy = RetryPolicy(
    max_retries=3,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    initial_delay_seconds=1.0,
    max_delay_seconds=300.0,
    backoff_multiplier=2.0,
)
```

### 3. Resource Manager (`resource_manager.py`)

Tracks and enforces resource limits:

- **Memory Allocation**: Set per-experiment max memory (MB)
- **CPU Limits**: Monitor and enforce CPU percentage thresholds
- **Disk Quota**: Track disk usage per experiment
- **System Status**: Aggregate resource view across all experiments

**Configuration:**
```python
config = ResourceConfig(
    max_memory_mb=2048,
    max_cpu_percent=80.0,
    max_disk_usage_mb=10000,
    timeout_seconds=3600,
)
```

### 4. Experiment Validator (`experiment_validator.py`)

Validates configurations before execution:

- **Schema Validation**: Name, task, dependencies, timeouts, retries
- **Dependency Graph Analysis**: Detects circular dependencies
- **Range Checking**: Ensures values are within acceptable bounds
- **Custom Validators**: Extensible validation framework

**Validation:**
```python
validator = ExperimentValidator()
errors = validator.validate_experiment({"name": "...", "task": ...})
```

### 5. Event Bus (`event_bus.py`)

Central publish-subscribe system for real-time events:

**Event Types:**
- Experiment lifecycle: REGISTERED, QUEUED, STARTED, COMPLETED, FAILED, PAUSED, RESUMED
- Resource events: ALLOCATED, RELEASED, WARNING, EXCEEDED
- Scheduler events: STARTED, PAUSED, COMPLETED, ERROR

**Usage:**
```python
bus = EventBus()
bus.subscribe(EventType.EXPERIMENT_COMPLETED, my_handler)
event = Event(type=EventType.EXPERIMENT_STARTED, source="orchestrator", ...)
bus.emit(event)
```

### 6. Telemetry System (`telemetry.py`)

Collects and aggregates operational metrics:

- **TelemetryCollector**: Subscribes to events and builds metrics
- **WebSocketTelemetrySender**: Streams events to connected clients
- **TelemetryDatabaseWriter**: Persists events to database
- **DashboardDataProvider**: Prepares aggregated data for dashboards

### 7. Database Layer (`database.py`)

Abstract repository pattern for persistence:

**Records:**
- `ExperimentRecord`: Experiment metadata and results
- `EventRecord`: Raw event stream
- `ResourceUsageRecord`: Resource consumption timeline

**Repositories:**
- `ExperimentRepository`: CRUD for experiments
- `EventRepository`: Query events by experiment or time
- `ResourceUsageRepository`: Query resource usage trends

### 8. Research Orchestrator (`orchestrator.py`)

Unified API that coordinates all components:

```python
orchestrator = ResearchOrchestrator(max_concurrent=4)

# Register experiments
exp_id = orchestrator.register_experiment(
    name="My Experiment",
    task=my_function,
    dependencies=[...],
    priority=10,
    timeout_seconds=3600,
    retries=3,
    resource_config=ResourceConfig(...),
)

# Execute pipeline
result = await orchestrator.execute()

# Get status
status = orchestrator.get_status()
```

## Execution Model

### Dependency Graph

Experiments form a DAG (directed acyclic graph):

```
Experiment A (priority=20)
      |
      +---> Experiment B (priority=15)
      |
      +---> Experiment C (priority=15)
            |
            v
      Experiment D (priority=5)
```

**Execution:**
1. A and B,C run in parallel (max_concurrent=4 allows this)
2. D waits for B and C to complete
3. All dependencies must complete before dependent starts

### State Machine

```
┌─────────┐
│ PENDING │  (initial state)
└────┬────┘
     │
     v
┌─────────┐
│ QUEUED  │  (waiting for resources)
└────┬────┘
     │
     v
┌─────────┐
│ RUNNING │  (executing)
└─┬───┬───┘
  │   │
  │   └──> FAILED (error)
  │
  └──> COMPLETED (success)

PAUSED state can be entered/exited from RUNNING
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  ResearchOrchestrator                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐         ┌──────────────────┐         │
│  │   Scheduler     │────────→│   Event Bus      │         │
│  │   (execution)   │         │   (publisher)    │         │
│  └─────────────────┘         └──────────────────┘         │
│           │                          │                     │
│           v                          v                     │
│  ┌─────────────────┐         ┌──────────────────┐         │
│  │ ResourceManager │         │ TelemetryCollector         │
│  │ (allocation)    │         │ (metrics)        │         │
│  └─────────────────┘         └──────────────────┘         │
│           │                          │                     │
│           v                          v                     │
│  ┌─────────────────────────────────────────────┐          │
│  │ Storage Layer (Database/Dashboard)          │          │
│  └─────────────────────────────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Thread Safety

The orchestrator is designed for async/await patterns:

- **Scheduler**: Uses `asyncio.Queue` and `asyncio.Task` for concurrency
- **Event Bus**: Thread-safe event subscription and emission
- **Resource Manager**: Uses `psutil` for system-level queries (GIL-safe)

## Error Handling

**Timeout Handling:**
- Each experiment has a `timeout_seconds` parameter
- Exceeded timeouts raise `asyncio.TimeoutError` → FAILED state

**Retry Logic:**
- Failed experiments can be retried with exponential backoff
- Configurable via `RetryPolicy`

**Resource Exhaustion:**
- Memory exhaustion → experiment fails
- CPU limits → experiment throttled (monitored, not enforced)

## Performance Characteristics

- **Scheduler**: O(E log E) for topological sort (E = experiments)
- **Event Bus**: O(1) emit, O(H) history query (H = history size)
- **Dependency Graph**: O(E + D) for cycle detection (D = dependencies)

## Future Enhancements

- [ ] Distributed scheduling (multi-machine)
- [ ] Checkpoint/restore for long-running experiments
- [ ] Advanced resource allocation (GPU support)
- [ ] Real-time WebSocket dashboard
- [ ] Experiment replay and debugging
- [ ] Integration with container runtimes (Docker, Kubernetes)
