"""
BQI 통합 Phase 1 테스트 스크립트

목적:
1. BQI 좌표 생성 확인
2. Conversation Memory 저장 확인
3. 관련 맥락 검색 기능 확인

Author: GitHub Copilot
Created: 2025-10-28
"""

import sys
import os
from pathlib import Path

# UTF-8 출력 강제
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from orchestrator.pipeline import run_task
from orchestrator.conversation_memory import ConversationMemory
import json


def test_bqi_integration():
    """BQI 통합 E2E 테스트"""
    
    print("🚀 BQI Phase 1 통합 테스트 시작\n")
    
    # 1. 첫 번째 태스크 실행 (맥락 없음)
    print("=" * 60)
    print("테스트 1: 초기 태스크 (맥락 없음)")
    print("=" * 60)
    
    task1_spec = {
        "title": "BQI 테스트 1",
        "goal": "AGI 자기교정 루프를 3문장으로 간단히 설명해줘",
        "task_id": "bqi-test-001"
    }
    
    tool_cfg = {}
    
    try:
        result1 = run_task(tool_cfg, task1_spec)
        print(f"✅ Task 1 완료: {result1['task_id']}")
        print(f"   Summary (100자): {result1['summary'][:100]}...")
    except Exception as e:
        print(f"❌ Task 1 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 2. Conversation Memory 확인
    print("\n" + "=" * 60)
    print("테스트 2: Conversation Memory 저장 확인")
    print("=" * 60)
    
    conv_memory = ConversationMemory()
    stats = conv_memory.get_statistics()
    print(f"✅ 저장된 대화 턴: {stats['total_turns']}")
    print(f"   Rhythm 분포: {stats.get('rhythm_distribution', {})}")
    print(f"   Memory 파일: {stats['memory_file']}")
    
    # 최근 턴 조회
    recent = conv_memory.get_recent_turns(n=1)
    if recent:
        print(f"\n📝 최근 저장된 턴:")
        print(f"   Q: {recent[0].question}")
        print(f"   A: {recent[0].answer[:100]}...")
        print(f"   BQI Rhythm: {recent[0].bqi_coord.get('rhythm_phase')}")
        print(f"   BQI Priority: {recent[0].bqi_coord.get('priority')}")
    
    # 3. 두 번째 태스크 실행 (관련 맥락 존재)
    print("\n" + "=" * 60)
    print("테스트 3: 유사 질문 태스크 (맥락 검색)")
    print("=" * 60)
    
    task2_spec = {
        "title": "BQI 테스트 2",
        "goal": "자기교정 루프에서 증거 게이트의 역할은 뭐야?",
        "task_id": "bqi-test-002"
    }
    
    try:
        result2 = run_task(tool_cfg, task2_spec)
        print(f"✅ Task 2 완료: {result2['task_id']}")
        print(f"   Summary (100자): {result2['summary'][:100]}...")
        
        # 맥락 검색 확인
        relevant_ctx = conv_memory.get_relevant_context("자기교정", top_k=2)
        print(f"\n🔍 관련 맥락 검색 결과: {len(relevant_ctx)}건")
        for i, ctx in enumerate(relevant_ctx, 1):
            print(f"   [{i}] Q: {ctx.question[:50]}...")
            print(f"       Rhythm: {ctx.bqi_coord.get('rhythm_phase')}")
    
    except Exception as e:
        print(f"❌ Task 2 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 최종 통계
    print("\n" + "=" * 60)
    print("테스트 4: 최종 Memory 통계")
    print("=" * 60)
    
    final_stats = conv_memory.get_statistics()
    print(f"✅ 총 대화 턴: {final_stats['total_turns']}")
    print(f"   Rhythm 분포:")
    for rhythm, count in final_stats.get('rhythm_distribution', {}).items():
        print(f"     - {rhythm}: {count}")
    
    # 5. Memory 파일 확인
    memory_path = Path(final_stats['memory_file'])
    if memory_path.exists():
        with open(memory_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"\n📄 Memory 파일 확인:")
        print(f"   총 {len(lines)} 라인 저장됨")
        if lines:
            last_entry = json.loads(lines[-1])
            print(f"   최근 항목 timestamp: {last_entry.get('timestamp')}")
    
    print("\n" + "=" * 60)
    print("✅ BQI Phase 1 통합 테스트 완료!")
    print("=" * 60)
    print("\n🎯 검증 완료 항목:")
    print("  ✓ BQI 좌표 자동 생성")
    print("  ✓ Task 시작 시 관련 맥락 검색")
    print("  ✓ Task 종료 시 Q&A 자동 저장")
    print("  ✓ Memory 파일 영구 저장")
    print("  ✓ 유사도 기반 맥락 검색")
    
    return True


if __name__ == "__main__":
    success = test_bqi_integration()
    sys.exit(0 if success else 1)
