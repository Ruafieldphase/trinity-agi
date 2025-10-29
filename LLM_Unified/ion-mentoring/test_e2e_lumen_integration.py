#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 2 Day 2 - E2E Integration Test
Lumen Gateway + Ion Mentoring API 통합 테스트
"""

import json
import time
from datetime import datetime

import requests

# Test configuration
LUMEN_GATEWAY_URL = "http://localhost:5000"
ION_API_URL = "http://localhost:8000"  # FastAPI default port


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
        print(f"✅ Timestamp: {data.get('timestamp')}")

        personas = data.get("persona_network", {})
        print(f"\n✅ Persona Network ({len(personas)} personas):")
        for key, persona in personas.items():
            print(f"   {persona['emoji']} {persona['name']} ({key}): {persona['specialty']}")

        return True
    except Exception as e:
        print(f"❌ Lumen Gateway 연결 실패: {e}")
        return False


def test_lumen_chat_direct():
    """Test 2: Lumen Gateway 직접 채팅 테스트"""
    print_section("Test 2: Lumen Gateway Direct Chat")

    test_cases = [
        {
            "message": "창의적인 아이디어를 제안해줘",
            "expected_persona": "moon",  # 루아 (감응형)
            "description": "창의 키워드 → 루아(Moon) 선택 확인",
        },
        {
            "message": "이 프로젝트를 단계별로 정리해줘",
            "expected_persona": "square",  # 엘로 (구조형)
            "description": "구조 키워드 → 엘로(Square) 선택 확인",
        },
        {
            "message": "전체적인 패턴을 관찰해줘",
            "expected_persona": "earth",  # 누리 (관찰형)
            "description": "메타 키워드 → 누리(Earth) 선택 확인",
        },
        {
            "message": "안녕하세요",
            "expected_persona": "pen",  # 세나 (브리지형, 기본값)
            "description": "일반 메시지 → 세나(Pen) 기본값 확인",
        },
    ]

    success_count = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test Case {i}] {test['description']}")
        print(f"   Message: '{test['message']}'")

        try:
            response = requests.post(
                f"{LUMEN_GATEWAY_URL}/chat", json={"message": test["message"]}, timeout=30
            )

            data = response.json()

            if data.get("success"):
                persona = data.get("persona", {})
                persona_key = None

                # Detect which persona was selected
                persona_name = persona.get("name")
                persona_mapping = {"루아": "moon", "엘로": "square", "누리": "earth", "세나": "pen"}
                persona_key = persona_mapping.get(persona_name)

                print(f"   ✅ Success: {data.get('success')}")
                print(
                    f"   ✅ Persona: {persona.get('emoji')} {persona.get('name')} ({persona.get('type')})"
                )
                print(f"   ✅ Sources: {', '.join(data.get('sources', []))}")
                print(f"   ✅ Response Preview: {data.get('response', '')[:100]}...")

                if persona_key == test["expected_persona"]:
                    print(f"   ✅ Persona Selection: CORRECT (expected {test['expected_persona']})")
                    success_count += 1
                else:
                    print(
                        f"   ⚠️ Persona Selection: Got {persona_key}, expected {test['expected_persona']}"
                    )
            else:
                print(f"   ❌ Failed: {data.get('error')}")

        except Exception as e:
            print(f"   ❌ Request failed: {e}")

        time.sleep(1)  # Rate limiting

    print(
        f"\n✅ Persona Detection Success Rate: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.0f}%)"
    )
    return success_count == len(test_cases)


def test_ion_api_with_lumen_disabled():
    """Test 3: Ion API with LUMEN_ENABLED=false (Legacy Mode)"""
    print_section("Test 3: Ion Mentoring API (Legacy Mode)")

    print("⚠️ 이 테스트는 Ion Mentoring API가 실행 중이어야 합니다.")
    print(f"   Expected: uvicorn app.main:app --reload (at {ION_API_URL})")
    print("   Environment: LUMEN_ENABLED=false (default)")

    try:
        response = requests.post(
            f"{ION_API_URL}/api/v2/recommend/personalized",
            json={"user_id": "test-user-123", "query": "창의적인 AI 프로젝트 아이디어를 추천해줘"},
            timeout=10,
        )

        data = response.json()

        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response: {json.dumps(data, indent=2, ensure_ascii=False)[:300]}...")

        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print(f"❌ Ion Mentoring API가 실행되지 않았습니다 ({ION_API_URL})")
        print(
            "   실행 방법: cd d:\\nas_backup\\LLM_Unified\\ion-mentoring && uvicorn app.main:app --reload"
        )
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def test_ion_api_with_lumen_enabled():
    """Test 4: Ion API with LUMEN_ENABLED=true (Lumen Integration)"""
    print_section("Test 4: Ion Mentoring API (Lumen Integration Mode)")

    print("⚠️ 이 테스트는 Ion Mentoring API가 LUMEN_ENABLED=true로 실행되어야 합니다.")
    print("   Expected: set LUMEN_ENABLED=true && uvicorn app.main:app --reload")

    try:
        response = requests.post(
            f"{ION_API_URL}/api/v2/recommend/personalized",
            json={"user_id": "test-user-456", "query": "프로젝트를 체계적으로 구조화해줘"},
            timeout=30,
        )

        data = response.json()

        print(f"✅ Status Code: {response.status_code}")

        # Check if Lumen Gateway was used
        if "lumen" in str(data).lower() or "엘로" in str(data) or "루아" in str(data):
            print("✅ Lumen Integration: ACTIVE (detected Lumen response)")
        else:
            print("⚠️ Lumen Integration: Possibly using Legacy system")

        print(f"✅ Response Preview: {json.dumps(data, indent=2, ensure_ascii=False)[:300]}...")

        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Ion Mentoring API가 실행되지 않았습니다")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 70)
    print("  🧪 Week 2 Day 2 - E2E Integration Test")
    print("  Lumen Gateway + Ion Mentoring API")
    print("=" * 70)

    results = {"timestamp": datetime.now().isoformat(), "tests": []}

    # Test 1: Lumen Gateway Health
    test1_result = test_lumen_gateway_health()
    results["tests"].append({"test": "Lumen Gateway Health", "passed": test1_result})

    # Test 2: Lumen Direct Chat
    test2_result = test_lumen_chat_direct()
    results["tests"].append({"test": "Lumen Direct Chat", "passed": test2_result})

    # Test 3: Ion API Legacy Mode
    test3_result = test_ion_api_with_lumen_disabled()
    results["tests"].append({"test": "Ion API Legacy Mode", "passed": test3_result})

    # Test 4: Ion API Lumen Integration
    test4_result = test_ion_api_with_lumen_enabled()
    results["tests"].append({"test": "Ion API Lumen Integration", "passed": test4_result})

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
    output_file = "outputs/e2e_test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Results saved to: {output_file}")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
