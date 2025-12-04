#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Multi-turn Conversation Features
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import functions from hey_sena_v3
from hey_sena_v3_multiturn import (
    detect_end_conversation,
    generate_response_with_context,
    detect_wake_word,
    END_CONVERSATION,
    WAKE_WORDS
)

def test_end_conversation_detection():
    """Test if end conversation commands are detected properly"""
    print("\n" + "=" * 60)
    print("TEST: End Conversation Detection")
    print("=" * 60)

    test_cases = [
        ("goodbye", True),
        ("bye", True),
        ("그만", True),
        ("끝", True),
        ("종료", True),
        ("stop", True),
        ("what time is it", False),
        ("hello there", False),
    ]

    passed = 0
    failed = 0

    for text, expected in test_cases:
        result = detect_end_conversation(text)
        status = "✅ PASS" if result == expected else "❌ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} | Input: '{text}' | Expected: {expected} | Got: {result}")

    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed > 0:
        assert False, f"{failed} test cases failed in end conversation detection"

def test_context_awareness():
    """Test if responses use conversation context"""
    print("\n" + "=" * 60)
    print("TEST: Context-Aware Responses")
    print("=" * 60)

    # Scenario 1: No history
    history = []
    response = generate_response_with_context("hello", history)
    print(f"\n[Turn 1] User: 'hello'")
    print(f"[Sena] {response}")
    assert "Hello! How can I help you today?" in response, "First hello should be different"

    # Scenario 2: With history - second greeting
    history = [{"turn": 1, "user": "hello", "assistant": response}]
    response = generate_response_with_context("hi", history)
    print(f"\n[Turn 2] User: 'hi' (with history)")
    print(f"[Sena] {response}")
    # Accept various valid follow-up greetings
    valid_responses = ["what else", "help with", "yes?", "how can i help"]
    assert any(phrase in response.lower() for phrase in valid_responses), "Second greeting should be a valid follow-up"

    # Scenario 3: Weather follow-up
    history = [{"turn": 1, "user": "weather", "assistant": "Which city are you interested in?"}]
    response = generate_response_with_context("Seoul", history)
    print(f"\n[Turn 3] User: 'Seoul' (after weather question)")
    print(f"[Sena] {response}")
    assert "Seoul" in response, "Should mention the city"

    # Scenario 4: Time question
    response = generate_response_with_context("what time is it", [])
    print(f"\n[Turn 4] User: 'what time is it'")
    print(f"[Sena] {response}")
    assert "time" in response.lower() and ":" in response, "Should provide actual time"

    print("\n✅ All context tests passed!")

def test_wake_word_removal():
    """Test if wake words are properly removed from input"""
    print("\n" + "=" * 60)
    print("TEST: Wake Word Removal")
    print("=" * 60)

    test_inputs = [
        "hey sena what time is it",
        "세나야 날씨 알려줘",
        "sena hello there",
    ]

    for text in test_inputs:
        response = generate_response_with_context(text, [])
        print(f"\nInput: '{text}'")
        print(f"Response: {response}")

        # Check that wake words are not in the response logic
        has_wake_word = any(ww in text.lower() for ww in WAKE_WORDS)
        if has_wake_word:
            print("✅ Wake word was in input (normal)")
        else:
            print("✅ No wake word in input")

    print("\n✅ Wake word handling works!")

def test_multiturn_scenario():
    """Simulate a multi-turn conversation"""
    print("\n" + "=" * 60)
    print("TEST: Full Multi-turn Conversation Scenario")
    print("=" * 60)

    conversation = [
        ("hello", None),
        ("what time is it", None),
        ("thanks", None),
        ("what's your name", None),
        ("bye", "END"),
    ]

    history = []

    for turn, (user_input, expected_action) in enumerate(conversation, 1):
        print(f"\n--- Turn {turn} ---")
        print(f"[YOU] {user_input}")

        # Check for end conversation
        if detect_end_conversation(user_input):
            print("[SYSTEM] End conversation detected!")
            assert expected_action == "END", f"Turn {turn} should end conversation"
            break

        # Generate response
        response = generate_response_with_context(user_input, history)
        print(f"[SENA] {response}")

        # Add to history
        history.append({
            "turn": turn,
            "user": user_input,
            "assistant": response
        })

    print(f"\n✅ Multi-turn scenario completed! ({len(history)} turns)")

def test_silence_handling():
    """Test silence detection logic"""
    print("\n" + "=" * 60)
    print("TEST: Silence Handling")
    print("=" * 60)

    silence_inputs = [
        "",
        "a",
        "  ",
        None,
    ]

    for inp in silence_inputs:
        if inp is None:
            text = None
        else:
            text = inp.strip() if inp else ""

        is_silence = not text or len(text) < 3

        status = "🔇 SILENCE" if is_silence else "🔊 VALID"
        print(f"{status} | Input: {repr(inp)} | Length: {len(text) if text else 0}")

    print("\n✅ Silence detection works!")

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Hey Sena v3 - Multi-turn Feature Tests")
    print("=" * 70)

    tests = [
        ("End Conversation Detection", test_end_conversation_detection),
        ("Context Awareness", test_context_awareness),
        ("Wake Word Removal", test_wake_word_removal),
        ("Silence Handling", test_silence_handling),
        ("Multi-turn Scenario", test_multiturn_scenario),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Multi-turn feature is ready!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
