import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from core.simulation.simulation_runner import SimulationRunner
from pydantic import BaseModel
import os

app = FastAPI()

@app.get("/")
async def get():
    with open("index.html", "r") as f:
        return HTMLResponse(f.read())

active_websockets = set()
simulation_running = False

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        active_websockets.remove(websocket)

@app.post("/start")
async def start_sim():
    global simulation_running
    if simulation_running:
        return {"status": "already running"}
    
    simulation_running = True
    asyncio.create_task(run_sim_loop())
    return {"status": "started"}

async def run_sim_loop():
    global simulation_running
    inp_file = "config/catchments/assam_real_mini.inp"
    runner = SimulationRunner(inp_file, {"run_id": "ui-demo", "critical_depth_threshold_m": 0.5})
    
    try:
        async for tick in runner.run():
            payload = tick.model_dump(mode='json')
            
            # Send to all connected UIs
            dead_sockets = set()
            for ws in active_websockets:
                try:
                    await ws.send_json({"type": "simulation.tick", "payload": payload})
                except:
                    dead_sockets.add(ws)
            
            for ws in dead_sockets:
                active_websockets.remove(ws)
                
            # Slow down simulation slightly for dramatic visual effect in UI
            await asyncio.sleep(0.15)
    except Exception as e:
        print(f"Simulation error: {e}")
    finally:
        simulation_running = False

if __name__ == "__main__":
    import uvicorn
    print("Starting API and UI server on http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
