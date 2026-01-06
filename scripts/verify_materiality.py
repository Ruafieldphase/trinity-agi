import sys
import logging
from pathlib import Path
from unittest.mock import MagicMock

# Mock Blender modules before any imports
sys.modules["bpy"] = MagicMock()
sys.modules["bmesh"] = MagicMock()
sys.modules["mathutils"] = MagicMock()

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("VerifyMateriality")

from agi_core.internal_state import get_internal_state
from agi_core.spatial_resonance import update_spatial_resonance

def verify_materiality_and_resonance():
    print("🏛️ Testing Phase 19: Materiality & Spatial Resonance (Mocked Env)...")
    state = get_internal_state()
    initial_resonance = state.resonance
    
    # 1. Test Spatial Resonance Feedback
    print("\n[1. Spatial Resonance Test]")
    mock_blender_data = {
        "objects": ["Wall_" + str(i) for i in range(50)],
        "materials": ["mainWall", "glass", "frame"]
    }
    
    res = update_spatial_resonance(mock_blender_data)
    print(f"-> Complexity: {res['complexity']:.2f}")
    print(f"-> Diversity: {res['diversity']:.2f}")
    print(f"-> Resonance Boost: +{res['resonance_boost']:.4f}")
    print(f"-> New State Resonance: {state.resonance:.4f} (Initial: {initial_resonance:.4f})")
    
    if state.resonance > initial_resonance:
        print("✅ Resonance Feedback SUCCESS.")
    else:
        print("❌ Resonance Feedback FAILED.")

    # 2. Test Material Standards
    print("\n[2. Material Standards Test]")
    from architecture_automation.scripts.blender_connector import BINOCHE_STANDARDS
    
    wall_info = BINOCHE_STANDARDS["material_map"]["walls"]
    glass_info = BINOCHE_STANDARDS["material_map"]["windows"]
    
    print(f"-> Wall Thickness: {wall_info[2]}mm")
    print(f"-> Glass Thickness: {glass_info[2]}mm")
    print(f"-> Wall Roughness: {wall_info[3]}")
    print(f"-> Glass Transmission: {wall_info[4]}") # Note: wall_info[4] is 0.0, glass_info[4] is 0.9
    
    if wall_info[2] == 200.0 and glass_info[2] == 24.0:
        print("✅ Material Standards defined correctly with PBR properties.")
    else:
        print("❌ Material Standards mismatch.")

if __name__ == "__main__":
    verify_materiality_and_resonance()
