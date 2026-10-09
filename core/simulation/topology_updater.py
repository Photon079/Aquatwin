import logging
from .models.sim_tick import SimulationTick
from .flood_state import FloodState
from .telemetry_broadcaster import TelemetryBroadcaster

logger = logging.getLogger(__name__)

class TopologyUpdater:
    """Detects mutations in the topological graph based on flood states and publishes updates."""
    
    def __init__(self, broadcaster: TelemetryBroadcaster):
        self.broadcaster = broadcaster
        self.last_flooded_nodes = set()
        
    async def process_tick(self, tick: SimulationTick, flood_state: FloodState) -> None:
        """Check if flooded nodes have changed, and broadcast topology update if they have."""
        current_flooded_nodes = flood_state.flooded_nodes()
        
        # If there's a difference in the sets, the topology has effectively changed
        if current_flooded_nodes != self.last_flooded_nodes:
            logger.info(f"Topology mutation detected: {len(current_flooded_nodes)} nodes flooded.")
            topology_snapshot = flood_state.snapshot()
            await self.broadcaster.broadcast_topology(topology_snapshot)
            self.last_flooded_nodes = current_flooded_nodes
