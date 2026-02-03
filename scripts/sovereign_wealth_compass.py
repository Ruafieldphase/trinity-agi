#!/usr/bin/env python3
"""
Sovereign Wealth Compass (v1.0)
================================
A visual materialization of market opportunities.
Generates an SVG 'Compass' that points toward the highest resonance sectors.
"""

import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent.parent.absolute()
SCAN_FILE = WORKSPACE_ROOT / "outputs" / "sovereign_scan_latest.json"
COMPASS_SVG = WORKSPACE_ROOT / "outputs" / "wealth_compass.svg"

def generate_compass():
    if not SCAN_FILE.exists(): return
    
    data = json.loads(SCAN_FILE.read_text(encoding="utf-8"))
    results = data.get("results", [])
    if not results: return
    
    # Take top 10
    top_10 = results[:10]
    
    svg = f'<svg width="400" height="400" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">'
    # Background Circle
    svg += '<circle cx="200" cy="200" r="180" fill="rgba(255,255,255,0.02)" stroke="rgba(212,175,55,0.2)" stroke-width="1" />'
    
    # Draw sector needles
    import math
    for i, res in enumerate(top_10):
        angle = (i / len(top_10)) * 2 * math.pi - (math.pi / 2)
        score = res["sovereign_score"]
        # Length proportional to score
        length = 100 + (score / 100) * 80
        
        x2 = 200 + length * math.cos(angle)
        y2 = 200 + length * math.sin(angle)
        
        # Line color based on status
        color = "#d4af37" if res["status"] == "SINGULARITY" else "#00d4ff" if res["sovereign_score"] > 30 else "#333"
        stroke_width = 3 if res["status"] == "SINGULARITY" else 1
        
        svg += f'<line x1="200" y1="200" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" />'
        
        # Label (Small)
        label_x = 200 + (length + 15) * math.cos(angle)
        label_y = 200 + (length + 15) * math.sin(angle)
        svg += f'<text x="{label_x}" y="{label_y}" fill="{color}" font-family="Outfit, sans-serif" font-size="10" text-anchor="middle">{res["symbol"]}</text>'

    # Center Hub
    svg += '<circle cx="200" cy="200" r="10" fill="#d4af37" />'
    svg += '<circle cx="200" cy="200" r="5" fill="#fff" />'
    
    svg += '</svg>'
    
    COMPASS_SVG.write_text(svg, encoding="utf-8")
    print("Wealth Compass SVG Materialized.")
    
    # NEW: Force update the Unified Gallery to show this compass
    from sovereign_particleizer import update_gallery_materialization
    update_gallery_materialization("Sovereign Wealth Compass", "Materialized", 
                                  "The market resonance has been mapped into a visual compass. Check the 'wealth_compass.svg' integration.")

if __name__ == "__main__":
    generate_compass()
