"""Experiment Scheduler - orchestrates experiment execution with dependency resolution."""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ExperimentState(str, Enum):
    """State machine for experiments."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Experiment:
    """Experiment definition and execution state."""
    name: str
    task: Callable
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    timeout_seconds: int = 3600
    retries: int = 3
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: ExperimentState = ExperimentState.PENDING
    result: Optional[any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Experiment):
            return self.id == other.id
        return False


class DependencyGraph:
    """Manages experiment dependency resolution and topological sorting."""
    
    def __init__(self):
        self.graph: Dict[str, Set[str]] = {}
        self.in_degree: Dict[str, int] = {}
    
    def add_experiment(self, exp_id: str, dependencies: List[str]):
        """Register experiment with its dependencies."""
        if exp_id not in self.graph:
            self.graph[exp_id] = set()
            self.in_degree[exp_id] = 0
        
        for dep in dependencies:
            if dep not in self.graph:
                self.graph[dep] = set()
                self.in_degree[dep] = 0
            
            self.graph[dep].add(exp_id)
            self.in_degree[exp_id] += 1
    
    def topological_sort(self) -> List[str]:
        """Return experiments in execution order (Kahn's algorithm)."""
        in_degree = self.in_degree.copy()
        queue = [exp_id for exp_id in in_degree if in_degree[exp_id] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for dependent in self.graph.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        if len(result) != len(self.graph):
            raise ValueError("Circular dependency detected in experiment graph")
        
        return result
    
    def get_ready_experiments(self, completed: Set[str]) -> List[str]:
        """Return experiments whose dependencies are satisfied."""
        ready = []
        for exp_id, deps in self.graph.items():
            if exp_id not in completed and all(dep in completed for dep in deps):
                ready.append(exp_id)
        return ready


class ExperimentScheduler:
    """Schedules and orchestrates experiment execution with dependency resolution."""
    
    def __init__(self, max_concurrent: int = 4):
        self.max_concurrent = max_concurrent
        self.experiments: Dict[str, Experiment] = {}
        self.dependency_graph = DependencyGraph()
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Set[asyncio.Task] = set()
        self.paused_experiments: Set[str] = set()
        self.event_handlers: List[Callable] = []
    
    def register_experiment(self, experiment: Experiment) -> str:
        """Register experiment in scheduler."""
        self.experiments[experiment.id] = experiment
        self.dependency_graph.add_experiment(experiment.id, experiment.dependencies)
        logger.info(f"Registered experiment: {experiment.name} ({experiment.id})")
        return experiment.id
    
    def register_event_handler(self, handler: Callable):
        """Register handler for experiment state changes."""
        self.event_handlers.append(handler)
    
    async def _emit_event(self, exp_id: str, event_type: str, data: dict = None):
        """Emit event to all registered handlers."""
        event_data = {
            "experiment_id": exp_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        for handler in self.event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    async def _execute_experiment(self, exp_id: str):
        """Execute a single experiment with error handling."""
        experiment = self.experiments[exp_id]
        
        try:
            experiment.state = ExperimentState.RUNNING
            experiment.started_at = datetime.utcnow()
            await self._emit_event(exp_id, "started", {"name": experiment.name})
            logger.info(f"Starting experiment: {experiment.name}")
            
            # Execute with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(experiment.task),
                timeout=experiment.timeout_seconds
            )
            
            experiment.result = result
            experiment.state = ExperimentState.COMPLETED
            experiment.completed_at = datetime.utcnow()
            await self._emit_event(exp_id, "completed", {"result": str(result)[:200]})
            logger.info(f"Completed experiment: {experiment.name}")
            
        except asyncio.TimeoutError:
            experiment.error = f"Timeout after {experiment.timeout_seconds}s"
            experiment.state = ExperimentState.FAILED
            experiment.completed_at = datetime.utcnow()
            await self._emit_event(exp_id, "failed", {"error": experiment.error})
            logger.error(f"Timeout in experiment {experiment.name}: {experiment.error}")
            
        except Exception as e:
            experiment.error = str(e)
            experiment.state = ExperimentState.FAILED
            experiment.completed_at = datetime.utcnow()
            await self._emit_event(exp_id, "failed", {"error": experiment.error})
            logger.error(f"Error in experiment {experiment.name}: {e}", exc_info=True)
    
    async def run(self):
        """Main scheduler loop - manages concurrent execution and dependencies."""
        logger.info(f"Scheduler started with max_concurrent={self.max_concurrent}")
        completed = set()
        
        try:
            while len(completed) < len(self.experiments):
                # Get ready experiments (dependencies satisfied)
                ready = self.dependency_graph.get_ready_experiments(completed)
                ready = [e for e in ready if self.experiments[e].state == ExperimentState.PENDING]
                
                # Queue ready experiments up to concurrency limit
                available_slots = self.max_concurrent - len(self.active_tasks)
                for exp_id in ready[:available_slots]:
                    if exp_id not in self.paused_experiments:
                        self.experiments[exp_id].state = ExperimentState.QUEUED
                        task = asyncio.create_task(self._execute_experiment(exp_id))
                        self.active_tasks.add(task)
                        task.add_done_callback(self.active_tasks.discard)
                
                # Wait for at least one task to complete
                if self.active_tasks:
                    done, _ = await asyncio.wait(
                        self.active_tasks,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in done:
                        try:
                            await task
                        except Exception:
                            pass
                    
                    # Mark completed experiments
                    for exp_id, exp in self.experiments.items():
                        if exp.state == ExperimentState.COMPLETED and exp_id not in completed:
                            completed.add(exp_id)
                else:
                    await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            raise
        
        logger.info(f"Scheduler completed: {len(completed)}/{len(self.experiments)} experiments")
    
    def pause_experiment(self, exp_id: str):
        """Pause a running experiment."""
        if exp_id in self.experiments:
            self.paused_experiments.add(exp_id)
            self.experiments[exp_id].state = ExperimentState.PAUSED
            logger.info(f"Paused experiment: {exp_id}")
    
    def resume_experiment(self, exp_id: str):
        """Resume a paused experiment."""
        if exp_id in self.paused_experiments:
            self.paused_experiments.remove(exp_id)
            self.experiments[exp_id].state = ExperimentState.PENDING
            logger.info(f"Resumed experiment: {exp_id}")
    
    def get_status(self) -> Dict:
        """Get current scheduler status."""
        states = {}
        for exp_id, exp in self.experiments.items():
            states[exp.name] = {
                "id": exp_id,
                "state": exp.state.value,
                "priority": exp.priority,
                "created_at": exp.created_at.isoformat(),
                "started_at": exp.started_at.isoformat() if exp.started_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
                "error": exp.error,
            }
        return {
            "total": len(self.experiments),
            "active": len(self.active_tasks),
            "max_concurrent": self.max_concurrent,
            "experiments": states
        }
