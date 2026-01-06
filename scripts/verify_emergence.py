import sys
import time
import logging
from pathlib import Path

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("VerifyEmergence")

from agi_core.internal_state import get_internal_state
from agi_core.latent_drives import update_latent_drives

def verify_emergence():
    print("🌌 Testing Phase 18: Emergent Autonomy & Meta-Learning...")
    state = get_internal_state()
    
    # 1. Test Latent Drives
    print("\n[1. Latent Drives Test]")
    modifier = update_latent_drives(state)
    print(f"-> Emergent Latent Modifier: {modifier:.4f}")
    
    # 2. Test Homeostatic Throttle with Latent Modifier
    print("\n[2. Dynamic Throttle Test]")
    state.body_stress = 0.6 # Moderate stress
    throttle_normal = state.get_homeostatic_throttle(latent_modifier=1.0)
    throttle_emergent = state.get_homeostatic_throttle(latent_modifier=modifier)
    print(f"-> Base Stress: {state.body_stress}")
    print(f"-> Throttle (Standard): {throttle_normal:.4f}")
    print(f"-> Throttle (Emergent): {throttle_emergent:.4f}")

    # 3. Test Meta-Learning (Threshold Adaptation)
    print("\n[3. Meta-Learning Test - Adaptation to Failures]")
    initial_threshold = state.setpoints['stress_alert_threshold']
    print(f"-> Initial Stress Alert Threshold: {initial_threshold:.4f}")
    
    # Simulate 20 failures to lower the success rate
    print("-> Simulating 20 consecutive failures...")
    for _ in range(20):
        state.apply_experience("explore", success=False, duration=10)
    
    # Manually trigger meta_learn (normally happens every 100 heartbeats)
    print("-> Triggering Meta-Learn...")
    state.meta_learn()
    
    final_threshold = state.setpoints['stress_alert_threshold']
    print(f"-> Adjusted Stress Alert Threshold: {final_threshold:.4f}")
    
    if final_threshold < initial_threshold:
        print("\n✅ Meta-Learning SUCCESS. RUD is adapting its skin to the environment.")
    else:
        print("\n❌ Meta-Learning FAILED. Threshold did not move.")

if __name__ == "__main__":
    verify_emergence()
