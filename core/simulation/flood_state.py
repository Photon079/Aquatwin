from typing import Dict, Set
from .models.sim_tick import SimulationTick

class FloodState:
    """Manages the active flood state of nodes and passable edges."""
    
    def __init__(self, critical_depth_m: float = 0.5):
        self.critical_depth_m = critical_depth_m
        self._flooded_nodes: Set[str] = set()
        self._passable_edges: Set[str] = set()
        self._all_edges: Set[str] = set()
        self._node_depths: Dict[str, float] = {}
        
    def check_threshold(self, node_id: str, depth_m: float) -> bool:
        """Check if a node depth exceeds the critical threshold."""
        return depth_m >= self.critical_depth_m
        
    def update(self, tick: SimulationTick) -> None:
        """Update state based on a simulation tick."""
        for node in tick.nodes:
            self._node_depths[node.node_id] = node.depth_m
            if self.check_threshold(node.node_id, node.depth_m):
                self._flooded_nodes.add(node.node_id)
            else:
                self._flooded_nodes.discard(node.node_id)
                
        for link in tick.links:
            self._all_edges.add(link.link_id)
            if link.from_node in self._flooded_nodes or link.to_node in self._flooded_nodes:
                self._passable_edges.discard(link.link_id)
                link.passable = False
            else:
                self._passable_edges.add(link.link_id)
                link.passable = True
                
    def flooded_nodes(self) -> Set[str]:
        """Return the set of currently flooded nodes."""
        return set(self._flooded_nodes)
        
    def passable_edges(self) -> Set[str]:
        """Return the set of currently passable edges."""
        return set(self._passable_edges)
        
    def snapshot(self) -> dict:
        """Return a serializable snapshot of the current flood state."""
        return {
            "critical_depth_m": self.critical_depth_m,
            "flooded_nodes_count": len(self._flooded_nodes),
            "passable_edges_count": len(self._passable_edges),
            "flooded_nodes": list(self._flooded_nodes),
            "passable_edges": list(self._passable_edges)
        }
