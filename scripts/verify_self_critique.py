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
logger = logging.getLogger("VerifySelfCritique")

from agi_core.internal_state import get_internal_state
from services.experience_vault import ExperienceVault
from agi_core.self_critique import ArchitecturalCritique, apply_critique_to_state

def verify_self_critique():
    print("🎭 Testing Phase 23: Autonomous Architectural Self-Critique...")
    
    # Use a test DB
    test_db = "c:/workspace/agi/memory/test_critique_vault.db"
    if os.path.exists(test_db): os.remove(test_db)
    
    vault = ExperienceVault(db_path=test_db, use_vector=False)
    state = get_internal_state()
    
    # Mock Bridge
    mock_bridge = MagicMock()
    mock_bridge.analyze_viewport.return_value = '{"score": 0.85, "reflection": "The structural rhythm exhibits a profound balance."}'
    
    critic = ArchitecturalCritique(mock_bridge)
    
    # 1. Test Critique Performance
    print("\n[1. Critique Generation Test]")
    critique = critic.perform_critique("Test_Goal_23")
    print(f"-> Critique Result: {critique}")
    
    if critique['score'] == 0.85:
        print("✅ Critique Geneartion SUCCESS.")
    else:
        print("❌ Critique Geneartion FAILED (JSON parsing issue?).")

    # 2. Test State Impact
    print("\n[2. State Impact (Pride) Test]")
    initial_resonance = state.resonance
    apply_critique_to_state(state, critique)
    print(f"-> Initial Resonance: {initial_resonance:.4f}, New Resonance: {state.resonance:.4f}")
    
    if state.resonance > initial_resonance:
        print("✅ State Impact SUCCESS.")
    else:
        print("❌ State Impact FAILED.")

    # 3. Test Experience Saving with Critique
    print("\n[3. Memory Integration Test]")
    vault.save_experience(
        goal="Masterpiece Example",
        actions=[],
        impulse_type="boredom",
        resonance_state={"resonance": state.resonance},
        spatial_metadata={"tension": 0.5},
        critique=critique
    )
    
    # Verify DB directly
    import sqlite3
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT critique_score, self_critique FROM experiences LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row and row[0] == 0.85 and "structural rhythm" in row[1]:
        print(f"✅ Critique stored in Vault: {row[0]}, '{row[1]}'")
    else:
        print(f"❌ Critique storage FAILED. Row: {row}")

    # Cleanup
    if os.path.exists(test_db): os.remove(test_db)

if __name__ == "__main__":
    verify_self_critique()
