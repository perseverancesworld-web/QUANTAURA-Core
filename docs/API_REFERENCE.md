# API Reference - QUANTAURA-Core v0.4

## ResearchOrchestrator

Main entry point for orchestration.

### Constructor

```python
ResearchOrchestrator(max_concurrent: int = 4)
```

**Parameters:**
- `max_concurrent`: Maximum number of concurrent experiments (default: 4)

### Methods

#### register_experiment

```python
register_experiment(
    name: str,
    task: Callable,
    dependencies: Optional[List[str]] = None,
    priority: int = 0,
    timeout_seconds: int = 3600,
    retries: int = 3,
    resource_config: Optional[ResourceConfig] = None,
    retry_policy: Optional[RetryPolicy] = None,
) -> str
```

Register an experiment in the orchestration system.

**Parameters:**
- `name`: Human-readable experiment name
- `task`: Callable that performs the work
- `dependencies`: List of experiment IDs this depends on
- `priority`: Execution priority (-100 to 100, higher runs first)
- `timeout_seconds`: Maximum execution time
- `retries`: Number of retry attempts on failure
- `resource_config`: Resource allocation config (see ResourceConfig)
- `retry_policy`: Custom retry policy (see RetryPolicy)

**Returns:** Experiment ID (string UUID)

**Raises:** `ValueError` if configuration is invalid

**Example:**
```python
exp_id = orchestrator.register_experiment(
    name="My Experiment",
    task=my_function,
    priority=10,
    timeout_seconds=3600,
)
```

#### execute

```python
async def execute() -> dict
```

Execute all registered experiments.

**Returns:** Dictionary with execution summary:
```python
{
    "total_experiments": int,
    "completed": int,
    "failed": int,
    "success_rate": float,  # 0.0 to 1.0
    "experiments": dict,
    "dashboard_data": dict,
}
```

**Raises:** Exception if orchestration fails

**Example:**
```python
result = await orchestrator.execute()
print(f"Success rate: {result['success_rate']*100:.1f}%")
```

#### get_status

```python
get_status() -> dict
```

Get current orchestration status.

**Returns:** Dictionary with scheduler, resources, and telemetry status

**Example:**
```python
status = orchestrator.get_status()
print(status["resources"]["active_experiments"])
```

#### pause_experiment

```python
pause_experiment(exp_id: str) -> None
```

Pause a running experiment.

**Parameters:**
- `exp_id`: Experiment ID to pause

#### resume_experiment

```python
resume_experiment(exp_id: str) -> None
```

Resume a paused experiment.

**Parameters:**
- `exp_id`: Experiment ID to resume

## ResourceConfig

Resource allocation configuration.

```python
@dataclass
class ResourceConfig:
    max_memory_mb: int = 2048
    max_cpu_percent: float = 80.0
    max_disk_usage_mb: int = 10000
    timeout_seconds: int = 3600
```

**Example:**
```python
config = ResourceConfig(
    max_memory_mb=1024,
    max_cpu_percent=50.0,
    timeout_seconds=1800,
)
```

## RetryPolicy

Failure recovery configuration.

```python
@dataclass
class RetryPolicy:
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0
    backoff_multiplier: float = 2.0
    retryable_exceptions: tuple = (Exception,)
```

### Methods

#### get_delay

```python
get_delay(attempt: int) -> float
```

Calculate delay before retry.

**Parameters:**
- `attempt`: Retry attempt number (0-indexed)

**Returns:** Delay in seconds

#### should_retry

```python
should_retry(exception: Exception, attempt: int) -> bool
```

Determine if exception should trigger retry.

**Parameters:**
- `exception`: The raised exception
- `attempt`: Current attempt number

**Returns:** True if should retry, False otherwise

#### execute_with_retry

```python
async def execute_with_retry(func: Callable, *args, **kwargs) -> any
```

Execute function with automatic retry.

**Parameters:**
- `func`: Callable to execute
- `*args`, `**kwargs`: Arguments to pass to function

**Returns:** Function result

**Raises:** Last exception if all retries exhausted

**Example:**
```python
policy = RetryPolicy(max_retries=3)
result = await policy.execute_with_retry(my_function, arg1, arg2)
```

## EventBus

Central event publication system.

### Methods

#### subscribe

```python
subscribe(event_type: EventType, handler: Callable) -> None
```

Subscribe to events of a type.

**Parameters:**
- `event_type`: EventType to subscribe to
- `handler`: Callable(event) to invoke

**Example:**
```python
def on_complete(event):
    print(f"Experiment complete: {event.experiment_id}")

orchestrator.event_bus.subscribe(EventType.EXPERIMENT_COMPLETED, on_complete)
```

#### subscribe_async

```python
subscribe_async(event_type: EventType, handler: Callable) -> None
```

Subscribe with async handler.

**Example:**
```python
async def on_complete(event):
    await save_to_database(event)

orchestrator.event_bus.subscribe_async(EventType.EXPERIMENT_COMPLETED, on_complete)
```

#### emit

```python
emit(event: Event) -> None
```

Emit synchronous event.

#### emit_async

```python
async def emit_async(event: Event) -> None
```

Emit asynchronous event.

#### get_history

```python
get_history(event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]
```

Query event history.

**Parameters:**
- `event_type`: Filter by type (optional)
- `limit`: Maximum events to return

**Returns:** List of events

#### get_experiment_events

```python
get_experiment_events(experiment_id: str, limit: int = 100) -> List[Event]
```

Get events for specific experiment.

**Parameters:**
- `experiment_id`: Experiment ID to query
- `limit`: Maximum events to return

**Returns:** List of events

#### get_stats

```python
get_stats() -> dict
```

Get event bus statistics.

**Returns:**
```python
{
    "total_events": int,
    "unique_event_types": int,
    "event_counts": dict,
    "subscribers_count": int,
    "async_subscribers_count": int,
}
```

## ExperimentValidator

Configuration validation.

### Methods

#### validate_experiment

```python
validate_experiment(experiment_data: dict) -> List[ValidationError]
```

Validate experiment configuration.

**Parameters:**
- `experiment_data`: Configuration dict

**Returns:** List of ValidationError (empty if valid)

#### validate_dependency_graph

```python
validate_dependency_graph(experiments: dict) -> List[ValidationError]
```

Validate experiment dependency graph.

**Returns:** List of ValidationError (empty if valid DAG)

#### register_validator

```python
register_validator(field: str, validator: Callable) -> None
```

Register custom validation function.

**Parameters:**
- `field`: Field name
- `validator`: Callable that returns ValidationError or None

## ExperimentScheduler

Low-level scheduling engine (usually accessed via ResearchOrchestrator).

### Methods

#### register_experiment

```python
register_experiment(experiment: Experiment) -> str
```

Register experiment in scheduler.

#### pause_experiment

```python
pause_experiment(exp_id: str) -> None
```

Pause experiment execution.

#### resume_experiment

```python
resume_experiment(exp_id: str) -> None
```

Resume paused experiment.

#### run

```python
async def run() -> None
```

Main scheduling loop (called by orchestrator).

#### get_status

```python
get_status() -> dict
```

Get scheduler status.

## ResourceManager

Resource tracking and enforcement.

### Methods

#### allocate_resources

```python
allocate_resources(exp_id: str, config: Optional[ResourceConfig] = None) -> bool
```

Allocate resources for experiment.

**Returns:** True if allocation succeeded

#### release_resources

```python
release_resources(exp_id: str) -> dict
```

Release resources and return usage stats.

#### check_resource_limits

```python
check_resource_limits(exp_id: str) -> tuple[bool, str]
```

Check if experiment is within limits.

**Returns:** (within_limits, reason_string)

#### get_resource_usage

```python
get_resource_usage(exp_id: str) -> dict
```

Get current resource usage for experiment.

#### get_system_status

```python
get_system_status() -> dict
```

Get overall system resource status.
