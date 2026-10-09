import os
import asyncio
import logging
from typing import AsyncIterator, Optional, Dict, Any
from pyswmm import Simulation, Nodes, Links

from .models.sim_tick import SimulationTick, NodeState, LinkState
from .flood_state import FloodState

logger = logging.getLogger(__name__)

class SimulationRunner:
    """Runner for PySWMM simulations, extracting state and building ticks."""
    
    def __init__(self, inp_path: str, config: Dict[str, Any]):
        self.inp_path = inp_path
        self.config = config
        self.sim: Optional[Simulation] = None
        self.run_id = config.get("run_id", "default-run")
        self.critical_depth_m = config.get("critical_depth_threshold_m", 0.5)
        
        self._swmm_nodes = None
        self._swmm_links = None
        
        self.flood_state = FloodState(critical_depth_m=self.critical_depth_m)
        self.step_index = 0
        
    def load(self) -> None:
        """Initialize the PySWMM Simulation."""
        if not os.path.exists(self.inp_path):
            raise FileNotFoundError(f"SWMM INP file not found: {self.inp_path}")
            
        logger.info(f"Loading PySWMM simulation from {self.inp_path}")
        self.sim = Simulation(self.inp_path)
        self._swmm_nodes = Nodes(self.sim)
        self._swmm_links = Links(self.sim)
        self.step_index = 0
        
    def get_node_depth(self, node_id: str) -> float:
        """Get the current depth of a specific node."""
        if not self._swmm_nodes or node_id not in self._swmm_nodes:
            return 0.0
        return self._swmm_nodes[node_id].depth
        
    def get_conduit_flow(self, link_id: str) -> float:
        """Get the current flow of a specific link."""
        if not self._swmm_links or link_id not in self._swmm_links:
            return 0.0
        return self._swmm_links[link_id].flow
        
    def step(self) -> SimulationTick:
        """Perform a single step mapping PySWMM state to a SimulationTick."""
        if not self.sim:
            raise RuntimeError("Simulation not loaded.")
            
        sim_time = self.sim.current_time
        
        tick = SimulationTick(
            run_id=self.run_id,
            sim_time=sim_time,
            step=self.step_index,
            critical_depth_m=self.critical_depth_m,
            nodes=[],
            links=[]
        )
        
        # Extract Node state
        for node in self._swmm_nodes:
            depth = node.depth
            flooded = depth >= self.critical_depth_m
            tick.nodes.append(NodeState(
                node_id=node.nodeid,
                depth_m=depth,
                flooded=flooded,
                flow_cms=node.total_inflow,
            ))
            
        # Extract Link state
        for link in self._swmm_links:
            connections = link.connections
            tick.links.append(LinkState(
                link_id=link.linkid,
                from_node=connections[0],
                to_node=connections[1],
                flow_cms=link.flow,
                passable=True
            ))
            
        # Update internal flood state (will also update passable flag on links)
        self.flood_state.update(tick)
        
        self.step_index += 1
        return tick

    async def run(self) -> AsyncIterator[SimulationTick]:
        """Run the simulation loop asynchronously."""
        if not self.sim:
            self.load()
            
        logger.info(f"Starting PySWMM simulation run {self.run_id}")
        
        try:
            with self.sim:
                for _ in self.sim:
                    tick = self.step()
                    yield tick
                    await asyncio.sleep(0) # Yield control to async loop
        finally:
            self.sim = None
            
    def reset(self) -> None:
        """Reset the simulation."""
        if self.sim:
            self.sim.close()
            self.sim = None
        self.step_index = 0
        self.flood_state = FloodState(critical_depth_m=self.critical_depth_m)
