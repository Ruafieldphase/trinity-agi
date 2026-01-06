#!/usr/bin/env python3
"""
Simple test script for gemini_chat_simple.py
Tests basic functionality and encoding handling.
"""

import subprocess
import sys
from pathlib import Path
from workspace_root import get_workspace_root

# Ensure UTF-8 output for Windows console
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = get_workspace_root()
GEMINI_SCRIPT = ROOT / "scripts" / "gemini_chat_simple.py"


def test_gemini(prompt: str, description: str) -> bool:
    """Test gemini_chat_simple.py with a given prompt."""
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"{'='*60}")
    print(f"Input prompt: {prompt}")
    print("-" * 60)

    try:
        result = subprocess.run(
            [sys.executable, str(GEMINI_SCRIPT), "--stdin", "--max-tokens", "100"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",  # Replace invalid chars instead of failing
            timeout=30,
        )

        if result.returncode != 0:
            print(f"❌ FAILED (exit code {result.returncode})")
            print(f"stderr: {result.stderr}")
            return False

        output = result.stdout.strip()
        print(f"✓ SUCCESS")
        print(f"Output length: {len(output)} characters")
        print(f"Output preview (first 200 chars):")
        print(output[:200])

        # Check for common encoding issues
        if "�" in output:
            print("⚠ WARNING: Replacement character (�) detected in output")
            return False

        return True

    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT: Request took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Gemini CLI Simple Test Suite")
    print("="*60)
    print(f"Testing script: {GEMINI_SCRIPT}")
    print(f"Python version: {sys.version}")
    print(f"Default encoding: {sys.getdefaultencoding()}")

    tests = [
        ("What is creativity?", "Basic ASCII query"),
        ("한글로 대답해주세요: 창의성이란?", "Korean text query"),
        ("Explain AI in 20 words.", "Short response test"),
    ]

    results = []
    for prompt, description in tests:
        success = test_gemini(prompt, description)
        results.append((description, success))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✓ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
