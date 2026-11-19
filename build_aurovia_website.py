from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parent
IMAGE_DIR = ROOT / "docs" / "images"
INDEX = ROOT / "index.html"

images = [
    "aurovia-report-cover.png",
    "aurovia-city-entrance.png",
    "aurovia_daytime_city_view.png",
    "aurovia_nighttime_city_view.png",
    "aurovia_flyover_intersection_detail_v2.png",
    "aurovia_full_city_layout.png",
    "aurovia_overall_city_map_v2.png",
    "AUROVIA_System_Architecture.png",
    "AUROVIA_Ackermann_Steering_Geometry.png",
    "AUROVIA_Vehicle_Dimensions.png",
]

missing = [name for name in images if not (IMAGE_DIR / name).is_file()]

if missing:
    print("ERROR: These required images are missing:")
    for name in missing:
        print(" -", name)
    raise SystemExit(1)

html = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>AUROVIA | Autonomous Vehicle Simulation</title>

<meta name="description" content="Explore AUROVIA, an autonomous vehicle simulation in a smart urban environment, developed using ROS 2 and Gazebo.">
<meta name="keywords" content="AUROVIA, autonomous vehicle simulation, ROS 2, Gazebo, Ackermann steering, robotics, autonomous navigation, LiDAR, smart city">
<meta name="author" content="AUROVIA Engineering Project">
<meta name="theme-color" content="#061426">

<style>
:root {
    --navy: #061426;
    --navy-light: #0b2036;
    --card: #102943;
    --cyan: #00d9ff;
    --white: #f5f9ff;
    --muted: #b9c8d9;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    scroll-behavior: smooth;
}

body {
    font-family: Arial, Helvetica, sans-serif;
    background: var(--navy);
    color: var(--white);
    line-height: 1.6;
}

a {
    color: inherit;
}

/* NAVIGATION */

header {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    padding: 24px 7%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 10;
    border-bottom: 1px solid rgba(0,217,255,0.2);
    background: rgba(4,17,33,0.65);
    backdrop-filter: blur(12px);
}

.logo {
    font-size: 27px;
    font-weight: 800;
    letter-spacing: 3px;
    color: var(--cyan);
    text-decoration: none;
}

nav {
    display: flex;
    gap: 25px;
    flex-wrap: wrap;
}

nav a {
    color: white;
    text-decoration: none;
    font-size: 14px;
    transition: 0.3s;
}

nav a:hover {
    color: var(--cyan);
}

/* HERO */

.hero {
    min-height: 100vh;
    display: flex;
    align-items: center;
    padding: 140px 9% 100px;
    position: relative;
    background:
        linear-gradient(90deg,
        rgba(3,14,29,0.88) 0%,
        rgba(3,14,29,0.62) 42%,
        rgba(3,14,29,0.12) 100%),
        linear-gradient(0deg,
        rgba(3,14,29,0.38),
        transparent 45%),
        url("docs/images/aurovia-report-cover.png");
    background-size: cover;
    background-position: center;
}

.hero::after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
    box-shadow: 0 0 20px var(--cyan);
}

.hero-content {
    max-width: 650px;
    position: relative;
    z-index: 2;
}

.eyebrow {
    color: var(--cyan);
    font-size: 13px;
    letter-spacing: 4px;
    font-weight: bold;
    margin-bottom: 22px;
}

.hero h1 {
    font-size: clamp(48px, 7vw, 82px);
    line-height: 1;
    letter-spacing: 3px;
    margin-bottom: 22px;
}

.hero h1 span {
    color: var(--cyan);
}

.hero h2 {
    font-size: clamp(20px, 3vw, 27px);
    font-weight: 400;
    line-height: 1.4;
    margin-bottom: 22px;
}

.hero p {
    color: var(--muted);
    font-size: 16px;
    line-height: 1.8;
    max-width: 580px;
}

.buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    margin-top: 32px;
}

.btn {
    display: inline-block;
    padding: 14px 22px;
    border-radius: 4px;
    text-decoration: none;
    font-size: 13px;
    font-weight: bold;
    text-align: center;
    transition: 0.3s;
}

.btn-primary {
    background: var(--cyan);
    color: #041426;
}

.btn-outline {
    border: 1px solid var(--cyan);
    color: white;
}

.btn:hover {
    transform: translateY(-4px);
    box-shadow: 0 0 20px rgba(0,217,255,0.35);
}

/* TECHNOLOGY STRIP */

.tech-strip {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 35px;
    padding: 25px 5%;
    background: #091c32;
    border-top: 1px solid rgba(0,217,255,0.15);
    border-bottom: 1px solid rgba(0,217,255,0.15);
}

.tech-strip span {
    color: var(--muted);
    font-size: 13px;
    letter-spacing: 1px;
}

.tech-strip strong {
    color: var(--cyan);
}

/* GENERAL SECTIONS */

section {
    padding: 85px 9%;
}

.section-title {
    text-align: center;
    margin: 0 auto 48px;
    max-width: 780px;
}

.section-title small {
    color: var(--cyan);
    letter-spacing: 3px;
    font-weight: bold;
}

.section-title h2 {
    font-size: clamp(27px, 4vw, 36px);
    margin-top: 12px;
}

.section-title p {
    color: var(--muted);
    margin-top: 15px;
    line-height: 1.8;
}

/* OVERVIEW */

.overview-section {
    background: var(--navy);
}

.overview-content {
    max-width: 900px;
    margin: auto;
    text-align: center;
}

.overview-content p {
    color: var(--muted);
    line-height: 1.9;
    margin-bottom: 16px;
}

/* FEATURE CARDS */

.features {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 22px;
}

.feature-card {
    padding: 30px 25px;
    background: linear-gradient(145deg, #102943, #08182a);
    border: 1px solid rgba(0,217,255,0.17);
    border-radius: 8px;
    transition: 0.3s;
}

.feature-card:hover {
    transform: translateY(-7px);
    border-color: var(--cyan);
    box-shadow: 0 10px 30px rgba(0,217,255,0.10);
}

.feature-icon {
    color: var(--cyan);
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 15px;
}

.feature-card h3 {
    color: var(--cyan);
    font-size: 18px;
    margin-bottom: 12px;
}

.feature-card p {
    color: var(--muted);
    font-size: 14px;
    line-height: 1.8;
}

/* GALLERY */

.gallery-section {
    background: linear-gradient(180deg, #061426, #091c32);
    border-top: 1px solid rgba(0,217,255,0.12);
    border-bottom: 1px solid rgba(0,217,255,0.12);
}

.gallery-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 22px;
}

.gallery-card {
    overflow: hidden;
    background: #10243a;
    border: 1px solid rgba(0,217,255,0.2);
    border-radius: 8px;
    transition: 0.3s;
}

.gallery-card:hover {
    transform: translateY(-6px);
    border-color: var(--cyan);
    box-shadow: 0 10px 28px rgba(0,217,255,0.15);
}

.gallery-card img {
    width: 100%;
    height: 220px;
    object-fit: cover;
    display: block;
    cursor: zoom-in;
    transition: 0.4s;
}

.gallery-card:hover img {
    transform: scale(1.035);
}

.gallery-caption {
    padding: 18px;
}

.gallery-caption h3 {
    color: var(--cyan);
    font-size: 16px;
    margin-bottom: 8px;
}

.gallery-caption p {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.7;
}

.technical-gallery {
    margin-top: 75px;
}

/* IMAGE VIEWER */

.image-viewer {
    display: none;
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: rgba(2,9,19,0.96);
    align-items: center;
    justify-content: center;
    padding: 40px;
}

.image-viewer.active {
    display: flex;
}

.image-viewer img {
    max-width: 92%;
    max-height: 85vh;
    object-fit: contain;
    border: 1px solid var(--cyan);
    border-radius: 5px;
    box-shadow: 0 0 30px rgba(0,217,255,0.15);
}

.image-viewer button {
    position: absolute;
    top: 18px;
    right: 30px;
    background: none;
    border: none;
    color: white;
    font-size: 42px;
    cursor: pointer;
}

/* RESOURCES */

.resources-section {
    background: var(--navy);
}

.resources-box {
    max-width: 850px;
    margin: auto;
    padding: 38px;
    text-align: center;
    background: linear-gradient(145deg, #102943, #08182a);
    border: 1px solid rgba(0,217,255,0.2);
    border-radius: 8px;
}

.resources-box p {
    color: var(--muted);
    margin-top: 12px;
}

/* FOOTER */

footer {
    text-align: center;
    padding: 38px 15px;
    background: #040e1b;
    border-top: 1px solid rgba(0,217,255,0.2);
}

footer strong {
    color: var(--cyan);
    letter-spacing: 2px;
}

footer p {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.9;
}

/* RESPONSIVE LAYOUT */

@media(max-width: 900px) {
    header {
        padding: 20px 5%;
    }

    nav {
        gap: 14px;
    }

    .features,
    .gallery-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media(max-width: 600px) {
    header {
        flex-direction: column;
        gap: 15px;
    }

    nav {
        justify-content: center;
        gap: 12px;
    }

    nav a {
        font-size: 12px;
    }

    .hero {
        padding: 165px 7% 85px;
        background-position: center;
    }

    .hero p {
        font-size: 14px;
    }

    .features,
    .gallery-grid {
        grid-template-columns: 1fr;
    }

    section {
        padding: 65px 7%;
    }

    .resources-box {
        padding: 25px 18px;
    }

    .image-viewer {
        padding: 15px;
    }

    .image-viewer img {
        max-width: 100%;
    }

    .image-viewer button {
        top: 8px;
        right: 15px;
    }
}
</style>
</head>

<body>

<header>
    <a class="logo" href="#home">AUROVIA</a>

    <nav aria-label="Main navigation">
        <a href="#home">Home</a>
        <a href="#overview">Overview</a>
        <a href="#features">Features</a>
        <a href="#gallery">Gallery</a>
        <a href="#resources">Resources</a>
    </nav>
</header>

<main>

<!-- HERO -->

<section class="hero" id="home">
    <div class="hero-content">

        <div class="eyebrow">
            AUTONOMOUS MOBILITY · SMART URBAN INFRASTRUCTURE
        </div>

        <h1>AURO<span>VIA</span></h1>

        <h2>
            Autonomous Vehicle Simulation
            in a Smart Urban Environment
        </h2>

        <p>
            Exploring intelligent mobility through ROS 2 and Gazebo.
            AUROVIA integrates Ackermann vehicle control, autonomous
            navigation, multi-sensor perception and smart urban
            infrastructure within a custom simulated city.
        </p>

        <div class="buttons">
            <a href="#overview" class="btn btn-primary">EXPLORE PROJECT</a>

            <a href="AUROVIA_Engineering_Project_Report.pdf"
               class="btn btn-outline" target="_blank" rel="noopener">
                ENGINEERING REPORT
            </a>

            <a href="https://github.com/Akinlatauto19/aurovia-autonomous-vehicle-simulation"
               class="btn btn-outline" target="_blank" rel="noopener">
                GITHUB REPOSITORY
            </a>
        </div>

    </div>
</section>

<!-- TECHNOLOGY STRIP -->

<div class="tech-strip">
    <span><strong>ROS 2</strong> Lyrical</span>
    <span><strong>GAZEBO</strong> Simulation</span>
    <span><strong>ACKERMANN</strong> Steering</span>
    <span><strong>LiDAR</strong> Perception</span>
    <span><strong>SMART CITY</strong> Infrastructure</span>
</div>

<!-- PROJECT OVERVIEW -->

<section class="overview-section" id="overview">

    <div class="section-title">
        <small>ABOUT THE PROJECT</small>
        <h2>Engineering Intelligent Mobility</h2>
        <p>
            A robotics and autonomous vehicle engineering project
            bringing together vehicle dynamics, perception,
            navigation and intelligent urban systems.
        </p>
    </div>

    <div class="overview-content">
        <p>
            AUROVIA is an autonomous vehicle simulation project
            developed using ROS 2 and Gazebo. It provides a custom
            urban environment in which vehicle control, navigation,
            sensor integration and smart infrastructure can be
            developed and evaluated.
        </p>

        <p>
            The project brings together an Ackermann-steered vehicle,
            a structured urban road network, environmental sensors,
            traffic infrastructure and autonomous driving functions.
        </p>
    </div>

</section>

<!-- PROJECT FEATURES -->

<section id="features">

    <div class="section-title">
        <small>PROJECT CAPABILITIES</small>
        <h2>Core Technologies</h2>
        <p>
            Integrated vehicle systems and smart infrastructure
            developed within the AUROVIA simulation environment.
        </p>
    </div>

    <div class="features">

        <article class="feature-card">
            <div class="feature-icon">01</div>
            <h3>Ackermann Vehicle Control</h3>
            <p>
                Vehicle motion, steering, acceleration, braking
                and manual control using an Ackermann steering
                configuration.
            </p>
        </article>

        <article class="feature-card">
            <div class="feature-icon">02</div>
            <h3>Multi-Sensor Perception</h3>
            <p>
                LiDAR, camera, IMU and GNSS sensor integration
                for environmental awareness and vehicle data
                monitoring.
            </p>
        </article>

        <article class="feature-card">
            <div class="feature-icon">03</div>
            <h3>Autonomous Navigation</h3>
            <p>
                Road-network navigation, waypoint following
                and autonomous vehicle movement through the
                simulated city.
            </p>
        </article>

        <article class="feature-card">
            <div class="feature-icon">04</div>
            <h3>Traffic-Light Awareness</h3>
            <p>
                Traffic-light-aware driving with signal-state
                handling and stopping behaviour.
            </p>
        </article>

        <article class="feature-card">
            <div class="feature-icon">05</div>
            <h3>Obstacle Awareness</h3>
            <p>
                LiDAR-based obstacle detection, distance
                assessment and navigation response.
            </p>
        </article>

        <article class="feature-card">
            <div class="feature-icon">06</div>
            <h3>Smart Urban Environment</h3>
            <p>
                A custom simulated city with road networks,
                intersections, flyovers, traffic infrastructure
                and dynamic day/night lighting.
            </p>
        </article>

    </div>

</section>

<!-- SIMULATION GALLERY -->

<section class="gallery-section" id="gallery">

    <div class="section-title">
        <small>INSIDE AUROVIA</small>
        <h2>Simulation Gallery</h2>
        <p>
            Explore the simulated urban environment, road infrastructure
            and engineering designs developed for AUROVIA.
        </p>
    </div>

    <div class="gallery-grid">

        <article class="gallery-card">
            <img src="docs/images/aurovia-city-entrance.png"
                 alt="AUROVIA city entrance"
                 loading="lazy" onclick="openImage(this)">
            <div class="gallery-caption">
                <h3>Welcome to AUROVIA</h3>
                <p>The entrance to the autonomous urban simulation environment.</p>
            </div>
        </article>

        <article class="gallery-card">
            <img src="docs/images/aurovia_daytime_city_view.png"
                 alt="AUROVIA daytime city"
                 loading="lazy" onclick="openImage(this)">
            <div class="gallery-caption">
                <h3>Urban Environment – Daytime</h3>
                <p>The simulated city under daytime lighting conditions.</p>
            </div>
        </article>

        <article class="gallery-card">
            <img src="docs/images/aurovia_nighttime_city_view.png"
                 alt="AUROVIA nighttime city"
                 loading="lazy" onclick="openImage(this)">
            <div class="gallery-caption">
                <h3>Urban Environment – Nighttime</h3>
                <p>Dynamic night lighting and vehicle headlamp integration.</p>
            </div>
        </article>

        <article class="gallery-card">
            <img src="docs/images/aurovia_flyover_intersection_detail_v2.png"
                 alt="AUROVIA flyover intersection"
                 loading="lazy" onclick="openImage(this)">
            <div class="gallery-caption">
                <h3>Flyover and Road Infrastructure</h3>
                <p>Detailed road connections and elevated urban infrastructure.</p>
            </div>
        </article>

        <article class="gallery-card">
            <img src="docs/images/aurovia_full_city_layout.png"
                 alt="AUROVIA full city layout"
                 loading="lazy" onclick="openImage(this)">
            <div class="gallery-caption">
                <h3>AUROVIA City Layout</h3>
                <p>An overview of the custom-designed simulated city.</p>
            </div>
        </article>

        <article class="gallery-card">
            <img src="docs/images/aurovia_overall_city_map_v2.png"
                 alt="AUROVIA overall city map"
                 loading="lazy" onclick="openImage(this)">
            <div class="gallery-caption">
                <h3>Complete Urban Road Network</h3>
                <p>The road network supporting autonomous navigation.</p>
            </div>
        </article>

    </div>

    <div class="technical-gallery">

        <div class="section-title">
            <small>ENGINEERING DESIGN</small>
            <h2>Technical Illustrations</h2>
            <p>
                Engineering diagrams supporting the AUROVIA
                vehicle and system design.
            </p>
        </div>

        <div class="gallery-grid">

            <article class="gallery-card">
                <img src="docs/images/AUROVIA_System_Architecture.png"
                     alt="AUROVIA system architecture"
                     loading="lazy" onclick="openImage(this)">
                <div class="gallery-caption">
                    <h3>System Architecture</h3>
                    <p>The architecture of the AUROVIA simulation system.</p>
                </div>
            </article>

            <article class="gallery-card">
                <img src="docs/images/AUROVIA_Ackermann_Steering_Geometry.png"
                     alt="Ackermann steering geometry"
                     loading="lazy" onclick="openImage(this)">
                <div class="gallery-caption">
                    <h3>Ackermann Steering Geometry</h3>
                    <p>The steering geometry behind the simulated vehicle motion.</p>
                </div>
            </article>

            <article class="gallery-card">
                <img src="docs/images/AUROVIA_Vehicle_Dimensions.png"
                     alt="AUROVIA vehicle dimensions"
                     loading="lazy" onclick="openImage(this)">
                <div class="gallery-caption">
                    <h3>Vehicle Dimensions</h3>
                    <p>Vehicle dimensions used in the engineering design.</p>
                </div>
            </article>

        </div>
    </div>

</section>

<!-- IMAGE ENLARGEMENT VIEWER -->

<div class="image-viewer" id="imageViewer"
     role="dialog" aria-modal="true" aria-label="Expanded gallery image"
     onclick="closeImage()">

    <button type="button" aria-label="Close image"
            onclick="closeImage()">&times;</button>

    <img id="expandedImage" src="" alt="Expanded AUROVIA image">
</div>

<!-- PROJECT RESOURCES -->

<section class="resources-section" id="resources">

    <div class="section-title">
        <small>PROJECT DOCUMENTATION</small>
        <h2>Explore the Engineering Work</h2>
        <p>
            Access the technical report, project documentation
            and source code.
        </p>
    </div>

    <div class="resources-box">
        <h3>AUROVIA Engineering Resources</h3>
        <p>
            Explore the project implementation, engineering
            documentation and development repository.
        </p>

        <div class="buttons" style="justify-content:center">

            <a href="AUROVIA_Engineering_Project_Report.pdf"
               class="btn btn-primary" target="_blank" rel="noopener">
                READ ENGINEERING REPORT
            </a>

            <a href="https://github.com/Akinlatauto19/aurovia-autonomous-vehicle-simulation/blob/main/docs/AUROVIA_USER_GUIDE.md"
               class="btn btn-outline" target="_blank" rel="noopener">
                USER GUIDE
            </a>

            <a href="https://github.com/Akinlatauto19/aurovia-autonomous-vehicle-simulation"
               class="btn btn-outline" target="_blank" rel="noopener">
                VIEW SOURCE CODE
            </a>

        </div>
    </div>

</section>

</main>

<!-- FOOTER -->

<footer>
    <p>
        <strong>AUROVIA</strong><br>
        Autonomous Vehicle Simulation in a Smart Urban Environment<br>
        Built with ROS 2 and Gazebo<br><br>
        © 2026 AUROVIA Engineering Project
    </p>
</footer>

<script>
function openImage(image) {
    const viewer = document.getElementById("imageViewer");
    const expandedImage = document.getElementById("expandedImage");

    expandedImage.src = image.src;
    expandedImage.alt = image.alt;

    viewer.classList.add("active");
    document.body.style.overflow = "hidden";
}

function closeImage() {
    const viewer = document.getElementById("imageViewer");

    viewer.classList.remove("active");
    document.body.style.overflow = "auto";
}

document.getElementById("expandedImage").addEventListener("click", function(event) {
    event.stopPropagation();
});

document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
        closeImage();
    }
});
</script>

</body>
</html>
'''

# Preserve the existing homepage before replacing it.
if INDEX.exists():
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = ROOT / f"index.html.backup-{timestamp}"
    shutil.copy2(INDEX, backup)
    print(f"Previous homepage backed up to: {backup.name}")

INDEX.write_text(html, encoding="utf-8")

print("\nAUROVIA website generated successfully.")
print(f"Homepage: {INDEX}")
print(f"Gallery images checked: {len(images)}")
print("Original simulation images have not been modified.")
