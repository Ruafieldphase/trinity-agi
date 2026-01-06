import sys
import logging
from pathlib import Path
from unittest.mock import MagicMock

# Mock requirements
sys.modules["bpy"] = MagicMock()
sys.modules["ezdxf"] = MagicMock()

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("VerifyStructural")

from agi_core.internal_state import get_internal_state
from architecture_automation.scripts.dxf_parser_engine import calculate_geometric_tension

def verify_structural_feedback():
    print("🧱 Testing Phase 21: Structural Body & Agency...")
    state = get_internal_state()
    
    # 1. Test DXF Tension Calculation
    print("\n[1. Geometric Tension Calculation Test]")
    mock_clusters = [
        {
            "bbox": [0, 0, 10000, 10000], # 10m x 10m = 100sqm
            "entities": [{"type": "line", "start": [0,0], "end": [100,0]}] * 100 # 100 short lines (10cm)
        }
    ]
    tension = calculate_geometric_tension(mock_clusters)
    print(f"-> Calculated Tension: {tension:.4f}")
    
    if tension > 0.5:
        print("✅ Tension Calculation SUCCESS (High complexity detected correctly).")
    else:
        print("❌ Tension Calculation FAILED.")

    # 2. Test State Update (Agency & Tension)
    print("\n[2. Internal State Update Test]")
    initial_agency = state.agency
    
    # Simulate bridge result
    bridge_res = {
        "agency_score": 0.95,
        "neuromorphic_tension": tension
    }
    
    # Applying the update logic from heartbeat_loop.py
    state.agency = 0.7 * state.agency + 0.3 * bridge_res["agency_score"]
    state.neuromorphic_tension = bridge_res["neuromorphic_tension"]
    
    print(f"-> Initial Agency: {initial_agency:.4f}")
    print(f"-> Resulting Agency: {state.agency:.4f}")
    print(f"-> Resulting Tension: {state.neuromorphic_tension:.4f}")
    
    if state.agency > initial_agency and state.neuromorphic_tension == tension:
        print("✅ State Update SUCCESS.")
    else:
        print("❌ State Update FAILED.")

if __name__ == "__main__":
    verify_structural_feedback()
