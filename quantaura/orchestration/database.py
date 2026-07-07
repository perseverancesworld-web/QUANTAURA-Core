"""Database models and repository layer for experiment and telemetry persistence."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ExperimentStatus(str, Enum):
    """Database representation of experiment status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExperimentRecord:
    """Database record for experiment."""
    id: str
    name: str
    status: ExperimentStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class EventRecord:
    """Database record for event."""
    id: str
    event_type: str
    source: str
    timestamp: datetime
    experiment_id: Optional[str] = None
    correlation_id: Optional[str] = None
    data: Dict[str, Any] = None


@dataclass
class ResourceUsageRecord:
    """Database record for resource usage snapshot."""
    id: str
    experiment_id: str
    timestamp: datetime
    memory_mb: float
    cpu_percent: float
    disk_usage_mb: Optional[float] = None


class ExperimentRepository:
    """Abstract repository for experiment persistence."""
    
    async def create(self, record: ExperimentRecord) -> str:
        """Create experiment record. Returns record ID."""
        raise NotImplementedError()
    
    async def get(self, exp_id: str) -> Optional[ExperimentRecord]:
        """Get experiment record by ID."""
        raise NotImplementedError()
    
    async def list(self, status: Optional[ExperimentStatus] = None) -> List[ExperimentRecord]:
        """List experiments, optionally filtered by status."""
        raise NotImplementedError()
    
    async def update(self, record: ExperimentRecord) -> bool:
        """Update experiment record. Returns success."""
        raise NotImplementedError()
    
    async def delete(self, exp_id: str) -> bool:
        """Delete experiment record."""
        raise NotImplementedError()


class EventRepository:
    """Abstract repository for event persistence."""
    
    async def create(self, record: EventRecord) -> str:
        """Create event record."""
        raise NotImplementedError()
    
    async def list_by_experiment(self, exp_id: str, limit: int = 100) -> List[EventRecord]:
        """List events for experiment."""
        raise NotImplementedError()
    
    async def list_recent(self, limit: int = 100) -> List[EventRecord]:
        """List recent events."""
        raise NotImplementedError()


class ResourceUsageRepository:
    """Abstract repository for resource usage tracking."""
    
    async def create(self, record: ResourceUsageRecord) -> str:
        """Create resource usage record."""
        raise NotImplementedError()
    
    async def list_by_experiment(self, exp_id: str) -> List[ResourceUsageRecord]:
        """Get resource usage timeline for experiment."""
        raise NotImplementedError()
    
    async def get_peak_usage(self, exp_id: str) -> Optional[Dict[str, float]]:
        """Get peak memory and CPU usage for experiment."""
        raise NotImplementedError()
