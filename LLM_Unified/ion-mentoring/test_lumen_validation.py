#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 2 Day 2 - Simplified E2E Test (Mock Mode)
Lumen Gateway 기능 검증 (Ion API 없이)
"""

import json
from datetime import datetime

import requests

# Test configuration
LUMEN_GATEWAY_URL = "http://localhost:5000"


def print_section(title):
    """섹션 구분선 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_lumen_gateway_health():
    """Test 1: Lumen Gateway 헬스 체크"""
    print_section("Test 1: Lumen Gateway Health Check")

    try:
        response = requests.get(f"{LUMEN_GATEWAY_URL}/", timeout=5)
        data = response.json()

        print(f"✅ Status: {data.get('status')}")
        print(f"✅ Port: {data.get('port')}")
        print(f"✅ Model: {data.get('model')}")
        print(f"✅ Google AI Studio: {data.get('google_ai_studio')}")

        personas = data.get("persona_network", {})
        print(f"\n✅ Persona Network ({len(personas)} personas):")
        for key, persona in personas.items():
            print(f"   {persona['emoji']} {persona['name']} ({key}): {persona['specialty']}")

        return True
    except Exception as e:
        print(f"❌ Lumen Gateway 연결 실패: {e}")
        return False


def test_persona_detection():
    """Test 2: 페르소나 자동 선택 검증"""
    print_section("Test 2: Persona Auto-Detection")

    test_cases = [
        {
            "message": "창의적이고 혁신적인 아이디어를 제안해줘",
            "expected_persona": "moon",
            "expected_name": "루아",
            "keywords": "창의, 아이디어",
        },
        {
            "message": "이 프로젝트를 체계적으로 단계별로 정리해줘",
            "expected_persona": "square",
            "expected_name": "엘로",
            "keywords": "체계, 단계",
        },
        {
            "message": "전체적인 패턴을 관찰하고 메타 분석해줘",
            "expected_persona": "earth",
            "expected_name": "누리",
            "keywords": "패턴, 메타",
        },
        {
            "message": "안녕하세요, 도움이 필요해요",
            "expected_persona": "pen",
            "expected_name": "세나",
            "keywords": "일반 메시지",
        },
    ]

    success_count = 0

    for i, test in enumerate(test_cases, 1):
        print(
            f"\n[Test {i}] {test['keywords']} → {test['expected_name']} ({test['expected_persona']})"
        )
        print(f"   Query: '{test['message']}'")

        try:
            response = requests.post(
                f"{LUMEN_GATEWAY_URL}/chat", json={"message": test["message"]}, timeout=10
            )

            data = response.json()

            if data.get("success"):
                persona = data.get("persona", {})
                persona_name = persona.get("name")

                print("   ✅ Response Success: True")
                print(
                    f"   ✅ Selected Persona: {persona.get('emoji')} {persona_name} ({persona.get('type')})"
                )
                print(f"   ✅ Sources: {', '.join(data.get('sources', []))}")

                # Check if correct persona was selected
                if persona_name == test["expected_name"]:
                    print("   ✅ Persona Detection: CORRECT ✓")
                    success_count += 1
                else:
                    print(
                        f"   ⚠️ Persona Detection: Got {persona_name}, expected {test['expected_name']}"
                    )

                # Print response preview
                response_text = data.get("response", "")
                if len(response_text) > 100:
                    print(f"   📝 Response Preview: {response_text[:100]}...")
                else:
                    print(f"   📝 Response: {response_text}")
            else:
                print(f"   ❌ Request Failed: {data.get('error')}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

    print(f"\n{'='*70}")
    print(
        f"✅ Persona Detection Accuracy: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.0f}%)"
    )
    print(f"{'='*70}")

    return success_count == len(test_cases)


def test_lumen_status():
    """Test 3: Lumen Gateway 상태 확인"""
    print_section("Test 3: Lumen Gateway Status Check")

    try:
        response = requests.get(f"{LUMEN_GATEWAY_URL}/status", timeout=5)
        data = response.json()

        print(f"✅ System: {data.get('system')}")
        print(f"✅ Google AI Studio: {data.get('google_ai_studio')}")
        print(f"✅ Model: {data.get('model')}")
        print(f"✅ Ready: {data.get('ready')}")
        print(f"✅ Hybrid Sources: {', '.join(data.get('hybrid_sources', []))}")

        return data.get("ready", False)
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False


def test_personas_endpoint():
    """Test 4: Personas 엔드포인트 확인"""
    print_section("Test 4: Personas Endpoint")

    try:
        response = requests.get(f"{LUMEN_GATEWAY_URL}/personas", timeout=5)
        data = response.json()

        available = data.get("available_personas", {})
        print(f"✅ Available Personas: {len(available)}")

        for key, persona in available.items():
            print(f"   {persona['emoji']} {persona['name']} - {persona['specialty']}")

        print(f"\n✅ Default Persona: {data.get('current_default')}")
        print(f"✅ Auto Detection: {data.get('auto_detection')}")

        return True
    except Exception as e:
        print(f"❌ Personas endpoint failed: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 70)
    print("  🧪 Week 2 Day 2 - Lumen Gateway Validation Test")
    print("  Simplified E2E Test (Mock Mode)")
    print("=" * 70)

    results = {"timestamp": datetime.now().isoformat(), "mode": "mock", "tests": []}

    # Test 1: Health Check
    test1_result = test_lumen_gateway_health()
    results["tests"].append({"test": "Lumen Gateway Health", "passed": test1_result})

    # Test 2: Persona Detection
    test2_result = test_persona_detection()
    results["tests"].append({"test": "Persona Auto-Detection", "passed": test2_result})

    # Test 3: Status Check
    test3_result = test_lumen_status()
    results["tests"].append({"test": "Lumen Gateway Status", "passed": test3_result})

    # Test 4: Personas Endpoint
    test4_result = test_personas_endpoint()
    results["tests"].append({"test": "Personas Endpoint", "passed": test4_result})

    # Summary
    print_section("📊 Test Summary")

    passed = sum(1 for t in results["tests"] if t["passed"])
    total = len(results["tests"])

    for i, test in enumerate(results["tests"], 1):
        status = "✅ PASSED" if test["passed"] else "❌ FAILED"
        print(f"Test {i}: {test['test']} - {status}")

    print(f"\n{'='*70}")
    print(f"  Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*70}\n")

    # Save results
    output_file = "outputs/lumen_gateway_validation.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✅ Results saved to: {output_file}")
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
