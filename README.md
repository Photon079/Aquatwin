# AquaTwin DFOE - Part A (Hydrology Physics & Simulation)

This repository contains the completed **Part A** implementation for the AquaTwin Dynamic Flood Operating Environment (DFOE). It serves as the headless backend physics engine that mathematically models flood propagation across physical city streets, evaluates critical water depths, and broadcasts live topology mutations to the rest of the AquaTwin ecosystem (Digital Twin & AI Agents).

## 🌊 Overview

The core engine utilizes **PySWMM** (Python wrapped SWMM5) to run Kinematic Wave routing calculations over a geographically anchored street network. 

At every simulation tick, the engine:
1. Calculates current water depths (`depth_m`) and flow rates (`flow_cms`) for every intersection.
2. Evaluates the depth against a predefined threshold (default: `0.5m`).
3. Flags flooded nodes and recalculates the overall street passability (Topological Mutability).
4. Broadcasts a highly structured JSON payload representing the current state of the city.

---

## 🏗️ Architecture & Files

* **`core/simulation/pyswmm_wrapper.py`**: The main async entry point.
* **`core/simulation/simulation_runner.py`**: Wraps the PySWMM environment and advances the physical clock.
* **`core/simulation/flood_state.py`**: Manages the threshold tracking logic and identifies impassable routes.
* **`core/simulation/telemetry_broadcaster.py`**: Broadcasts the JSON payload. Gracefully falls back to standard output if a Redis connection cannot be established, allowing for easy local testing without Docker.
* **`config/catchments/assam_real_mini.inp`**: A custom, geo-anchored drainage network mapped exactly to **Lokhra-Lalganesh Road** and **Barsapara Road** in Guwahati, Assam.

### 🌐 Integration Bridge (Web UI)
To prove the backend is outputting correctly for Part C (Spatial UI), a local integration bridge is provided:
* **`server.py`**: A FastAPI server that runs the simulation and pipes the JSON ticks through a WebSocket.
* **`index.html`**: A premium Leaflet.js map that overlays the PySWMM data directly onto a real dark-mode map of Guwahati.

---

## 🚀 Setup & Installation

1. Ensure you have Python installed.
2. Install the core physics dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install the integration UI dependencies:
   ```bash
   pip install fastapi uvicorn websockets
   ```

---

## 💻 How to Run

### Option 1: Full Visual Integration Test (Recommended)
This runs the simulation and provides a beautiful, real-time 2D visualization of the flood spreading across the physical map of Guwahati.

1. Start the integration server:
   ```bash
   python server.py
   ```
2. Open your web browser and navigate to: **http://localhost:8080**
3. Click **"Initialize Sim Engine"** to watch the water flow and nodes dynamically turn red as they cross the 0.5m threshold.

### Option 2: Headless Backend (Production Mode)
This runs the pure physics engine and outputs the raw JSON payloads to your terminal (or Redis if available), exactly as the AI Agents and Digital Twin will consume it.

```bash
$env:SIMULATION_INP_PATH="config/catchments/assam_real_mini.inp"
python -m core.simulation.pyswmm_wrapper
```
*(On Mac/Linux, use `export SIMULATION_INP_PATH=...`)*

---

## 📡 Payload Schema for Teammates (Part B, C, D)

When the simulation runs, it broadcasts `SimulationTick` events in JSON format. Your teammates can consume this payload via Redis (or WebSockets via `server.py`).

**Example Payload:**
```json
{
  "run_id": "ui-demo",
  "sim_time": "2026-07-19T00:30:15",
  "step": 120,
  "critical_depth_m": 0.5,
  "nodes": [
    {
      "node_id": "J1",
      "depth_m": 0.62,
      "flow_cms": 3.45,
      "head_m": 50.62
    }
  ],
  "links": [
    {
      "link_id": "C1",
      "flow_cms": 3.40,
      "velocity_ms": 1.2,
      "passable": false
    }
  ]
}
```
*Note: A link is marked `"passable": false` if either of its connected nodes has a `depth_m` >= `critical_depth_m`.*
