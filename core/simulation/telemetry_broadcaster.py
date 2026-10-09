import json
import logging
from typing import Optional
import redis.asyncio as redis
from .models.sim_tick import SimulationTick

logger = logging.getLogger(__name__)

class TelemetryBroadcaster:
    """Publishes simulation telemetry to Redis Pub/Sub channels."""
    
    def __init__(self, redis_url: str, ws_port: Optional[int] = None):
        self.redis_url = redis_url
        self.ws_port = ws_port # For future direct WS integration if needed
        self.redis: Optional[redis.Redis] = None
        
    async def connect(self):
        """Establish connection to Redis."""
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.info("Running in fallback mode: broadcasting to standard output instead of Redis.")
            self.redis = None
            
    async def close(self):
        """Close connection to Redis."""
        if self.redis:
            await self.redis.aclose()
            
    async def broadcast_tick(self, tick: SimulationTick) -> None:
        """Broadcast a simulation tick to the simulation.tick channel."""
        if not self.redis:
            payload = tick.model_dump(mode='json')
            print(f"[FALLBACK TICK] Time: {tick.sim_time} | Step: {tick.step}")
            return
            
        payload = {
            "type": "simulation.tick",
            "ts": tick.sim_time.isoformat(),
            "run_id": tick.run_id,
            "payload": tick.model_dump(mode='json')
        }
        await self.redis.publish("simulation.tick", json.dumps(payload))
        
    async def broadcast_topology(self, topology: dict) -> None:
        """Broadcast updated topology graph after flood state changes."""
        if not self.redis:
            print("\n[FALLBACK TOPOLOGY MUTATION] 🚨 Water threshold breached! Payload:")
            print(json.dumps(topology, indent=2))
            print("-" * 60)
            return
            
        payload = {
            "type": "simulation.topology",
            "payload": topology
        }
        await self.redis.publish("simulation.topology", json.dumps(payload))
        
    async def broadcast_status(self, status: str, run_id: str) -> None:
        """Broadcast simulation run status."""
        if not self.redis:
            print(f"[FALLBACK STATUS] Run ID: {run_id} is now {status.upper()}")
            return
            
        payload = {
            "type": "simulation.status",
            "run_id": run_id,
            "status": status
        }
        await self.redis.publish("simulation.status", json.dumps(payload))
