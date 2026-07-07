"""WebSocket server for real-time visualization streaming.

Provides streaming of experiment state, metrics, and events to connected
WebXR/web clients.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketMessage:
    """Structured WebSocket message."""
    
    def __init__(self, message_type: str, data: Dict, timestamp: Optional[datetime] = None):
        self.type = message_type
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_json(self) -> str:
        """Convert to JSON for transmission."""
        return json.dumps({
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        })


class WebSocketConnectionManager:
    """Manages connected WebSocket clients."""
    
    def __init__(self):
        self.active_connections: Set = set()
        self.message_queue: asyncio.Queue = asyncio.Queue()
    
    async def connect(self, connection_id: str):
        """Register new connection."""
        self.active_connections.add(connection_id)
        logger.info(f"Client connected: {connection_id}. Total: {len(self.active_connections)}")
    
    async def disconnect(self, connection_id: str):
        """Unregister connection."""
        self.active_connections.discard(connection_id)
        logger.info(f"Client disconnected: {connection_id}. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: WebSocketMessage):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            logger.debug("No connected clients")
            return
        
        json_message = message.to_json()
        # In real implementation, send to each connection via websockets library
        logger.debug(f"Would broadcast to {len(self.active_connections)} clients: {message.type}")
    
    async def send_to_client(self, connection_id: str, message: WebSocketMessage):
        """Send message to specific client."""
        if connection_id not in self.active_connections:
            logger.warning(f"Client {connection_id} not connected")
            return
        
        # In real implementation, send via websockets
        logger.debug(f"Would send to {connection_id}: {message.type}")


class VisualizationStreamServer:
    """Streams visualization state to connected clients."""
    
    def __init__(self, visualizer):
        self.visualizer = visualizer
        self.connection_manager = WebSocketConnectionManager()
        self.update_interval = 0.1  # 100ms updates
        self.is_running = False
    
    async def start(self):
        """Start streaming server."""
        self.is_running = True
        logger.info("Visualization streaming server started")
        
        # Start broadcast loop
        asyncio.create_task(self._broadcast_loop())
    
    async def stop(self):
        """Stop streaming server."""
        self.is_running = False
        logger.info("Visualization streaming server stopped")
    
    async def _broadcast_loop(self):
        """Main broadcast loop."""
        while self.is_running:
            try:
                # Get current visualization state
                state = self.visualizer.get_current_state()
                
                # Create and broadcast message
                message = WebSocketMessage("graph_update", state)
                await self.connection_manager.broadcast(message)
                
                # Wait before next update
                await asyncio.sleep(self.update_interval)
            
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}", exc_info=True)
                await asyncio.sleep(1)  # Back off on error
    
    async def send_event_update(self, event_type: str, event_data: Dict):
        """Send event update to clients."""
        message = WebSocketMessage(f"event_{event_type}", event_data)
        await self.connection_manager.broadcast(message)
    
    async def send_metrics_update(self, metrics: Dict):
        """Send metrics update to clients."""
        message = WebSocketMessage("metrics_update", metrics)
        await self.connection_manager.broadcast(message)


class DashboardDataStreamProvider:
    """Provides streamed dashboard data."""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    async def get_live_metrics(self) -> Dict:
        """Get current live metrics."""
        status = self.orchestrator.get_status()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "experiments": status["scheduler"],
            "resources": status["resources"],
            "telemetry": status["telemetry"],
        }
    
    async def get_experiment_details(self, exp_id: str) -> Dict:
        """Get detailed information about an experiment."""
        status = self.orchestrator.get_status()
        experiments = status["scheduler"]["experiments"]
        return experiments.get(exp_id, {})
    
    async def stream_metrics(self, callback: Callable, interval: float = 0.5):
        """Stream metrics updates at interval."""
        while True:
            try:
                metrics = await self.get_live_metrics()
                await callback(metrics)
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error streaming metrics: {e}")
                await asyncio.sleep(1)
