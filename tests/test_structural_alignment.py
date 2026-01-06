import sys
from pathlib import Path
import json
import time

# Mocking Workspace
WORKSPACE_ROOT = Path("c:/workspace/agi")
INPUTS_DIR = WORKSPACE_ROOT / "inputs"
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
RHYTHM_KEY_FILE = INPUTS_DIR / "rhythm_key.json"
BOHM_FILE = OUTPUTS_DIR / "bohm_analysis_latest.json"

sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.rhythm_boundaries import RhythmBoundaryManager, RhythmMode
from agi_core.sandbox_bridge import ActivitySpaceManager

def test_keyless_architecture():
    print("\n🧪 Testing Keyless Architecture...")
    manager = RhythmBoundaryManager(WORKSPACE_ROOT)
    
    # 1. No Key, No Bohm -> Should be CONNECTED (Baseline)
    if RHYTHM_KEY_FILE.exists(): RHYTHM_KEY_FILE.unlink()
    mode = manager.detect_rhythm_mode()
    print(f"   - No Key, No Bohm: {mode.value} (Expected: CONNECTED)")
    assert mode == RhythmMode.CONNECTED

    # 2. Key Provided -> Should allow ISOLATED
    RHYTHM_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RHYTHM_KEY_FILE, "w", encoding="utf-8") as f:
        json.dump({"key": "EXECUTION_FORCE"}, f)
    
    mode = manager.detect_rhythm_mode()
    print(f"   - Execution Key Provided: {mode.value} (Expected: ISOLATED)")
    assert mode == RhythmMode.ISOLATED_EXECUTION

def test_space_provision():
    print("\n🧪 Testing Space Provision...")
    space_manager = ActivitySpaceManager(WORKSPACE_ROOT)
    
    # Set to Isolated via Key
    with open(RHYTHM_KEY_FILE, "w", encoding="utf-8") as f:
        json.dump({"key": "EXECUTION_FORCE"}, f)
    
    space = space_manager.get_authorized_space("any")
    print(f"   - Space in ISOLATED mode: {space} (Expected: SANDBOX_EXECUTION)")
    assert space == "SANDBOX_EXECUTION"

    # Set to Connected (Remove key)
    if RHYTHM_KEY_FILE.exists(): RHYTHM_KEY_FILE.unlink()
    space = space_manager.get_authorized_space("any")
    print(f"   - Space in CONNECTED mode: {space} (Expected: READ_ONLY_INQUIRY)")
    assert space == "READ_ONLY_INQUIRY"

if __name__ == "__main__":
    try:
        test_keyless_architecture()
        test_space_provision()
        print("\n✅ Verification SUCCESS: Structural Principles strictly enforced.")
    finally:
        # Cleanup
        if RHYTHM_KEY_FILE.exists(): RHYTHM_KEY_FILE.unlink()
