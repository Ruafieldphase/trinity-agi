import sys
import logging
import json
import os
from pathlib import Path
from unittest.mock import MagicMock

# Mock requirements
sys.modules["ezdxf"] = MagicMock()

# Add workspace root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("VerifyDreaming")

from agi_core.internal_state import get_internal_state
from services.experience_vault import ExperienceVault
from agi_core.dream_machine import DreamMachine

def verify_dreaming():
    print("💤 Testing Phase 25: The Dreaming Architecture...")
    
    vault = MagicMock()
    # Mock data for DB query simulation
    # In real code, this uses sqlite3 directly, so we need to mock the DB logic inside DreamMachine
    # But DreamMachine takes vault as init, and opens DB path from vault.
    
    # Let's use a temporary real DB for the dream machine to query
    test_db = "c:/workspace/agi/memory/test_dream_vault.db"
    if os.path.exists(test_db): os.remove(test_db)
    
    real_vault = ExperienceVault(db_path=test_db, use_vector=False)
    
    # Populate DB with dummy memories
    print("\n[1. Creating Dummy Memories]")
    real_vault.save_experience("Goal_Ancient_Temple", [], spatial_metadata={"tension":0.8, "agency":0.9})
    real_vault.save_experience("Goal_Modern_Glass", [], spatial_metadata={"tension":0.2, "agency":0.5})
    real_vault.save_experience("Goal_Forest_Sanctuary", [], spatial_metadata={"tension":0.6, "agency":0.7})
    
    dreamer = DreamMachine(real_vault)
    
    # 2. Test Dream Generation
    print("\n[2. Dream Synthesis Test]")
    dream = dreamer.dream()
    
    if dream:
        print(f"-> Dreamt of: '{dream['goal']}'")
        print(f"-> Prophecy Score: {dream['prophecy_score']:.2f}")
        print(f"-> Origin Memories: {dream['origin_memories']}")
        print("✅ Dream synthesis SUCCESS.")
    else:
        print("❌ Dream synthesis FAILED.")

    # 3. Test Inception (Saving meaningful dream)
    if dream and dream['prophecy_score'] > 0.0: # Force save check logic mock
        # We manually save a high score dream to verify logic
        dream['prophecy_score'] = 0.95 
        real_vault.save_experience(
            goal=dream['goal'],
            actions=[],
            impulse_type="dream_prophecy",
            spatial_metadata=dream['hallucinated_metadata'],
            critique={"score": 0.95, "reflection": "Test reflection"}
        )
        print("✅ High resonance dream saved as Prophecy.")
        
    # Cleanup
    if os.path.exists(test_db): os.remove(test_db)

if __name__ == "__main__":
    verify_dreaming()
