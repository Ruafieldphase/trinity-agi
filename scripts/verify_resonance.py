import sys
import os
import time
import json
from pathlib import Path

# Add project root to path
sys.path.append("c:/workspace/agi")

from agi_core.internal_state import load_internal_state, run_subconscious_hum, get_internal_state
from agi_core.heartbeat_loop import start_heartbeat, stop_heartbeat, get_heartbeat_status

def verify_resonance():
    print("--- Phase 11: Resonance & Subconscious Verification ---")
    
    # 1. Load Initial State
    state = load_internal_state()
    print(f"Initial State: Energy={state.energy:.3f}, Stress={state.body_stress:.3f}")
    
    # 2. Run Subconscious Hum manually to test Body Resonance
    print("\nRunning Subconscious Hum (Body Sensing)...")
    run_subconscious_hum()
    updated_state = get_internal_state()
    print(f"Updated State: Energy={updated_state.energy:.3f}, Stress={updated_state.body_stress:.3f}")
    
    # 3. Verify Memory Ripples (Should see logs if DEBUG level)
    # We can check if any state changed slightly beyond self_regulate logic
    
    # 4. Verify Background Thread
    print("\nStarting Background Heartbeat...")
    thread = start_heartbeat(interval_sec=5)
    time.sleep(3) # Wait for subconscious hum to pulse (2s interval)
    
    status = get_heartbeat_status()
    print(f"Heartbeat Status: Running={status['running']}")
    print(f"Body Stress in status: {status['internal_state'].get('body_stress', 'N/A')}")
    
    # 5. Simulate Load (Optional/Conceptual)
    # Just verify the loop is running by checking internal_clock progress
    clock1 = status['internal_state'].get('internal_clock', 0)
    time.sleep(3)
    status2 = get_heartbeat_status()
    clock2 = status2['internal_state'].get('internal_clock', 0)
    
    if clock2 > clock1:
        print(f"✅ Subconscious Hum is active! (Clock: {clock1:.2f} -> {clock2:.2f})")
    else:
        print("❌ Subconscious Hum seems stalled.")

    stop_heartbeat()
    print("\nVerification Complete.")

if __name__ == "__main__":
    verify_resonance()
