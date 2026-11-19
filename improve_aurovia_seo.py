from pathlib import Path
import shutil
import re
import json

file = Path("index.html")
html = file.read_text(encoding="utf-8")

# Preserve the current website.
backup = Path("index.html.before-seo-improvements")
shutil.copy2(file, backup)

SITE = "https://akinlatauto19.github.io/aurovia-autonomous-vehicle-simulation/"
GITHUB = "https://github.com/Akinlatauto19/aurovia-autonomous-vehicle-simulation"
IMAGE = SITE + "docs/images/aurovia-report-cover.png"

# 1. Improve the page title.
html = re.sub(
    r"<title>.*?</title>",
    "<title>AUROVIA | ROS 2 &amp; Gazebo Autonomous Vehicle Simulation</title>",
    html,
    count=1,
    flags=re.I | re.S
)

# 2. Update and add search metadata.
def set_meta(html, attribute, key, content):
    pattern = (
        r'<meta\s+' + re.escape(attribute) +
        r'=["\']' + re.escape(key) +
        r'["\'][^>]*>'
    )

    tag = f'<meta {attribute}="{key}" content="{content}">'

    if re.search(pattern, html, flags=re.I):
        return re.sub(pattern, tag, html, count=1, flags=re.I)

    return html.replace("</head>", "    " + tag + "\n</head>", 1)


html = set_meta(
    html, "name", "description",
    "AUROVIA is an autonomous vehicle simulation in a smart urban environment, developed with ROS 2 and Gazebo. Explore Ackermann steering, autonomous navigation, LiDAR perception, obstacle avoidance and smart city infrastructure."
)

html = set_meta(
    html, "name", "keywords",
    "AUROVIA, autonomous vehicle simulation, ROS 2 Lyrical, Gazebo, Ackermann steering, autonomous driving, robotics engineering, autonomous navigation, LiDAR, obstacle avoidance, smart city simulation, vehicle dynamics"
)

html = set_meta(html, "name", "robots", "index, follow")
html = set_meta(html, "name", "author", "AUROVIA Engineering Project")

# 3. Add canonical and social-sharing metadata.
canonical = f'<link rel="canonical" href="{SITE}">'

if re.search(r'<link\s+rel=["\']canonical["\']', html, re.I):
    html = re.sub(
        r'<link\s+rel=["\']canonical["\'][^>]*>',
        canonical,
        html,
        count=1,
        flags=re.I
    )
else:
    html = html.replace("</head>", canonical + "\n</head>", 1)

social_tags = {
    "og:type": "website",
    "og:site_name": "AUROVIA",
    "og:title": "AUROVIA | Autonomous Vehicle Simulation",
    "og:description": "Explore AUROVIA, a ROS 2 and Gazebo autonomous vehicle simulation featuring Ackermann steering, autonomous navigation and smart urban infrastructure.",
    "og:url": SITE,
    "og:image": IMAGE,
    "twitter:card": "summary_large_image",
    "twitter:title": "AUROVIA | Autonomous Vehicle Simulation",
    "twitter:description": "Autonomous mobility, Ackermann vehicle control and smart urban simulation using ROS 2 and Gazebo.",
    "twitter:image": IMAGE
}

for key, value in social_tags.items():
    html = set_meta(html, "property" if key.startswith("og:") else "name", key, value)

# 4. Add structured data connecting the website and project repository.
structured_data = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebSite",
            "@id": SITE + "#website",
            "name": "AUROVIA",
            "alternateName": "AUROVIA Autonomous Vehicle Simulation",
            "url": SITE,
            "publisher": {
                "@id": SITE + "#project"
            }
        },
        {
            "@type": "Organization",
            "@id": SITE + "#project",
            "name": "AUROVIA Engineering Project",
            "url": SITE,
            "sameAs": [GITHUB],
            "description": "An autonomous vehicle simulation in a smart urban environment, developed using ROS 2 and Gazebo."
        }
    ]
}

json_script = (
    '<!-- aurovia-website-structured-data -->\n'
    '<script type="application/ld+json">\n'
    + json.dumps(structured_data, indent=2)
    + '\n</script>'
)

pattern = (
    r'<!--\s*aurovia-website-structured-data\s*-->\s*'
    r'<script\s+type=["\']application/ld\+json["\']>.*?</script>'
)

if re.search(pattern, html, flags=re.I | re.S):
    html = re.sub(pattern, json_script, html, count=1, flags=re.I | re.S)
else:
    html = html.replace("</head>", json_script + "\n</head>", 1)

# 5. Preserve all existing image descriptions.
# Confirm that every gallery image has alternative text.
img_tags = re.findall(r'<img\b[^>]*>', html, flags=re.I)
missing_alt = [
    tag for tag in img_tags
    if not re.search(r'\balt\s*=', tag, flags=re.I)
]

if missing_alt:
    raise SystemExit(
        f"Stopped: {len(missing_alt)} image(s) need alt descriptions. "
        "Original homepage remains backed up."
    )

# Write the updated homepage.
file.write_text(html, encoding="utf-8")

print("\nAUROVIA SEO improvements completed.")
print("------------------------------------")
print("Page title: Updated")
print("Meta description: Updated")
print("Canonical URL: Added")
print("Open Graph metadata: Added")
print("Twitter sharing metadata: Added")
print("Structured project data: Updated")
print("Image alternative text: Checked")
print("Google verification tag:",
      "google-site-verification" in html)
print("Original homepage backup:", backup)
