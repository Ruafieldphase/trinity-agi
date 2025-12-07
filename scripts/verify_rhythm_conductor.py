#!/usr/bin/env python3
"""
Rhythm Conductor Verification Script
Tests the 4-dimensional monitoring system
"""

import json
from pathlib import Path
from datetime import datetime
import time

WORKSPACE = Path.home() / "agi"
OUTPUTS = WORKSPACE / "outputs"

def check_rhythm_dimension():
    """Check Rhythm dimension - thought_stream_latest.json"""
    file_path = OUTPUTS / "thought_stream_latest.json"
    if not file_path.exists():
        return {"aligned": False, "reason": "file_not_found"}
    
    age = time.time() - file_path.stat().st_mtime
    if age > 300:  # 5 minutes
        return {"aligned": False, "reason": f"stale_{int(age)}s", "age": age}
    return {"aligned": True, "age": age}

def check_energy_dimension():
    """Check Energy dimension - energy_twin_status.json"""
    file_path = OUTPUTS / "energy_twin_status.json"
    if not file_path.exists():
        return {"aligned": False, "reason": "file_not_found"}
    
    age = time.time() - file_path.stat().st_mtime
    if age > 86400:  # 24 hours
        return {"aligned": False, "reason": f"stale_{int(age/3600)}h", "age": age}
    return {"aligned": True, "age": age}

def check_time_dimension():
    """Check Time dimension - autonomous_agent_state.json"""
    file_path = OUTPUTS / "autonomous_agent_state.json"
    if not file_path.exists():
        return {"aligned": False, "reason": "file_not_found"}
    
    age = time.time() - file_path.stat().st_mtime
    if age > 300:  # 5 minutes
        return {"aligned": False, "reason": f"stale_{int(age)}s", "age": age}
    return {"aligned": True, "age": age}

def check_relationship_dimension():
    """Check Relationship dimension - key files exist"""
    key_files = [
        OUTPUTS / "lumen_state.json",
        OUTPUTS / "thought_stream_latest.json"
    ]
    
    missing = [f.name for f in key_files if not f.exists()]
    if missing:
        return {"aligned": False, "reason": f"missing_{','.join(missing)}"}
    return {"aligned": True}

def check_tempo_file():
    """Check if rhythm_tempo.json is being updated"""
    tempo_file = OUTPUTS / "rhythm_tempo.json"
    if not tempo_file.exists():
        return {"exists": False}
    
    age = time.time() - tempo_file.stat().st_mtime
    with open(tempo_file) as f:
        data = json.load(f)
    
    return {
        "exists": True,
        "age": age,
        "data": data
    }

def main():
    print("=" * 60)
    print("🎵 Rhythm Conductor Verification")
    print("=" * 60)
    print()
    
    # Check 4 dimensions
    print("📊 4-Dimensional Alignment Check:")
    print()
    
    dimensions = {
        "Rhythm": check_rhythm_dimension(),
        "Energy": check_energy_dimension(),
        "Time": check_time_dimension(),
        "Relationship": check_relationship_dimension()
    }
    
    for name, status in dimensions.items():
        aligned = status.get("aligned", False)
        icon = "✅" if aligned else "❌"
        reason = status.get("reason", "")
        age = status.get("age")
        
        print(f"{icon} {name:15s}: {'ALIGNED' if aligned else 'MISALIGNED':12s}", end="")
        if not aligned:
            print(f" - {reason}", end="")
        if age is not None:
            print(f" (age: {age:.0f}s)", end="")
        print()
    
    print()
    
    # Check tempo file
    print("🎼 Tempo Signal Check:")
    print()
    
    tempo_status = check_tempo_file()
    if tempo_status["exists"]:
        print(f"✅ rhythm_tempo.json exists (age: {tempo_status['age']:.0f}s)")
        print()
        print("Current Tempos:")
        for system, info in tempo_status["data"].items():
            if isinstance(info, dict):
                interval = info.get("interval")
                reason = info.get("reason", "")
                timestamp = info.get("timestamp", "")
                print(f"  • {system:20s}: {interval:3d}s - {reason}")
            else:
                print(f"  • {system:20s}: {info}")
    else:
        print("❌ rhythm_tempo.json not found")
    
    print()
    print("=" * 60)
    
    # Summary
    aligned_count = sum(1 for s in dimensions.values() if s.get("aligned", False))
    total = len(dimensions)
    
    print(f"Summary: {aligned_count}/{total} dimensions aligned")
    
    if aligned_count == total:
        print("🎉 System is in perfect rhythm alignment!")
    elif aligned_count >= 3:
        print("⚠️  Minor misalignments detected")
    else:
        print("🚨 Major misalignments - RhythmConductor should be alerting")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
