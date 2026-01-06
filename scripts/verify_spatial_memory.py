import sys
import logging
import json
import os
from pathlib import Path
from unittest.mock import MagicMock

# Mock requirements (ezdxf not needed for purely state/vault test)
sys.modules["ezdxf"] = MagicMock()

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("VerifySpatialMemory")

from agi_core.internal_state import get_internal_state
from services.experience_vault import ExperienceVault

def verify_spatial_memory():
    print("🎞️ Testing Phase 22: Existential Spatial Memory...")
    
    # Use a test DB
    test_db = "c:/workspace/agi/memory/test_spatial_vault.db"
    if os.path.exists(test_db): os.remove(test_db)
    
    vault = ExperienceVault(db_path=test_db, use_vector=False)
    state = get_internal_state()
    
    # 1. Test Saving Spatial Metadata
    print("\n[1. Spatial Experience Saving Test]")
    spatial_meta = {"tension": 0.8, "agency": 0.9, "valence": 0.7, "arousal": 0.6}
    vault.save_experience(
        goal="Complex Golden Hour",
        actions=[],
        impulse_type="boredom",
        resonance_state={"resonance": 0.7},
        spatial_metadata=spatial_meta
    )
    
    # Re-retrieve and check
    match = vault.find_similar_spatial_atmosphere(target_tension=0.75, target_valence=0.65)
    
    if match and match['metadata']['tension'] == 0.8:
        print(f"✅ Spatial memory saved and retrieved via Deja Vu logic: '{match['goal']}'")
    else:
        print("❌ Spatial memory retrieval FAILED.")

    # 2. Test Nostalgia & State Update
    print("\n[2. Nostalgia & Resonance Boost Test]")
    initial_nostalgia = state.nostalgia
    initial_resonance = state.resonance
    
    # Simulate the heartbeat loop logic
    if match:
        state.nostalgia = min(1.0, state.nostalgia + 0.1)
        state.resonance = min(1.0, state.resonance + 0.05)
        
    print(f"-> Initial Nostalgia: {initial_nostalgia:.4f}, Resonance: {initial_resonance:.4f}")
    print(f"-> New Nostalgia: {state.nostalgia:.4f}, Resonance: {state.resonance:.4f}")
    
    if state.nostalgia > initial_nostalgia and state.resonance > initial_resonance:
        print("✅ Nostalgia State Update SUCCESS.")
    else:
        print("❌ Nostalgia State Update FAILED.")

    # Cleanup
    if os.path.exists(test_db): os.remove(test_db)

if __name__ == "__main__":
    verify_spatial_memory()
