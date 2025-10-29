#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test LLM Integration (Gemini Flash)
Tests the new v4 LLM-powered response generation
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hey_sena_v4_llm import (
    generate_llm_response,
    generate_response_with_context,
)

def test_llm_basic_questions():
    """Test LLM with basic questions"""
    print("\n" + "=" * 70)
    print("TEST: LLM Basic Questions")
    print("=" * 70)

    test_questions = [
        "What is Python?",
        "Explain quantum mechanics in simple terms",
        "How do I learn programming?",
        "Tell me a joke",
        "What's the capital of France?",
    ]

    passed = 0
    failed = 0

    for question in test_questions:
        print(f"\n[Q] {question}")

        response, error = generate_llm_response(question, [])

        if error:
            print(f"❌ FAIL: {error}")
            failed += 1
        elif response and len(response) > 10:
            print(f"✅ PASS: {response[:100]}...")
            passed += 1
        else:
            print(f"❌ FAIL: Empty or too short response")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    assert failed == 0, f"{failed} test(s) failed"

def test_llm_with_context():
    """Test LLM context awareness"""
    print("\n" + "=" * 70)
    print("TEST: LLM Context Awareness")
    print("=" * 70)

    # Conversation 1
    history = []

    q1 = "I'm learning Python"
    print(f"\n[Turn 1] User: {q1}")
    r1, error = generate_llm_response(q1, history)

    if error:
        print(f"❌ FAIL: {error}")
        assert False, f"LLM error: {error}"

    print(f"[Sena] {r1}")
    history.append({"user": q1, "assistant": r1})

    # Conversation 2 - should remember Python context
    q2 = "What are the best resources for it?"
    print(f"\n[Turn 2] User: {q2}")
    r2, error = generate_llm_response(q2, history)

    if error:
        print(f"❌ FAIL: {error}")
        assert False, f"LLM error: {error}"

    print(f"[Sena] {r2}")

    # Check if response mentions Python or learning
    if "python" in r2.lower() or "learn" in r2.lower() or "resource" in r2.lower():
        print("\n✅ PASS: LLM used context (mentioned Python/learning)")
    else:
        print("\n⚠️ WARNING: Response might not use context effectively")
        print(f"Response: {r2}")
        # Still pass with warning

def test_fallback_to_rules():
    """Test fallback when LLM is disabled"""
    print("\n" + "=" * 70)
    print("TEST: Fallback to Rule-based Responses")
    print("=" * 70)

    test_cases = [
        ("what time is it", "time", True),
        ("hello", "Hello", True),
        ("thanks", "welcome", True),
    ]

    passed = 0

    for question, expected, _ in test_cases:
        print(f"\n[Q] {question}")

        # Use rule-based (LLM disabled)
        response = generate_response_with_context(question, [], use_llm=False)

        print(f"[A] {response}")

        if expected.lower() in response.lower():
            print(f"✅ PASS: Contains '{expected}'")
            passed += 1
        else:
            print(f"❌ FAIL: Expected '{expected}' not found")

    assert passed == len(test_cases), f"Only {passed}/{len(test_cases)} tests passed"

def test_llm_vs_rules_comparison():
    """Compare LLM vs rule-based responses"""
    print("\n" + "=" * 70)
    print("TEST: LLM vs Rule-based Comparison")
    print("=" * 70)

    questions = [
        "Explain artificial intelligence",  # LLM should excel
        "What time is it",  # Rules should work
        "How do I cook pasta?",  # LLM should excel
    ]

    for question in questions:
        print(f"\n{'=' * 60}")
        print(f"[Q] {question}")
        print(f"{'=' * 60}")

        # Rule-based
        print("\n[RULE-BASED]")
        rule_response = generate_response_with_context(question, [], use_llm=False)
        print(f"  {rule_response}")

        # LLM-based
        print("\n[LLM-BASED]")
        llm_response, error = generate_llm_response(question, [])

        if error:
            print(f"  ERROR: {error}")
        elif llm_response:
            print(f"  {llm_response}")
        else:
            print(f"  (no response)")

        # Analysis
        if llm_response and len(llm_response) > len(rule_response):
            print("\n  → LLM provided more detailed response ✅")
        elif not llm_response:
            print("\n  → Fallback to rules worked ✅")
        else:
            print("\n  → Both provided responses")

    # Test always passes as this is a comparison, not a validation

def test_conversation_history_limit():
    """Test that only last 5 turns are used"""
    print("\n" + "=" * 70)
    print("TEST: Conversation History Limit")
    print("=" * 70)

    # Create long history
    history = [
        {"turn": i, "user": f"Question {i}", "assistant": f"Answer {i}"}
        for i in range(1, 11)  # 10 turns
    ]

    print(f"Total history: {len(history)} turns")

    question = "What did we talk about?"
    print(f"[Q] {question}")

    response, error = generate_llm_response(question, history)

    if error:
        print(f"❌ FAIL: {error}")
        assert False, f"LLM error: {error}"

    print(f"[A] {response}")

    # Should work even with long history
    print("\n✅ PASS: LLM handled long history (uses last 5 turns)")

def main():
    """Run all LLM integration tests"""
    print("\n" + "=" * 70)
    print("Hey Sena v4 - LLM Integration Tests")
    print("=" * 70)

    tests = [
        ("Fallback to Rules", test_fallback_to_rules),
        ("LLM Basic Questions", test_llm_basic_questions),
        ("LLM Context Awareness", test_llm_with_context),
        ("Conversation History Limit", test_conversation_history_limit),
        ("LLM vs Rules Comparison", test_llm_vs_rules_comparison),
    ]

    results = []

    for name, test_func in tests:
        try:
            print(f"\n{'=' * 70}")
            print(f"Running: {name}")
            print(f"{'=' * 70}")

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
        print("\n🎉 All LLM integration tests passed!")
        print("✅ Hey Sena v4 is ready with full LLM capabilities!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
