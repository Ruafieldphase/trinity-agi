"""
E2E Integration Test: Feedback Loop Pipeline

Tests the complete feedback loop integration:
1. RPA/YouTube events → merge to augmented ledger
2. BQI learner ingestion
3. Online learner weight updates
4. Monitoring dashboard reflection
5. Realtime pipeline integration
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from workspace_root import get_workspace_root

# Add workspace to path
WORKSPACE = get_workspace_root()
sys.path.insert(0, str(WORKSPACE))

print(f"[DEBUG] WORKSPACE: {WORKSPACE}")
print(f"[DEBUG] __file__: {Path(__file__).resolve()}")

def check_file_exists(path: Path, name: str) -> bool:
    """Check if file exists and has content."""
    if not path.exists():
        print(f"[FAIL] {name} not found: {path}")
        return False
    
    size = path.stat().st_size
    if size == 0:
        print(f"[FAIL] {name} is empty: {path}")
        return False
    
    print(f"[OK] {name} exists ({size} bytes)")
    return True


def check_jsonl(path: Path, name: str, min_count: int = 1) -> bool:
    """Check JSONL file has minimum entries."""
    if not check_file_exists(path, name):
        return False
    
    try:
        with path.open("r", encoding="utf-8") as f:
            lines = [line for line in f if line.strip()]
        
        count = len(lines)
        if count < min_count:
            print(f"[FAIL] {name} has {count} entries, expected >= {min_count}")
            return False
        
        print(f"[OK] {name} has {count} entries")
        
        # Verify JSON parse
        for i, line in enumerate(lines[:3], 1):  # Check first 3
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    print(f"[FAIL] {name} line {i} is not a dict")
                    return False
            except json.JSONDecodeError as e:
                print(f"[FAIL] {name} line {i} invalid JSON: {e}")
                return False
        
        return True
    
    except Exception as e:
        print(f"[FAIL] Error reading {name}: {e}")
        return False


def check_json(path: Path, name: str) -> dict:
    """Check JSON file exists and parse."""
    if not check_file_exists(path, name):
        return {}
    
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"[OK] {name} parsed successfully")
        return data
    
    except Exception as e:
        print(f"[FAIL] Error parsing {name}: {e}")
        return {}


def main():
    print("=" * 60)
    print("E2E Integration Test: Feedback Loop Pipeline")
    print("=" * 60)
    
    fdo_outputs = WORKSPACE / "fdo_agi_repo" / "outputs"
    workspace_outputs = WORKSPACE / "outputs"
    
    # Test 1: Feedback JSONL files
    print("\n[Test 1] Feedback Loop Sources")
    print("-" * 60)
    yt_feedback = fdo_outputs / "youtube_feedback_bqi.jsonl"
    rpa_feedback = fdo_outputs / "rpa_feedback_bqi.jsonl"
    
    test1a = check_jsonl(yt_feedback, "YouTube Feedback", min_count=1)
    test1b = check_jsonl(rpa_feedback, "RPA Feedback", min_count=1)
    test1 = test1a and test1b
    
    # Test 2: Augmented Ledger
    print("\n[Test 2] Augmented Ledger")
    print("-" * 60)
    aug_ledger = WORKSPACE / "fdo_agi_repo" / "memory" / "resonance_ledger_augmented.jsonl"
    test2 = check_jsonl(aug_ledger, "Augmented Ledger", min_count=7)  # Should have RPA+YT events
    
    # Test 3: BQI Pattern Model
    print("\n[Test 3] BQI Pattern Model")
    print("-" * 60)
    bqi_model = fdo_outputs / "bqi_pattern_model.json"
    model_data = check_json(bqi_model, "BQI Pattern Model")
    test3 = bool(model_data)
    
    if test3:
        patterns = model_data.get("patterns", {})
        print(f"  Patterns learned: {len(patterns)}")
        
        for k, v in list(patterns.items())[:3]:
            priority = v.get("priority", "?")
            count = v.get("count", 0)
            print(f"    {k}: priority={priority}, count={count}")
    
    # Test 4: Ensemble Weights
    print("\n[Test 4] Ensemble Weights")
    print("-" * 60)
    weights_path = fdo_outputs / "ensemble_weights.json"
    weights = check_json(weights_path, "Ensemble Weights")
    test4 = bool(weights)
    
    if test4:
        w = weights.get("weights", {})
        print(f"  Pattern weight: {w.get('pattern', 0):.4f}")
        print(f"  Feedback weight: {w.get('feedback', 0):.4f}")
        print(f"  Persona weight: {w.get('persona', 0):.4f}")
        print(f"  Last updated: {weights.get('updated_at', 'N/A')}")
    
    # Test 5: Monitoring Report Integration
    print("\n[Test 5] Monitoring Report Integration")
    print("-" * 60)
    report_md = workspace_outputs / "monitoring_report_latest.md"
    test5 = False
    
    if check_file_exists(report_md, "Monitoring Report"):
        with report_md.open("r", encoding="utf-8") as f:
            content = f.read()
        
        if "Feedback Loop:" in content and "YouTube=" in content:
            print("[OK] Feedback Loop stats found in report")
            test5 = True
        else:
            print("[FAIL] Feedback Loop stats NOT found in report")
    
    # Test 6: Realtime Pipeline Integration
    print("\n[Test 6] Realtime Pipeline Integration")
    print("-" * 60)
    rt_status = workspace_outputs / "realtime_pipeline_status.json"
    rt_data = check_json(rt_status, "Realtime Pipeline Status")
    test6 = False
    
    if rt_data:
        fb = rt_data.get("feedback_loop", {})
        if fb and fb.get("total", 0) > 0:
            print(f"  YouTube: {fb.get('youtube', 0)}")
            print(f"  RPA: {fb.get('rpa', 0)}")
            print(f"  Total: {fb.get('total', 0)}")
            test6 = True
        else:
            print("[FAIL] No feedback_loop data in realtime status")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    results = {
        "Feedback Sources": test1,
        "Augmented Ledger": test2,
        "BQI Model": test3,
        "Ensemble Weights": test4,
        "Monitoring Report": test5,
        "Realtime Pipeline": test6,
    }
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name}")
    
    print("-" * 60)
    
    total = len(results)
    passed_count = sum(1 for p in results.values() if p)
    
    print(f"\nPassed: {passed_count}/{total} ({100*passed_count/total:.1f}%)")
    
    if passed_count == total:
        print("\n🎉 All tests PASSED!")
        return 0
    else:
        print(f"\n⚠️ {total - passed_count} test(s) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
