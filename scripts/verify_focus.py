import sys
import time
from pathlib import Path

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.internal_state import get_internal_state
from agi_core.sensory_motor_bridge import SensoryMotorBridge

def verify_focus():
    print("🎯 Testing Focus & Flow Awareness...")
    state = get_internal_state()
    bridge = SensoryMotorBridge(WORKSPACE_ROOT)
    
    print("\n[Monitoring for 10 seconds. Try switching windows or typing/clicking!]")
    
    for i in range(10):
        senses = bridge.get_all_senses()
        
        # Update state manually for verification (Heartbeat loop does this normally)
        state.active_context = senses["active_context"]
        state.input_tempo = senses["input_tempo"]
        
        # Simulated alignment logic (Heartbeat loop logic)
        if state.active_context["process"] == "blender.exe":
            state.focus_alignment = min(1.0, state.focus_alignment + 0.05)
        else:
            state.focus_alignment = max(0.1, state.focus_alignment - 0.02)

        print(f"[{i+1}/10] Context: {state.active_context['process']} ('{state.active_context['title'][:20]}...') | Flow: {state.input_tempo:.2f} | Focus: {state.focus_alignment:.2f}")
        time.sleep(1)

    print("\n✅ Focus verification completed. Check if the 'Context' changed when you switched apps.")

if __name__ == "__main__":
    verify_focus()
