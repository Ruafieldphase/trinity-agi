#!/usr/bin/env python3
"""
HybridSummarizer 테스트

실시간 요약 + 백그라운드 LLM 요약 통합 테스트
"""

import sys
import asyncio
import time
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent))

from persona_system.utils.hybrid_summarizer import get_hybrid_summarizer


# 테스트 대화 샘플
SAMPLE_CONVERSATION = [
    {"role": "user", "content": "Vertex AI로 마이그레이션하는 프로젝트를 시작하려고 하는데 어떻게 시작해야 할까요?"},
    {"role": "assistant", "content": "Vertex AI 마이그레이션을 시작하시려면 먼저 현재 시스템 아키텍처를 분석하고, Vertex AI SDK를 설치한 후, 기본 연결 테스트부터 시작하는 것을 권장합니다."},
    {"role": "user", "content": "SDK 설치는 어떻게 하나요?"},
    {"role": "assistant", "content": "pip install google-cloud-aiplatform 명령어로 설치할 수 있습니다. Python 3.11 이상 버전이 필요합니다."},
    {"role": "user", "content": "설치 후 첫 번째 테스트 코드는 어떻게 작성하면 되나요?"},
    {"role": "assistant", "content": "Vertex AI 클라이언트를 초기화하고 간단한 텍스트 생성 요청을 보내보세요. 프로젝트 ID와 리전 설정이 필요합니다."},
]


def test_realtime_summary():
    """Test 1: 실시간 요약 (규칙 기반)"""
    print("=" * 60)
    print("Test 1: Realtime Summary (Rule-Based)")
    print("=" * 60)

    summarizer = get_hybrid_summarizer(auto_initialize=False)

    # 실시간 요약 생성
    print("\n[TEST] Generating realtime summary...")
    start = time.time()
    summary = summarizer.get_realtime_summary(
        messages=SAMPLE_CONVERSATION, max_bullets=6, max_chars=600
    )
    elapsed = (time.time() - start) * 1000

    print("\n[Result]:")
    print(summary)
    print(f"\n[Time]: {elapsed:.2f}ms")
    print(f"[Length]: {len(summary)} chars")

    assert summary, "Summary is empty!"
    assert elapsed < 10, f"Too slow: {elapsed:.2f}ms (expected <10ms)"

    print("\n[OK] Realtime summary is fast and working!")

    return summary


async def test_background_summary():
    """Test 2: 백그라운드 세션 요약 (LLM 기반)"""
    print("\n" + "=" * 60)
    print("Test 2: Background Session Summary (LLM-Based)")
    print("=" * 60)

    summarizer = get_hybrid_summarizer(auto_initialize=True)

    # 백그라운드 요약 큐에 추가
    print("\n[TEST] Queueing session summary...")
    session_id = "test-session-001"
    user_id = "test-user-001"
    success = summarizer.queue_session_summary(
        session_id=session_id,
        user_id=user_id,
        messages=SAMPLE_CONVERSATION,
        max_bullets=8,
        max_chars=800,
        temperature=0.3,
    )

    assert success, "Failed to queue session summary!"
    print(f"[OK] Session summary queued: {session_id}")

    # 작업 완료 대기
    print("\n[WAIT] Waiting for background worker to complete...")
    max_wait = 30  # 최대 30초 대기
    start = time.time()

    while time.time() - start < max_wait:
        await asyncio.sleep(1)
        stats = summarizer.get_stats()

        print(
            f"  [{int(time.time() - start)}s] "
            f"Completed: {stats['session_summaries_completed']}, "
            f"Queue: {stats['queue_size']}"
        )

        if stats["session_summaries_completed"] > 0:
            break

    elapsed = (time.time() - start) * 1000

    # 결과 조회
    summary = summarizer.get_session_summary(session_id)

    if summary:
        print("\n[Result]:")
        print(summary)
        print(f"\n[Time]: {elapsed:.0f}ms")
        print(f"[Length]: {len(summary)} chars")
        print("\n[OK] Background session summary completed!")
        return summary
    else:
        print("\n[WARNING] Session summary not completed within timeout")
        print(f"[Stats]: {summarizer.get_stats()}")
        return None


async def test_hybrid_workflow():
    """Test 3: 하이브리드 워크플로우"""
    print("\n" + "=" * 60)
    print("Test 3: Hybrid Workflow (Realtime + Background)")
    print("=" * 60)

    summarizer = get_hybrid_summarizer(auto_initialize=True)

    # Step 1: 실시간 요약 (대화 중)
    print("\n[Step 1] Realtime summary during conversation...")
    realtime_summary = summarizer.get_realtime_summary(
        messages=SAMPLE_CONVERSATION[-2:],  # 최근 2개 메시지만
        max_bullets=4,
        max_chars=400,
    )
    print(f"  Realtime: {len(realtime_summary)} chars")

    # Step 2: 세션 종료 시 백그라운드 요약 큐
    print("\n[Step 2] Queue session summary on session end...")
    session_id = "test-session-002"
    user_id = "test-user-002"
    summarizer.queue_session_summary(
        session_id=session_id,
        user_id=user_id,
        messages=SAMPLE_CONVERSATION,  # 전체 대화
        max_bullets=8,
        max_chars=800,
    )
    print(f"  Queued: {session_id}")

    # Step 3: 백그라운드 작업 완료 대기
    print("\n[Step 3] Wait for background completion...")
    await asyncio.sleep(5)

    session_summary = summarizer.get_session_summary(session_id)

    print("\n[Comparison]:")
    print(f"  Realtime summary: {len(realtime_summary)} chars (최근 2개 메시지)")
    print(f"  Session summary: {len(session_summary) if session_summary else 0} chars (전체 대화)")

    print("\n[OK] Hybrid workflow completed!")

    return realtime_summary, session_summary


async def test_stats():
    """Test 4: 통계 확인"""
    print("\n" + "=" * 60)
    print("Test 4: Statistics")
    print("=" * 60)

    summarizer = get_hybrid_summarizer()
    stats = summarizer.get_stats()

    print("\n[Stats]:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n[OK] Stats retrieved!")

    return stats


async def main():
    """메인 실행"""
    print("\n" + "=" * 60)
    print("HybridSummarizer Integration Tests")
    print("=" * 60)

    try:
        # Test 1: 실시간 요약
        realtime_result = test_realtime_summary()

        # Test 2: 백그라운드 요약
        background_result = await test_background_summary()

        # Test 3: 하이브리드 워크플로우
        realtime, session = await test_hybrid_workflow()

        # Test 4: 통계
        stats = await test_stats()

        # 워커 종료
        summarizer = get_hybrid_summarizer()
        await summarizer.shutdown()

        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("=" * 60)

        print("\n[Summary]:")
        print(f"  Realtime summaries: {stats['realtime_summaries']}")
        print(f"  Session summaries completed: {stats['session_summaries_completed']}")
        print(f"  Success rate: {stats['success_rate']}")

        print("\n[Next Steps]:")
        print("1. Integrate HybridSummarizer into OptimizedPersonaPipeline")
        print("2. Add session end hook to trigger background summaries")
        print("3. Store session summaries in long-term memory")
        print("4. Add monitoring to cache dashboard")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # asyncio 실행
    asyncio.run(main())
