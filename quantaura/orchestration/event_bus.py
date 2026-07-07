"""Event Bus - real-time event distribution for orchestration telemetry."""

import asyncio
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any, Set
from enum import Enum
import json

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types in the orchestration system."""
    # Experiment lifecycle
    EXPERIMENT_REGISTERED = "experiment_registered"
    EXPERIMENT_QUEUED = "experiment_queued"
    EXPERIMENT_STARTED = "experiment_started"
    EXPERIMENT_PROGRESS = "experiment_progress"
    EXPERIMENT_COMPLETED = "experiment_completed"
    EXPERIMENT_FAILED = "experiment_failed"
    EXPERIMENT_PAUSED = "experiment_paused"
    EXPERIMENT_RESUMED = "experiment_resumed"
    EXPERIMENT_CANCELLED = "experiment_cancelled"
    
    # Resource events
    RESOURCE_ALLOCATED = "resource_allocated"
    RESOURCE_RELEASED = "resource_released"
    RESOURCE_WARNING = "resource_warning"
    RESOURCE_EXCEEDED = "resource_exceeded"
    
    # Scheduler events
    SCHEDULER_STARTED = "scheduler_started"
    SCHEDULER_PAUSED = "scheduler_paused"
    SCHEDULER_RESUMED = "scheduler_resumed"
    SCHEDULER_COMPLETED = "scheduler_completed"
    SCHEDULER_ERROR = "scheduler_error"


@dataclass
class Event:
    """Event emitted by orchestration system."""
    type: EventType
    source: str  # module/component that emitted event
    timestamp: datetime
    data: Dict[str, Any]
    experiment_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary."""
        return {
            "type": self.type.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "experiment_id": self.experiment_id,
            "correlation_id": self.correlation_id,
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


EventHandler = Callable[[Event], None]
AsyncEventHandler = Callable[[Event], asyncio.coroutine]


class EventBus:
    """Central event distribution system for orchestration telemetry."""
    
    def __init__(self, max_history: int = 10000):
        self.handlers: Dict[EventType, Set[EventHandler]] = {}
        self.async_handlers: Dict[EventType, Set[AsyncEventHandler]] = {}
        self.event_history: List[Event] = []
        self.max_history = max_history
    
    def subscribe(self, event_type: EventType, handler: EventHandler):
        """Subscribe to events of a specific type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = set()
        self.handlers[event_type].add(handler)
        logger.debug(f"Subscribed handler {handler.__name__} to {event_type.value}")
    
    def subscribe_async(self, event_type: EventType, handler: AsyncEventHandler):
        """Subscribe to events with async handler."""
        if event_type not in self.async_handlers:
            self.async_handlers[event_type] = set()
        self.async_handlers[event_type].add(handler)
        logger.debug(f"Subscribed async handler {handler.__name__} to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler):
        """Unsubscribe from events."""
        if event_type in self.handlers:
            self.handlers[event_type].discard(handler)
    
    def unsubscribe_async(self, event_type: EventType, handler: AsyncEventHandler):
        """Unsubscribe async handler."""
        if event_type in self.async_handlers:
            self.async_handlers[event_type].discard(handler)
    
    def emit(self, event: Event):
        """Emit synchronous event to all subscribers."""
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Call sync handlers
        if event.type in self.handlers:
            for handler in self.handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(
                        f"Error in event handler {handler.__name__}: {e}",
                        exc_info=True
                    )
        
        # Call wildcard handlers (if any)
        logger.debug(f"Emitted event: {event.type.value} from {event.source}")
    
    async def emit_async(self, event: Event):
        """Emit event to async subscribers."""
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Call async handlers
        if event.type in self.async_handlers:
            tasks = []
            for handler in self.async_handlers[event.type]:
                try:
                    task = asyncio.create_task(handler(event))
                    tasks.append(task)
                except Exception as e:
                    logger.error(
                        f"Error scheduling async handler {handler.__name__}: {e}",
                        exc_info=True
                    )
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Emitted async event: {event.type.value} from {event.source}")
    
    def get_history(self, event_type: Optional[EventType] = None, limit: int = 100) -> List[Event]:
        """Get event history, optionally filtered by type."""
        if event_type:
            events = [e for e in self.event_history if e.type == event_type]
        else:
            events = self.event_history
        
        return events[-limit:]
    
    def get_experiment_events(self, experiment_id: str, limit: int = 100) -> List[Event]:
        """Get all events for a specific experiment."""
        events = [
            e for e in self.event_history
            if e.experiment_id == experiment_id
        ]
        return events[-limit:]
    
    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()
    
    def get_stats(self) -> Dict:
        """Get event bus statistics."""
        event_counts = {}
        for event in self.event_history:
            event_type = event.type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "total_events": len(self.event_history),
            "unique_event_types": len(event_counts),
            "event_counts": event_counts,
            "subscribers_count": sum(len(handlers) for handlers in self.handlers.values()),
            "async_subscribers_count": sum(len(handlers) for handlers in self.async_handlers.values()),
        }
