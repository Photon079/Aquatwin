import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from core.simulation.simulation_runner import SimulationRunner
import argparse

def parse_coordinates(inp_path):
    coords = {}
    with open(inp_path, 'r') as f:
        in_coords = False
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            if line.startswith('['):
                in_coords = (line == '[COORDINATES]')
                continue
            if in_coords:
                parts = line.split()
                if len(parts) >= 3:
                    coords[parts[0]] = (float(parts[1]), float(parts[2]))
    return coords

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inp', default='config/catchments/dummy_test.inp')
    args = parser.parse_args()
    
    runner = SimulationRunner(args.inp, {"run_id": "test-2d", "critical_depth_threshold_m": 0.5})
    runner.load()
    
    coords = parse_coordinates(args.inp)
    
    G = nx.Graph()
    for link in runner._swmm_links:
        G.add_edge(link.connections[0], link.connections[1], id=link.linkid)
        
    for node in runner._swmm_nodes:
        if node.nodeid not in G:
            G.add_node(node.nodeid)

    pos = coords.copy()
    missing_nodes = [n for n in G.nodes if n not in pos]
    if missing_nodes:
        spring_pos = nx.spring_layout(G)
        for n in missing_nodes:
            pos[n] = spring_pos[n]

    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Enter PySWMM simulation manually
    sim_iter = iter(runner.sim)
    
    def update(frame):
        try:
            # Advance simulation by one step
            next(sim_iter)
            tick = runner.step()
        except StopIteration:
            return
            
        ax.clear()
        
        flooded_nodes = runner.flood_state.flooded_nodes()
        passable_edges = runner.flood_state.passable_edges()
        
        node_colors = ['red' if node in flooded_nodes else 'lightblue' for node in G.nodes]
        
        edge_colors = []
        for u, v in G.edges:
            edge_id = G.get_edge_data(u, v).get('id')
            if edge_id in passable_edges:
                edge_colors.append('black')
            else:
                edge_colors.append('red') 
        
        ax.set_title(f"2D Map | Time: {tick.sim_time} | Step: {tick.step} | Flooded Nodes: {len(flooded_nodes)}")
        nx.draw(G, pos, ax=ax, with_labels=True, node_color=node_colors, edge_color=edge_colors,
                node_size=500, font_size=8, font_weight='bold')

    ani = animation.FuncAnimation(fig, update, interval=100, cache_frame_data=False)
    plt.show()

if __name__ == '__main__':
    main()
