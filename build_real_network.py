import json
import urllib.request
import math
from collections import defaultdict
import os

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

print("Fetching OSM data for Guwahati Silsako area...")
# Fetch a tiny 500m x 500m bounding box to prevent timeouts
q = '[out:json];way["highway"~"primary|secondary|tertiary|residential"](26.140,91.735,26.145,91.745);out geom;'
req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=q.encode('utf-8'))
req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
res = urllib.request.urlopen(req).read()
data = json.loads(res.decode('utf-8'))

nodes = {}
links = []

for way in data.get('elements', []):
    geom = way.get('geometry', [])
    nodes_ids = way.get('nodes', [])
    for i in range(len(geom)):
        nid = f"N{nodes_ids[i]}"
        nodes[nid] = (geom[i]['lon'], geom[i]['lat'])
        if i > 0:
            prev_nid = f"N{nodes_ids[i-1]}"
            links.append((prev_nid, nid))

# Build adjacency list
adj = defaultdict(list)
for u, v in links:
    adj[u].append(v)
    adj[v].append(u)

# Pick a central node as outfall
outfall = list(nodes.keys())[0]
tree_links = []
visited = {outfall}
queue = [outfall]

# BFS to build a strictly converging drainage tree (perfect for KINWAVE)
limit = 120 # Grab up to 120 real street nodes
while queue and len(visited) < limit:
    curr = queue.pop(0)
    for neighbor in adj[curr]:
        if neighbor not in visited and len(visited) < limit:
            visited.add(neighbor)
            queue.append(neighbor)
            # Edge directed FROM neighbor TO curr (so water flows towards outfall)
            tree_links.append((neighbor, curr))

selected_nodes = list(visited)
selected_nodes.remove(outfall)
selected_links = tree_links

# Generate INP
inp_content = """[TITLE]
Guwahati Real Street Network (OSM)

[OPTIONS]
FLOW_UNITS           CMS
INFILTRATION         HORTON
FLOW_ROUTING         KINWAVE
LINK_OFFSETS         DEPTH
MIN_SLOPE            0
ALLOW_PONDING        NO
SKIP_STEADY_STATE    NO
START_DATE           07/19/2026
START_TIME           00:00:00
REPORT_START_DATE    07/19/2026
REPORT_START_TIME    00:00:00
END_DATE             07/19/2026
END_TIME             01:00:00
REPORT_STEP          00:02:00
WET_STEP             00:01:00
DRY_STEP             01:00:00
ROUTING_STEP         00:00:15

[JUNCTIONS]
"""

for n in selected_nodes:
    inp_content += f"{n} 50 2 0 0 0\n"

inp_content += f"\n[OUTFALLS]\n{outfall} 40 FREE NO\n\n[CONDUITS]\n"

xsections = "[XSECTIONS]\n"
for i, l in enumerate(selected_links):
    cname = f"C{i}"
    dist = max(1.0, haversine(nodes[l[0]][1], nodes[l[0]][0], nodes[l[1]][1], nodes[l[1]][0]))
    inp_content += f"{cname} {l[0]} {l[1]} {dist:.2f} 0.01 0 0 0 0\n"
    xsections += f"{cname} CIRCULAR 0.5 0 0 0 1\n"

inp_content += f"\n{xsections}\n[INFLOWS]\n"
# Flood the outer edges heavily so water flows in
for i, n in enumerate(selected_nodes[-20:]):
    inp_content += f"{n} FLOW \"\" FLOW 1.0 1.0 5.0\n"

inp_content += "\n[COORDINATES]\n"
for n in selected_nodes + [outfall]:
    inp_content += f"{n} {nodes[n][0]:.6f} {nodes[n][1]:.6f}\n"

os.makedirs("config/catchments", exist_ok=True)
with open("config/catchments/guwahati_osm.inp", "w") as f:
    f.write(inp_content)

print(f"Successfully mapped {len(selected_nodes)+1} real nodes and {len(selected_links)} conduits from OSM!")
