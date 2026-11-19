from pathlib import Path

file = Path("index.html")
html = file.read_text(encoding="utf-8")

backup = Path("index.html.before-feature-card-update")
backup.write_text(html, encoding="utf-8")

start_marker = '    <div class="features">'
end_marker = '\n    </div>\n\n</section>\n\n<!-- SIMULATION GALLERY -->'

start = html.index(start_marker)
end = html.index(end_marker, start) + len('\n    </div>')

new_cards = '''    <div class="features">

        <article class="feature-card">
            <div class="feature-icon">01</div>
            <h3>Ackermann Vehicle Control</h3>
            <p>Discover the vehicle model, Ackermann steering geometry and ROS 2 control implementation.</p>
            <a class="feature-read-more" href="AUROVIA_Engineering_Project_Report.pdf#page=19">READ MORE <span aria-hidden="true">→</span></a>
        </article>

        <article class="feature-card">
            <div class="feature-icon">02</div>
            <h3>Multi-Sensor Perception</h3>
            <p>Explore the integration of LiDAR, camera, IMU and GNSS within the vehicle system.</p>
            <a class="feature-read-more" href="AUROVIA_Engineering_Project_Report.pdf#page=52">READ MORE <span aria-hidden="true">→</span></a>
        </article>

        <article class="feature-card">
            <div class="feature-icon">03</div>
            <h3>Autonomous Navigation</h3>
            <p>See how odometry feedback and destination-based control guide vehicle movement.</p>
            <a class="feature-read-more" href="AUROVIA_Engineering_Project_Report.pdf#page=62">READ MORE <span aria-hidden="true">→</span></a>
        </article>

        <article class="feature-card">
            <div class="feature-icon">04</div>
            <h3>Traffic-Light Awareness</h3>
            <p>Explore traffic-light infrastructure, signal-state handling and stopping logic.</p>
            <a class="feature-read-more" href="AUROVIA_Engineering_Project_Report.pdf#page=70">READ MORE <span aria-hidden="true">→</span></a>
        </article>

        <article class="feature-card">
            <div class="feature-icon">05</div>
            <h3>Obstacle Awareness</h3>
            <p>Learn how LiDAR data supports proximity monitoring and obstacle assessment.</p>
            <a class="feature-read-more" href="AUROVIA_Engineering_Project_Report.pdf#page=52">READ MORE <span aria-hidden="true">→</span></a>
        </article>

        <article class="feature-card">
            <div class="feature-icon">06</div>
            <h3>Smart Urban Environment</h3>
            <p>Explore AUROVIA's urban road network, intersections, flyover and infrastructure.</p>
            <a class="feature-read-more" href="AUROVIA_Engineering_Project_Report.pdf#page=26">READ MORE <span aria-hidden="true">→</span></a>
        </article>

    </div>'''

html = html[:start] + new_cards + html[end:]

css_marker = """.feature-card p {
    color: var(--muted);
    font-size: 14px;
    line-height: 1.8;
}"""

new_css = css_marker + """

.feature-read-more {
    display: inline-block;
    margin-top: 18px;
    color: var(--cyan);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    text-decoration: none;
    transition: 0.3s;
}

.feature-read-more:hover {
    color: #ffffff;
    transform: translateX(4px);
}

.feature-read-more span {
    display: inline-block;
    margin-left: 5px;
}"""

if css_marker not in html:
    raise SystemExit("Could not find the existing feature-card CSS. No changes saved.")

html = html.replace(css_marker, new_css, 1)
file.write_text(html, encoding="utf-8")

print("SUCCESS: All six feature cards updated.")
print("SUCCESS: Direct PDF chapter links added.")
print("SUCCESS: Existing website styling preserved.")
print(f"Backup saved as: {backup}")
