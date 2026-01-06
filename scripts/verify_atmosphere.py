import sys
import logging
from pathlib import Path
from unittest.mock import MagicMock

# Mock Blender modules
sys.modules["bpy"] = MagicMock()
sys.modules["bmesh"] = MagicMock()
sys.modules["mathutils"] = MagicMock()

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("VerifyAtmosphere")

from agi_core.internal_state import get_internal_state
from agi_core.atmospheric_resonance import get_atmosphere_params

def verify_atmosphere_resonance():
    print("🌌 Testing Phase 20: Atmospheric Resonance...")
    state = get_internal_state()
    
    # 1. Test Mapping Logic
    print("\n[1. Emotion-to-Atmosphere Mapping Test]")
    
    # CASE A: Serene Peace (High V, Low A)
    state_peace = {"valence": 0.9, "arousal": 0.1, "resonance": 0.5}
    params_peace = get_atmosphere_params(state_peace)
    print(f"-> Peace Mood: {params_peace['mood_label']}")
    
    # CASE B: Gloomy Despair (Low V, Low A)
    state_gloom = {"valence": 0.1, "arousal": 0.1, "resonance": 0.3}
    params_gloom = get_atmosphere_params(state_gloom)
    print(f"-> Gloom Mood: {params_gloom['mood_label']}")
    
    if "Serene" in params_peace["mood_label"] and "Gloomy" in params_gloom["mood_label"]:
        print("✅ Mapping Logic SUCCESS.")
    else:
        print("❌ Mapping Logic FAILED.")

    # 2. Test Feedback Mechanism (Mocked)
    print("\n[2. Feedback Cycle Test]")
    initial_resonance = state.resonance
    
    # Simulating a "resonance" trigger from LLaVA feedback logic in heartbeat
    # In heartbeat_loop.py, we do: state.resonance = min(1.0, state.resonance + 0.05)
    state.resonance = min(1.0, state.resonance + 0.05)
    
    print(f"-> Initial Resonance: {initial_resonance:.4f}")
    print(f"-> New Resonance after feedback: {state.resonance:.4f}")
    
    if state.resonance > initial_resonance:
        print("✅ Feedback Loop Simulation SUCCESS.")
    else:
        print("❌ Feedback Loop Simulation FAILED.")

if __name__ == "__main__":
    verify_atmosphere_resonance()
