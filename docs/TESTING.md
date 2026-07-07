# Testing Guide - QUANTAURA-Core

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_orchestration.py -v
```

### Run Specific Test

```bash
pytest tests/test_orchestration.py::TestDependencyGraph::test_simple_linear_dependency -v
```

### Run with Coverage

```bash
pytest tests/ --cov=quantaura --cov-report=html
```

## Test Structure

```
tests/
├── test_orchestration.py       # Core orchestration tests
├── test_scheduler.py           # Scheduler-specific tests (future)
├── test_telemetry.py           # Telemetry collection tests (future)
├── integration/                # Integration tests (future)
│   └── test_full_pipeline.py
└── fixtures/                   # Test data and helpers (future)
    └── conftest.py
```

## Test Coverage

### Current (v0.4)

- `DependencyGraph`: Linear, parallel, circular dependency detection
- `RetryPolicy`: Backoff strategies, retry decision logic, async execution
- `ResourceManager`: Allocation, release, system status
- `ExperimentValidator`: Schema validation, dependency graph validation
- `EventBus`: Subscription, emission, history, statistics
- `ResearchOrchestrator`: Simple execution, dependent experiments, status

### Target Coverage

- Scheduler: 90%+
- Orchestrator: 85%+
- Event Bus: 95%+
- Telemetry: 80%+
- Overall: 85%+

## Writing Tests

### Async Test Example

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    orchestrator = ResearchOrchestrator()
    result = await orchestrator.execute()
    assert result["completed"] > 0
```

### Fixture Example

```python
@pytest.fixture
def orchestrator():
    return ResearchOrchestrator(max_concurrent=2)

def test_with_fixture(orchestrator):
    exp_id = orchestrator.register_experiment(
        name="Test",
        task=lambda: None,
    )
    assert exp_id is not None
```

## Performance Tests

### Run Performance Benchmarks

```bash
pytest tests/test_performance.py -v
```

### Expected Performance

- Scheduler throughput: 1000+ exp/min
- Event bus latency: <10ms
- Memory overhead: <50MB

## Continuous Integration

### GitHub Actions Setup

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -e .[dev]
      - run: pytest tests/ --cov
```

## Code Quality

### Format Code

```bash
black quantaura/
isort quantaura/
```

### Check Linting

```bash
flake8 quantaura/ --max-line-length=100
```

### Type Checking

```bash
mypy quantaura/
```

### Pre-commit Hook

```bash
# Create .git/hooks/pre-commit
#!/bin/bash
black quantaura/
isort quantaura/
flake8 quantaura/
pytest tests/ -x
```

## Debugging Tests

### Verbose Output

```bash
pytest tests/ -vv --tb=long
```

### Drop into Debugger

```python
def test_something():
    orchestrator = ResearchOrchestrator()
    breakpoint()  # Drops to pdb
    # Continue testing
```

### Print Statements

```bash
pytest tests/ -s  # Show print output
```

## Troubleshooting

### ImportError

```bash
# Make sure package is installed in dev mode
pip install -e .
```

### Async Test Errors

```bash
# Make sure pytest-asyncio is installed
pip install pytest-asyncio
```

### Resource Warnings

Set environment variable:

```bash
export PYTHONWARNINGS=always
```

## Adding New Tests

1. Create test file in `tests/`
2. Follow naming convention: `test_*.py`
3. Use descriptive test names: `test_<feature>_<scenario>`
4. Add docstrings explaining what is tested
5. Run locally before submitting PR

```python
class TestNewFeature:
    """Test the new feature."""
    
    def test_basic_functionality(self):
        """Test that basic functionality works."""
        # Arrange
        component = NewComponent()
        
        # Act
        result = component.do_something()
        
        # Assert
        assert result is not None
```

## Test Data

For integration tests with real data, use `tests/fixtures/` directory:

```python
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_with_fixture_data():
    data = (FIXTURES_DIR / "sample_data.json").read_text()
    # Use data in test
```
