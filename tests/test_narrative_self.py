import sys
import os
from pathlib import Path
import json
import time

# Add workspace root for imports
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.narrative_self import should_generate_narrative, NARRATIVE_FILE, INTERNAL_STATE_FILE, CORE_STATE_FILE

def test_cooldown():
    print("Testing cooldown...")
    if NARRATIVE_FILE.exists():
        NARRATIVE_FILE.unlink()
    
    # Create a fresh file
    with open(NARRATIVE_FILE, "w") as f:
        f.write("{}")
    
    # Should be false immediately after creation
    can_gen, reason = should_generate_narrative()
    assert can_gen is False
    assert reason == "cooldown_active"
    print("✅ Cooldown test passed.")

def test_safety_triggers():
    print("Testing safety triggers...")
    
    # Reset file to bypass cooldown
    if NARRATIVE_FILE.exists():
        NARRATIVE_FILE.unlink()
        
    # Mock Fear
    with open(CORE_STATE_FILE, "w") as f:
        json.dump({"fear": {"level": 0.8}}, f)
    
    with open(INTERNAL_STATE_FILE, "w") as f:
        json.dump({"boredom": 0.1}, f) # Safety: reset boredom

    can_gen, reason = should_generate_narrative()
    assert can_gen is False
    assert reason == "high_fear"
    print("✅ Fear trigger test passed.")

    # Mock Boredom
    with open(CORE_STATE_FILE, "w") as f:
        json.dump({"fear": {"level": 0.1}}, f)
    with open(INTERNAL_STATE_FILE, "w") as f:
        json.dump({"boredom": 0.95}, f)
        
    can_gen, reason = should_generate_narrative()
    assert can_gen is False
    assert reason == "high_boredom"
    print("✅ Boredom trigger test passed.")

if __name__ == "__main__":
    # Backup existing files
    temp_narrative = None
    if NARRATIVE_FILE.exists():
        temp_narrative = NARRATIVE_FILE.read_bytes()
    
    try:
        test_cooldown()
        test_safety_triggers()
        print("\nAll narrative_self tests passed!")
    finally:
        # Restore if needed
        if temp_narrative:
            NARRATIVE_FILE.write_bytes(temp_narrative)
