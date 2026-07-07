"""Experimental orchestration - integration of all components."""

import asyncio
import logging
from typing import List, Optional, Callable
from quantaura.orchestration.scheduler import ExperimentScheduler, Experiment
from quantaura.orchestration.retry_policy import RetryPolicy
from quantaura.orchestration.resource_manager import ResourceManager, ResourceConfig
from quantaura.orchestration.experiment_validator import ExperimentValidator
from quantaura.orchestration.event_bus import EventBus, Event, EventType
from quantaura.orchestration.telemetry import TelemetryCollector, DashboardDataProvider

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    """Unified orchestration system for research experiments.
    
    Coordinates scheduling, resource management, validation, retry policies,
    and real-time telemetry for complex experiment pipelines.
    """
    
    def __init__(self, max_concurrent: int = 4):
        self.scheduler = ExperimentScheduler(max_concurrent=max_concurrent)
        self.resource_manager = ResourceManager()
        self.validator = ExperimentValidator()
        self.event_bus = EventBus()
        self.telemetry_collector = TelemetryCollector(self.event_bus)
        self.dashboard_provider = DashboardDataProvider(self.event_bus, self.telemetry_collector)
        self.retry_policies: dict = {}
        
        # Wire up event handlers
        self.scheduler.register_event_handler(self._on_scheduler_event)
        
        logger.info(f"ResearchOrchestrator initialized (max_concurrent={max_concurrent})")
    
    def register_experiment(
        self,
        name: str,
        task: Callable,
        dependencies: Optional[List[str]] = None,
        priority: int = 0,
        timeout_seconds: int = 3600,
        retries: int = 3,
        resource_config: Optional[ResourceConfig] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ) -> str:
        """Register experiment in the orchestration system.
        
        Args:
            name: Experiment name
            task: Callable to execute
            dependencies: List of experiment IDs this depends on
            priority: Execution priority (-100 to 100)
            timeout_seconds: Max execution time
            retries: Max retry attempts
            resource_config: Resource allocation config
            retry_policy: Custom retry policy
        
        Returns:
            Experiment ID
        """
        # Validate experiment config
        config = {
            "name": name,
            "task": task,
            "dependencies": dependencies or [],
            "priority": priority,
            "timeout_seconds": timeout_seconds,
            "retries": retries,
        }
        
        errors = self.validator.validate_experiment(config)
        if errors:
            logger.error(f"Validation errors for {name}:\n{self.validator.format_errors(errors)}")
            raise ValueError(f"Invalid experiment configuration: {errors}")
        
        # Create experiment
        experiment = Experiment(
            name=name,
            task=task,
            dependencies=dependencies or [],
            priority=priority,
            timeout_seconds=timeout_seconds,
            retries=retries,
        )
        
        # Register in scheduler
        exp_id = self.scheduler.register_experiment(experiment)
        
        # Allocate resources
        res_config = resource_config or ResourceConfig()
        if not self.resource_manager.allocate_resources(exp_id, res_config):
            logger.warning(f"Failed to allocate resources for {exp_id}")
        
        # Store retry policy
        if retry_policy:
            self.retry_policies[exp_id] = retry_policy
        
        # Emit registration event
        event = Event(
            type=EventType.EXPERIMENT_REGISTERED,
            source="orchestrator",
            timestamp=__import__("datetime").datetime.utcnow(),
            experiment_id=exp_id,
            data={"name": name, "dependencies": dependencies or []}
        )
        self.event_bus.emit(event)
        
        return exp_id
    
    async def _on_scheduler_event(self, event_data: dict):
        """Handle events from scheduler."""
        exp_id = event_data.get("experiment_id")
        event_type_str = event_data.get("event_type", "unknown")
        
        # Map scheduler events to EventBus events
        event_type_map = {
            "started": EventType.EXPERIMENT_STARTED,
            "completed": EventType.EXPERIMENT_COMPLETED,
            "failed": EventType.EXPERIMENT_FAILED,
            "paused": EventType.EXPERIMENT_PAUSED,
        }
        
        event_type = event_type_map.get(event_type_str)
        if event_type:
            event = Event(
                type=event_type,
                source="scheduler",
                timestamp=__import__("datetime").datetime.fromisoformat(
                    event_data.get("timestamp", __import__("datetime").datetime.utcnow().isoformat())
                ),
                experiment_id=exp_id,
                data=event_data.get("data", {})
            )
            await self.event_bus.emit_async(event)
    
    async def execute(self) -> dict:
        """Execute all registered experiments.
        
        Returns:
            Summary of execution results
        """
        try:
            logger.info("Starting experiment execution")
            event = Event(
                type=EventType.SCHEDULER_STARTED,
                source="orchestrator",
                timestamp=__import__("datetime").datetime.utcnow(),
                data={"experiment_count": len(self.scheduler.experiments)}
            )
            self.event_bus.emit(event)
            
            # Run scheduler
            await self.scheduler.run()
            
            event = Event(
                type=EventType.SCHEDULER_COMPLETED,
                source="orchestrator",
                timestamp=__import__("datetime").datetime.utcnow(),
                data=self.scheduler.get_status()
            )
            self.event_bus.emit(event)
            
            # Release resources
            for exp_id in self.scheduler.experiments:
                self.resource_manager.release_resources(exp_id)
            
            return self.get_execution_summary()
        
        except Exception as e:
            logger.error(f"Orchestration error: {e}", exc_info=True)
            event = Event(
                type=EventType.SCHEDULER_ERROR,
                source="orchestrator",
                timestamp=__import__("datetime").datetime.utcnow(),
                data={"error": str(e)}
            )
            self.event_bus.emit(event)
            raise
    
    def pause_experiment(self, exp_id: str):
        """Pause a running experiment."""
        self.scheduler.pause_experiment(exp_id)
        event = Event(
            type=EventType.EXPERIMENT_PAUSED,
            source="orchestrator",
            timestamp=__import__("datetime").datetime.utcnow(),
            experiment_id=exp_id,
            data={}
        )
        self.event_bus.emit(event)
    
    def resume_experiment(self, exp_id: str):
        """Resume a paused experiment."""
        self.scheduler.resume_experiment(exp_id)
        event = Event(
            type=EventType.EXPERIMENT_RESUMED,
            source="orchestrator",
            timestamp=__import__("datetime").datetime.utcnow(),
            experiment_id=exp_id,
            data={}
        )
        self.event_bus.emit(event)
    
    def get_status(self) -> dict:
        """Get orchestration status."""
        return {
            "scheduler": self.scheduler.get_status(),
            "resources": self.resource_manager.get_system_status(),
            "telemetry": self.dashboard_provider.get_dashboard_data(),
        }
    
    def get_execution_summary(self) -> dict:
        """Get summary of execution results."""
        status = self.scheduler.get_status()
        experiments = status["experiments"]
        
        completed = sum(1 for e in experiments.values() if e["state"] == "completed")
        failed = sum(1 for e in experiments.values() if e["state"] == "failed")
        
        return {
            "total_experiments": len(experiments),
            "completed": completed,
            "failed": failed,
            "success_rate": completed / len(experiments) if experiments else 0,
            "experiments": experiments,
            "dashboard_data": self.dashboard_provider.get_dashboard_data(),
        }
