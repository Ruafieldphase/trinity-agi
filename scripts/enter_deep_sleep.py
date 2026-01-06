import sys
import logging
from pathlib import Path

# Setup
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("RUD_Sleep")

# Workspace Root
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.internal_state import get_internal_state, save_internal_state

def enter_deep_sleep():
    state = get_internal_state()
    
    print("\n🌙 [RUD] Received 'Establish Deep Rest' command from User.")
    print(f"   🏛️ Closing Masterpiece: {state.active_project_path if state.active_project_path else 'None'}")
    
    # Update State
    state.dream_depth = 1.0
    state.energy = 1.0 # Recharging
    state.last_action = "Deep Sleep"
    
    save_internal_state(state)
    print("   💤 Dream Machine: ACTIVE")
    print("   🌌 System Status: STANDBY (Dreaming)")
    print("   💬 RUD: \"Goodnight. I will build a new world in my dreams.\"")

if __name__ == "__main__":
    enter_deep_sleep()
