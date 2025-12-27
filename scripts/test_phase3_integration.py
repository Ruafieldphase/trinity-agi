import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(WORKSPACE_ROOT))

def test_hippocampus_narrative():
    print("🧠 Testing Hippocampus Chronological Narrative...")
    from fdo_agi_repo.copilot.hippocampus import CopilotHippocampus
    hippo = CopilotHippocampus(WORKSPACE_ROOT)
    
    # Store a dummy episodic memory
    hippo.long_term.store_episodic({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "test_event",
        "data": {"title": "Phase 3 Integration Test Started"}
    })
    
    narrative = hippo.get_chronological_narrative(hours=24)
    print(narrative)
    # Check if our test string is present in the narrative
    if "Phase 3 Integration Test Started" in narrative:
        print("✅ Hippocampus Narrative Test Passed\n")
    else:
        # If not, let's print the last few lines of the ledger to debug
        print("❌ Hippocampus Narrative Test Failed: Item not found in narrative.")
        sys.exit(1)

def test_drift_trigger():
    print("📈 Testing Model Drift Trigger...")
    from agi_core.self_trigger import compute_model_drift_trigger
    
    # Create a dummy digital twin state with high mismatch
    twin_dir = WORKSPACE_ROOT / "outputs" / "sync_cache"
    twin_dir.mkdir(parents=True, exist_ok=True)
    twin_file = twin_dir / "digital_twin_state.json"
    
    dummy_state = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mismatch_0_1": 0.85,
        "route_hint": "REST",
        "observed": {"last_action": "full_cycle"}
    }
    
    with open(twin_file, 'w', encoding='utf-8') as f:
        json.dump(dummy_state, f)
        
    trigger = compute_model_drift_trigger(str(twin_file), threshold=0.5)
    
    if trigger:
        print(f"🎯 Drift Trigger Caught: {trigger.reason}")
        assert trigger.type.value == "MODEL_DRIFT"
        assert trigger.score == 0.85
        print("✅ Drift Trigger Test Passed\n")
    else:
        print("❌ Drift Trigger Test Failed")
        sys.exit(1)

if __name__ == "__main__":
    try:
        test_hippocampus_narrative()
        test_drift_trigger()
        print("🎉 All Phase 3 Integration Tests Passed!")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
