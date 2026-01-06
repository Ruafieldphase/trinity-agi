import sys
import os
import time
from pathlib import Path

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.internal_state import get_internal_state, update_internal_state
from agi_core.sensory_motor_bridge import SensoryMotorBridge

def verify_senses():
    print("🎧 Testing Multisensory Perception...")
    state = get_internal_state()
    bridge = SensoryMotorBridge(WORKSPACE_ROOT)
    
    # 1. Test Sensory Bridge directly
    print("\n[Bridge Scan]")
    senses = bridge.get_all_senses()
    print(f"Network Wind: {senses['network_wind']:.2f}")
    print(f"Audio Ambience: {senses['audio_ambience']:.2f}")
    print(f"Mutation Detected: {senses['has_mutation']}")
    
    # 2. Test State Integration
    print("\n[State Integration]")
    state.network_wind = senses['network_wind']
    state.audio_ambience = senses['audio_ambience']
    
    # Trigger self-regulation to see circadian and sensory effects
    state.self_regulate()
    
    print(f"Internal Circadian Factor: {state.sensory_circadian_factor:.3f}")
    print(f"Current Resonance: {state.resonance:.3f}")
    print(f"Current Unconscious: {state.unconscious:.3f}")
    
    if 0.5 <= state.sensory_circadian_factor <= 1.0:
        print("\n✅ Sensory verification SUCCESS.")
    else:
        print("\n❌ Sensory verification FAILED (Circadian out of range).")

if __name__ == "__main__":
    verify_senses()
