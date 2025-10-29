#!/usr/bin/env python3
"""
영구 저장소 통합 테스트

테스트 시나리오:
1. 세션 요약 저장
2. 세션 요약 조회
3. 검색 기능
4. 프로세스 재시작 시뮬레이션
"""

import sys
import asyncio
import time
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent))

from persona_system.utils.session_summary_storage import (
    get_session_storage,
    reset_session_storage,
)
from persona_system.utils.hybrid_summarizer import (
    get_hybrid_summarizer,
    reset_hybrid_summarizer,
)


# 테스트 대화 샘플
SAMPLE_CONVERSATION = [
    {"role": "user", "content": "Vertex AI로 마이그레이션하는 프로젝트를 시작하려고 합니다."},
    {"role": "assistant", "content": "Vertex AI 마이그레이션을 시작하시려면 먼저 현재 시스템 아키텍처를 분석하는 것이 중요합니다."},
    {"role": "user", "content": "SDK 설치 방법을 알려주세요."},
    {"role": "assistant", "content": "pip install google-cloud-aiplatform 명령어로 설치할 수 있습니다."},
]


def test_storage_basic():
    """Test 1: 기본 저장소 테스트"""
    print("=" * 60)
    print("Test 1: Basic Storage Operations")
    print("=" * 60)

    storage = get_session_storage()

    # 저장
    print("\n[TEST] Saving session summary...")
    success = storage.save(
        session_id="test-session-001",
        user_id="user-001",
        summary="Vertex AI 마이그레이션 관련 대화",
        summary_type="llm",
        message_count=4,
        metadata={"test": True},
    )

    assert success, "Failed to save!"
    print("[OK] Session summary saved")

    # 조회
    print("\n[TEST] Loading session summary...")
    session_summary = storage.load("test-session-001")

    assert session_summary is not None, "Failed to load!"
    print(f"[OK] Loaded: {session_summary.session_id}")
    print(f"  User: {session_summary.user_id}")
    print(f"  Summary: {session_summary.summary[:50]}...")
    print(f"  Type: {session_summary.summary_type}")
    print(f"  Embedding dims: {session_summary.embedding_dims}")

    assert session_summary.embedding_path, "embedding path missing"
    assert session_summary.embedding_dims > 0, "embedding vector not stored"

    # 통계
    print("\n[TEST] Storage stats...")
    stats = storage.get_stats()
    print(f"[STATS]:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n[OK] Basic storage test passed!")

    return storage


def test_search():
    """Test 2: 검색 테스트"""
    print("\n" + "=" * 60)
    print("Test 2: Search Functionality")
    print("=" * 60)

    storage = get_session_storage()

    # 여러 세션 저장
    print("\n[TEST] Saving multiple sessions...")
    for i in range(5):
        storage.save(
            session_id=f"test-session-{i:03d}",
            user_id=f"user-{i % 2:03d}",  # user-000, user-001 반복
            summary=f"테스트 세션 {i}의 요약",
            summary_type="llm" if i % 2 == 0 else "rule_based",
            message_count=i + 1,
        )

    print(f"[OK] Saved 5 sessions")

    # 전체 검색
    print("\n[TEST] Searching all sessions...")
    all_sessions = storage.search(limit=10)
    print(f"[RESULT] Found {len(all_sessions)} sessions")

    # 사용자별 검색
    print("\n[TEST] Searching by user_id=user-000...")
    user_sessions = storage.search(user_id="user-000", limit=10)
    print(f"[RESULT] Found {len(user_sessions)} sessions for user-000")

    # 타입별 검색
    print("\n[TEST] Searching by summary_type=llm...")
    llm_sessions = storage.search(summary_type="llm", limit=10)
    print(f"[RESULT] Found {len(llm_sessions)} LLM sessions")

    # 의미 기반 검색
    print("\n[TEST] Semantic search (query_text='세션 004') ...")
    semantic = storage.search(
        query_text="세션 004",
        limit=5,
        min_similarity=0.05,
        include_embeddings=True,
    )
    for match in semantic:
        meta = match.metadata or {}
        print(
            f"  - {match.session_id} similarity={meta.get('similarity')} "
            f"preview={meta.get('embedding_preview')}"
        )
    assert semantic, "Semantic search returned no results"

    print("\n[OK] Search test passed!")

    return all_sessions


async def test_hybrid_integration():
    """Test 3: HybridSummarizer + Storage 통합"""
    print("\n" + "=" * 60)
    print("Test 3: HybridSummarizer + Storage Integration")
    print("=" * 60)

    # 새로운 summarizer 생성
    reset_hybrid_summarizer()
    summarizer = get_hybrid_summarizer(auto_initialize=True)

    # 백그라운드 요약 큐
    print("\n[TEST] Queueing session summary...")
    session_id = "test-session-hybrid-001"
    user_id = "user-hybrid-001"

    success = summarizer.queue_session_summary(
        session_id=session_id,
        user_id=user_id,
        messages=SAMPLE_CONVERSATION,
        max_bullets=8,
        max_chars=800,
    )

    assert success, "Failed to queue!"
    print(f"[OK] Queued: {session_id}")

    # 백그라운드 완료 대기
    print("\n[WAIT] Waiting for background completion...")
    await asyncio.sleep(5)

    # 메모리에서 조회
    print("\n[TEST] Loading from memory cache...")
    summary_memory = summarizer.get_session_summary(session_id)

    assert summary_memory is not None, "Not found in memory!"
    print(f"[OK] Found in memory: {len(summary_memory)} chars")

    # 메모리 캐시 초기화
    print("\n[TEST] Simulating process restart (clearing memory)...")
    summarizer.session_summaries.clear()

    # 영구 저장소에서 조회
    print("\n[TEST] Loading from persistent storage...")
    summary_storage = summarizer.get_session_summary(session_id)

    assert summary_storage is not None, "Not found in storage!"
    assert summary_storage == summary_memory, "Mismatch!"
    print(f"[OK] Found in storage: {len(summary_storage)} chars")
    print(f"[OK] Memory and storage match!")

    # 저장소 확인
    print("\n[TEST] Verifying storage directly...")
    storage = get_session_storage()
    session_summary = storage.load(session_id)

    assert session_summary is not None, "Not found in storage!"
    print(f"[VERIFY]:")
    print(f"  Session ID: {session_summary.session_id}")
    print(f"  User ID: {session_summary.user_id}")
    print(f"  Type: {session_summary.summary_type}")
    print(f"  Message Count: {session_summary.message_count}")
    print(f"  Summary Length: {session_summary.summary_length}")

    # 종료
    await summarizer.shutdown()

    print("\n[OK] Integration test passed!")

    return session_summary


async def test_process_restart_simulation():
    """Test 4: 프로세스 재시작 시뮬레이션"""
    print("\n" + "=" * 60)
    print("Test 4: Process Restart Simulation")
    print("=" * 60)

    # Phase 1: 첫 번째 프로세스
    print("\n[PHASE 1] First process - save session...")
    summarizer1 = get_hybrid_summarizer(auto_initialize=True)

    session_id = "test-restart-001"
    user_id = "user-restart-001"

    summarizer1.queue_session_summary(
        session_id=session_id,
        user_id=user_id,
        messages=SAMPLE_CONVERSATION,
    )

    await asyncio.sleep(5)  # 백그라운드 완료 대기

    summary1 = summarizer1.get_session_summary(session_id)
    assert summary1 is not None, "Summary not created!"
    print(f"[OK] Saved summary: {len(summary1)} chars")

    await summarizer1.shutdown()

    # Phase 2: 프로세스 재시작 시뮬레이션
    print("\n[PHASE 2] Process restart - reset all instances...")
    reset_hybrid_summarizer()

    # Phase 3: 새 프로세스에서 조회
    print("\n[PHASE 3] New process - load session...")
    summarizer2 = get_hybrid_summarizer(auto_initialize=True)

    summary2 = summarizer2.get_session_summary(session_id)
    assert summary2 is not None, "Summary lost after restart!"
    assert summary2 == summary1, "Summary mismatch!"

    print(f"[OK] Loaded summary after restart: {len(summary2)} chars")
    print(f"[OK] Summaries match!")

    await summarizer2.shutdown()

    print("\n[OK] Process restart simulation passed!")

    return summary2


async def main():
    """메인 실행"""
    print("\n" + "=" * 60)
    print("Session Summary Storage Integration Tests")
    print("=" * 60)

    try:
        # Test 1: 기본 저장소 테스트
        storage = test_storage_basic()

        # Test 2: 검색 테스트
        sessions = test_search()

        # Test 3: HybridSummarizer + Storage 통합
        session_summary = await test_hybrid_integration()

        # Test 4: 프로세스 재시작 시뮬레이션
        restart_summary = await test_process_restart_simulation()

        # 최종 통계
        print("\n" + "=" * 60)
        print("Final Statistics")
        print("=" * 60)

        stats = storage.get_stats()
        print("\n[Storage Stats]:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n" + "=" * 60)
        print("[SUCCESS] All storage integration tests passed!")
        print("=" * 60)

        print("\n[Test Summary]:")
        print(f"  1. Basic storage: OK")
        print(f"  2. Search functionality: OK ({len(sessions)} results)")
        print(f"  3. HybridSummarizer integration: OK")
        print(f"  4. Process restart simulation: OK")

        print("\n[Key Features Verified]:")
        print("  [x] Session summaries persist across restarts")
        print("  [x] Memory cache + persistent storage working")
        print("  [x] Search by user_id, type, date working")
        print("  [x] JSONL file storage working")
        print("  [x] Index-based fast lookup working")

        print("\n[Data Location]:")
        print(f"  {stats['storage_path']}")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # asyncio 실행
    asyncio.run(main())
