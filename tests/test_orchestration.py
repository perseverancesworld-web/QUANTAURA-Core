"""Test suite for orchestration components."""

import pytest
import asyncio
from quantaura.orchestration.scheduler import (
    ExperimentScheduler,
    Experiment,
    ExperimentState,
    DependencyGraph,
)
from quantaura.orchestration.retry_policy import RetryPolicy, RetryStrategy
from quantaura.orchestration.resource_manager import ResourceManager, ResourceConfig
from quantaura.orchestration.experiment_validator import ExperimentValidator
from quantaura.orchestration.event_bus import EventBus, EventType, Event
from quantaura.orchestration.orchestrator import ResearchOrchestrator
from datetime import datetime


class TestDependencyGraph:
    """Test dependency graph operations."""
    
    def test_simple_linear_dependency(self):
        """Test A -> B -> C linear dependency."""
        graph = DependencyGraph()
        graph.add_experiment("A", [])
        graph.add_experiment("B", ["A"])
        graph.add_experiment("C", ["B"])
        
        order = graph.topological_sort()
        assert order == ["A", "B", "C"]
    
    def test_parallel_dependencies(self):
        """Test A -> B,C -> D (diamond)."""
        graph = DependencyGraph()
        graph.add_experiment("A", [])
        graph.add_experiment("B", ["A"])
        graph.add_experiment("C", ["A"])
        graph.add_experiment("D", ["B", "C"])
        
        order = graph.topological_sort()
        assert order[0] == "A"  # A first
        assert set(order[1:3]) == {"B", "C"}  # B and C in middle (any order)
        assert order[3] == "D"  # D last
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        graph = DependencyGraph()
        graph.add_experiment("A", ["B"])
        graph.add_experiment("B", ["A"])
        
        with pytest.raises(ValueError, match="Circular dependency"):
            graph.topological_sort()
    
    def test_get_ready_experiments(self):
        """Test getting experiments ready for execution."""
        graph = DependencyGraph()
        graph.add_experiment("A", [])
        graph.add_experiment("B", ["A"])
        graph.add_experiment("C", ["A"])
        
        # Initially only A is ready
        ready = graph.get_ready_experiments(set())
        assert ready == ["A"]
        
        # After A completes, B and C are ready
        ready = graph.get_ready_experiments({"A"})
        assert set(ready) == {"B", "C"}
        
        # After all complete, nothing is ready
        ready = graph.get_ready_experiments({"A", "B", "C"})
        assert ready == []


class TestRetryPolicy:
    """Test retry policy logic."""
    
    def test_exponential_backoff(self):
        """Test exponential backoff delays."""
        policy = RetryPolicy(
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            initial_delay_seconds=1.0,
            backoff_multiplier=2.0,
        )
        
        assert policy.get_delay(0) == 1.0
        assert policy.get_delay(1) == 2.0
        assert policy.get_delay(2) == 4.0
        assert policy.get_delay(3) == 8.0
    
    def test_linear_backoff(self):
        """Test linear backoff delays."""
        policy = RetryPolicy(
            max_retries=3,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            initial_delay_seconds=2.0,
        )
        
        assert policy.get_delay(0) == 2.0
        assert policy.get_delay(1) == 4.0
        assert policy.get_delay(2) == 6.0
    
    def test_should_retry(self):
        """Test retry decision logic."""
        policy = RetryPolicy(max_retries=3)
        
        # Should retry on first two attempts
        assert policy.should_retry(Exception("test"), 0)
        assert policy.should_retry(Exception("test"), 1)
        assert policy.should_retry(Exception("test"), 2)
        
        # Should not retry on attempt 3 (max reached)
        assert not policy.should_retry(Exception("test"), 3)
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Test successful execution with retry."""
        call_count = 0
        
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("First call fails")
            return "success"
        
        policy = RetryPolicy(max_retries=3)
        result = await policy.execute_with_retry(flaky_func)
        
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_exhausted(self):
        """Test retry exhaustion."""
        async def always_fails():
            raise ValueError("Always fails")
        
        policy = RetryPolicy(max_retries=2)
        
        with pytest.raises(ValueError, match="Always fails"):
            await policy.execute_with_retry(always_fails)


class TestResourceManager:
    """Test resource management."""
    
    def test_resource_allocation(self):
        """Test resource allocation."""
        manager = ResourceManager()
        config = ResourceConfig(max_memory_mb=512)
        
        success = manager.allocate_resources("exp1", config)
        assert success
        
        # Should have allocation recorded
        usage = manager.get_resource_usage("exp1")
        assert usage["config"]["max_memory_mb"] == 512
    
    def test_resource_release(self):
        """Test resource release."""
        manager = ResourceManager()
        manager.allocate_resources("exp1")
        
        stats = manager.release_resources("exp1")
        assert "peak_memory_mb" in stats
        assert "peak_cpu_percent" in stats
        
        # Should no longer have allocation
        assert manager.get_resource_usage("exp1") == {}
    
    def test_system_status(self):
        """Test system status query."""
        manager = ResourceManager()
        manager.allocate_resources("exp1")
        manager.allocate_resources("exp2")
        
        status = manager.get_system_status()
        assert status["active_experiments"] == 2
        assert status["available_memory_mb"] > 0
        assert status["cpu_cores"] > 0


class TestExperimentValidator:
    """Test experiment validation."""
    
    def test_valid_experiment(self):
        """Test validation of valid experiment."""
        validator = ExperimentValidator()
        
        config = {
            "name": "Valid Experiment",
            "task": lambda: None,
        }
        
        errors = validator.validate_experiment(config)
        assert len(errors) == 0
    
    def test_missing_required_field(self):
        """Test validation with missing required field."""
        validator = ExperimentValidator()
        
        config = {
            "task": lambda: None,
            # name is missing
        }
        
        errors = validator.validate_experiment(config)
        assert len(errors) > 0
        assert any(e.field == "name" for e in errors)
    
    def test_invalid_timeout(self):
        """Test validation of invalid timeout."""
        validator = ExperimentValidator()
        
        config = {
            "name": "Test",
            "task": lambda: None,
            "timeout_seconds": -10,  # Invalid
        }
        
        errors = validator.validate_experiment(config)
        assert len(errors) > 0
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection in graphs."""
        validator = ExperimentValidator()
        
        experiments = {
            "A": {"name": "A", "dependencies": ["B"]},
            "B": {"name": "B", "dependencies": ["A"]},
        }
        
        errors = validator.validate_dependency_graph(experiments)
        assert len(errors) > 0
        assert any("circular" in e.message.lower() for e in errors)


class TestEventBus:
    """Test event bus functionality."""
    
    def test_event_subscription(self):
        """Test event subscription and emission."""
        bus = EventBus()
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        bus.subscribe(EventType.EXPERIMENT_COMPLETED, handler)
        
        event = Event(
            type=EventType.EXPERIMENT_COMPLETED,
            source="test",
            timestamp=datetime.utcnow(),
            experiment_id="exp1",
            data={},
        )
        bus.emit(event)
        
        assert len(received_events) == 1
        assert received_events[0] == event
    
    def test_event_history(self):
        """Test event history tracking."""
        bus = EventBus()
        
        for i in range(5):
            event = Event(
                type=EventType.EXPERIMENT_STARTED,
                source="test",
                timestamp=datetime.utcnow(),
                experiment_id=f"exp{i}",
                data={},
            )
            bus.emit(event)
        
        history = bus.get_history(limit=10)
        assert len(history) == 5
    
    def test_event_bus_stats(self):
        """Test event bus statistics."""
        bus = EventBus()
        
        for i in range(3):
            bus.emit(Event(
                type=EventType.EXPERIMENT_STARTED,
                source="test",
                timestamp=datetime.utcnow(),
                data={},
            ))
            bus.emit(Event(
                type=EventType.EXPERIMENT_COMPLETED,
                source="test",
                timestamp=datetime.utcnow(),
                data={},
            ))
        
        stats = bus.get_stats()
        assert stats["total_events"] == 6
        assert stats["unique_event_types"] == 2


class TestOrchestrator:
    """Test ResearchOrchestrator integration."""
    
    @pytest.mark.asyncio
    async def test_simple_execution(self):
        """Test simple experiment execution."""
        orchestrator = ResearchOrchestrator(max_concurrent=2)
        results = []
        
        def task():
            results.append("executed")
            return "done"
        
        exp_id = orchestrator.register_experiment(
            name="Simple",
            task=task,
        )
        
        result = await orchestrator.execute()
        
        assert result["total_experiments"] == 1
        assert result["completed"] == 1
        assert result["failed"] == 0
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_dependent_experiments(self):
        """Test dependent experiment execution."""
        orchestrator = ResearchOrchestrator(max_concurrent=2)
        execution_order = []
        
        def task_a():
            execution_order.append("A")
            return "A_result"
        
        def task_b():
            execution_order.append("B")
            return "B_result"
        
        a_id = orchestrator.register_experiment(name="A", task=task_a)
        b_id = orchestrator.register_experiment(
            name="B",
            task=task_b,
            dependencies=[a_id],
        )
        
        result = await orchestrator.execute()
        
        assert result["completed"] == 2
        assert execution_order[0] == "A"
        assert execution_order[1] == "B"
    
    def test_get_status(self):
        """Test status retrieval."""
        orchestrator = ResearchOrchestrator()
        
        orchestrator.register_experiment(
            name="Test",
            task=lambda: None,
        )
        
        status = orchestrator.get_status()
        
        assert "scheduler" in status
        assert "resources" in status
        assert "telemetry" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
