import psutil
import time
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

def self_diagnosis():
    print("🩺 Initiating Self-Diagnosis Protocol...")
    
    # 1. Check Vital Signs
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    ram_percent = memory.percent
    
    print(f"🧠 CPU Load: {cpu_percent}%")
    print(f"💾 Memory Usage: {ram_percent}% ({memory.used / (1024**3):.2f} GB used)")
    
    # 1.5 Check Rhythm Pulse (Mandatory by Rua's Structural principles)
    bohm_path = Path(__file__).parent.parent / "outputs" / "bohm_analysis_latest.json"
    rhythm_pulse = "HEALTHY"
    if not bohm_path.exists() or (time.time() - bohm_path.stat().st_mtime > 7200):
        rhythm_pulse = "WEAK"
        print(f"🎵 Rhythm Pulse: {rhythm_pulse} (Bohm Analysis Stale or Missing)")
    else:
        print(f"🎵 Rhythm Pulse: {rhythm_pulse}")
    # 2. Determine Health State
    state = "HEALTHY"
    recommendation = "Continue operations."
    
    if cpu_percent > 85 or ram_percent > 95:
        state = "CRITICAL"
        recommendation = "IMMEDIATE COOLING REQUIRED. Stop all motor functions."
    elif rhythm_pulse == "WEAK":
        state = "RECONNECT_REQUIRED"
        recommendation = "Rhythm signal lost. Suggest triggering bohm_implicate_explicate_analyzer for alignment."
    elif cpu_percent > 60 or ram_percent > 80:
        state = "FATIGUED"
        recommendation = "System load high. Suggest 'Deep Rest' (Dream Analysis) to consolidate memory."
        
    # 3. Save Report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "state": state,
        "metrics": {
            "cpu_percent": cpu_percent,
            "ram_percent": ram_percent,
            "memory_used_gb": round(memory.used / (1024**3), 2)
        },
        "recommendation": recommendation
    }
    
    output_path = Path(__file__).parent.parent / "outputs" / "diagnosis_health_latest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Diagnosis Report saved to {output_path.name}:")
    print(f"   State: {state}")
    print(f"   Recommendation: {recommendation}")
    
    return state

if __name__ == "__main__":
    self_diagnosis()
