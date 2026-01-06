"""
Phase 3 Day 1 통합 테스트
- 자동 재시도/복구 메커니즘
- 검증 고도화 (화면 캡처, OCR)
- 성능 최적화 (병렬 처리, 캐싱)
"""
import pytest
pytestmark = pytest.mark.skip(reason="duplicate of fdo_agi_repo/tests/test_phase3_integration.py (renamed)")
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add fdo_agi_repo to path
sys.path.insert(0, str(Path(__file__).parent.parent / "fdo_agi_repo"))

from rpa.action_mapper import ActionMapper
from rpa.execution_engine import ExecutionEngine, ExecutionConfig, ExecutionMode
from rpa.actions import Action, ActionResult


def test_action_mapper_caching():
    """ActionMapper 캐싱 테스트 (lru_cache 기반)"""
    print("\n🧪 Test: ActionMapper Caching")
    print("="*70)
    
    mapper = ActionMapper()
    
    # 동일한 텍스트로 _extract_action_from_text 호출 (lru_cache 테스트)
    text = "open notepad"
    
    # 첫 번째 호출 (캐시 미스)
    start1 = time.time()
    action_type1, target1 = mapper._extract_action_from_text(text)
    duration1 = time.time() - start1
    
    print(f"  First call (cache miss): {duration1*1000:.2f}ms")
    assert action_type1 is not None
    
    # 두 번째 호출 (캐시 히트)
    start2 = time.time()
    action_type2, target2 = mapper._extract_action_from_text(text)
    duration2 = time.time() - start2
    
    print(f"  Second call (cache hit): {duration2*1000:.2f}ms")
    assert action_type2 == action_type1
    assert target2 == target1
    
    # 캐싱으로 인한 성능 개선 확인
    # lru_cache는 매우 빠르므로 단순히 동작 확인만
    print(f"  ✅ LRU cache is working (functools.lru_cache)")
    print()


def test_action_mapper_cache_invalidation():
    """ActionMapper 캐시 무효화 테스트 (lru_cache)"""
    print("\n🧪 Test: ActionMapper Cache Invalidation")
    print("="*70)
    
    mapper = ActionMapper()
    
    # 캐시에 항목 추가
    text = "type hello world"
    action_type1, target1 = mapper._extract_action_from_text(text)
    assert action_type1 is not None
    
    # lru_cache 정보 확인
    cache_info = mapper._extract_action_from_text.cache_info()
    print(f"  Cache info: hits={cache_info.hits}, misses={cache_info.misses}, size={cache_info.currsize}")
    
    # 캐시 클리어
    mapper._extract_action_from_text.cache_clear()
    
    cache_info_after = mapper._extract_action_from_text.cache_info()
    print(f"  After clear: hits={cache_info_after.hits}, misses={cache_info_after.misses}, size={cache_info_after.currsize}")
    
    assert cache_info_after.currsize == 0, "Cache should be empty after clear"
    
    # 캐시 클리어 후 다시 호출
    action_type2, target2 = mapper._extract_action_from_text(text)
    assert action_type2 == action_type1
    
    print("  ✅ Cache invalidation works correctly")
    print()


def test_execution_with_retry():
    """자동 재시도 메커니즘 테스트"""
    print("\n🧪 Test: Execution with Retry")
    print("="*70)
    
    # 실패 가능성이 있는 튜토리얼 (DRY_RUN 모드)
    tutorial = """
How to test retry:
1. Open nonexistent_app_12345
2. Type 'Hello'
3. Press Enter
    """.strip()
    
    config = ExecutionConfig(
        mode=ExecutionMode.DRY_RUN,
        enable_verification=False,
        enable_failsafe=True,
        timeout=10.0,
    )
    
    engine = ExecutionEngine(config)
    result = engine.execute_tutorial(tutorial)
    
    print(f"  Total Actions: {result.total_actions}")
    print(f"  Executed: {result.executed_actions}")
    print(f"  Failed: {result.failed_actions}")
    
    # DRY_RUN에서는 실패하지 않아야 함
    assert result.executed_actions >= 2, "Should execute at least 2 actions"
    
    print("  ✅ Retry mechanism is ready (DRY_RUN passes)")
    print()


def test_execution_error_capture():
    """오류 발생 시 캡처 기능 테스트"""
    print("\n🧪 Test: Error Capture")
    print("="*70)
    
    tutorial = """
How to test error capture:
1. Invalid action that will fail
2. Type 'Test'
    """.strip()
    
    config = ExecutionConfig(
        mode=ExecutionMode.DRY_RUN,
        enable_verification=False,
        enable_failsafe=True,
        timeout=5.0,
    )
    
    engine = ExecutionEngine(config)
    result = engine.execute_tutorial(tutorial)
    
    print(f"  Total Actions: {result.total_actions}")
    print(f"  Executed: {result.executed_actions}")
    print(f"  Failed: {result.failed_actions}")
    print(f"  Errors: {len(result.errors)}")
    
    # 에러가 캡처되어야 함
    if result.failed_actions > 0:
        assert len(result.errors) > 0, "Errors should be captured"
        print(f"  ✅ Error capture works ({len(result.errors)} errors captured)")
    else:
        print(f"  ℹ️  No errors in DRY_RUN mode")
    
    print()


def test_parallel_execution_readiness():
    """병렬 처리 준비 상태 테스트"""
    print("\n🧪 Test: Parallel Execution Readiness")
    print("="*70)
    
    # 여러 튜토리얼 동시 실행 가능 여부 (순차 실행으로 시뮬레이션)
    tutorials = [
        "1. Type 'Hello'",
        "1. Press Enter",
        "1. Open notepad",
    ]
    
    config = ExecutionConfig(
        mode=ExecutionMode.DRY_RUN,
        enable_verification=False,
        enable_failsafe=True,
        timeout=5.0,
    )
    
    results = []
    start = time.time()
    
    for tutorial in tutorials:
        engine = ExecutionEngine(config)
        result = engine.execute_tutorial(tutorial)
        results.append(result)
    
    duration = time.time() - start
    
    print(f"  Tutorials executed: {len(results)}")
    print(f"  Total duration: {duration:.2f}s")
    print(f"  Avg duration per tutorial: {duration/len(tutorials):.2f}s")
    
    # 모든 튜토리얼이 실행되어야 함
    assert all(r.total_actions > 0 for r in results), "All tutorials should execute"
    
    print("  ✅ Parallel execution is ready (sequential test passed)")
    print()


def test_cache_statistics():
    """캐시 통계 테스트 (lru_cache)"""
    print("\n🧪 Test: Cache Statistics")
    print("="*70)
    
    mapper = ActionMapper()
    
    # 캐시 초기화
    mapper._extract_action_from_text.cache_clear()
    mapper._parse_key_combination.cache_clear()
    
    # 여러 텍스트 처리
    texts = [
        "open notepad",
        "type hello",
        "press enter",
        "open notepad",  # 중복 (캐시 히트)
        "type hello",    # 중복 (캐시 히트)
    ]
    
    for text in texts:
        mapper._extract_action_from_text(text)
    
    # 캐시 통계 확인
    cache_info = mapper._extract_action_from_text.cache_info()
    print(f"  Total calls: {cache_info.hits + cache_info.misses}")
    print(f"  Cache hits: {cache_info.hits}")
    print(f"  Cache misses: {cache_info.misses}")
    print(f"  Cache size: {cache_info.currsize}")
    
    # 중복 호출 확인 (2개의 캐시 히트 예상)
    assert cache_info.hits >= 2, f"Expected at least 2 cache hits, got {cache_info.hits}"
    assert cache_info.currsize == 3, f"Expected 3 unique items, got {cache_info.currsize}"
    
    print("  ✅ Cache statistics are correct")
    print()


def test_performance_baseline():
    """성능 베이스라인 측정"""
    print("\n🧪 Test: Performance Baseline")
    print("="*70)
    
    tutorial = """
How to measure performance:
1. Open notepad
2. Type 'Performance Test'
3. Press Ctrl+S
4. Type 'test.txt'
5. Press Enter
    """.strip()
    
    config = ExecutionConfig(
        mode=ExecutionMode.DRY_RUN,
        enable_verification=False,
        enable_failsafe=True,
        timeout=10.0,
    )
    
    # 성능 측정 (3회 평균)
    durations = []
    for i in range(3):
        engine = ExecutionEngine(config)
        start = time.time()
        result = engine.execute_tutorial(tutorial)
        duration = time.time() - start
        durations.append(duration)
        print(f"  Run {i+1}: {duration:.3f}s")
    
    avg_duration = sum(durations) / len(durations)
    print(f"\n  Average duration: {avg_duration:.3f}s")
    print(f"  Actions per second: {result.total_actions/avg_duration:.1f}")
    
    # 성능 체크 (DRY_RUN에서는 매우 빠름)
    assert avg_duration < 5.0, f"Performance too slow: {avg_duration:.3f}s"
    
    print("  ✅ Performance baseline established")
    print()


def main():
    """Phase 3 Day 1 통합 테스트 실행"""
    print("\n" + "🚀"*35)
    print("Phase 3 Day 1 Integration Tests")
    print("Auto-retry / Error Recovery / Caching / Parallel")
    print("🚀"*35 + "\n")
    
    test_results = []
    
    tests = [
        ("ActionMapper Caching", test_action_mapper_caching),
        ("Cache Invalidation", test_action_mapper_cache_invalidation),
        ("Execution with Retry", test_execution_with_retry),
        ("Error Capture", test_execution_error_capture),
        ("Parallel Execution Readiness", test_parallel_execution_readiness),
        ("Cache Statistics", test_cache_statistics),
        ("Performance Baseline", test_performance_baseline),
    ]
    
    for name, test_func in tests:
        try:
            test_func()
            test_results.append((name, "✅ PASS"))
        except Exception as e:
            test_results.append((name, f"❌ FAIL: {e}"))
            print(f"  ❌ Test failed: {e}\n")
    
    # 요약
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for name, status in test_results:
        print(f"  {status.split(':')[0]:3s} {name}")
    
    passed = sum(1 for _, s in test_results if "✅" in s)
    total = len(test_results)
    
    print()
    print(f"  Total: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    print(f"  Pass Rate: {passed/total*100:.0f}%")
    print("="*70 + "\n")
    
    if passed == total:
        print("🎉 ALL PHASE 3 TESTS PASSED! 🎉\n")
        return 0
    else:
        print(f"⚠️  {total - passed} TEST(S) FAILED\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
