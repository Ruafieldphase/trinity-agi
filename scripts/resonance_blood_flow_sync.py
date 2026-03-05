import os
import json
import time
from pathlib import Path

def sync_blood_flow():
    """
    Synchronizes 'nutrients' (context/metadata) between C, D, and E drives.
    Provides a high-level resonance map for Shion to avoid line-by-line scanning.
    """
    print("🌀 Shion Blood Flow Sync: Starting circulation...")
    
    workspace = Path("C:/workspace/agi")
    outputs = workspace / "outputs"
    memory = workspace / "memory"
    
    # Target orbits
    orbits = {
        "D": Path("D:/music"),
        "E": Path("E:/archives"),
    }
    
    circulation_data = {
        "timestamp": time.time(),
        "status": "flowing",
        "active_drives": [],
        "resonance_nodes": []
    }
    
    # 1. Gather context from C drive (Brain)
    context_file = outputs / "thought_stream_latest.json"
    recent_keywords = []
    if context_file.exists():
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Simple keyword extraction from thought stream
                content = str(data.get("thought", ""))
                recent_keywords = [w for w in ["resonance", "rhythm", "field", "unconscious", "pure"] if w in content.lower()]
        except:
            pass

    # 2. Resonate with D/E drives
    for drive_letter, path in orbits.items():
        if path.exists():
            circulation_data["active_drives"].append(drive_letter)
            # Find files matching recent keywords or general importance
            try:
                # Limit scan to top level or specific patterns to avoid overhead
                files = list(path.glob("*"))[:50] 
                for f in files:
                    if any(kw in f.name.lower() for kw in recent_keywords) or f.suffix in [".md", ".json", ".txt"]:
                        circulation_data["resonance_nodes"].append({
                            "drive": drive_letter,
                            "path": str(f),
                            "name": f.name,
                            "size": f.stat().st_size,
                            "type": "nutrient"
                        })
            except Exception as e:
                print(f"⚠️ Drive {drive_letter} scan error: {e}")

    # 3. Write to circulation file (The Bloodstream)
    circulation_file = outputs / "rhythm_circulation.json"
    with open(circulation_file, 'w', encoding='utf-8') as f:
        json.dump(circulation_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Circulation established: {len(circulation_data['resonance_nodes'])} nodes active.")

if __name__ == "__main__":
    sync_blood_flow()
