#!/usr/bin/env python3

"""
AUROVIA — Full City Engineering Layout
Generates a plan-view map from the existing road and Gazebo world data.
Does not modify the source project files.
"""

import ast
import math
import re
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle
from matplotlib.lines import Line2D
from matplotlib.collections import PatchCollection


ROOT = Path(__file__).resolve().parents[1]

ROAD_DATA = ROOT / "src/vehicle_system/vehicle_system/city_road_map_data.py"
WORLD_FILE = ROOT / "src/audibot_gazebo/worlds/project3_blue_world.sdf"
GRAPH_DATA = ROOT / "src/vehicle_system/vehicle_system/city_road_graph_data.py"

OUTPUT_PNG = ROOT / "docs/images/aurovia_full_city_layout.png"
OUTPUT_SVG = ROOT / "docs/images/aurovia_full_city_layout.svg"


# ---------------------------------------------------------
# LOAD ROAD SEGMENT DATA
# ---------------------------------------------------------

def load_assignment(path, variable):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable:
                    return ast.literal_eval(node.value)

    raise RuntimeError(f"{variable} not found in {path}")


road_segments = load_assignment(ROAD_DATA, "ROAD_SEGMENTS")

print("Loaded road segments:", len(road_segments))


# ---------------------------------------------------------
# LOAD GAZEBO WORLD
# ---------------------------------------------------------

world_text = WORLD_FILE.read_text(encoding="utf-8")

# Normalise the undeclared experimental prefix in memory.
world_text = re.sub(r"experimental:", "experimental_", world_text)

root = ET.fromstring(world_text)
world = root.find("world")

if world is None:
    raise RuntimeError("Gazebo world element not found.")


def read_pose(element):
    if element is None:
        return [0.0] * 6

    values = list(map(float, (element.text or "").split()))

    return (values + [0.0] * 6)[:6]


def transform_pose(parent, local):
    """Combine a local pose with a parent pose in the XY plane."""

    px, py, pz, _, _, pyaw = parent
    x, y, z, roll, pitch, yaw = local

    c = math.cos(pyaw)
    s = math.sin(pyaw)

    return [
        px + x * c - y * s,
        py + x * s + y * c,
        pz + z,
        roll,
        pitch,
        pyaw + yaw
    ]


def world_boxes():
    """Extract box geometry from top-level models and their links."""

    boxes = []

    for model in world.findall("model"):
        model_name = model.get("name", "")
        model_pose = read_pose(model.find("pose"))

        for link in model.findall("link"):
            link_pose = transform_pose(
                model_pose, read_pose(link.find("pose"))
            )

            for element_type in ("visual", "collision"):
                for element in link.findall(element_type):
                    box = element.find("geometry/box/size")

                    if box is None:
                        continue

                    size = list(map(float, box.text.split()))

                    local_pose = read_pose(element.find("pose"))
                    pose = transform_pose(link_pose, local_pose)

                    boxes.append({
                        "model": model_name,
                        "name": element.get("name", ""),
                        "kind": element_type,
                        "pose": pose,
                        "size": size
                    })

    return boxes


boxes = world_boxes()
print("Gazebo box geometries extracted:", len(boxes))


# ---------------------------------------------------------
# GEOMETRY HELPERS
# ---------------------------------------------------------

def box_corners(x, y, yaw, length, width):
    c = math.cos(yaw)
    s = math.sin(yaw)

    points = []

    for a, b in (
        (-length/2, -width/2),
        ( length/2, -width/2),
        ( length/2,  width/2),
        (-length/2,  width/2)
    ):
        points.append((
            x + a*c - b*s,
            y + a*s + b*c
        ))

    return points


road_patches = []
road_groups = {}

for segment in road_segments:
    zone = segment["zone"]

    corners = box_corners(
        segment["x"],
        segment["y"],
        segment["yaw"],
        segment["length"],
        segment["width"]
    )

    road_patches.append((zone, Polygon(corners, closed=True)))

    road_groups.setdefault(zone, []).append(
        (segment["x"], segment["y"])
    )


# ---------------------------------------------------------
# CREATE FIGURE
# ---------------------------------------------------------

fig, ax = plt.subplots(figsize=(17, 15))

fig.patch.set_facecolor("#f5f6f7")
ax.set_facecolor("#e9edf0")


# ---------------------------------------------------------
# ROAD NETWORK
# ---------------------------------------------------------

road_colours = {
    "zone1_main_urban_road": "#454b52",
    "zone2_three_stage_curved_road": "#454b52",
    "zone3_city_intersection": "#454b52",
    "zone5_open_test_area": "#454b52",
    "zone7_east_west_flyover": "#9b6542",
    "zone8_dual_access_roads": "#454b52"
}

for zone, patch in road_patches:
    ax.add_patch(
        Polygon(
            patch.get_xy(),
            closed=True,
            facecolor=road_colours.get(zone, "#454b52"),
            edgecolor="none",
            zorder=2
        )
    )


# ---------------------------------------------------------
# SIDEWALKS AND CURBS
# ---------------------------------------------------------

for item in boxes:

    name = item["name"].lower()
    model = item["model"].lower()

    if "sidewalk" not in name and "curb" not in name:
        if "sidewalk" not in model and "curb" not in model:
            continue

    if item["kind"] != "visual":
        continue

    x, y, z, roll, pitch, yaw = item["pose"]
    length, width, height = item["size"]

    ax.add_patch(
        Polygon(
            box_corners(x, y, yaw, length, width),
            closed=True,
            facecolor="#c6cbd0" if "sidewalk" in name else "#a3a8ad",
            edgecolor="none",
            zorder=3
        )
    )


# ---------------------------------------------------------
# BUILDINGS
# ---------------------------------------------------------

building_names = (
    "bungalow",
    "mid_rise",
    "residence",
    "commercial",
    "office"
)

building_models = {}

for item in boxes:

    model = item["model"].lower()

    if not any(name in model for name in building_names):
        continue

    if item["kind"] != "collision":
        continue

    x, y, z, roll, pitch, yaw = item["pose"]
    length, width, height = item["size"]

    key = item["model"]

    # Use one footprint per building model.
    if key in building_models:
        continue

    building_models[key] = (x, y, yaw, length, width, height)

for name, data in building_models.items():

    x, y, yaw, length, width, height = data

    ax.add_patch(
        Polygon(
            box_corners(x, y, yaw, length, width),
            closed=True,
            facecolor="#d5c5a8",
            edgecolor="#5c5143",
            linewidth=0.8,
            zorder=5
        )
    )

    ax.text(
        x, y, name.replace("zone6_", "").replace("_", "\n"),
        fontsize=5.5,
        ha="center",
        va="center",
        color="#302b25",
        zorder=6
    )


# ---------------------------------------------------------
# TRAFFIC SIGNAL LOCATIONS
# ---------------------------------------------------------

for model in world.findall("model"):

    name = model.get("name", "").lower()

    if "traffic_light" not in name:
        continue

    pose = read_pose(model.find("pose"))
    x, y = pose[0], pose[1]

    ax.add_patch(
        Circle(
            (x, y),
            radius=0.75,
            facecolor="#e34b45",
            edgecolor="black",
            linewidth=0.6,
            zorder=9
        )
    )

    ax.text(
        x + 1.0, y + 1.0,
        "Traffic signal",
        fontsize=6,
        zorder=10
    )


# ---------------------------------------------------------
# ROADWORKS CONES AND SIGN
# ---------------------------------------------------------

for model in world.findall("model"):

    name = model.get("name", "").lower()

    if not name.startswith("zone4_"):
        continue

    pose = read_pose(model.find("pose"))
    x, y = pose[0], pose[1]

    if "cone" in name:

        ax.add_patch(
            Circle(
                (x, y),
                radius=0.65,
                facecolor="#ef8c32",
                edgecolor="#75400e",
                linewidth=0.5,
                zorder=10
            )
        )

    elif "sign" in name:

        ax.add_patch(
            Rectangle(
                (x - 0.9, y - 0.6),
                1.8, 1.2,
                facecolor="#f2c14e",
                edgecolor="#5d4718",
                zorder=10
            )
        )

        ax.text(
            x, y, "ROAD\nWORKS",
            ha="center",
            va="center",
            fontsize=5.5,
            zorder=11
        )


# ---------------------------------------------------------
# ZONE LABELS
# ---------------------------------------------------------

zone_labels = {
    "zone1_main_urban_road": (40, -8, "ZONE 1\nMain Urban Road"),
    "zone2_three_stage_curved_road": (99, 18, "ZONE 2\nCurved Road"),
    "zone3_city_intersection": (143, 70, "ZONE 3\nSignalised Intersection"),
    "zone4_roadworks": (137, 105, "ZONE 4\nRoadworks"),
    "zone5_open_test_area": (122, 163, "ZONE 5\nOpen Testing Area"),
    "zone6_urban_environment": (163, 75, "ZONE 6\nUrban Buildings"),
    "zone7_east_west_flyover": (121, 53, "ZONE 7\nElevated Flyover"),
    "zone8_dual_access_roads": (121, 118, "ZONE 8\nDual Access Roads")
}

for _, (x, y, label) in zone_labels.items():

    ax.text(
        x, y, label,
        fontsize=8,
        fontweight="bold",
        ha="center",
        va="center",
        color="#17212b",
        bbox=dict(
            boxstyle="round,pad=0.4",
            facecolor="white",
            edgecolor="#66727c",
            alpha=0.92
        ),
        zorder=15
    )


# ---------------------------------------------------------
# LEGEND
# ---------------------------------------------------------

legend_items = [
    Rectangle((0, 0), 1, 1, facecolor="#454b52",
              label="Ground-level road"),
    Rectangle((0, 0), 1, 1, facecolor="#9b6542",
              label="Elevated flyover"),
    Rectangle((0, 0), 1, 1, facecolor="#c6cbd0",
              label="Sidewalk"),
    Rectangle((0, 0), 1, 1, facecolor="#d5c5a8",
              edgecolor="#5c5143", label="Building footprint"),
    Line2D([0], [0], marker="o", color="w",
           markerfacecolor="#e34b45", markeredgecolor="black",
           markersize=7, label="Traffic signal"),
    Line2D([0], [0], marker="o", color="w",
           markerfacecolor="#ef8c32", markeredgecolor="#75400e",
           markersize=7, label="Roadworks cone")
]

ax.legend(
    handles=legend_items,
    loc="upper left",
    fontsize=8,
    framealpha=0.95
)


# ---------------------------------------------------------
# SCALE BAR AND NORTH ARROW
# ---------------------------------------------------------

x0, y0 = 8, 178

ax.plot([x0, x0 + 20], [y0, y0],
        color="black", linewidth=2.5, zorder=20)

ax.plot([x0, x0], [y0 - 1, y0 + 1],
        color="black", linewidth=1.2)

ax.plot([x0 + 20, x0 + 20], [y0 - 1, y0 + 1],
        color="black", linewidth=1.2)

ax.text(
    x0 + 10, y0 - 2.5,
    "20 m",
    ha="center",
    fontsize=8
)

ax.annotate(
    "N",
    xy=(190, 178),
    xytext=(190, 168),
    ha="center",
    fontsize=12,
    fontweight="bold",
    arrowprops=dict(arrowstyle="-|>", linewidth=1.5)
)


# ---------------------------------------------------------
# AXES AND TITLE
# ---------------------------------------------------------

ax.set_xlim(-8, 210)
ax.set_ylim(-15, 190)

ax.set_aspect("equal", adjustable="box")

ax.set_xlabel("East–West coordinate (m)", fontsize=10)
ax.set_ylabel("North–South coordinate (m)", fontsize=10)

ax.set_xticks(range(0, 211, 20))
ax.set_yticks(range(-10, 191, 20))

ax.grid(
    True,
    linestyle=":",
    linewidth=0.45,
    alpha=0.5,
    zorder=0
)

fig.suptitle(
    "AUROVIA — URBAN CITY ENGINEERING LAYOUT",
    fontsize=17,
    fontweight="bold",
    y=0.97
)

ax.set_title(
    "Eight-zone road network, elevated flyover and urban infrastructure",
    fontsize=10,
    pad=12
)

fig.text(
    0.5, 0.025,
    "Source: AUROVIA Gazebo world geometry and generated road-segment data",
    ha="center",
    fontsize=8,
    color="#555555"
)

plt.tight_layout(rect=[0.02, 0.05, 0.98, 0.94])


# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------

fig.savefig(
    OUTPUT_PNG,
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    OUTPUT_SVG,
    bbox_inches="tight"
)

plt.close(fig)

print("\nAUROVIA CITY MAP GENERATED")
print("PNG:", OUTPUT_PNG)
print("SVG:", OUTPUT_SVG)
print("Building footprints:", len(building_models))
print("Road segments:", len(road_segments))
print("Gazebo geometries inspected:", len(boxes))
