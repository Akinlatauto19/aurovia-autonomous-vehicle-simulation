#!/bin/bash
set -e

REPORT="AUROVIA_Engineering_Project_Report.pdf"
OUT="docs/chapters"
TMP="/tmp/aurovia-chapter-extracts"

mkdir -p "$OUT" "$TMP"

if [ ! -f "$REPORT" ]; then
    echo "ERROR: Main engineering report not found."
    exit 1
fi

extract_range() {
    local name="$1"
    local first="$2"
    local last="$3"

    echo "Extracting $name: pages $first-$last"

    pdfseparate -f "$first" -l "$last" \
        "$REPORT" "$TMP/$name-%d.pdf"

    local files=()
    for ((page=first; page<=last; page++)); do
        files+=("$TMP/$name-$page.pdf")
    done

    pdfunite "${files[@]}" "$OUT/$name.pdf"
}

# 01 — Ackermann Vehicle Control (Chapter 4)
extract_range "01-ackermann-vehicle-control" 19 25

# 02 — Multi-Sensor Perception (Chapter 8, Sections 8.1–8.5)
extract_range "02-multi-sensor-perception" 52 61

# 03 — Autonomous Navigation (Section 8.6)
extract_range "03-autonomous-navigation" 62 65

# Append the verified cropped final navigation page.
pdfunite \
    "$OUT/03-autonomous-navigation.pdf" \
    "$OUT/autonomous-navigation-final-page.pdf" \
    "$TMP/autonomous-navigation-complete.pdf"

mv "$TMP/autonomous-navigation-complete.pdf" \
   "$OUT/03-autonomous-navigation.pdf"

# 04 — Traffic-Light Awareness (Chapter 9)
extract_range "04-traffic-light-awareness" 70 74

# 05 — Obstacle Awareness (Sections 8.2–8.2.4)
extract_range "05-obstacle-awareness" 52 54

# 06 — Smart Urban Environment (Chapter 5)
extract_range "06-smart-urban-environment" 26 31

echo
echo "======================================"
echo "AUROVIA CHAPTER PDF EXTRACTION COMPLETE"
echo "======================================"

for file in "$OUT"/*.pdf; do
    if [ "$(basename "$file")" = "autonomous-navigation-final-page.pdf" ]; then
        continue
    fi

    echo
    echo "FILE: $(basename "$file")"
    pdfinfo "$file" | grep -E 'Pages|Page size'
done
