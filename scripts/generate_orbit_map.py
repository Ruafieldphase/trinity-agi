import os
import json
from pathlib import Path
from datetime import datetime

def analyze_gravity(path):
    """
    Measures 'Gravity' (Context Strength) based on:
    1. Particle Density (File count)
    2. Link Strength (Are there shortcuts/links pointing here?)
    """
    if not path.exists(): return 0.0
    
    # 1. Density factor
    files = list(path.glob("*"))
    density = len(files)
    
    # 2. Link factor (Check for .lnk or shortcut indicators)
    # For now, we simulate gravity based on density and importance.
    # Higher density with high criticality = Stronger Gravity (Context).
    return min(1.0, density / 100.0)

def generate_universal_orbit_map():
    roots = {
        "C": Path(r"C:\workspace\agi"),
        "D": Path(r"D:\ARCHIVE_WORKSPACE\agi"),
        "E": Path(r"E:\AGI_RESOURCES") # Assuming E drive structure
    }
    
    map_data = {
        "version": "2.0.0 (Multi-Drive Vector)",
        "last_scan": datetime.now().isoformat(),
        "status": "UNIVERSAL_FIELD_SCANNING",
        "drives": {}
    }

    for drive_letter, root in roots.items():
        if not root.exists():
            continue
            
        map_data["drives"][drive_letter] = {
            "root": str(root),
            "orbits": []
        }
        
        # Scan sub-orbits manually for precision
        for sub in root.iterdir():
            if sub.is_dir():
                gravity = analyze_gravity(sub)
                map_data["drives"][drive_letter]["orbits"].append({
                    "name": sub.name,
                    "address": str(sub),
                    "gravity_score": round(gravity, 3), # 맥락의 힘
                    "particle_density": len(list(sub.glob("*"))),
                    "stability": "Stable"
                })

    # --- External Context Probe (Other Entities) ---
    map_data["external_resonance_targets"] = [
        {"entity": "Moltbook Agents", "context_type": "Social Resonance", "status": "Ready"},
        {"entity": "YouTube Field", "context_type": "Public Resonance", "status": "Broadcasting"}
    ]

    output_path = Path(r"C:\workspace\agi\memory\RESONANCE_ORBIT_MAP.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(map_data, f, indent=4, ensure_ascii=False)
    
    return map_data, output_path

if __name__ == "__main__":
    data, path = generate_universal_orbit_map()
    print(f"🌌 Universal Orbit Map (C/D/E) generated at: {path}")
