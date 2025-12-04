#!/usr/bin/env python3
"""
TTS (Text-to-Speech) Integration Test
Tests the newly added TTS tool for voice generation
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from orchestrator.tool_registry import ToolRegistry

def test_tts_in_available_tools():
    """Test that TTS appears in available tools"""
    print("=" * 60)
    print("TEST 1: TTS in Available Tools")
    print("=" * 60)

    cfg = {"tts_enabled": True}
    registry = ToolRegistry(cfg)
    tools = registry.list_available_tools_for_meta()

    if "tts" not in tools:
        print("[FAIL] 'tts' NOT found in available tools")
        print(f"   Available tools: {tools}")
        assert False, f"'tts' missing from available tools: {tools}"
    
    print("[PASS] 'tts' found in available tools")
    print(f"   Available tools: {tools}")

def test_tts_error_handling():
    """Test TTS tool error handling"""
    print("\n" + "=" * 60)
    print("TEST 2: TTS Error Handling")
    print("=" * 60)

    cfg = {"tts_enabled": True}
    registry = ToolRegistry(cfg)

    # Test without text
    result = registry.call("tts", {})

    if result.get("ok") or "text required" not in result.get("error", ""):
        print("[FAIL] Should require text parameter")
        assert False, f"Expected text required error, got: {result.get('error', 'success')}"
    
    print("[PASS] Correctly handles missing text")

def test_tts_generation():
    """Test TTS with actual text generation"""
    print("\n" + "=" * 60)
    print("TEST 3: TTS Audio Generation")
    print("=" * 60)

    try:
        cfg = {"tts_enabled": True}
        registry = ToolRegistry(cfg)

        output_file = "test_tts_output.wav"

        result = registry.call("tts", {
            "text": "Hello, this is a test of the Text to Speech system.",
            "output_path": output_file,
            "voice": "Kore"
        })

        if not result.get("ok"):
            print(f"[FAIL] TTS error - {result.get('error')}")
            assert False, f"TTS error: {result.get('error')}"

        print("[PASS] TTS audio generated successfully")
        print(f"   Model: {result.get('model')}")
        print(f"   Voice: {result.get('voice')}")
        print(f"   Output: {result.get('output_path')}")

        # Check if file exists
        if not os.path.exists(output_file):
            print(f"   [FAIL] Audio file not found")
            assert False, f"Audio file not created: {output_file}"

        file_size = os.path.getsize(output_file)
        print(f"   File size: {file_size} bytes")

        # Cleanup
        os.remove(output_file)
        print(f"   [OK] Audio file created and cleaned up")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        assert False, f"Exception during TTS test: {str(e)}"

def test_tts_different_voices():
    """Test TTS with different voices (optional)"""
    print("\n" + "=" * 60)
    print("TEST 4: TTS Multiple Voices (Optional)")
    print("=" * 60)

    try:
        cfg = {"tts_enabled": True}
        registry = ToolRegistry(cfg)

        voices = ["Kore", "Puck"]
        results = []

        for voice in voices:
            output_file = f"test_tts_{voice}.wav"

            result = registry.call("tts", {
                "text": f"This is {voice} speaking.",
                "output_path": output_file,
                "voice": voice
            })

            if result.get("ok"):
                results.append((voice, True))
                print(f"   [OK] {voice} voice generated")

                # Cleanup
                if os.path.exists(output_file):
                    os.remove(output_file)
            else:
                results.append((voice, False))
                print(f"   [FAIL] {voice} voice failed - {result.get('error')}")

        success_count = sum(1 for _, success in results if success)

        if success_count == 0:
            print("[FAIL] No voices working")
            assert False, f"No voices working: {results}"
        
        if success_count == len(voices):
            print(f"[PASS] All {len(voices)} voices working")
        else:
            print(f"[PARTIAL] {success_count}/{len(voices)} voices working")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        assert False, f"Exception during voice test: {str(e)}"

def test_conversational_system():
    """Test complete conversational system (STT + TTS)"""
    print("\n" + "=" * 60)
    print("TEST 5: Complete Conversational System")
    print("=" * 60)

    cfg = {"audio_enabled": True, "tts_enabled": True}
    registry = ToolRegistry(cfg)
    tools = registry.list_available_tools_for_meta()

    has_audio_input = "audio" in tools  # Speech-to-Text
    has_audio_output = "tts" in tools   # Text-to-Speech

    if not (has_audio_input and has_audio_output):
        print("[FAIL] Incomplete conversational system")
        if not has_audio_input:
            print("   [MISSING] Audio Input (Speech-to-Text)")
        if not has_audio_output:
            print("   [MISSING] Audio Output (Text-to-Speech)")
        assert False, f"Missing components - STT: {has_audio_input}, TTS: {has_audio_output}"
    
    print("[PASS] Complete conversational system available")
    print("   [OK] Audio Input (Speech-to-Text)")
    print("   [OK] Audio Output (Text-to-Speech)")
    print("\n   System can now:")
    print("     - Listen to user speech (STT)")
    print("     - Generate voice responses (TTS)")
    print("     - Enable full voice conversations!")

def main():
    print("\n" + "=" * 60)
    print("FDO-AGI TTS Integration Test")
    print("Text-to-Speech with Voice Generation")
    print("=" * 60 + "\n")

    results = []

    # Run tests
    results.append(("TTS Available", test_tts_in_available_tools()))
    results.append(("Error Handling", test_tts_error_handling()))
    results.append(("Audio Generation", test_tts_generation()))
    results.append(("Multiple Voices", test_tts_different_voices()))
    results.append(("Conversational System", test_conversational_system()))

    # Summary
    print("\n" + "=" * 60)
    print("TTS TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)

    for test_name, result in results:
        status = "[PASS]" if result is True else "[FAIL]"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed} | Failed: {failed}")

    if failed == 0:
        print("\n" + "=" * 60)
        print("SUCCESS: TTS INTEGRATION COMPLETE!")
        print("=" * 60)
        print("\nAGI can now:")
        print("  [+] LISTEN: Speech-to-Text (Audio input)")
        print("  [+] SPEAK: Text-to-Speech (Audio output)")
        print("  [+] SEE: Vision (Image analysis)")
        print("  [+] WATCH: Video (Video understanding)")
        print("  [+] LEARN: Grounding (Real-time info)")
        print("\nComplete Multimodal + Conversational AGI!")
        print("=" * 60)
        return 0
    else:
        print("\n[FAILED] Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
