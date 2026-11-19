#!/usr/bin/env python3
"""
AUROVIA — IEEE-style engineering cartographic figures.

Generates:
  Figure 5.1: Overall city layout (plan view)
  Figure 5.2: Zone 3 intersection and Zone 7 flyover detail

The original generator and its outputs are not modified.
"""

import ast
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[1]

ROAD_DATA = ROOT / "src/vehicle_system/vehicle_system/city_road_map_data.py"
WORLD_FILE = ROOT / "src/audibot_gazebo/worlds/project3_blue_world.sdf"

OUT_DIR = ROOT / "docs/images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FIG51_PNG = OUT_DIR / "aurovia_overall_city_map_v2.png"
FIG51_SVG = OUT_DIR / "aurovia_overall_city_map_v2.svg"
FIG52_PNG = OUT_DIR / "aurovia_flyover_intersection_detail_v2.png"
FIG52_SVG = OUT_DIR / "aurovia_flyover_intersection_detail_v2.svg"


# ------------------------------------------------------------
# TECHNICAL DRAWING STYLE
# ------------------------------------------------------------

INK = "#202020"
DARK = "#555555"
ROAD = "#d1d1d1"
ROAD_EDGE = "#555555"
SIDEWALK = "#e8e8e8"
BUILDING = "#f7f7f7"
BUILDING_EDGE = "#555555"
OPEN_AREA = "#eeeeee"
PAPER = "#ffffff"
LIGHT = "#f5f5f5"
GRID = "#dedede"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "figure.facecolor": PAPER,
    "axes.facecolor": PAPER,
    "savefig.facecolor": PAPER,
    "svg.fonttype": "none",
})


# ------------------------------------------------------------
# LOAD SOURCE ROAD DATA
# ------------------------------------------------------------

def load_assignment(path, variable):
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable:
                    return ast.literal_eval(node.value)

    raise RuntimeError(f"Could not find {variable} in {path}")


road_segments = load_assignment(ROAD_DATA, "ROAD_SEGMENTS")


# ------------------------------------------------------------
# GEOMETRY HELPERS
# ------------------------------------------------------------

def corners(x, y, yaw, length, width):
    c, s = math.cos(yaw), math.sin(yaw)
    points = []

    for a, b in (
        (-length / 2, -width / 2),
        ( length / 2, -width / 2),
        ( length / 2,  width / 2),
        (-length / 2,  width / 2),
    ):
        points.append((
            x + a * c - b * s,
            y + a * s + b * c
        ))

    return points


def add_box(ax, x, y, yaw, length, width, face, edge=INK,
            linewidth=0.55, zorder=4):
    patch = Polygon(
        corners(x, y, yaw, length, width),
        closed=True,
        facecolor=face,
        edgecolor=edge,
        linewidth=linewidth,
        joinstyle="round",
        zorder=zorder
    )
    ax.add_patch(patch)
    return patch


def add_text(ax, x, y, text, size=8, weight="normal",
             ha="center", va="center", zorder=20, **kwargs):
    ax.text(
        x, y, text,
        fontsize=size,
        fontweight=weight,
        color=INK,
        ha=ha,
        va=va,
        zorder=zorder,
        **kwargs
    )


# ------------------------------------------------------------
# READ WORLD FILE FOR FLYOVER LINK ELEVATIONS
# ------------------------------------------------------------

world_text = WORLD_FILE.read_text(encoding="utf-8")
world_text = re.sub(r"experimental:", "experimental_", world_text)
xml_root = ET.fromstring(world_text)
world = xml_root.find("world")

if world is None:
    raise RuntimeError("Could not find <world> in Gazebo SDF.")


def pose_values(element):
    if element is None or not element.text:
        return [0.0] * 6

    values = [float(v) for v in element.text.split()]
    return (values + [0.0] * 6)[:6]


def combine_pose(parent, local):
    px, py, pz, _, _, pyaw = parent
    x, y, z, roll, pitch, yaw = local

    c, s = math.cos(pyaw), math.sin(pyaw)

    return [
        px + x * c - y * s,
        py + x * s + y * c,
        pz + z,
        roll,
        pitch,
        pyaw + yaw
    ]


flyover_profile = []

flyover_model = world.find(
    "model[@name='zone7_east_west_flyover']"
)

if flyover_model is not None:
    model_pose = pose_values(flyover_model.find("pose"))

    for link in flyover_model.findall("link"):
        name = link.get("name", "")

        if not re.fullmatch(r"road_segment_\d+", name):
            continue

        link_pose = combine_pose(
            model_pose,
            pose_values(link.find("pose"))
        )

        flyover_profile.append({
            "name": name,
            "x": link_pose[0],
            "y": link_pose[1],
            "z": link_pose[2],
            "pitch": link_pose[4]
        })

flyover_profile.sort(key=lambda item: item["x"])


# ------------------------------------------------------------
# COMMON ROAD DRAWING
# ------------------------------------------------------------

def draw_roads(ax, zones=None, flyover_emphasis=False):
    patches = []
    flyover_patches = []

    for segment in road_segments:
        zone = segment["zone"]

        if zones is not None and zone not in zones:
            continue

        patch = Polygon(
            corners(
                segment["x"],
                segment["y"],
                segment["yaw"],
                segment["length"],
                segment["width"]
            ),
            closed=True
        )

        if zone == "zone7_east_west_flyover":
            flyover_patches.append(patch)
        else:
            patches.append(patch)

    if patches:
        ax.add_collection(PatchCollection(
            patches,
            facecolor=ROAD,
            edgecolor=ROAD_EDGE,
            linewidth=0.12,
            zorder=2
        ))

    if flyover_patches:
        ax.add_collection(PatchCollection(
            flyover_patches,
            facecolor="#777777" if flyover_emphasis else "#999999",
            edgecolor=INK,
            linewidth=0.18,
            zorder=7
        ))


# ------------------------------------------------------------
# BUILDING FOOTPRINTS
# Positions and dimensions from the inspected AUROVIA SDF.
# ------------------------------------------------------------

ZONE1_BUILDINGS = [
    (25,  12, 8, 7, 18),
    (25, -12, 9, 7, 24),
    (43,  12.5, 9, 7, 29),
    (43, -12.5, 8, 7, 20),
    (61,  12, 8, 7, 22),
    (61, -12, 9, 7, 31),
    (75,  12, 8, 7, 17),
    (75, -12, 8, 7, 23),
]

ZONE6_BUILDINGS = [
    (91,  33, 9, 7, 3.4, "Bungalow"),
    (158, 33, 8, 7, 3.2, "Bungalow"),
    (87,  61, 10, 8, 8.0, "Mid-rise"),
    (104, 62, 8, 7, 6.2, "Residence"),
    (145, 62, 10, 8, 10.0, "Commercial"),
    (164, 62, 11, 8, 9.2, "Office"),
    (104, 82, 8, 7, 5.6, "Residence"),
    (139, 82, 9, 7, 7.0, "Residence"),
]


def draw_buildings(ax, zone1=True, zone6=True, labels=False):
    if zone1:
        for index, (x, y, length, width, height) in enumerate(
            ZONE1_BUILDINGS, start=1
        ):
            add_box(
                ax, x, y, 0, length, width,
                BUILDING, BUILDING_EDGE, 0.7, 5
            )

            if labels:
                add_text(
                    ax, x, y, f"Z1-{index}",
                    size=5.8, weight="bold", zorder=6
                )

    if zone6:
        for index, (x, y, length, width, height, kind) in enumerate(
            ZONE6_BUILDINGS, start=1
        ):
            add_box(
                ax, x, y, 0, length, width,
                "#e3e3e3", BUILDING_EDGE, 0.65, 5
            )

            if labels:
                add_text(
                    ax, x, y, f"{kind}\n{index}",
                    size=5.5, zorder=6
                )


# ------------------------------------------------------------
# SIDEWALKS AND CURBS — SELECTED URBAN AREAS
# ------------------------------------------------------------

def draw_zone1_sidewalks(ax):
    for x in (10, 30, 50, 70):
        for y in (-5, 5):
            add_box(
                ax, x, y, 0, 20, 1.8,
                SIDEWALK, "#999999", 0.3, 3
            )


# ------------------------------------------------------------
# ZONE 5 OPEN TESTING PAD
# ------------------------------------------------------------

def draw_testing_pad(ax, detailed=False):
    x0, y0 = 121.4664, 158.5

    ax.add_patch(Rectangle(
        (x0 - 18, y0 - 18),
        36, 36,
        facecolor=OPEN_AREA,
        edgecolor=INK,
        linewidth=1.0,
        linestyle="-" if detailed else "--",
        zorder=3
    ))

    # Inner boundary marking
    ax.add_patch(Rectangle(
        (x0 - 17.9, y0 - 17.9),
        35.8, 35.8,
        fill=False,
        edgecolor="#777777",
        linewidth=0.45,
        zorder=4
    ))

    add_text(
        ax, x0, y0,
        "OPEN TESTING AREA\n36 m × 36 m",
        size=8 if detailed else 7,
        weight="bold",
        zorder=8
    )


# ------------------------------------------------------------
# ZONE 4 ROADWORKS SYMBOLS
# ------------------------------------------------------------

def draw_roadworks(ax):
    cone_positions = [
        (124.650, 98.500),
        (124.250, 101.500),
        (123.850, 104.500),
        (123.450, 107.500),
        (123.050, 110.500),
        (122.000, 114.500),
    ]

    for x, y in cone_positions:
        ax.add_patch(Circle(
            (x, y), 0.48,
            facecolor="#777777",
            edgecolor=INK,
            linewidth=0.55,
            zorder=10
        ))

    ax.add_patch(Rectangle(
        (125.1, 95.4), 1.8, 1.2,
        facecolor="#dddddd",
        edgecolor=INK,
        linewidth=0.7,
        zorder=10
    ))

    add_text(ax, 126, 96, "WORKS", size=5.5, weight="bold", zorder=11)


# ------------------------------------------------------------
# INTERSECTION FEATURES
# ------------------------------------------------------------

def draw_intersection_features(ax):
    # Traffic signal locations
    for x, y in ((117.35, 34.3), (117.35, 58.8)):
        ax.add_patch(Circle(
            (x, y), 0.55,
            facecolor="#555555",
            edgecolor=INK,
            linewidth=0.7,
            zorder=12
        ))

    # Approximate crosswalk bars based on the SDF stripe arrangement.
    for y in (36.9, 56.1):
        for i in range(7):
            x = 118.0 + i * 0.72
            add_box(
                ax, x, y, 0, 0.42, 7.05,
                "#fafafa", "#777777", 0.25, 5
            )


# ------------------------------------------------------------
# MAP ANNOTATIONS
# ------------------------------------------------------------

def zone_label(ax, x, y, title, subtitle=None, size=8):
    text = title if subtitle is None else f"{title}\n{subtitle}"

    ax.text(
        x, y, text,
        ha="center",
        va="center",
        fontsize=size,
        fontweight="bold",
        color=INK,
        linespacing=1.25,
        bbox=dict(
            boxstyle="round,pad=0.35",
            facecolor=PAPER,
            edgecolor="#777777",
            linewidth=0.55,
            alpha=0.96
        ),
        zorder=30
    )


def add_north_arrow(ax, x, y):
    ax.annotate(
        "N",
        xy=(x, y + 7),
        xytext=(x, y),
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        arrowprops=dict(
            arrowstyle="-|>",
            color=INK,
            linewidth=1.2
        ),
        zorder=40
    )


def add_scale_bar(ax, x, y, length=20):
    ax.plot(
        [x, x + length], [y, y],
        color=INK, linewidth=2.0, zorder=40
    )
    ax.plot(
        [x, x], [y - 0.8, y + 0.8],
        color=INK, linewidth=0.9, zorder=40
    )
    ax.plot(
        [x + length, x + length],
        [y - 0.8, y + 0.8],
        color=INK, linewidth=0.9, zorder=40
    )
    add_text(
        ax, x + length / 2, y - 2.0,
        f"{length} m", size=7, zorder=40
    )


# ------------------------------------------------------------
# FIGURE 5.1 — OVERALL CITY MAP
# ------------------------------------------------------------

fig, ax = plt.subplots(figsize=(16, 12))

draw_roads(ax, flyover_emphasis=True)
draw_zone1_sidewalks(ax)
draw_buildings(ax, zone1=True, zone6=True, labels=False)
draw_testing_pad(ax)
draw_roadworks(ax)
draw_intersection_features(ax)

# Flyover crossing annotation
ax.annotate(
    "ZONE 7 — ELEVATED FLYOVER",
    xy=(121.5, 46.54),
    xytext=(151, 31),
    fontsize=8,
    fontweight="bold",
    color=INK,
    arrowprops=dict(
        arrowstyle="->",
        color=INK,
        linewidth=0.8
    ),
    bbox=dict(
        boxstyle="round,pad=0.3",
        facecolor=PAPER,
        edgecolor="#777777",
        linewidth=0.5
    ),
    zorder=35
)

zone_label(ax, 40, -11, "ZONE 1", "Main urban road", 8)
zone_label(ax, 96, 16, "ZONE 2", "Curved connecting road", 8)
zone_label(ax, 151, 76, "ZONE 3", "Signalised intersection", 8)
zone_label(ax, 137, 108, "ZONE 4", "Roadworks area", 7.5)
zone_label(ax, 121.5, 163, "ZONE 5", "Open testing area", 8)
zone_label(ax, 159, 88, "ZONE 6", "Urban built environment", 7.5)
zone_label(ax, 121, 52, "ZONE 7", "Elevated east–west flyover", 7.5)
zone_label(ax, 121, 126, "ZONE 8", "Dual flyover access ramps", 7.5)

# Main map framing
ax.set_xlim(-8, 205)
ax.set_ylim(-19, 187)
ax.set_aspect("equal", adjustable="box")

ax.set_xlabel("East–west coordinate (m)")
ax.set_ylabel("North–south coordinate (m)")

ax.set_xticks(range(0, 201, 20))
ax.set_yticks(range(-10, 181, 20))
ax.grid(
    True,
    color=GRID,
    linewidth=0.35,
    linestyle=":",
    zorder=0
)

add_north_arrow(ax, 194, 160)
add_scale_bar(ax, 8, -12, 20)

legend = [
    Rectangle((0, 0), 1, 1, facecolor=ROAD,
              edgecolor=ROAD_EDGE, label="Ground-level road"),
    Rectangle((0, 0), 1, 1, facecolor="#999999",
              edgecolor=INK, label="Elevated flyover"),
    Rectangle((0, 0), 1, 1, facecolor=SIDEWALK,
              edgecolor="#999999", label="Sidewalk"),
    Rectangle((0, 0), 1, 1, facecolor=BUILDING,
              edgecolor=BUILDING_EDGE, label="Building footprint"),
    Rectangle((0, 0), 1, 1, facecolor=OPEN_AREA,
              edgecolor=INK, linestyle="--", label="Open testing area"),
    Line2D([0], [0], marker="o", linestyle="none",
           markerfacecolor="#777777", markeredgecolor=INK,
           markersize=5, label="Roadworks / traffic-control feature"),
]

ax.legend(
    handles=legend,
    loc="upper left",
    frameon=True,
    facecolor=PAPER,
    edgecolor="#777777",
    framealpha=0.98,
    fontsize=7.5,
    ncol=2
)

fig.suptitle(
    "AUROVIA: OVERALL URBAN ROAD NETWORK AND BUILT ENVIRONMENT",
    fontsize=13,
    fontweight="bold",
    y=0.975
)

fig.text(
    0.5, 0.018,
    "Plan view derived from AUROVIA road-segment data and Gazebo world geometry.",
    ha="center",
    fontsize=7.5,
    color=DARK
)

fig.subplots_adjust(
    left=0.08, right=0.97,
    bottom=0.07, top=0.92
)

fig.savefig(FIG51_PNG, dpi=400, bbox_inches="tight")
fig.savefig(FIG51_SVG, bbox_inches="tight")
plt.close(fig)


# ------------------------------------------------------------
# FIGURE 5.2 — FLYOVER / INTERSECTION DETAIL
# ------------------------------------------------------------

fig = plt.figure(figsize=(14, 9))
gs = fig.add_gridspec(
    2, 1,
    height_ratios=[1.35, 1],
    hspace=0.32
)

ax_plan = fig.add_subplot(gs[0])
ax_profile = fig.add_subplot(gs[1])

# Plan view: ground-level intersection and flyover.
draw_roads(
    ax_plan,
    zones={
        "zone3_city_intersection",
        "zone7_east_west_flyover"
    },
    flyover_emphasis=True
)

draw_intersection_features(ax_plan)

ax_plan.set_xlim(72, 171)
ax_plan.set_ylim(24, 68)
ax_plan.set_aspect("equal", adjustable="box")
ax_plan.set_xlabel("East–west coordinate (m)")
ax_plan.set_ylabel("North–south coordinate (m)")
ax_plan.grid(color=GRID, linewidth=0.35, linestyle=":")

ax_plan.annotate(
    "Elevated flyover deck",
    xy=(121.5, 46.54),
    xytext=(139, 60),
    fontsize=8,
    fontweight="bold",
    arrowprops=dict(arrowstyle="->", linewidth=0.8, color=INK)
)

ax_plan.annotate(
    "Ground-level intersection",
    xy=(121.5, 39.5),
    xytext=(91, 29),
    fontsize=8,
    fontweight="bold",
    arrowprops=dict(arrowstyle="->", linewidth=0.8, color=INK)
)

ax_plan.set_title(
    "(a) Plan view of the elevated flyover crossing the Zone 3 intersection",
    loc="left",
    fontweight="bold",
    pad=8
)

# Elevation profile: actual road_segment link reference poses.
if len(flyover_profile) >= 2:
    xs = [p["x"] for p in flyover_profile]
    zs = [p["z"] for p in flyover_profile]

    ax_profile.plot(
        xs, zs,
        color=INK,
        linewidth=1.5,
        label="Flyover road-section reference elevation"
    )

    ax_profile.fill_between(
        xs, zs, min(zs) - 0.25,
        color="#e5e5e5",
        alpha=0.8
    )

    ax_profile.axvspan(
        116.4664, 126.4664,
        facecolor="#d9d9d9",
        alpha=0.35,
        label="Zone 3 intersection vicinity"
    )

    ax_profile.set_xlim(min(xs), max(xs))
    ax_profile.set_xlabel("East–west coordinate (m)")
    ax_profile.set_ylabel("Road-section reference elevation (m)")
    ax_profile.grid(color=GRID, linewidth=0.4, linestyle=":")
    ax_profile.legend(loc="best", fontsize=7)

    ax_profile.set_title(
        "(b) Longitudinal elevation profile of the Zone 7 flyover",
        loc="left",
        fontweight="bold",
        pad=8
    )
else:
    ax_profile.text(
        0.5, 0.5,
        "Flyover road-section profile could not be extracted from the SDF.",
        ha="center",
        va="center",
        transform=ax_profile.transAxes
    )
    ax_profile.set_axis_off()

fig.suptitle(
    "AUROVIA: ZONE 7 FLYOVER AND ZONE 3 INTERSECTION",
    fontsize=13,
    fontweight="bold",
    y=0.98
)

fig.text(
    0.5, 0.018,
    "Elevation values represent SDF road-section link reference poses; "
    "they are not independently measured clearance values.",
    ha="center",
    fontsize=7.5,
    color=DARK
)

fig.subplots_adjust(
    left=0.09, right=0.97,
    bottom=0.08, top=0.91
)

fig.savefig(FIG52_PNG, dpi=400, bbox_inches="tight")
fig.savefig(FIG52_SVG, bbox_inches="tight")
plt.close(fig)


# ------------------------------------------------------------
# GENERATION SUMMARY
# ------------------------------------------------------------

print("\nAUROVIA V2 ENGINEERING FIGURES GENERATED")
print("----------------------------------------")
print("Road segments loaded:", len(road_segments))
print("Zone 1 building footprints:", len(ZONE1_BUILDINGS))
print("Zone 6 building footprints:", len(ZONE6_BUILDINGS))
print("Flyover road-section poses:", len(flyover_profile))
print()
print("Figure 5.1 PNG:", FIG51_PNG)
print("Figure 5.1 SVG:", FIG51_SVG)
print("Figure 5.2 PNG:", FIG52_PNG)
print("Figure 5.2 SVG:", FIG52_SVG)
print()
print("Original generator and original map images were not modified.")
