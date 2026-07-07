"""Telemetry and database integration for real-time observation."""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from quantaura.orchestration.event_bus import Event, EventType, EventBus

logger = logging.getLogger(__name__)


class TelemetryCollector:
    """Collects and aggregates telemetry from event bus."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.metrics: Dict[str, Any] = {}
        self._setup_collectors()
    
    def _setup_collectors(self):
        """Register telemetry collection handlers."""
        self.event_bus.subscribe(EventType.EXPERIMENT_STARTED, self._on_experiment_started)
        self.event_bus.subscribe(EventType.EXPERIMENT_COMPLETED, self._on_experiment_completed)
        self.event_bus.subscribe(EventType.EXPERIMENT_FAILED, self._on_experiment_failed)
        self.event_bus.subscribe(EventType.RESOURCE_WARNING, self._on_resource_warning)
    
    def _on_experiment_started(self, event: Event):
        """Track experiment start."""
        exp_id = event.experiment_id
        if exp_id not in self.metrics:
            self.metrics[exp_id] = {"started_at": event.timestamp, "events": []}
        self.metrics[exp_id]["events"].append(event.to_dict())
    
    def _on_experiment_completed(self, event: Event):
        """Track experiment completion."""
        exp_id = event.experiment_id
        if exp_id in self.metrics:
            self.metrics[exp_id]["completed_at"] = event.timestamp
            duration = (event.timestamp - self.metrics[exp_id]["started_at"]).total_seconds()
            self.metrics[exp_id]["duration_seconds"] = duration
            logger.info(f"Experiment {exp_id} completed in {duration:.2f}s")
        self.metrics[exp_id]["events"].append(event.to_dict())
    
    def _on_experiment_failed(self, event: Event):
        """Track experiment failure."""
        exp_id = event.experiment_id
        if exp_id in self.metrics:
            self.metrics[exp_id]["failed_at"] = event.timestamp
            self.metrics[exp_id]["error"] = event.data.get("error")
        self.metrics[exp_id]["events"].append(event.to_dict())
    
    def _on_resource_warning(self, event: Event):
        """Track resource warnings."""
        exp_id = event.experiment_id
        if exp_id not in self.metrics:
            self.metrics[exp_id] = {"warnings": []}
        if "warnings" not in self.metrics[exp_id]:
            self.metrics[exp_id]["warnings"] = []
        self.metrics[exp_id]["warnings"].append(event.data)
    
    def get_metrics(self, exp_id: Optional[str] = None) -> Dict:
        """Get collected metrics."""
        if exp_id:
            return self.metrics.get(exp_id, {})
        return self.metrics


class WebSocketTelemetrySender:
    """Sends telemetry events to connected WebSocket clients."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.connected_clients = set()
        self.event_bus.subscribe_async(EventType.EXPERIMENT_STARTED, self._broadcast_event)
        self.event_bus.subscribe_async(EventType.EXPERIMENT_PROGRESS, self._broadcast_event)
        self.event_bus.subscribe_async(EventType.EXPERIMENT_COMPLETED, self._broadcast_event)
        self.event_bus.subscribe_async(EventType.RESOURCE_WARNING, self._broadcast_event)
    
    async def _broadcast_event(self, event: Event):
        """Broadcast event to all connected clients (placeholder for actual WebSocket impl)."""
        logger.debug(f"Would broadcast to {len(self.connected_clients)} clients: {event.type.value}")
        # In real implementation, iterate over self.connected_clients and send event


class TelemetryDatabaseWriter:
    """Persists telemetry events to database."""
    
    def __init__(self, event_bus: EventBus, db_connection_string: Optional[str] = None):
        self.event_bus = event_bus
        self.db_connection_string = db_connection_string or "sqlite:///quantaura_telemetry.db"
        self.event_bus.subscribe_async(EventType.EXPERIMENT_STARTED, self._persist_event)
        self.event_bus.subscribe_async(EventType.EXPERIMENT_COMPLETED, self._persist_event)
        self.event_bus.subscribe_async(EventType.EXPERIMENT_FAILED, self._persist_event)
        self.event_bus.subscribe_async(EventType.RESOURCE_WARNING, self._persist_event)
        logger.info(f"Telemetry database: {self.db_connection_string}")
    
    async def _persist_event(self, event: Event):
        """Persist event to database (placeholder for actual DB impl)."""
        logger.debug(f"Would persist to DB: {event.type.value} - {event.experiment_id}")
        # In real implementation, use SQLAlchemy or similar to insert into database


class DashboardDataProvider:
    """Provides aggregated data for real-time dashboard."""
    
    def __init__(self, event_bus: EventBus, collector: TelemetryCollector):
        self.event_bus = event_bus
        self.collector = collector
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data snapshot."""
        stats = self.event_bus.get_stats()
        metrics = self.collector.get_metrics()
        
        # Calculate aggregate metrics
        completed = sum(1 for m in metrics.values() if "completed_at" in m)
        failed = sum(1 for m in metrics.values() if "failed_at" in m)
        avg_duration = sum(
            m.get("duration_seconds", 0) for m in metrics.values() if "duration_seconds" in m
        ) / (completed or 1)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "event_bus_stats": stats,
            "experiments": {
                "total": len(metrics),
                "completed": completed,
                "failed": failed,
                "running": sum(1 for m in metrics.values() if "completed_at" not in m and "failed_at" not in m),
            },
            "performance": {
                "avg_duration_seconds": avg_duration,
                "total_events": stats["total_events"],
            },
            "recent_events": [e.to_dict() for e in self.event_bus.get_history(limit=20)],
        }
