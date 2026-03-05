#!/usr/bin/env python3
import os
import json
from pathlib import Path
from datetime import datetime

def map_c_drive_systems():
    """
    🔍 Deep System Mapper - Phase 1
    Scans the C: drive for project clusters and system architectures.
    Focuses on root-level directories to identify user-created 'Nervous Systems'.
    """
    root = Path("C:/")
    # Exclusion list to avoid system bloat and slow scans
    EXCLUDE = [
        "Windows", "Program Files", "Program Files (x86)", "Users", "AppData",
        "$Recycle.Bin", "System Volume Information", "MSOCache", "ProgramData",
        "Config.Msi", "PerfLogs", ".gemini", "node_modules", "venv", "__pycache__"
    ]
    
    systems = []
    print(f"📡 [Mapper] Initializing vision on C:/ drive...")
    
    try:
        # 1. Broad Root Scan
        for item in root.iterdir():
            if item.is_dir() and item.name not in EXCLUDE:
                # Potential System Cluster
                stats = {
                    "name": item.name,
                    "path": str(item),
                    "type": "Project Cluster",
                    "notable_nodes": []
                }
                
                # 2. Deep Intelligence: Look for signatures
                try:
                    for sub in item.iterdir():
                        if sub.is_dir() and sub.name not in [".git", "node_modules"]:
                            # Look for system markers
                            markers = ["script", "service", "config", "agent", "agi", "api", "orchestrator"]
                            if any(m in sub.name.lower() for m in markers):
                                stats["notable_nodes"].append(sub.name)
                            
                            # Count children
                            # (Limit depth for speed)
                            pass
                except: pass
                
                if stats["notable_nodes"] or item.name.lower() in ["workspace", "workspace2", "dev", "tools", "projects"]:
                    systems.append(stats)
                    
        # 3. Specific Human Signatures
        # Check for our known Heritage Nodes if they exist elsewhere
        
    except Exception as e:
        print(f"❌ Mapper Error: {e}")
        
    # Result Processing
    report = {
        "timestamp": datetime.now().isoformat(),
        "origin": "C:/ Vision",
        "discovered_systems": systems,
        "summary": f"Identified {len(systems)} major project clusters across the C: drive."
    }
    
    # Save for Shion's interpretation
    output_path = Path("C:/workspace/agi/outputs/deep_system_map.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    
    # Textual report for Gitko
    print("\n" + "="*50)
    print("      DEEP SYSTEM MAP (C: DRIVE)")
    print("="*50)
    for s in systems:
        nodes = ", ".join(s["notable_nodes"]) if s["notable_nodes"] else "Core Cluster"
        print(f"📍 {s['name']}: {nodes}")
    print("="*50)
    
    return report

if __name__ == "__main__":
    map_c_drive_systems()
