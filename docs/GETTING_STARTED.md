# Getting Started with QUANTAURA-Core v0.4

## Installation

```bash
git clone https://github.com/perseverancesworld-web/QUANTAURA-Core.git
cd QUANTAURA-Core
pip install -e .
```

## Quick Start (5 minutes)

### 1. Define Your Experiments

```python
import asyncio
from quantaura.orchestration.orchestrator import ResearchOrchestrator

def experiment_a():
    """First experiment."""
    print("Running experiment A...")
    return {"result": "A_complete"}

def experiment_b():
    """Second experiment (depends on A)."""
    print("Running experiment B...")
    return {"result": "B_complete"}

def experiment_c(result_a, result_b):
    """Third experiment (depends on both)."""
    print(f"Running experiment C with {result_a} and {result_b}...")
    return {"result": "C_complete"}
```

### 2. Register and Execute

```python
async def main():
    # Create orchestrator
    orchestrator = ResearchOrchestrator(max_concurrent=2)
    
    # Register experiments
    a_id = orchestrator.register_experiment(
        name="Experiment A",
        task=experiment_a,
    )
    
    b_id = orchestrator.register_experiment(
        name="Experiment B",
        task=experiment_b,
    )
    
    c_id = orchestrator.register_experiment(
        name="Experiment C",
        task=lambda: experiment_c(
            experiment_a(),
            experiment_b()
        ),
        dependencies=[a_id, b_id],
    )
    
    # Execute the pipeline
    result = await orchestrator.execute()
    print(result)

# Run it
asyncio.run(main())
```

### 3. View Results

```python
result = await orchestrator.execute()
print(f"Success rate: {result['success_rate']*100:.1f}%")
print(f"Completed: {result['completed']}")
print(f"Failed: {result['failed']}")
```

## Working with Dependencies

### Sequential Pipeline

```
A → B → C → D
```

```python
b_id = orchestrator.register_experiment(
    name="B",
    task=task_b,
    dependencies=[a_id],
)
```

### Parallel with Join

```
  A \
      D
  B /
```

```python
a_id = orchestrator.register_experiment(name="A", task=task_a)
b_id = orchestrator.register_experiment(name="B", task=task_b)
d_id = orchestrator.register_experiment(
    name="D",
    task=task_d,
    dependencies=[a_id, b_id],  # Both must complete
)
```

### Fan-out Pattern

```
  A
 / | \
B  C  D
```

```python
a_id = orchestrator.register_experiment(name="A", task=task_a)
b_id = orchestrator.register_experiment(name="B", task=task_b, dependencies=[a_id])
c_id = orchestrator.register_experiment(name="C", task=task_c, dependencies=[a_id])
d_id = orchestrator.register_experiment(name="D", task=task_d, dependencies=[a_id])
```

## Resource Management

### Setting Resource Limits

```python
from quantaura.orchestration.resource_manager import ResourceConfig

config = ResourceConfig(
    max_memory_mb=1024,      # 1 GB
    max_cpu_percent=80.0,    # 80% CPU
    max_disk_usage_mb=5000,  # 5 GB disk
    timeout_seconds=3600,    # 1 hour
)

exp_id = orchestrator.register_experiment(
    name="Memory Intensive",
    task=my_task,
    resource_config=config,
)
```

### Monitoring Resources

```python
status = orchestrator.get_status()
resources = status["resources"]

print(f"Available memory: {resources['available_memory_mb']:.0f} MB")
print(f"CPU cores: {resources['cpu_cores']}")
print(f"Active experiments: {resources['active_experiments']}")
```

## Retry Strategies

### Exponential Backoff (Default)

```python
from quantaura.orchestration.retry_policy import RetryPolicy, RetryStrategy

policy = RetryPolicy(
    max_retries=3,
    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    initial_delay_seconds=1.0,
    backoff_multiplier=2.0,
)
# Delays: 1s, 2s, 4s
```

### Linear Backoff

```python
policy = RetryPolicy(
    max_retries=3,
    strategy=RetryStrategy.LINEAR_BACKOFF,
    initial_delay_seconds=2.0,
)
# Delays: 2s, 4s, 6s
```

### Fixed Delay

```python
policy = RetryPolicy(
    max_retries=5,
    strategy=RetryStrategy.FIXED_DELAY,
    initial_delay_seconds=5.0,
)
# Delays: 5s, 5s, 5s, 5s, 5s
```

### Immediate Retry

```python
policy = RetryPolicy(
    max_retries=2,
    strategy=RetryStrategy.IMMEDIATE,
)
# Delays: 0s, 0s
```

## Monitoring Execution

### Get Dashboard Data

```python
status = orchestrator.get_status()
dashboard = status["telemetry"]

print(f"Total events: {dashboard['event_bus_stats']['total_events']}")
print(f"Experiments completed: {dashboard['experiments']['completed']}")
print(f"Average duration: {dashboard['performance']['avg_duration_seconds']:.2f}s")
print(f"Recent events: {dashboard['recent_events'][:5]}")
```

### Event Bus Queries

```python
# Get recent events
recent = orchestrator.event_bus.get_history(limit=20)

# Get events for specific experiment
exp_events = orchestrator.event_bus.get_experiment_events(exp_id, limit=50)

# Get events of specific type
from quantaura.orchestration.event_bus import EventType
completed = orchestrator.event_bus.get_history(EventType.EXPERIMENT_COMPLETED)
```

## Pause and Resume

```python
# Pause a running experiment
orchestrator.pause_experiment(exp_id)

# Resume it later
orchestrator.resume_experiment(exp_id)
```

## Example: Real Workflow

See the examples directory for complete working implementations:

- `examples/fractal_experiment.py` - Fractal geometry with dependencies
- `examples/quant_pipeline.py` - Quantitative trading workflow
- `examples/resonance_simulation.py` - Physics simulation with parallel tasks

Run them:

```bash
python examples/fractal_experiment.py
python examples/quant_pipeline.py
python examples/resonance_simulation.py
```

## Troubleshooting

### Circular Dependency Error

**Error:** `ValueError: Circular dependency detected`

**Solution:** Check your experiment dependencies form a DAG (no cycles).

```python
# BAD: A → B → A (cycle)
a_id = orchestrator.register_experiment(name="A", task=task_a, dependencies=[b_id])
b_id = orchestrator.register_experiment(name="B", task=task_b, dependencies=[a_id])

# GOOD: A → B → C (linear)
a_id = orchestrator.register_experiment(name="A", task=task_a)
b_id = orchestrator.register_experiment(name="B", task=task_b, dependencies=[a_id])
c_id = orchestrator.register_experiment(name="C", task=task_c, dependencies=[b_id])
```

### Timeout Errors

**Error:** `asyncio.TimeoutError: Timeout after 3600s`

**Solution:** Increase `timeout_seconds` or optimize your task:

```python
orchestrator.register_experiment(
    name="Long Task",
    task=slow_function,
    timeout_seconds=7200,  # 2 hours instead of 1
)
```

### Resource Exhaustion

**Error:** `Insufficient memory`

**Solution:** Reduce `max_concurrent` to run fewer experiments in parallel, or increase `max_memory_mb`:

```python
orchestrator = ResearchOrchestrator(max_concurrent=2)  # Was 4

config = ResourceConfig(max_memory_mb=4096)  # Increase from 2048
```

## Next Steps

1. Run the examples to understand orchestration patterns
2. Read the API reference (`docs/API_REFERENCE.md`)
3. Check the architecture guide (`docs/ARCHITECTURE.md`)
4. Explore the development roadmap (`docs/ROADMAP.md`)
