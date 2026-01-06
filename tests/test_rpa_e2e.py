#!/usr/bin/env python3
"""
E2E Test: YouTube Learner → RPA Execution
Phase 2.5 Week 3 Day 14

Test flow:
1. Create simple tutorial text
2. Execute via ExecutionEngine (DRY_RUN)
3. Verify result structure
4. Test CLI command
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "fdo_agi_repo"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rpa.execution_engine import ExecutionEngine, ExecutionConfig, ExecutionMode


def test_direct_execution():
    """Test 1: Direct ExecutionEngine usage"""
    print("\n" + "="*60)
    print("Test 1: Direct ExecutionEngine Execution")
    print("="*60)
    
    tutorial = """
How to take a screenshot in Windows:
1. Press Windows key + Shift + S to open Snipping Tool
2. Click on the screen area you want to capture
3. The screenshot is copied to clipboard
4. Open Paint (search for 'paint' in Start menu)
5. Press Ctrl+V to paste the screenshot
6. Click File → Save As → PNG
7. Choose location and filename
8. Click Save button
    """.strip()
    
    config = ExecutionConfig(
        mode=ExecutionMode.DRY_RUN,
        enable_verification=False,
        enable_failsafe=False,
    )
    
    engine = ExecutionEngine(config)
    result = engine.execute_tutorial(tutorial)
    
    print(f"✅ Success: {result.success}")
    print(f"📊 Total Actions: {result.total_actions}")
    print(f"⚙️  Executed: {result.executed_actions}")
    print(f"❌ Failed: {result.failed_actions}")
    print(f"⏱️  Time: {result.execution_time:.2f}s")
    
    assert result.success, "Execution should succeed"
    assert result.total_actions > 0, "Should have actions"
    assert result.mode == ExecutionMode.DRY_RUN, "Should be DRY_RUN mode"
    
    print("✅ Test 1 PASSED\n")
    return True


def test_cli_command():
    """Test 2: CLI command execution"""
    print("="*60)
    print("Test 2: CLI Command Execution")
    print("="*60)
    
    tutorial = "1. Open notepad\\n2. Type hello world\\n3. Press Ctrl+S to save"
    cmd = [
        sys.executable,
        "scripts/rpa_execute.py",
        "--text", tutorial,
        "--mode", "DRY_RUN",
        "--log-level", "WARNING"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"Exit Code: {result.returncode}")
    if result.stdout:
        print(f"STDOUT:\n{result.stdout[:500]}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr[:500]}")
    
    assert result.returncode == 0, f"CLI should succeed, got exit code {result.returncode}"
    assert "EXECUTION RESULT" in result.stdout, "Should have result output"
    
    print("✅ Test 2 PASSED\n")
    return True


def test_json_output():
    """Test 3: JSON output file"""
    print("="*60)
    print("Test 3: JSON Output File")
    print("="*60)
    
    output_file = Path("outputs/test_rpa_result.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    tutorial = "1. Open calculator\\n2. Type 2+2\\n3. Press Enter"
    cmd = [
        sys.executable,
        "scripts/rpa_execute.py",
        "--text", tutorial,
        "--mode", "DRY_RUN",
        "--output", str(output_file),
        "--log-level", "WARNING"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0, "CLI should succeed"
    assert output_file.exists(), "Output file should be created"
    
    # Load and verify JSON
    data = json.loads(output_file.read_text(encoding="utf-8"))
    print(f"📄 JSON Keys: {list(data.keys())}")
    print(f"   Success: {data['success']}")
    print(f"   Total Actions: {data['total_actions']}")
    print(f"   Executed: {data['executed_actions']}")
    
    assert data["success"] == True, "Should be successful"
    assert data["mode"] == "dry_run", "Should be dry_run mode"
    assert data["total_actions"] > 0, "Should have actions"
    
    print("✅ Test 3 PASSED\n")
    return True


def test_error_handling():
    """Test 4: Error handling"""
    print("="*60)
    print("Test 4: Error Handling (Invalid Input)")
    print("="*60)
    
    # Missing input
    cmd = [
        sys.executable,
        "scripts/rpa_execute.py",
        "--mode", "DRY_RUN"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"Exit Code: {result.returncode}")
    assert result.returncode != 0, "Should fail without input"
    
    print("✅ Test 4 PASSED\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "🎯"*30)
    print("E2E Test: YouTube Learner → RPA Execution")
    print("🎯"*30 + "\n")
    
    tests = [
        test_direct_execution,
        test_cli_command,
        test_json_output,
        test_error_handling,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}\n")
            failed += 1
    
    # Summary
    print("="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    print(f"📈 Pass Rate: {passed/len(tests)*100:.0f}%")
    print("="*60 + "\n")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! 🎉\n")
        return 0
    else:
        print(f"⚠️  {failed} TEST(S) FAILED\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
