import sys
import os
import time
from pathlib import Path

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.internal_state import get_internal_state
from agi_core.heartbeat_loop import calculate_pulse_interval

def verify_homeostasis():
    print("🌿 Testing Homeostatic Reflex...")
    state = get_internal_state()
    
    # 1. Normal State
    state.body_stress = 0.1
    state.is_hibernating = False
    throttle = state.get_homeostatic_throttle()
    print(f"Normal Stress (0.1): Throttle = {throttle:.2f} (Expected: 1.0)")
    
    # 2. High Stress
    state.body_stress = 0.8
    throttle = state.get_homeostatic_throttle()
    print(f"High Stress (0.8): Throttle = {throttle:.2f} (Expected: ~0.5)")
    
    # 3. Hibernation State
    state.is_hibernating = True
    throttle = state.get_homeostatic_throttle()
    print(f"Hibernating: Throttle = {throttle:.2f} (Expected: 0.1)")
    
    # 4. Heartbeat Interval Integration
    state.is_hibernating = False
    state.body_stress = 0.9
    throttle = state.get_homeostatic_throttle()
    
    base_interval = 5.0
    throttled_interval = base_interval / throttle
    print(f"Throttled Heartbeat: {base_interval}s -> {throttled_interval:.1f}s")
    
    if throttled_interval > base_interval:
        print("✅ Homeostasis verification SUCCESS.")
    else:
        print("❌ Homeostasis verification FAILED.")

if __name__ == "__main__":
    verify_homeostasis()
