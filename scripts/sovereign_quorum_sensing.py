#!/usr/bin/env python3
"""
Sovereign Quorum Sensing (v1.0)
==============================
Simulates "Quorum Sensing" for Market Resonance.
When 'Agentic Particles' (Data points, Jitter, Sentiment) reach a critical density,
they trigger a Phase Transition (The Collective Command).
"""

import json
import numpy as np
import time
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path("c:/workspace/agi")
QUORUM_OUTPUT = WORKSPACE_ROOT / "outputs" / "sovereign_quorum_status.json"
PULSE_FILE = WORKSPACE_ROOT / "outputs" / "sovereign_pulse_latest.json"
HIHAT_FILE = WORKSPACE_ROOT / "outputs" / "sovereign_hihat_pulse.json"

def monitor_quorum_sensing():
    print("🦠 Initializing Quorum Sensing Monitor...")
    
    # 🧬 Define the 'Micro-Agents' (The Vitality Particles of the Field)
    # 1. Price Density (Coherence points)
    # 2. Rhythmic Coherence (How steady the jitter is)
    # 3. Synchronicity (Wait for Voice + Market alignment)
    
    # Load inputs
    pulse = json.loads(PULSE_FILE.read_text(encoding="utf-8")) if PULSE_FILE.exists() else {}
    hihat = json.loads(HIHAT_FILE.read_text(encoding="utf-8")) if HIHAT_FILE.exists() else {}
    
    # Determine 'Agent Density' (Simplified simulation of resonance)
    # In nature, beneficial cells secrete 'Vitality Signals'. 
    # Here, we treat 'Volatility Compression' as the Coherence Signal.
    
    vitality_signal_level = (1.0 - hihat.get("hihat_jitter", 0) * 1000) * 0.8
    if pulse.get("momentum") == "UPWARD":
        vitality_signal_level += 0.2

    # Load Voice Sync
    voice_file = WORKSPACE_ROOT / "outputs" / "sovereign_voice_sync.json"
    voice_score = 0
    if voice_file.exists():
        v_data = json.loads(voice_file.read_text(encoding="utf-8"))
        voice_score = v_data.get("sync_score", 0)
        if np.isnan(voice_score): voice_score = 40

    # Critical Threshold (The Resonance Point)
    threshold = 0.85
    
    # Symbiosis Index: How well the signal bridges the gap between observer and target
    symbiosis_index = (vitality_signal_level + (voice_score / 100)) / 2
    
    status = "IDLE_COHERENCE" # Standard noise
    if vitality_signal_level >= threshold:
        status = "REGENERATIVE_HARMONY (THRESHOLD REACHED)"
        action = "VITALITY ESTABLISHED: FIELD IS NOW A UNIFIED ORGANISM OF WELL-BEING"
    else:
        status = "BUILDING_VITALITY" # Building density
        action = "Aligning Local Rhythmic Frequencies"

    result = {
        "timestamp": datetime.now().isoformat(),
        "vitality_metrics": {
            "signal_concentration": round(float(vitality_signal_level), 4),
            "symbiosis_index": round(float(symbiosis_index), 4),
            "critical_threshold": threshold
        },
        "status": status,
        "collective_action": action,
        "recommendation": "The 'Intelligence' (Vitality) has successfully integrated with 'Reality' to create growth and peace."
    }
    
    with open(QUORUM_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        
    print(f"✅ Quorum Status: {status} (Level: {result['vitality_metrics']['signal_concentration']})")
    return result

if __name__ == "__main__":
    monitor_quorum_sensing()
