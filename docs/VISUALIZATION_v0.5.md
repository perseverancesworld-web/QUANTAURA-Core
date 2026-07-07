# WebXR Visualization - v0.5 Development Plan

## Overview

Phase 1 (Alpha): Foundation and Core Components

This phase establishes the 3D visualization engine and real-time streaming infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WebXR Visualization System                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐        ┌──────────────────────┐      │
│  │  Visualization       │◄──────►│  WebSocket           │      │
│  │  Engine              │        │  Server              │      │
│  │                      │        │                      │      │
│  │ - ExperimentGraph3D  │        │ - ConnectionManager  │      │
│  │ - ResonanceVisualizer│        │ - StreamServer       │      │
│  │ - TimelineVisualizer │        │ - MessageBroker      │      │
│  └──────────────────────┘        └──────────────────────┘      │
│         │                                 ▲                    │
│         │                                 │                    │
│         ▼                                 │                    │
│  ┌──────────────────────┐        ┌──────────────────────┐      │
│  │  Event Handlers      │        │  Dashboard           │      │
│  │                      │        │  (React Frontend)    │      │
│  │ - on_experiment_     │        │                      │      │
│  │   registered         │        │ - 3D Graph View      │      │
│  │ - on_started         │        │ - Metrics Display    │      │
│  │ - on_completed       │        │ - Event Log          │      │
│  │ - on_failed          │        │ - Timeline           │      │
│  └──────────────────────┘        └──────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components Implemented

### 1. Visualization Engine (`engine.py`)

**Core Classes:**

- `Vector3`: 3D position/rotation representation
- `Color`: RGBA color with state-based mapping
- `ExperimentNode`: 3D sphere representing experiment
  - Updates color/scale based on state
  - Tracks dependencies
  - Serializable to JSON
- `DependencyLink`: Visual connection between experiments
  - Animates when dependent starts
  - Semi-transparent by default
- `ExperimentGraph3D`: Scene management
  - Auto-positions nodes in circular layout
  - Manages links between experiments
  - Provides circular camera position
  - Serializes to JSON for transmission
- `WebXRVisualizationServer`: Integration with orchestrator
  - Subscribes to orchestrator events
  - Updates graph in real-time
  - Broadcasts state changes
- `ResonanceFieldVisualizer`: Specialized wave visualization
  - Tracks field frequency/amplitude/phase
  - Manages harmonic series
  - Provides particle data for waves
- `TimelineVisualizer`: Time-series event visualization
  - Tracks event timestamps
  - Calculates total duration
  - Provides timeline data for rendering

**Key Features:**

- Automatic layout calculation for experiments
- Color coding by state (pending/queued/running/completed/failed)
- Scale animations based on execution state
- Link animation on dependency execution
- Full JSON serialization for network transmission

### 2. WebSocket Server (`websocket_server.py`)

**Core Classes:**

- `WebSocketMessage`: Structured message format
  - Type (graph_update, event_*, metrics_update)
  - Timestamp
  - Data payload
  - JSON serialization
- `WebSocketConnectionManager`: Connection management
  - Tracks active connections
  - Broadcast capability
  - Per-client messaging
- `VisualizationStreamServer`: Real-time streaming
  - Update loop at configurable interval
  - Event-based updates
  - Metrics streaming
- `DashboardDataStreamProvider`: Metrics aggregation
  - Live metrics from orchestrator
  - Experiment details
  - Streamed updates at interval

**Streaming Protocol:**

```json
{
  "type": "graph_update",
  "data": {
    "nodes": {...},
    "links": [...],
    "camera": {...}
  },
  "timestamp": "2026-07-07T18:20:00Z"
}
```

### 3. Dashboard Configuration (`dashboard.py`)

**Core Classes:**

- `DashboardMetric`: Metric value with metadata
- `DashboardPanel`: Widget configuration
- `DashboardLayout`: Panel arrangement
- `DashboardComponentRegistry`: Available React components

**Default Dashboard Panels:**

1. **3D Dependency Graph** (8x6) - Main visualization
2. **Execution Timeline** (8x2) - Time-series of events
3. **Resource Monitor** (4x3) - Memory/CPU/Disk gauges
4. **Status Summary** (4x3) - Counts and rates
5. **Event Log** (4x2) - Recent events scroll

**React Components Available:**

- `ExperimentGraphView3D` - 3D graph visualization
- `ExecutionTimeline` - Timeline view
- `ResourceMonitor` - Resource gauges
- `StatusSummary` - Status cards
- `EventLog` - Event list
- `MetricsGraph` - Time-series charts

## Integration with v0.4

The visualization system integrates with v0.4 orchestrator via:

1. **Event Subscription:**
   - Subscribes to EXPERIMENT_REGISTERED, STARTED, COMPLETED, FAILED
   - Updates graph nodes in real-time

2. **Status Queries:**
   - Polls orchestrator.get_status() for metrics
   - Aggregates into dashboard data

3. **WebSocket Broadcasting:**
   - Sends updates to connected clients
   - 100ms update interval (configurable)

## Next Steps (v0.5 Development)

### Phase 1A: WebSocket Server (Week 1)
- [ ] Implement using FastAPI + python-socketio
- [ ] Add real WebSocket connection handling
- [ ] Message queue for reliable delivery
- [ ] Client authentication

### Phase 1B: React Dashboard (Week 2)
- [ ] Project setup (Create React App / Vite)
- [ ] Component structure
- [ ] WebSocket client library
- [ ] Responsive layout

### Phase 1C: 3D Visualization (Week 3)
- [ ] Three.js or Babylon.js integration
- [ ] Experiment node rendering
- [ ] Dependency link rendering
- [ ] Camera controls
- [ ] Animation system

### Phase 1D: Testing & Documentation (Week 4)
- [ ] Integration tests
- [ ] E2E tests
- [ ] Performance optimization
- [ ] Documentation

## Performance Targets

- **WebSocket Throughput:** 10,000+ events/second
- **Dashboard Update Latency:** <500ms from event to UI
- **3D Rendering:** 60 FPS with 1000+ nodes
- **Memory (Dashboard):** <200MB

## File Structure

```
QUANTAURA-Core/
├── quantaura/
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── engine.py                 (350 LOC) ✓
│   │   ├── websocket_server.py       (200 LOC) ✓
│   │   ├── dashboard.py              (200 LOC) ✓
│   │   └── three_js_adapter.py       (TBD)
│   └── orchestration/
│       └── ... (existing v0.4)
├── frontend/                           (TBD)
│   ├── package.json
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ExperimentGraphView3D.tsx
│   │   │   ├── ExecutionTimeline.tsx
│   │   │   ├── ResourceMonitor.tsx
│   │   │   ├── StatusSummary.tsx
│   │   │   └── EventLog.tsx
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useOrchestrator.ts
│   │   │   └── useVisualization.ts
│   │   └── App.tsx
│   └── ... (build config)
└── docs/
    └── VISUALIZATION.md              (TBD)
```

## Success Criteria

✅ **Phase 1 Complete When:**

1. WebXR visualization engine renders experiment DAGs in 3D
2. WebSocket server streams real-time updates to clients
3. React dashboard displays:
   - 3D experiment graph
   - Execution timeline
   - Resource usage
   - Status summary
   - Event log
4. All components tested with v0.4 orchestrator
5. 60 FPS rendering with 100+ experiments
6. Documentation complete

## Resources

- Three.js: https://threejs.org/
- Babylon.js: https://www.babylonjs.com/
- FastAPI: https://fastapi.tiangolo.com/
- Socket.IO: https://socket.io/
- React: https://react.dev/
- Vite: https://vitejs.dev/
