#!/usr/bin/env python3
"""Build a preliminary 3-D-aware road graph from extracted road segments."""

import ast
import math
from pathlib import Path
from collections import defaultdict, deque

ROOT = Path(__file__).resolve().parents[1]
MAP_FILE = ROOT / "src/vehicle_system/vehicle_system/city_road_map_data.py"
OUTPUT_FILE = ROOT / "src/vehicle_system/vehicle_system/city_road_graph_data.py"

# Conservative tolerances: nearby roads at different heights must stay separate.
XY_JOIN = 0.20
Z_JOIN = 0.20
INTERSECTION_Z_LIMIT = 0.75
EPS = 1e-8


def load_segments():
    tree = ast.parse(MAP_FILE.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "ROAD_SEGMENTS"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise RuntimeError("ROAD_SEGMENTS not found in generated map.")


def cross(ax, ay, bx, by):
    return ax * by - ay * bx


def make_segment(item, index):
    yaw = item["yaw"]
    half = item["length"] / 2.0
    dx, dy = math.cos(yaw) * half, math.sin(yaw) * half
    return {
        "index": index,
        "zone": item["zone"],
        "name": item.get("collision", item.get("link", str(index))),
        "z": item["z"],
        "x1": item["x"] - dx,
        "y1": item["y"] - dy,
        "x2": item["x"] + dx,
        "y2": item["y"] + dy,
        "cuts": [0.0, 1.0],
    }


def find_intersections(segments):
    # Split long roads where other road centre-lines cross them.
    for i, a in enumerate(segments):
        px, py = a["x1"], a["y1"]
        rx, ry = a["x2"] - px, a["y2"] - py
        for b in segments[i + 1:]:
            if abs(a["z"] - b["z"]) > INTERSECTION_Z_LIMIT:
                continue

            qx, qy = b["x1"], b["y1"]
            sx, sy = b["x2"] - qx, b["y2"] - qy
            qpx, qpy = qx - px, qy - py
            denom = cross(rx, ry, sx, sy)

            if abs(denom) < EPS:
                # Parallel roads only share a connection when they are
                # geometrically collinear and at compatible elevations.
                r2 = rx * rx + ry * ry
                s2 = sx * sx + sy * sy
                if r2 < EPS or s2 < EPS:
                    continue

                perpendicular_distance = abs(cross(qpx, qpy, rx, ry)) / math.sqrt(r2)
                if perpendicular_distance > 0.15:
                    continue

                # Split either road wherever an endpoint of the other road
                # lies on it. This represents collinear overlaps explicitly.
                for bx, by, bu in (
                    (b["x1"], b["y1"], 0.0),
                    (b["x2"], b["y2"], 1.0),
                ):
                    t = ((bx - px) * rx + (by - py) * ry) / r2
                    if -EPS <= t <= 1.0 + EPS:
                        a["cuts"].append(min(1.0, max(0.0, t)))

                for ax, ay in (
                    (a["x1"], a["y1"]),
                    (a["x2"], a["y2"]),
                ):
                    u = ((ax - qx) * sx + (ay - qy) * sy) / s2
                    if -EPS <= u <= 1.0 + EPS:
                        b["cuts"].append(min(1.0, max(0.0, u)))
                continue
            t = cross(qpx, qpy, sx, sy) / denom
            u = cross(qpx, qpy, rx, ry) / denom

            if -0.0002 <= t <= 1.0002 and -0.0002 <= u <= 1.0002:
                a["cuts"].append(min(1.0, max(0.0, t)))
                b["cuts"].append(min(1.0, max(0.0, u)))


def build_graph(segments):
    find_intersections(segments)

    # Create one point for each endpoint/intersection on each road segment.
    points = []
    pieces = []

    for seg in segments:
        cuts = sorted(seg["cuts"])
        unique = []
        for t in cuts:
            if not unique or abs(t - unique[-1]) > 1e-6:
                unique.append(t)

        ids = []
        for t in unique:
            x = seg["x1"] + t * (seg["x2"] - seg["x1"])
            y = seg["y1"] + t * (seg["y2"] - seg["y1"])
            ids.append(len(points))
            points.append((x, y, seg["z"]))

        for j in range(len(ids) - 1):
            p, q = ids[j], ids[j + 1]
            a, b = points[p], points[q]
            length = math.dist(a[:2], b[:2])
            if length > 0.03:
                pieces.append((p, q, length, seg["zone"], seg["name"]))

    # Cluster geometrically coincident points, but never merge separated levels.
    parent = list(range(len(points)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    grid = defaultdict(list)
    cell_size = XY_JOIN

    for i, (x, y, z) in enumerate(points):
        gx, gy = math.floor(x / cell_size), math.floor(y / cell_size)
        for ix in range(gx - 1, gx + 2):
            for iy in range(gy - 1, gy + 2):
                for j in grid[(ix, iy)]:
                    ox, oy, oz = points[j]
                    if math.hypot(x - ox, y - oy) <= XY_JOIN and abs(z - oz) <= Z_JOIN:
                        union(i, j)
        grid[(gx, gy)].append(i)

    members = defaultdict(list)
    for i, p in enumerate(points):
        members[find(i)].append(p)

    roots = sorted(members, key=lambda r: (
        sum(p[0] for p in members[r]) / len(members[r]),
        sum(p[1] for p in members[r]) / len(members[r]),
        sum(p[2] for p in members[r]) / len(members[r]),
    ))
    node_id = {root: i for i, root in enumerate(roots)}
    point_node = {i: node_id[find(i)] for i in range(len(points))}

    nodes = []
    for root in roots:
        group = members[root]
        nodes.append({
            "id": node_id[root],
            "x": round(sum(p[0] for p in group) / len(group), 4),
            "y": round(sum(p[1] for p in group) / len(group), 4),
            "z": round(sum(p[2] for p in group) / len(group), 4),
        })

    edge_map = {}
    for p, q, length, zone, name in pieces:
        u, v = point_node[p], point_node[q]
        if u == v:
            continue
        key = tuple(sorted((u, v)))
        if key not in edge_map or length < edge_map[key]["length"]:
            edge_map[key] = {
                "u": key[0],
                "v": key[1],
                "length": round(length, 4),
                "zone": zone,
                "segment": name,
            }

    edges = list(edge_map.values())
    return nodes, edges


def components(nodes, edges):
    adj = defaultdict(list)
    for e in edges:
        adj[e["u"]].append(e["v"])
        adj[e["v"]].append(e["u"])

    unseen = {n["id"] for n in nodes}
    result = []

    while unseen:
        start = next(iter(unseen))
        queue = deque([start])
        unseen.remove(start)
        group = []

        while queue:
            u = queue.popleft()
            group.append(u)
            for v in adj[u]:
                if v in unseen:
                    unseen.remove(v)
                    queue.append(v)

        result.append(group)

    return sorted(result, key=len, reverse=True), adj


def main():
    raw = load_segments()
    segments = [make_segment(item, i) for i, item in enumerate(raw)]
    nodes, edges = build_graph(segments)
    groups, adj = components(nodes, edges)

    OUTPUT_FILE.write_text(
        "# Generated by scripts/build_city_road_graph.py; do not edit manually.\n"
        f"NODES = {nodes!r}\n"
        f"EDGES = {edges!r}\n"
    )

    print("===== CITY ROAD GRAPH =====")
    print(f"Input road segments: {len(raw)}")
    print(f"Graph nodes: {len(nodes)}")
    print(f"Graph edges: {len(edges)}")
    print(f"Connected components: {len(groups)}")
    print(f"Graph data: {OUTPUT_FILE.relative_to(ROOT)}")

    print("\nLargest components:")
    node_lookup = {n["id"]: n for n in nodes}
    edge_lookup = defaultdict(list)
    for e in edges:
        edge_lookup[e["u"]].append(e)
        edge_lookup[e["v"]].append(e)

    for i, group in enumerate(groups[:8], start=1):
        zone_names = set()
        group_set = set(group)
        for e in edges:
            if e["u"] in group_set and e["v"] in group_set:
                zone_names.add(e["zone"])
        print(
            f"  Component {i}: {len(group)} nodes, "
            f"{len([e for e in edges if e['u'] in group_set and e['v'] in group_set])} edges, "
            f"zones={', '.join(sorted(zone_names))}"
        )

    start = min(nodes, key=lambda n: math.hypot(n["x"], n["y"]))
    print(
        f"\nNearest road node to vehicle start (0,0): "
        f"id={start['id']}, x={start['x']}, y={start['y']}, z={start['z']}, "
        f"distance={math.hypot(start['x'], start['y']):.2f} m"
    )

    degree_one = [n for n in nodes if len(adj[n["id"]]) == 1]
    print(f"Dead-end nodes: {len(degree_one)}")
    for n in degree_one[:10]:
        print(f"  node {n['id']}: ({n['x']}, {n['y']}, {n['z']})")

    if not nodes or not edges:
        raise SystemExit("ERROR: The road graph is empty or has no edges.")


if __name__ == "__main__":
    main()
