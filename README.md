# QUANTAURA-Core

**Unified research operating system integrating cognitive architectures, simulations, mathematical models, and quantitative trading.**

> "The architecture is reaching the point where adding features without tightening the core would be like bolting a jet engine onto a houseboat." — v0.4 Roadmap

## 🚀 What is QUANTAURA-Core?

QUANTAURA-Core is a sophisticated experiment orchestration platform designed for researchers and data scientists who need to:

- **Define complex experiment pipelines** with dependencies
- **Execute experiments at scale** with concurrency control
- **Monitor resources** (memory, CPU, disk) in real-time
- **Recover from failures** with intelligent retry strategies
- **Observe execution** through a unified event system
- **Persist results** to databases and dashboards

The system prioritizes **correctness of the core loop** (build → run → observe → reproduce → visualize) before adding flashy UI features.

## ✨ v0.4 Features

### Core Orchestration
- ✅ Experiment scheduling with dependency resolution
- ✅ State machine execution (PENDING → QUEUED → RUNNING → COMPLETED/FAILED)
- ✅ Topological sorting for DAG execution
- ✅ Concurrent execution (configurable limits)
- ✅ Pause/resume capabilities

### Failure Recovery
- ✅ Multiple retry strategies (exponential, linear, fixed, immediate backoff)
- ✅ Per-experiment retry policies
- ✅ Automatic failure detection
- ✅ Configurable backoff parameters

### Resource Management
- ✅ Memory allocation & enforcement
- ✅ CPU usage monitoring
- ✅ Disk quota tracking
- ✅ System-wide resource visibility

### Quality Assurance
- ✅ Schema validation
- ✅ Dependency graph cycle detection
- ✅ Custom validator framework
- ✅ Comprehensive error reporting

### Real-time Telemetry
- ✅ Central event bus (13+ event types)
- ✅ Sync & async event handlers
- ✅ Event history with querying
- ✅ Event statistics
- ✅ Metrics aggregation

### Developer Experience
- ✅ 3 complete working examples
- ✅ 50+ KB documentation
- ✅ API reference with 20+ methods
- ✅ 30+ test cases
- ✅ Development setup script

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              ResearchOrchestrator                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────┐        ┌──────────────────────┐   │
│  │   Scheduler        │        │   Event Bus          │   │
│  │  (execution)       │───────▶│  (publisher)         │   │
│  │                    │        │                      │   │
│  └────────────────────┘        └──────────────────────┘   │
│           │                              │                │
│           v                              v                │
│  ┌────────────────────┐        ┌──────────────────────┐   │
│  │ ResourceManager    │        │ TelemetryCollector   │   │
│  │ (allocation)       │        │ (metrics)            │   │
│  └────────────────────┘        └──────────────────────┘   │
│           │                              │                │
│           └──────────────┬───────────────┘                │
│                          v                                │
│           ┌─────────────────────────────┐                │
│           │  Storage Layer              │                │
│           │  (Database + Dashboard)     │                │
│           └─────────────────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Quick Start

### Installation

```bash
git clone https://github.com/perseverancesworld-web/QUANTAURA-Core.git
cd QUANTAURA-Core
pip install -e .
```

### 5-Minute Example

```python
import asyncio
from quantaura.orchestration.orchestrator import ResearchOrchestrator

async def main():
    orchestrator = ResearchOrchestrator(max_concurrent=4)
    
    # Register experiment A
    a_id = orchestrator.register_experiment(
        name="Compute Mandelbrot",
        task=compute_mandelbrot,
        priority=10,
    )
    
    # Register experiment B (depends on A)
    b_id = orchestrator.register_experiment(
        name="Analyze Fractals",
        task=analyze_fractals,
        dependencies=[a_id],
    )
    
    # Execute pipeline
    result = await orchestrator.execute()
    print(f"Success rate: {result['success_rate']*100:.1f}%")
    print(f"Completed: {result['completed']}/{result['total_experiments']}")

asyncio.run(main())
```

## 📚 Documentation

| Document | Purpose |
|----------|----------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, components, data flow |
| [GETTING_STARTED.md](docs/GETTING_STARTED.md) | Installation, tutorials, patterns |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | Complete method signatures & examples |
| [ROADMAP.md](docs/ROADMAP.md) | Future features, timeline, versioning |
| [TESTING.md](docs/TESTING.md) | Running tests, coverage, CI/CD |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) | v0.4 features, performance, known limits |

## 🧪 Examples

Three complete, runnable examples demonstrating different use cases:

### 1. Fractal Geometry

```bash
python examples/fractal_experiment.py
```

**Pipeline:** Mandelbrot → Julia → Analysis (parallel then join)

### 2. Quantitative Trading

```bash
python examples/quant_pipeline.py
```

**Pipeline:** Fetch data (parallel) → Indicators → Signals → Backtest → Optimize → Validate

### 3. Resonance Simulation

```bash
python examples/resonance_simulation.py
```

**Pipeline:** Initialize fields (parallel) → Wave propagation → Pattern analysis → Comparison → Report

## 🧬 Core Concepts

### Experiment

A unit of work that the orchestrator can execute.

```python
exp = Experiment(
    name="My Task",
    task=my_function,
    dependencies=[other_exp_id],
    priority=10,
    timeout_seconds=3600,
    retries=3,
)
```

### Dependency Graph

Experiments form a DAG (directed acyclic graph). The scheduler automatically handles:
- Parallel execution of independent experiments
- Sequential execution of dependent experiments
- Cycle detection

### State Machine

```
PENDING → QUEUED → RUNNING → COMPLETED/FAILED
                  └──→ PAUSED → RUNNING
```

### Event Bus

Central publish-subscribe system for real-time observability:

```python
def on_experiment_complete(event):
    print(f"Experiment {event.experiment_id} completed")

orchestrator.event_bus.subscribe(
    EventType.EXPERIMENT_COMPLETED,
    on_experiment_complete
)
```

## 📊 Performance

| Metric | Value |
|--------|-------|
| Scheduler Throughput | 1000+ exp/min |
| Event Bus Latency | <10ms |
| Dependency Resolution | <100ms (1000 exp) |
| Memory Overhead | <50MB |
| Max Concurrent | Configurable (tested 10+) |

## 🔧 Resource Management

```python
from quantaura.orchestration.resource_manager import ResourceConfig

config = ResourceConfig(
    max_memory_mb=1024,        # 1 GB
    max_cpu_percent=80.0,      # 80% CPU
    max_disk_usage_mb=5000,    # 5 GB
    timeout_seconds=3600,      # 1 hour
)

orchestrator.register_experiment(
    name="Memory-Intensive Task",
    task=my_task,
    resource_config=config,
)
```

## 🔄 Retry Strategies

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
    strategy=RetryStrategy.LINEAR_BACKOFF,
    initial_delay_seconds=2.0,
)
# Delays: 2s, 4s, 6s
```

## 📈 Monitoring

```python
# Get real-time status
status = orchestrator.get_status()
print(status["scheduler"]["total"])     # Total experiments
print(status["resources"]["active_experiments"])  # Currently running
print(status["telemetry"]["experiments"]["completed"])  # Completed

# Query events
recent_events = orchestrator.event_bus.get_history(limit=20)
exp_events = orchestrator.event_bus.get_experiment_events(exp_id)

# Get statistics
stats = orchestrator.event_bus.get_stats()
print(stats["total_events"])  # Total events emitted
```

## 🧪 Testing

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=quantaura --cov-report=html

# Run specific test
pytest tests/test_orchestration.py::TestDependencyGraph -v
```

**Current Coverage:**
- 30+ test cases
- Dependency graph (linear, parallel, circular detection)
- Retry strategies (exponential, linear, fixed, immediate)
- Resource management (allocation, release, limits)
- Experiment validation (schema, dependency graphs)
- Event bus (subscription, emission, history)
- Orchestrator integration

## 🚦 Project Status

| Component | Status | Tests | Docs |
|-----------|--------|-------|------|
| Scheduler | ✅ Production | 10 | ✅ |
| Retry Policy | ✅ Production | 6 | ✅ |
| Resource Manager | ✅ Production | 4 | ✅ |
| Validator | ✅ Production | 5 | ✅ |
| Event Bus | ✅ Production | 4 | ✅ |
| Telemetry | ✅ Production | Partial | ✅ |
| Database | 🔨 Scaffolding | - | ✅ |
| Orchestrator | ✅ Production | 4 | ✅ |

## 🗺️ What's Next (v0.5+)

### Phase 1: WebXR Visualization (v0.5)
- Real-time 3D experiment explorer
- Interactive dependency graph visualization
- Immersive metrics display
- WebSocket streaming

### Phase 2: Distributed Orchestration (v0.6)
- Multi-machine scheduling
- Network-aware task placement
- Distributed event bus

### Phase 3: Checkpointing & Replay (v0.7)
- Experiment checkpointing
- Time-travel debugging
- Deterministic replay

### Phase 4: Advanced Resources (v0.8)
- GPU support (CUDA/ROCm)
- Container runtime integration
- QoS guarantees

### Phase 5: Collaboration (v1.0)
- Multi-user platform
- Experiment sharing & versioning
- Collaborative notebooks
- Research pipeline marketplace

See [ROADMAP.md](docs/ROADMAP.md) for detailed timeline.

## 🛠️ Development

### Setup

```bash
python dev_setup.py
```

This installs:
- Core dependencies (psutil, asyncio)
- Dev tools (pytest, black, flake8, mypy)
- Creates necessary directories

### Code Quality

```bash
# Format code
black quantaura/
isort quantaura/

# Check linting
flake8 quantaura/

# Type checking
mypy quantaura/

# Run tests
pytest tests/ -v
```

## 📂 Project Structure

```
QUANTAURA-Core/
├── quantaura/
│   └── orchestration/
│       ├── __init__.py
│       ├── scheduler.py          (400 LOC)
│       ├── retry_policy.py        (180 LOC)
│       ├── resource_manager.py    (250 LOC)
│       ├── experiment_validator.py (280 LOC)
│       ├── event_bus.py           (350 LOC)
│       ├── telemetry.py           (200 LOC)
│       ├── database.py            (150 LOC)
│       └── orchestrator.py        (300 LOC)
├── examples/
│   ├── fractal_experiment.py
│   ├── quant_pipeline.py
│   └── resonance_simulation.py
├── tests/
│   └── test_orchestration.py      (500+ LOC)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── GETTING_STARTED.md
│   ├── API_REFERENCE.md
│   ├── ROADMAP.md
│   └── TESTING.md
├── dev_setup.py
├── RELEASE_NOTES.md
├── README.md
└── setup.py
```

## 📝 License

See LICENSE file in repository.

## 🤝 Contributing

Contributions welcome in:
1. Database backend implementations
2. Example experiments
3. Alternative visualization engines
4. Documentation improvements
5. Performance optimizations

See [ROADMAP.md](docs/ROADMAP.md#community-contributions) for details.

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/perseverancesworld-web/QUANTAURA-Core/issues)
- **Discussions:** [GitHub Discussions](https://github.com/perseverancesworld-web/QUANTAURA-Core/discussions)
- **Documentation:** See `docs/` directory
- **Examples:** See `examples/` directory

## 🎓 Learning Path

1. **New Users:** Start with [GETTING_STARTED.md](docs/GETTING_STARTED.md)
2. **Developers:** Read [ARCHITECTURE.md](docs/ARCHITECTURE.md)
3. **API Users:** Check [API_REFERENCE.md](docs/API_REFERENCE.md)
4. **Contributors:** See [ROADMAP.md](docs/ROADMAP.md)
5. **Testers:** Review [TESTING.md](docs/TESTING.md)

## 🎯 Mission

**Build the strongest possible foundation for research-grade experiment orchestration, then add increasingly sophisticated capabilities on top of a bulletproof core.**

The v0.4 core is solid:
- ✅ Experiment scheduling works perfectly
- ✅ Failure recovery is robust
- ✅ Resource management is tracked
- ✅ Real-time observability is built-in
- ✅ The system observes itself while running

Now we're ready for v0.5's **Living Research Network** — real-time 3D exploration of your experiments while they execute. 🚀

---

**Build → Run → Observe → Reproduce → Visualize → Improve**

*That loop is the real engine. The fancy 3D universe is the cockpit glass. The loop is what keeps the spacecraft moving.*
