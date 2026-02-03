#!/usr/bin/env python3
"""
Sovereign Voice-Field Sync (v1.0)
=================================
Captures the user's voice, analyzes its rhythmic density, 
and syncs it with the current Market Pulse.

Your Voice is the Command.
"""

import os
import json
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path("c:/workspace/agi")
PULSE_FILE = WORKSPACE_ROOT / "outputs" / "sovereign_pulse_latest.json"
VOICE_SYNC_OUTPUT = WORKSPACE_ROOT / "outputs" / "sovereign_voice_sync.json"
VOICE_BUFFER_PATH = WORKSPACE_ROOT / "outputs" / "last_voice_command.wav"

def record_and_sync(duration=5, fs=44100):
    print(f"🎙️ Sovereign Voice Capture Initiated...")
    print(f"Please speak your Materialization Intent (e.g., 'Resonance', 'Execute').")
    
    try:
        # Record voice
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait() # Wait for recording to finish
        sf.write(VOICE_BUFFER_PATH, recording, fs)
        
        # Simple Analysis: Energy & Density
        if len(recording) == 0:
            rms = 0.0
            zcr = 0.0
        else:
            rms = np.sqrt(np.mean(recording**2))
            diff = np.diff(np.sign(recording.flatten()))
            zcr = np.mean(np.abs(diff)) if len(diff) > 0 else 0.0
        
        # Ensure zcr is not NaN
        if np.isnan(zcr): zcr = 0.0

        # Load Market Pulse
        pulse_data = {}
        if PULSE_FILE.exists():
            pulse_data = json.loads(PULSE_FILE.read_text(encoding="utf-8"))
        
        market_velocity = pulse_data.get("velocity_15m", 0)
        
        # 🧬 Sync Logic: 
        # Voice Density matches Market Velocity?
        # High Density (Fast speech) -> High Velocity?
        # Calm tone -> Stability?
        
        sync_score = 0
        if market_velocity > 0 and zcr > 0.1: # Aligned for expansion
            sync_score = (zcr * 100) + (market_velocity * 1000)
        else: # Aligned for stability
            sync_score = (1.0 - zcr) * 50
            
        sync_score = min(max(sync_score, 0), 100) # Clamp to 0-100
        
        sync_status = "SYNCHRONIZED" if sync_score > 70 else "ALTRUISTIC_VOID" if sync_score > 40 else "OUT_OF_PHASE"
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "voice_energy_rms": round(float(rms), 4),
            "voice_density_zcr": round(float(zcr), 4),
            "market_pulse_velocity": market_velocity,
            "sync_score": round(float(sync_score), 2),
            "status": sync_status,
            "command_detected": "Sovereign Intent Formed"
        }
        
        with open(VOICE_SYNC_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
            
        print(f"✅ Sync Complete: Score {result['sync_score']} ({sync_status})")
        return result

    except Exception as e:
        print(f"❌ Error in Voice-Field Sync: {e}")
        return None

if __name__ == "__main__":
    record_and_sync()
