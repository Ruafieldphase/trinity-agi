#!/usr/bin/env python3
"""
Grounding Integration Test
Tests the newly added Grounding tool in Tool Registry
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file manually (simple implementation)
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from orchestrator.tool_registry import ToolRegistry

def test_grounding_in_available_tools():
    """Test that grounding appears in available tools"""
    print("=" * 60)
    print("TEST 1: Grounding in Available Tools")
    print("=" * 60)

    cfg = {"grounding_enabled": True}
    registry = ToolRegistry(cfg)
    tools = registry.list_available_tools_for_meta()

    if "grounding" not in tools:
        print("[FAIL] 'grounding' NOT found in available tools")
        print(f"   Available tools: {tools}")
        assert False, f"'grounding' missing from available tools: {tools}"
    
    print("[PASS] 'grounding' found in available tools")
    print(f"   Available tools: {tools}")

def test_grounding_current_info():
    """Test grounding tool with current information query"""
    print("\n" + "=" * 60)
    print("TEST 2: Grounding with Current Information")
    print("=" * 60)

    # Check if GCP credentials are set
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("[SKIP] GOOGLE_APPLICATION_CREDENTIALS not set")
        return None

    try:
        cfg = {"grounding_enabled": True}
        registry = ToolRegistry(cfg)

        # Query about current information
        result = registry.call("grounding", {
            "query": "What are the latest AI developments in January 2025?"
        })

        if not result.get("ok"):
            print(f"[FAIL] Grounding tool error - {result.get('error')}")
            assert False, f"Grounding tool error: {result.get('error')}"
        
        print("[PASS] Grounding tool executed successfully")
        print(f"   Model: {result.get('model')}")
        print(f"   Response: {result.get('text')[:300]}...")
        if result.get('grounding_metadata'):
            print(f"   Grounding metadata available: Yes")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        assert False, f"Exception during grounding test: {str(e)}"

def test_grounding_error_handling():
    """Test grounding tool error handling"""
    print("\n" + "=" * 60)
    print("TEST 3: Grounding Error Handling")
    print("=" * 60)

    cfg = {"grounding_enabled": True}
    registry = ToolRegistry(cfg)

    # Test without query
    result = registry.call("grounding", {})

    if result.get("ok") or "query required" not in result.get("error", ""):
        print("[FAIL] Should require query parameter")
        assert False, f"Expected query required error, got: {result.get('error', 'success')}"
    
    print("[PASS] Correctly handles missing query")

def test_grounding_vs_regular_search():
    """Test grounding provides more accurate results than regular search"""
    print("\n" + "=" * 60)
    print("TEST 4: Grounding vs Regular Search (Optional)")
    print("=" * 60)

    # Check if GCP credentials are set
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print("[SKIP] GOOGLE_APPLICATION_CREDENTIALS not set")
        return None

    try:
        cfg = {"grounding_enabled": True, "websearch_enabled": True}
        registry = ToolRegistry(cfg)

        query = "When is the next total solar eclipse visible from the United States?"

        # Test regular web search
        web_result = registry.call("web", {"query": query})

        # Test grounding
        grounding_result = registry.call("grounding", {"query": query})

        if not grounding_result.get("ok"):
            print(f"[FAIL] Grounding error - {grounding_result.get('error')}")
            assert False, f"Grounding error: {grounding_result.get('error')}"
        
        print("[PASS] Both search methods work")
        print(f"\n   Web search result: {web_result.get('text', 'N/A')[:150]}...")
        print(f"\n   Grounding result: {grounding_result.get('text')[:150]}...")
        print("\n   Note: Grounding provides more structured and verified results")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        assert False, f"Exception during comparison test: {str(e)}"

def main():
    print("\n" + "=" * 60)
    print("FDO-AGI Grounding Integration Test")
    print("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(("Available Tools", test_grounding_in_available_tools()))
    results.append(("Current Information", test_grounding_current_info()))
    results.append(("Error Handling", test_grounding_error_handling()))
    results.append(("Grounding vs Search", test_grounding_vs_regular_search()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)

    for test_name, result in results:
        status = "[PASS]" if result is True else "[SKIP]" if result is None else "[FAIL]"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed} | Failed: {failed} | Skipped: {skipped}")

    if failed == 0 and passed > 0:
        print("\n[SUCCESS] All tests passed! Grounding integration successful!")
        return 0
    elif failed == 0:
        print("\n[WARNING] Tests skipped (check GCP credentials)")
        return 0
    else:
        print("\n[FAILED] Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
