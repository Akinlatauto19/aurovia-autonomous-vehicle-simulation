#!/usr/bin/env python3

import ast
import math
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path.cwd()
WORLD = ROOT / "src/audibot_gazebo/worlds/project3_blue_world.sdf"
OUTPUT = ROOT / "src/vehicle_system/vehicle_system/city_road_map_data.py"

TARGETS = {
    "zone1_main_urban_road",
    "zone2_three_stage_curved_road",
    "zone3_city_intersection",
    "zone5_open_test_area",
    "zone7_east_west_flyover",
    "zone8_dual_access_roads",
}

ROAD_WIDTH = 7.6
WIDTH_TOLERANCE = 0.25
MAX_THICKNESS = 0.25


def numbers(element):
    if element is None or not element.text:
        return [0.0] * 6
    values = [float(v) for v in element.text.split()]
    return (values + [0.0] * 6)[:6]


def compose_pose(parent, local):
    px, py, pz, _, _, pyaw = parent
    x, y, z, _, _, yaw = local
    c, s = math.cos(pyaw), math.sin(pyaw)
    return [
        px + c * x - s * y,
        py + s * x + c * y,
        pz + z,
        0.0, 0.0, pyaw + yaw,
    ]


def main():
    if not WORLD.is_file():
        sys.exit(f"ERROR: World file not found: {WORLD}")

    # The existing SDF contains an experimental: prefix without a declared
    # XML namespace. Normalize it in memory; never modify the world file.
    raw = WORLD.read_text(encoding="utf-8")
    raw = re.sub(r"experimental:", "experimental_", raw)
    world = ET.fromstring(raw)

    segments = []
    counts = defaultdict(int)

    for model in world.findall(".//model"):
        name = model.get("name", "")
        if name not in TARGETS:
            continue

        model_pose = numbers(model.find("pose"))

        for link in model.findall("link"):
            link_pose = compose_pose(
                model_pose, numbers(link.find("pose"))
            )

            for collision in (link.findall("collision") or link.findall("visual")):
                box = collision.find("geometry/box")
                if box is None:
                    continue

                size_element = box.find("size")
                if size_element is None or not size_element.text:
                    continue

                size = [float(v) for v in size_element.text.split()]
                if len(size) != 3:
                    continue

                sx, sy, sz = size
                width_x = abs(sx - ROAD_WIDTH) <= WIDTH_TOLERANCE
                width_y = abs(sy - ROAD_WIDTH) <= WIDTH_TOLERANCE

                # Keep thin, road-width box surfaces, not guardrails,
                # support pillars, cones, or unrelated objects.
                if not (width_x or width_y):
                    continue
                if sz <= 0.0 or sz > MAX_THICKNESS:
                    continue

                pose = compose_pose(
                    link_pose, numbers(collision.find("pose"))
                )

                if width_y:
                    length = sx
                    yaw = pose[5]
                else:
                    length = sy
                    yaw = pose[5] + math.pi / 2.0

                if length < 0.20:
                    continue

                segment = {
                    "zone": name,
                    "link": link.get("name", ""),
                    "collision": collision.get("name", ""),
                    "x": round(pose[0], 6),
                    "y": round(pose[1], 6),
                    "z": round(pose[2], 6),
                    "length": round(length, 6),
                    "width": round(ROAD_WIDTH, 3),
                    "thickness": round(sz, 6),
                    "yaw": round(
                        math.atan2(math.sin(yaw), math.cos(yaw)), 8
                    ),
                }
                segments.append(segment)
                counts[name] += 1

    if not segments:
        sys.exit(
            "ERROR: No matching road surfaces were extracted. "
            "No map file was written."
        )

    # Keep the data as Python so the ROS package can import it without
    # depending on the source-world path at runtime.
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        '"""Road-surface segments extracted from project3_blue_world.sdf."""\n\n'
        "ROAD_SEGMENTS = "
        + repr(segments)
        + "\n",
        encoding="utf-8",
    )

    print("===== CITY ROAD MAP GENERATED =====")
    print(f"World: {WORLD.relative_to(ROOT)}")
    print(f"Map:   {OUTPUT.relative_to(ROOT)}")
    print(f"Total road-surface segments: {len(segments)}")
    print()
    print("Segments by zone:")
    for zone in sorted(TARGETS):
        print(f"  {zone}: {counts[zone]}")

    print()
    print("Extracted map bounds:")
    for key in ("x", "y", "z"):
        values = [segment[key] for segment in segments]
        print(f"  {key}: {min(values):.2f} to {max(values):.2f}")

    print()
    print("Representative segments:")
    for zone in sorted(TARGETS):
        found = next((s for s in segments if s["zone"] == zone), None)
        if found:
            print(
                f"  {zone}: "
                f"({found['x']:.2f}, {found['y']:.2f}, {found['z']:.2f}), "
                f"length={found['length']:.2f} m, "
                f"yaw={found['yaw']:.3f} rad"
            )

    print()
    print("The world file and existing navigator were not modified.")


if __name__ == "__main__":
    main()
