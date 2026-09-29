#!/usr/bin/env python3
"""
Generates ORIGINAL, non-branded packaging illustrations (SVG) for every medicine
in data/medicines.csv, deliberately styled so that known LASA pairs look almost
identical (plain label, small font, same container shape) -- this is intentional:
it recreates the real-world look-alike risk that the safety interface must
compensate for. No real manufacturer branding, trademarks or trade dress are used.

Run:  python3 tools/generate_packaging.py
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MED_CSV = os.path.join(ROOT, "data", "medicines.csv")
OUT_DIR = os.path.join(ROOT, "data", "packaging")

VIAL_IDS = {"M03", "M04", "M05", "M06", "M09", "M10"}
PEN_IDS = {"M07", "M08"}
CAPSULE_IDS = {"M18"}
# everything else -> tablet box

def tablet_box_svg(name, tallman, strength, form, shelf):
    return f"""<svg viewBox="0 0 220 140" xmlns="http://www.w3.org/2000/svg">
  <rect x="4" y="4" width="212" height="132" rx="6" fill="#f5f3ee" stroke="#9a9488" stroke-width="2"/>
  <rect x="4" y="4" width="212" height="26" rx="6" fill="#d9d4c7"/>
  <text x="12" y="21" font-family="Helvetica, Arial" font-size="11" fill="#3a362e">HOSPITAL PHARMACY STOCK</text>
  <text x="12" y="58" font-family="Helvetica, Arial" font-size="16" font-weight="700" fill="#1f1c16">{tallman}</text>
  <text x="12" y="78" font-family="Helvetica, Arial" font-size="12" fill="#3a362e">{strength}</text>
  <text x="12" y="94" font-family="Helvetica, Arial" font-size="11" fill="#5a564a">{form}</text>
  <text x="12" y="112" font-family="Helvetica, Arial" font-size="10" fill="#5a564a">Shelf: {shelf}</text>
  <g transform="translate(150,96)">
    <rect x="0" y="0" width="56" height="18" fill="#1f1c16"/>
    <rect x="3" y="2" width="2" height="14" fill="#f5f3ee"/>
    <rect x="7" y="2" width="1" height="14" fill="#f5f3ee"/>
    <rect x="10" y="2" width="3" height="14" fill="#f5f3ee"/>
    <rect x="15" y="2" width="1" height="14" fill="#f5f3ee"/>
    <rect x="18" y="2" width="2" height="14" fill="#f5f3ee"/>
    <rect x="22" y="2" width="1" height="14" fill="#f5f3ee"/>
    <rect x="26" y="2" width="3" height="14" fill="#f5f3ee"/>
    <rect x="31" y="2" width="1" height="14" fill="#f5f3ee"/>
    <rect x="34" y="2" width="2" height="14" fill="#f5f3ee"/>
    <rect x="38" y="2" width="1" height="14" fill="#f5f3ee"/>
    <rect x="41" y="2" width="3" height="14" fill="#f5f3ee"/>
    <rect x="46" y="2" width="1" height="14" fill="#f5f3ee"/>
    <rect x="49" y="2" width="2" height="14" fill="#f5f3ee"/>
  </g>
</svg>"""

def vial_svg(name, tallman, strength, form, shelf):
    return f"""<svg viewBox="0 0 220 140" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="220" height="140" fill="#ffffff"/>
  <rect x="86" y="10" width="48" height="14" rx="3" fill="#c9c4b6"/>
  <rect x="70" y="24" width="80" height="96" rx="8" fill="#eef0ee" stroke="#8f9490" stroke-width="2"/>
  <rect x="74" y="46" width="72" height="46" fill="#ffffff" stroke="#8f9490" stroke-width="1"/>
  <text x="80" y="60" font-family="Helvetica, Arial" font-size="10" font-weight="700" fill="#1f1c16">{tallman}</text>
  <text x="80" y="74" font-family="Helvetica, Arial" font-size="9" fill="#3a362e">{strength}</text>
  <text x="80" y="86" font-family="Helvetica, Arial" font-size="8" fill="#5a564a">{form}</text>
  <text x="74" y="106" font-family="Helvetica, Arial" font-size="8" fill="#5a564a">Shelf: {shelf}</text>
  <line x1="70" y1="24" x2="150" y2="24" stroke="#8f9490" stroke-width="2"/>
</svg>"""

def pen_svg(name, tallman, strength, form, shelf):
    return f"""<svg viewBox="0 0 220 140" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="220" height="140" fill="#ffffff"/>
  <rect x="30" y="55" width="140" height="26" rx="13" fill="#e6e6e6" stroke="#8f9490" stroke-width="2"/>
  <rect x="150" y="60" width="20" height="16" rx="4" fill="#c9c4b6"/>
  <rect x="46" y="60" width="90" height="16" fill="#ffffff" stroke="#8f9490" stroke-width="1"/>
  <text x="50" y="71" font-family="Helvetica, Arial" font-size="8" font-weight="700" fill="#1f1c16">{tallman}</text>
  <text x="30" y="100" font-family="Helvetica, Arial" font-size="10" fill="#3a362e">{strength}</text>
  <text x="30" y="114" font-family="Helvetica, Arial" font-size="9" fill="#5a564a">{form} pen  |  Shelf: {shelf}</text>
</svg>"""

def capsule_svg(name, tallman, strength, form, shelf):
    return f"""<svg viewBox="0 0 220 140" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="220" height="140" fill="#ffffff"/>
  <rect x="10" y="10" width="200" height="120" rx="6" fill="#f5f3ee" stroke="#9a9488" stroke-width="2"/>
  <text x="20" y="45" font-family="Helvetica, Arial" font-size="16" font-weight="700" fill="#1f1c16">{tallman}</text>
  <text x="20" y="65" font-family="Helvetica, Arial" font-size="12" fill="#3a362e">{strength}</text>
  <text x="20" y="82" font-family="Helvetica, Arial" font-size="11" fill="#5a564a">{form}</text>
  <text x="20" y="100" font-family="Helvetica, Arial" font-size="10" fill="#5a564a">Shelf: {shelf}</text>
</svg>"""

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(MED_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    for row in rows:
        mid = row["id"]
        if mid in VIAL_IDS:
            svg = vial_svg(row["name"], row["tallman"], row["strength"], row["form"], row["shelf_location"])
        elif mid in PEN_IDS:
            svg = pen_svg(row["name"], row["tallman"], row["strength"], row["form"], row["shelf_location"])
        elif mid in CAPSULE_IDS:
            svg = capsule_svg(row["name"], row["tallman"], row["strength"], row["form"], row["shelf_location"])
        else:
            svg = tablet_box_svg(row["name"], row["tallman"], row["strength"], row["form"], row["shelf_location"])
        out_path = os.path.join(OUT_DIR, row["packaging_file"])
        with open(out_path, "w", encoding="utf-8") as out:
            out.write(svg)
        print("wrote", out_path)

if __name__ == "__main__":
    main()
