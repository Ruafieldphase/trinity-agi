#!/usr/bin/env python3
"""
LLM 기반 요약 vs 규칙 기반 요약 비교 테스트
"""

import sys
import time
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent))

from persona_system.utils.summary_llm import summarize_with_llm
from persona_system.utils.summary_utils import update_running_summary


# 테스트 대화 샘플
SAMPLE_CONVERSATION = [
    {
        "role": "user",
        "content": "Vertex AI로 마이그레이션하는 프로젝트를 시작하려고 하는데 어떻게 시작해야 할까요?",
    },
    {
        "role": "assistant",
        "content": "Vertex AI 마이그레이션을 시작하시려면 먼저 현재 시스템 아키텍처를 분석하고, Vertex AI SDK를 설치한 후, 기본 연결 테스트부터 시작하는 것을 권장합니다.",
    },
    {
        "role": "user",
        "content": "SDK 설치는 어떻게 하나요?",
    },
    {
        "role": "assistant",
        "content": "pip install google-cloud-aiplatform 명령어로 설치할 수 있습니다. Python 3.11 이상 버전이 필요합니다.",
    },
    {
        "role": "user",
        "content": "설치 후 첫 번째 테스트 코드는 어떻게 작성하면 되나요?",
    },
    {
        "role": "assistant",
        "content": "Vertex AI 클라이언트를 초기화하고 간단한 텍스트 생성 요청을 보내보세요. 프로젝트 ID와 리전 설정이 필요합니다.",
    },
]


def test_rule_based_summary():
    """규칙 기반 요약 테스트"""
    print("=" * 60)
    print("Test 1: Rule-Based Summary")
    print("=" * 60)

    start = time.time()
    summary = update_running_summary(
        running_summary=None,
        new_messages=SAMPLE_CONVERSATION,
        max_bullets=6,
        max_chars=600,
        per_line_max=120,
    )
    elapsed = (time.time() - start) * 1000

    print("\n[Result]:")
    print(summary)
    print(f"\n[Time]: {elapsed:.2f}ms")
    print(f"[Length]: {len(summary)} chars")
    print(f"[Bullets]: {summary.count('- ')}")

    return {
        "summary": summary,
        "time_ms": elapsed,
        "length": len(summary),
        "bullets": summary.count("- "),
    }


def test_llm_summary():
    """LLM 기반 요약 테스트"""
    print("\n" + "=" * 60)
    print("Test 2: LLM-Based Summary (Gemini)")
    print("=" * 60)

    start = time.time()
    summary = summarize_with_llm(
        messages=SAMPLE_CONVERSATION, max_bullets=6, max_chars=600, temperature=0.3
    )
    elapsed = (time.time() - start) * 1000

    print("\n[Result]:")
    print(summary)
    print(f"\n[Time]: {elapsed:.2f}ms")
    print(f"[Length]: {len(summary)} chars")
    print(f"[Bullets]: {summary.count('- ')}")

    return {
        "summary": summary,
        "time_ms": elapsed,
        "length": len(summary),
        "bullets": summary.count("- "),
    }


def compare_summaries(rule_result, llm_result):
    """두 요약 결과 비교"""
    print("\n" + "=" * 60)
    print("Comparison: Rule-Based vs LLM-Based")
    print("=" * 60)

    print("\n[Time Comparison]:")
    print(f"  Rule-Based: {rule_result['time_ms']:.2f}ms")
    print(f"  LLM-Based:  {llm_result['time_ms']:.2f}ms")
    speedup = llm_result["time_ms"] / rule_result["time_ms"]
    print(f"  LLM is {speedup:.1f}x slower (expected)")

    print("\n[Length Comparison]:")
    print(f"  Rule-Based: {rule_result['length']} chars")
    print(f"  LLM-Based:  {llm_result['length']} chars")

    print("\n[Bullets Comparison]:")
    print(f"  Rule-Based: {rule_result['bullets']} bullets")
    print(f"  LLM-Based:  {llm_result['bullets']} bullets")

    print("\n[Quality Assessment (Human Evaluation Required)]:")
    print("  Rule-Based:")
    print("    - Pros: Very fast, deterministic")
    print("    - Cons: Low quality, no semantic compression")
    print("  LLM-Based:")
    print("    - Pros: High quality, semantic understanding")
    print("    - Cons: Slower, API cost")

    print("\n[Recommendation]:")
    if llm_result["time_ms"] < 1000:  # < 1초
        print("  [OK] LLM response time is acceptable (<1s)")
        print("  [RECOMMEND] Use LLM-based summary with caching")
        print("  [CACHE] With 70% hit rate, avg time will be:")
        cached_time = 0.7 * 10 + 0.3 * llm_result["time_ms"]
        print(f"         {cached_time:.1f}ms (7ms hit + {llm_result['time_ms']:.0f}ms miss)")
    else:
        print("  [WARNING] LLM response time is slow (>1s)")
        print("  [RECOMMEND] Consider hybrid approach:")
        print("         - Use rule-based for real-time responses")
        print("         - Use LLM for background session summaries")


def test_caching_impact():
    """캐싱 적용 시 성능 시뮬레이션"""
    print("\n" + "=" * 60)
    print("Test 3: Caching Impact Simulation")
    print("=" * 60)

    # 규칙 기반
    rule_time = 0.3  # 실측값 사용

    # LLM 기반 (첫 호출)
    print("\n[LLM] First call (cache miss)...")
    start = time.time()
    summary1 = summarize_with_llm(
        messages=SAMPLE_CONVERSATION, max_bullets=6, max_chars=600
    )
    first_call = (time.time() - start) * 1000
    print(f"  Time: {first_call:.2f}ms")

    # LLM 기반 (두 번째 호출 - 동일 입력)
    print("\n[LLM] Second call (should use same model)...")
    start = time.time()
    summary2 = summarize_with_llm(
        messages=SAMPLE_CONVERSATION, max_bullets=6, max_chars=600
    )
    second_call = (time.time() - start) * 1000
    print(f"  Time: {second_call:.2f}ms")

    print("\n[Caching Simulation]:")
    print(f"  Rule-Based: {rule_time:.2f}ms (always)")
    print(f"  LLM-Based (no cache): {first_call:.2f}ms (always)")
    print(f"  LLM-Based (with cache, 70% hit rate):")

    # 캐시 히트 10ms 가정
    cache_hit_time = 10
    avg_with_cache = 0.7 * cache_hit_time + 0.3 * first_call
    print(f"    = 0.7 × {cache_hit_time}ms + 0.3 × {first_call:.0f}ms")
    print(f"    = {avg_with_cache:.1f}ms")

    if avg_with_cache < 50:
        print(f"\n  [OK] Average time {avg_with_cache:.1f}ms < 50ms target")
    else:
        print(f"\n  [WARNING] Average time {avg_with_cache:.1f}ms > 50ms target")


def main():
    """메인 실행"""
    print("\n" + "=" * 60)
    print("LLM vs Rule-Based Summary Comparison")
    print("=" * 60)

    try:
        # Test 1: 규칙 기반
        rule_result = test_rule_based_summary()

        # Test 2: LLM 기반
        llm_result = test_llm_summary()

        # Test 3: 비교
        compare_summaries(rule_result, llm_result)

        # Test 4: 캐싱 영향
        test_caching_impact()

        print("\n" + "=" * 60)
        print("[SUCCESS] All tests completed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Evaluate quality manually (read both summaries)")
        print("2. Run A/B test with real users")
        print("3. Measure cache hit rate in production")
        print("4. Decide: Rule-based vs LLM-based vs Hybrid")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
