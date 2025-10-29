#!/usr/bin/env python3
"""
Vision Integration Test
Tests the newly added Vision tool in Tool Registry
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

def test_vision_in_available_tools():
    """Test that vision appears in available tools"""
    print("=" * 60)
    print("TEST 1: Vision in Available Tools")
    print("=" * 60)

    cfg = {"vision_enabled": True}
    registry = ToolRegistry(cfg)
    tools = registry.list_available_tools_for_meta()

    if "vision" not in tools:
        print("[FAIL] 'vision' NOT found in available tools")
        print(f"   Available tools: {tools}")
        assert False, f"'vision' missing from available tools: {tools}"
    
    print("[PASS] 'vision' found in available tools")
    print(f"   Available tools: {tools}")

def test_vision_with_test_image():
    """Test vision tool with a test image"""
    print("\n" + "=" * 60)
    print("TEST 2: Vision Tool Execution")
    print("=" * 60)

    # Check if GEMINI_API_KEY is set
    if not os.environ.get("GEMINI_API_KEY"):
        print("[SKIP] GEMINI_API_KEY not set in environment")
        return None

    # Create a simple test image
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Create test image
        test_img_path = "test_vision_image.png"
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)

        # Draw some shapes
        draw.rectangle([50, 50, 150, 150], fill='red', outline='black', width=3)
        draw.ellipse([200, 50, 300, 150], fill='blue', outline='black', width=3)
        draw.text((150, 200), "AGI Vision Test", fill='black')

        img.save(test_img_path)
        print(f"[OK] Created test image: {test_img_path}")

        # Test vision tool
        cfg = {"vision_enabled": True}
        registry = ToolRegistry(cfg)

        result = registry.call("vision", {
            "image_path": test_img_path,
            "prompt": "Describe what you see in this image. What shapes and colors are present?"
        })

        if not result.get("ok"):
            print(f"[FAIL] Vision tool error - {result.get('error')}")
            assert False, f"Vision tool error: {result.get('error')}"

        print("[PASS] Vision tool executed successfully")
        print(f"   Model: {result.get('model')}")
        print(f"   Response: {result.get('text')[:200]}...")

        # Cleanup
        if os.path.exists(test_img_path):
            os.remove(test_img_path)

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        assert False, f"Exception during vision test: {str(e)}"

def test_vision_without_image():
    """Test vision tool error handling"""
    print("\n" + "=" * 60)
    print("TEST 3: Vision Error Handling")
    print("=" * 60)

    cfg = {"vision_enabled": True}
    registry = ToolRegistry(cfg)

    # Test without image_path
    result = registry.call("vision", {"prompt": "Test"})

    if result.get("ok") or "image_path required" not in result.get("error", ""):
        print("[FAIL] Should require image_path")
        assert False, f"Expected image_path required error, got: {result.get('error', 'success')}"
    
    print("[PASS] Correctly handles missing image_path")

def main():
    print("\n" + "=" * 60)
    print("FDO-AGI Vision Integration Test")
    print("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(("Available Tools", test_vision_in_available_tools()))
    results.append(("Vision Execution", test_vision_with_test_image()))
    results.append(("Error Handling", test_vision_without_image()))

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
        print("\n[SUCCESS] All tests passed! Vision integration successful!")
        return 0
    elif failed == 0:
        print("\n[WARNING] Tests skipped (check GEMINI_API_KEY)")
        return 0
    else:
        print("\n[FAILED] Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
