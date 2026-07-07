"""WebXR Visualization Engine - Real-time 3D experiment exploration.

Phase 1: Foundation and core components
- WebSocket server for real-time event streaming
- 3D scene management
- Experiment state visualization
- Interactive controls
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class Vector3:
    """3D vector for positioning."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y, "z": self.z}


@dataclass
class Color:
    """RGB color representation."""
    r: float = 1.0
    g: float = 1.0
    b: float = 1.0
    a: float = 1.0  # Alpha
    
    def to_dict(self) -> Dict:
        return {"r": self.r, "g": self.g, "b": self.b, "a": self.a}
    
    @staticmethod
    def from_state(state: str) -> 'Color':
        """Get color based on experiment state."""
        colors = {
            "pending": Color(0.8, 0.8, 0.8),      # Gray
            "queued": Color(1.0, 1.0, 0.0),      # Yellow
            "running": Color(0.0, 1.0, 0.0),     # Green
            "completed": Color(0.0, 0.5, 1.0),   # Blue
            "failed": Color(1.0, 0.0, 0.0),      # Red
            "paused": Color(1.0, 0.5, 0.0),      # Orange
        }
        return colors.get(state, Color(0.5, 0.5, 0.5))


class ExperimentNode:
    """3D representation of an experiment in the visualization."""
    
    def __init__(self, exp_id: str, name: str, position: Vector3):
        self.id = exp_id
        self.name = name
        self.position = position
        self.state = "pending"
        self.color = Color.from_state(self.state)
        self.scale = Vector3(1.0, 1.0, 1.0)
        self.rotation = Vector3(0.0, 0.0, 0.0)
        self.children: List[str] = []  # Connected experiment IDs
        self.metadata: Dict = {}
    
    def update_state(self, new_state: str):
        """Update node state and visual representation."""
        self.state = new_state
        self.color = Color.from_state(new_state)
        
        # Scale animation based on state
        if new_state == "running":
            self.scale = Vector3(1.2, 1.2, 1.2)
        elif new_state == "completed":
            self.scale = Vector3(0.9, 0.9, 0.9)
        elif new_state == "failed":
            self.scale = Vector3(1.1, 1.1, 1.1)
        else:
            self.scale = Vector3(1.0, 1.0, 1.0)
    
    def to_dict(self) -> Dict:
        """Convert to serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "position": self.position.to_dict(),
            "color": self.color.to_dict(),
            "scale": self.scale.to_dict(),
            "rotation": self.rotation.to_dict(),
            "children": self.children,
            "metadata": self.metadata,
        }


class DependencyLink:
    """Visual representation of dependency between experiments."""
    
    def __init__(self, from_id: str, to_id: str):
        self.from_id = from_id
        self.to_id = to_id
        self.color = Color(0.5, 0.5, 0.5, 0.5)  # Semi-transparent gray
        self.thickness = 2.0
        self.animated = False
    
    def animate_on_execution(self):
        """Animate when dependent experiment starts."""
        self.animated = True
        self.color = Color(0.0, 1.0, 1.0, 0.8)  # Bright cyan
    
    def to_dict(self) -> Dict:
        return {
            "from": self.from_id,
            "to": self.to_id,
            "color": self.color.to_dict(),
            "thickness": self.thickness,
            "animated": self.animated,
        }


class ExperimentGraph3D:
    """3D scene management for experiment dependency graph."""
    
    def __init__(self):
        self.nodes: Dict[str, ExperimentNode] = {}
        self.links: Dict[str, DependencyLink] = {}
        self.camera_position = Vector3(0, 10, 20)
        self.camera_target = Vector3(0, 0, 0)
    
    def add_experiment(self, exp_id: str, name: str, position: Optional[Vector3] = None) -> ExperimentNode:
        """Add experiment node to graph."""
        if position is None:
            # Auto-position based on existing nodes
            position = self._calculate_position(len(self.nodes))
        
        node = ExperimentNode(exp_id, name, position)
        self.nodes[exp_id] = node
        logger.info(f"Added node {name} at {position.to_dict()}")
        return node
    
    def _calculate_position(self, index: int) -> Vector3:
        """Calculate position for new node in circular layout."""
        import math
        angle = (index * 2 * math.pi) / 8  # 8 nodes per circle
        radius = 5.0
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        return Vector3(x, index * 2, z)  # Stagger by height too
    
    def add_dependency(self, from_id: str, to_id: str):
        """Add visual link between experiments."""
        link_key = f"{from_id}->{to_id}"
        link = DependencyLink(from_id, to_id)
        self.links[link_key] = link
        
        # Add to-id as child of from-id for structural info
        if from_id in self.nodes:
            self.nodes[from_id].children.append(to_id)
        
        logger.info(f"Added link {from_id} -> {to_id}")
    
    def update_experiment_state(self, exp_id: str, new_state: str):
        """Update experiment state and visual."""
        if exp_id in self.nodes:
            self.nodes[exp_id].update_state(new_state)
            
            # Animate outgoing links when experiment starts
            if new_state == "running":
                for link in self.links.values():
                    if link.from_id == exp_id:
                        link.animate_on_execution()
    
    def to_dict(self) -> Dict:
        """Convert entire graph to dictionary for JSON serialization."""
        return {
            "nodes": {id: node.to_dict() for id, node in self.nodes.items()},
            "links": list(link.to_dict() for link in self.links.values()),
            "camera": {
                "position": self.camera_position.to_dict(),
                "target": self.camera_target.to_dict(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }


class WebXRVisualizationServer:
    """WebXR visualization server (async, WebSocket-ready)."""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.graph = ExperimentGraph3D()
        self.connected_clients: Set = set()
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Register handlers for orchestrator events."""
        from quantaura.orchestration.event_bus import EventType
        
        self.orchestrator.event_bus.subscribe(
            EventType.EXPERIMENT_REGISTERED,
            self._on_experiment_registered
        )
        self.orchestrator.event_bus.subscribe(
            EventType.EXPERIMENT_STARTED,
            self._on_experiment_started
        )
        self.orchestrator.event_bus.subscribe(
            EventType.EXPERIMENT_COMPLETED,
            self._on_experiment_completed
        )
        self.orchestrator.event_bus.subscribe(
            EventType.EXPERIMENT_FAILED,
            self._on_experiment_failed
        )
    
    def _on_experiment_registered(self, event_data: Dict):
        """Handle experiment registration event."""
        exp_id = event_data["experiment_id"]
        name = event_data["data"].get("name", f"Exp-{exp_id[:8]}")
        self.graph.add_experiment(exp_id, name)
        logger.info(f"Visualization: Registered {name}")
    
    def _on_experiment_started(self, event_data: Dict):
        """Handle experiment start event."""
        exp_id = event_data["experiment_id"]
        self.graph.update_experiment_state(exp_id, "running")
        logger.info(f"Visualization: {exp_id} started")
    
    def _on_experiment_completed(self, event_data: Dict):
        """Handle experiment completion event."""
        exp_id = event_data["experiment_id"]
        self.graph.update_experiment_state(exp_id, "completed")
        logger.info(f"Visualization: {exp_id} completed")
    
    def _on_experiment_failed(self, event_data: Dict):
        """Handle experiment failure event."""
        exp_id = event_data["experiment_id"]
        self.graph.update_experiment_state(exp_id, "failed")
        logger.info(f"Visualization: {exp_id} failed")
    
    async def broadcast_state(self):
        """Broadcast current graph state to all connected clients."""
        state = self.graph.to_dict()
        message = json.dumps(state)
        
        # In production, iterate over self.connected_clients and send via WebSocket
        logger.debug(f"Would broadcast state to {len(self.connected_clients)} clients")
    
    def get_current_state(self) -> Dict:
        """Get current visualization state."""
        return self.graph.to_dict()


class ResonanceFieldVisualizer:
    """Specialized visualizer for resonance/wave simulations."""
    
    def __init__(self):
        self.field_data: Dict = {}
        self.wave_particles: List[Dict] = []
        self.harmonics: List[float] = []
    
    def update_field(self, frequency: float, amplitude: float, phase: float):
        """Update resonance field visualization."""
        self.field_data = {
            "frequency": frequency,
            "amplitude": amplitude,
            "phase": phase,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def add_harmonic(self, frequency: float):
        """Add harmonic to visualization."""
        if frequency not in self.harmonics:
            self.harmonics.append(frequency)
            self.harmonics.sort()
    
    def get_visualization_data(self) -> Dict:
        """Get data for 3D wave visualization."""
        return {
            "field": self.field_data,
            "harmonics": self.harmonics,
            "particle_count": len(self.wave_particles),
        }


class TimelineVisualizer:
    """Time-series visualization of experiment execution."""
    
    def __init__(self):
        self.events: List[Dict] = []
        self.timeline_scale = 1.0  # pixels per millisecond
    
    def add_event(self, exp_id: str, event_type: str, timestamp: datetime):
        """Add event to timeline."""
        self.events.append({
            "id": exp_id,
            "type": event_type,
            "timestamp": timestamp.isoformat(),
        })
    
    def get_timeline_data(self) -> Dict:
        """Get timeline data for rendering."""
        return {
            "events": self.events,
            "scale": self.timeline_scale,
            "total_duration_ms": self._calculate_duration(),
        }
    
    def _calculate_duration(self) -> int:
        """Calculate total timeline duration."""
        if not self.events:
            return 0
        
        times = [datetime.fromisoformat(e["timestamp"]) for e in self.events]
        return int((max(times) - min(times)).total_seconds() * 1000)
