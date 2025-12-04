#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversation Flow Simulation Test
Simulates a full multi-turn conversation without actual audio
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hey_sena_v3_multiturn import (
    detect_wake_word,
    detect_end_conversation,
    generate_response_with_context,
)

def simulate_conversation(turns):
    """
    Simulate a multi-turn conversation

    Args:
        turns: List of (user_input, expected_behavior) tuples

    Returns:
        bool: True if simulation successful
    """
    print("\n" + "=" * 70)
    print("SIMULATING MULTI-TURN CONVERSATION")
    print("=" * 70)

    conversation_history = []

    for turn_num, (user_input, expected) in enumerate(turns, 1):
        print(f"\n--- Turn {turn_num} ---")
        print(f"[YOU] {user_input}")

        # Check for end conversation
        if detect_end_conversation(user_input):
            print(f"[SYSTEM] End conversation detected!")
            print(f"[EXPECTED] {expected}")
            assert expected == "END", f"Turn {turn_num} should end conversation"
            print("✅ Correct behavior")
            break

        # Generate response
        response = generate_response_with_context(user_input, conversation_history)
        print(f"[SENA] {response}")

        # Verify expected behavior
        if expected:
            if expected in response or expected.lower() in response.lower():
                print(f"✅ Contains expected: '{expected}'")
            else:
                print(f"⚠️ Expected '{expected}' but got: {response}")

        # Add to history
        conversation_history.append({
            "turn": turn_num,
            "user": user_input,
            "assistant": response
        })

    print(f"\n✅ Conversation completed with {len(conversation_history)} turns")

def test_scenario_1_simple():
    """Simple conversation scenario"""
    print("\n" + "=" * 70)
    print("SCENARIO 1: Simple Multi-turn Conversation")
    print("=" * 70)

    turns = [
        ("hello", "Hello"),
        ("what time is it", "time"),
        ("thanks", "welcome"),
        ("bye", "END"),
    ]

    simulate_conversation(turns)

def test_scenario_2_context():
    """Context-aware conversation"""
    print("\n" + "=" * 70)
    print("SCENARIO 2: Context-Aware Conversation")
    print("=" * 70)

    turns = [
        ("weather", "city"),
        ("Seoul", "Seoul"),  # Should recognize city from previous question
        ("thanks", "welcome"),
        ("그만", "END"),
    ]

    simulate_conversation(turns)

def test_scenario_3_long():
    """Long conversation with multiple topics"""
    print("\n" + "=" * 70)
    print("SCENARIO 3: Long Multi-topic Conversation")
    print("=" * 70)

    turns = [
        ("hello", "Hello"),
        ("what's your name", "Sena"),
        ("how are you", "great"),
        ("what time is it", "time"),
        ("what's today's date", "day"),
        ("thanks for your help", "welcome"),
        ("goodbye", "END"),
    ]

    simulate_conversation(turns)

def test_scenario_4_mixed_languages():
    """Mixed Korean and English"""
    print("\n" + "=" * 70)
    print("SCENARIO 4: Mixed Language Conversation")
    print("=" * 70)

    turns = [
        ("안녕", None),  # Korean greeting
        ("what time is it", "time"),
        ("고마워", "welcome"),
        ("종료", "END"),  # Korean exit
    ]

    simulate_conversation(turns)

def test_wake_word_in_conversation():
    """Test wake word handling during conversation"""
    print("\n" + "=" * 70)
    print("TEST: Wake Word Handling in Conversation")
    print("=" * 70)

    test_cases = [
        ("hey sena what time is it", True, "time"),
        ("세나야 안녕", True, None),
        ("what time is it", False, "time"),  # No wake word
    ]

    for text, has_wake_word, expected_in_response in test_cases:
        print(f"\n[INPUT] {text}")

        # Check wake word detection
        wake_detected = detect_wake_word(text)
        print(f"[WAKE WORD] Detected: {wake_detected} | Expected: {has_wake_word}")

        if wake_detected != has_wake_word:
            print(f"❌ FAIL: Wake word detection mismatch")
            assert False, f"Wake word detection mismatch for: {text}"

        # Generate response
        response = generate_response_with_context(text, [])
        print(f"[RESPONSE] {response}")

        # Check that wake word is removed from processing
        if expected_in_response:
            if expected_in_response.lower() in response.lower():
                print(f"✅ PASS: Response contains '{expected_in_response}'")
            else:
                print(f"❌ FAIL: Expected '{expected_in_response}' in response")
                assert False, f"Response missing expected content: {expected_in_response}"
        else:
            print("✅ PASS: Response generated")

def test_conversation_state_transitions():
    """Test state transitions in conversation"""
    print("\n" + "=" * 70)
    print("TEST: Conversation State Transitions")
    print("=" * 70)

    states = []

    # State 1: Listen Mode -> Conversation Mode
    wake_input = "hey sena"
    if detect_wake_word(wake_input):
        states.append("WAKE_DETECTED")
        print(f"✅ State 1: Listen Mode -> Conversation Mode")

    # State 2: Conversation Mode -> Active
    user_question = "what time is it"
    if not detect_end_conversation(user_question):
        states.append("ACTIVE")
        print(f"✅ State 2: Conversation Mode Active")

    # State 3: Conversation Mode -> End
    end_command = "goodbye"
    if detect_end_conversation(end_command):
        states.append("END_DETECTED")
        print(f"✅ State 3: Conversation Mode -> Listen Mode")

    expected_states = ["WAKE_DETECTED", "ACTIVE", "END_DETECTED"]

    if states == expected_states:
        print(f"\n✅ All state transitions correct!")
    else:
        print(f"\n❌ State mismatch: {states} != {expected_states}")
        assert False, f"State transitions incorrect: {states} != {expected_states}"

def main():
    """Run all conversation flow tests"""
    print("\n" + "=" * 70)
    print("Hey Sena v3 - Conversation Flow Simulation Tests")
    print("=" * 70)

    tests = [
        ("Simple Conversation", test_scenario_1_simple),
        ("Context-Aware Conversation", test_scenario_2_context),
        ("Long Conversation", test_scenario_3_long),
        ("Mixed Language", test_scenario_4_mixed_languages),
        ("Wake Word Handling", test_wake_word_in_conversation),
        ("State Transitions", test_conversation_state_transitions),
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
    print("SIMULATION TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {name}")

    print(f"\nTotal: {passed}/{total} simulations passed")

    if passed == total:
        print("\n🎉 All conversation flow simulations passed!")
        print("✅ Multi-turn conversation logic is working correctly!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} simulation(s) failed. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
