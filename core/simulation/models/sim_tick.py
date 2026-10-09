"""
Simulation Tick models for PySWMM telemetry and flood state updates.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class NodeState(BaseModel):
    """Represents the state of a single node in the hydrology simulation."""
    node_id: str = Field(..., description="Unique identifier for the node (e.g., manhole, junction)")
    depth_m: float = Field(..., description="Current water depth at the node in meters")
    flooded: bool = Field(..., description="Whether the node is currently flooded (depth >= threshold)")
    flow_cms: float = Field(0.0, description="Current flow at the node in cubic meters per second")
    lat: Optional[float] = Field(None, description="Latitude of the node")
    lon: Optional[float] = Field(None, description="Longitude of the node")

class LinkState(BaseModel):
    """Represents the state of a single link (conduit) in the hydrology simulation."""
    link_id: str = Field(..., description="Unique identifier for the link")
    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Destination node ID")
    flow_cms: float = Field(0.0, description="Current flow through the link in cubic meters per second")
    passable: bool = Field(True, description="Whether the link is passable for routing")

class SimulationTick(BaseModel):
    """Represents a single step or tick in the hydrology simulation."""
    run_id: str = Field(..., description="Unique identifier for the simulation run")
    sim_time: datetime = Field(..., description="Current simulation time")
    step: int = Field(..., description="Simulation step index")
    critical_depth_m: float = Field(0.5, description="Depth threshold for flooding in meters")
    nodes: List[NodeState] = Field(default_factory=list, description="List of node states")
    links: List[LinkState] = Field(default_factory=list, description="List of link states")
