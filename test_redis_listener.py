import asyncio
import redis.asyncio as redis
import json

async def listen():
    # Connect to the local Redis instance
    r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    pubsub = r.pubsub()
    
    # Subscribe to the channels the Hydrology Worker uses
    await pubsub.subscribe("simulation.tick", "simulation.topology", "simulation.status")
    
    print("Listening for PySWMM telemetry on Redis channels...")
    print("Run: 'python -m core.simulation.pyswmm_wrapper' in another terminal to start the simulation.")
    print("-" * 60)
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"]
                data = json.loads(message["data"])
                
                if channel == "simulation.tick":
                    tick = data.get("payload", {})
                    print(f"[TICK] Time: {tick.get('sim_time')} | Step: {tick.get('step')}")
                
                elif channel == "simulation.topology":
                    print(f"\n[TOPOLOGY MUTATION] 🚨 Water threshold breached! Payload:")
                    print(json.dumps(data, indent=2))
                    print("-" * 60)
                
                elif channel == "simulation.status":
                    print(f"\n[STATUS] Run ID: {data.get('run_id')} is now {data.get('status').upper()}")
    
    except KeyboardInterrupt:
        print("\nListener stopped.")
    finally:
        await pubsub.close()
        await r.aclose()

if __name__ == "__main__":
    try:
        asyncio.run(listen())
    except KeyboardInterrupt:
        pass
