"""
Entrypoint for the Hydrology Worker. Runs a PySWMM simulation locally and broadcasts telemetry.
"""
import os
import asyncio
import logging
from .simulation_runner import SimulationRunner
from .telemetry_broadcaster import TelemetryBroadcaster
from .topology_updater import TopologyUpdater

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    run_id = os.environ.get("RUN_ID", "assam-2026-07-19")
    inp_path = os.environ.get("SIMULATION_INP_PATH", "config/catchments/silsako_basin.inp")
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    config = {
        "run_id": run_id,
        "critical_depth_threshold_m": float(os.environ.get("SIMULATION_CRITICAL_DEPTH_M", 0.5)),
        "broadcast_interval_ms": int(os.environ.get("SIMULATION_BROADCAST_INTERVAL_MS", 1000))
    }
    
    # We will instantiate the runner, but if INP file does not exist, it will throw an error when loaded.
    runner = SimulationRunner(inp_path=inp_path, config=config)
    broadcaster = TelemetryBroadcaster(redis_url=redis_url)
    topology_updater = TopologyUpdater(broadcaster)
    
    await broadcaster.connect()
    await broadcaster.broadcast_status("running", run_id)
    
    try:
        interval_s = config["broadcast_interval_ms"] / 1000.0
        
        async for tick in runner.run():
            # Broadcast the tick to Redis
            await broadcaster.broadcast_tick(tick)
            
            # Check for topological changes
            await topology_updater.process_tick(tick, runner.flood_state)
            
            if interval_s > 0:
                await asyncio.sleep(interval_s)
                
        await broadcaster.broadcast_status("complete", run_id)
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        await broadcaster.broadcast_status("error", run_id)
    finally:
        await broadcaster.close()

if __name__ == "__main__":
    asyncio.run(main())
