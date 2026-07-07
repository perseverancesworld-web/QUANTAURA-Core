"""Dashboard React component structure and data models.

Defines the structure for building a React-based dashboard that consumes
visualization data from the WebSocket server.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class DashboardMetric:
    """Single dashboard metric."""
    name: str
    value: float
    unit: str
    timestamp: str
    threshold: Optional[float] = None
    status: str = "normal"  # normal, warning, critical


@dataclass
class DashboardPanel:
    """Dashboard panel configuration."""
    id: str
    title: str
    panel_type: str  # "graph", "gauge", "timeline", "status"
    data_source: str  # WebSocket event type or metric name
    position: Dict  # {x, y, width, height}
    refresh_interval: float = 1.0
    config: Dict = None


class DashboardLayout:
    """Dashboard layout manager."""
    
    def __init__(self):
        self.panels: Dict[str, DashboardPanel] = {}
        self.global_settings = {
            "theme": "dark",
            "refresh_rate": 0.5,  # seconds
            "time_range": "5m",
        }
    
    def add_panel(self, panel: DashboardPanel):
        """Add panel to dashboard."""
        self.panels[panel.id] = panel
    
    def get_layout_config(self) -> Dict:
        """Export layout configuration as JSON."""
        return {
            "panels": [
                {
                    "id": p.id,
                    "title": p.title,
                    "type": p.panel_type,
                    "dataSource": p.data_source,
                    "position": p.position,
                    "refreshInterval": p.refresh_interval,
                    "config": p.config or {},
                }
                for p in self.panels.values()
            ],
            "settings": self.global_settings,
        }


def create_default_dashboard_layout() -> DashboardLayout:
    """Create default dashboard layout."""
    layout = DashboardLayout()
    
    # 3D Dependency Graph Panel
    layout.add_panel(DashboardPanel(
        id="graph",
        title="Experiment Dependency Graph (3D)",
        panel_type="graph",
        data_source="graph_update",
        position={"x": 0, "y": 0, "width": 8, "height": 6},
        config={"view": "3d", "animation": True}
    ))
    
    # Execution Timeline
    layout.add_panel(DashboardPanel(
        id="timeline",
        title="Execution Timeline",
        panel_type="timeline",
        data_source="event_experiment_started,event_experiment_completed",
        position={"x": 0, "y": 6, "width": 8, "height": 2},
    ))
    
    # Resource Monitor
    layout.add_panel(DashboardPanel(
        id="resources",
        title="Resource Usage",
        panel_type="graph",
        data_source="metrics_update",
        position={"x": 8, "y": 0, "width": 4, "height": 3},
        config={"metrics": ["memory", "cpu", "disk"]}
    ))
    
    # Status Summary
    layout.add_panel(DashboardPanel(
        id="status",
        title="Execution Status",
        panel_type="status",
        data_source="metrics_update",
        position={"x": 8, "y": 3, "width": 4, "height": 3},
        config={"show": ["total", "completed", "failed", "running"]}
    ))
    
    # Event Log
    layout.add_panel(DashboardPanel(
        id="events",
        title="Recent Events",
        panel_type="list",
        data_source="event_*",
        position={"x": 8, "y": 6, "width": 4, "height": 2},
        config={"limit": 10}
    ))
    
    return layout


class DashboardComponentRegistry:
    """Registry of available React dashboard components."""
    
    COMPONENTS = {
        "ExperimentGraphView3D": {
            "description": "3D visualization of experiment DAG",
            "props": ["nodes", "links", "camera", "onNodeClick"],
            "data_source": "graph_update",
        },
        "ExecutionTimeline": {
            "description": "Timeline view of experiment execution",
            "props": ["events", "scale", "onEventClick"],
            "data_source": "event_experiment_started,event_experiment_completed",
        },
        "ResourceMonitor": {
            "description": "Real-time resource usage gauge",
            "props": ["memory", "cpu", "disk", "threshold"],
            "data_source": "metrics_update",
        },
        "StatusSummary": {
            "description": "Summary of execution status",
            "props": ["total", "completed", "failed", "running"],
            "data_source": "metrics_update",
        },
        "EventLog": {
            "description": "Scrolling event log",
            "props": ["events", "limit", "filter"],
            "data_source": "event_*",
        },
        "MetricsGraph": {
            "description": "Time-series metrics graph",
            "props": ["metrics", "timeRange", "unit"],
            "data_source": "metrics_update",
        },
    }
    
    @classmethod
    def get_component_manifest(cls) -> Dict:
        """Get all available components."""
        return cls.COMPONENTS
    
    @classmethod
    def get_component(cls, component_name: str) -> Optional[Dict]:
        """Get specific component info."""
        return cls.COMPONENTS.get(component_name)
