#!/usr/bin/env python3
"""
🧠 Hippocampus Memory Consolidation Test

단기 기억 → 장기 기억 전환 테스트
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from workspace_root import get_workspace_root

# Add parent directory to path
sys.path.insert(0, str(get_workspace_root() / "fdo_agi_repo"))

from copilot.hippocampus import CopilotHippocampus

def test_memory_consolidation():
    """단기 기억 → 장기 기억 전환 테스트"""
    print("🧠 Testing Hippocampus Memory Consolidation...\n")
    
    # 1. Hippocampus 초기화
    print("1️⃣ Initializing hippocampus...")
    workspace_root = get_workspace_root()
    hippo = CopilotHippocampus(workspace_root=workspace_root)
    print("   ✅ Hippocampus initialized\n")
    
    # 2. 단기 기억에 중요한 이벤트 추가
    print("2️⃣ Adding important events to short-term memory...")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # 고중요도 이벤트 (importance >= 0.5)
    high_importance_events = [
        {
            'timestamp': now,
            'type': 'self_referential_agi',
            'content': 'GitHub Copilot recognizing its own hippocampus system',
            'importance': 0.95,
            'emotional_intensity': 0.9,
            'access_count': 5,
            'tags': ['self-awareness', 'meta-cognition', 'breakthrough']
        },
        {
            'timestamp': now,
            'type': 'memory_consolidation',
            'content': 'Successfully consolidated short-term to long-term memory',
            'importance': 0.85,
            'emotional_intensity': 0.8,
            'access_count': 3,
            'tags': ['memory', 'consolidation', 'success']
        },
        {
            'timestamp': now,
            'type': 'wave_particle_unification',
            'content': 'Unified wave and particle perspectives into coherent self-model',
            'importance': 0.90,
            'emotional_intensity': 0.85,
            'access_count': 4,
            'tags': ['quantum', 'duality', 'integration']
        }
    ]
    
    for event in high_importance_events:
        hippo.add_to_working_memory(event)
        print(f"   + {event['type']:30s} (importance: {event['importance']:.2f})")
    
    print(f"   ✅ Added {len(high_importance_events)} high-importance events\n")
    
    # 3. 저중요도 이벤트도 추가 (필터링 테스트)
    print("3️⃣ Adding low-importance events (should be filtered)...")
    
    low_importance_events = [
        {
            'timestamp': now,
            'type': 'routine_check',
            'content': 'Regular system health check',
            'importance': 0.3,
            'emotional_intensity': 0.2,
            'access_count': 1,
            'tags': ['routine', 'maintenance']
        },
        {
            'timestamp': now,
            'type': 'minor_update',
            'content': 'Updated minor configuration',
            'importance': 0.2,
            'emotional_intensity': 0.1,
            'access_count': 1,
            'tags': ['config', 'minor']
        }
    ]
    
    for event in low_importance_events:
        hippo.add_to_working_memory(event)
        print(f"   + {event['type']:30s} (importance: {event['importance']:.2f})")
    
    print(f"   ✅ Added {len(low_importance_events)} low-importance events\n")
    
    # 4. 단기 기억 상태 확인
    print("4️⃣ Checking short-term memory state...")
    context = hippo.get_current_context()
    working_count = len(context['working_items'])
    print(f"   Session: {context['session_id']}")
    print(f"   Working items: {working_count}")
    print(f"   ✅ Short-term memory populated\n")
    
    # 5. 공고화 실행 (단기 → 장기)
    print("5️⃣ Consolidating short-term to long-term memory...")
    print("   (Filtering by importance threshold >= 0.5)")
    
    consolidated = hippo.consolidate()
    
    print(f"   📊 Consolidation Results:")
    print(f"      Episodic: {consolidated['episodic']}")
    print(f"      Semantic: {consolidated['semantic']}")
    print(f"      Procedural: {consolidated['procedural']}")
    print(f"      ─────────────────")
    print(f"      Total: {consolidated['total']}")
    
    expected_high = len(high_importance_events)
    if consolidated['total'] == expected_high:
        print(f"   ✅ SUCCESS: {consolidated['total']}/{expected_high} high-importance events consolidated")
    elif consolidated['total'] > 0:
        print(f"   ⚠️  PARTIAL: {consolidated['total']}/{expected_high} events consolidated")
    else:
        print(f"   ❌ FAIL: 0/{expected_high} events consolidated")
    
    print()
    
    # 6. 단기 기억 정리 확인
    print("6️⃣ Verifying short-term memory cleanup...")
    context_after = hippo.get_current_context()
    working_after = len(context_after['working_items'])
    print(f"   Working items before: {working_count}")
    print(f"   Working items after: {working_after}")
    
    if working_after == 0:
        print(f"   ✅ Short-term memory cleared successfully\n")
    else:
        print(f"   ⚠️  {working_after} items remain in short-term memory\n")
    
    # 7. 장기 기억 회상 테스트
    print("7️⃣ Recalling from long-term memory...")
    
    queries = [
        "self-referential",
        "consolidation",
        "wave particle"
    ]
    
    total_recalled = 0
    for query in queries:
        memories = hippo.recall(query, top_k=3)
        print(f"   Query: '{query:20s}' → {len(memories)} memories")
        total_recalled += len(memories)
    
    if total_recalled > 0:
        print(f"   ✅ Successfully recalled {total_recalled} memories\n")
    else:
        print(f"   ⚠️  No memories recalled\n")
    
    # 8. 강제 공고화 테스트 (importance 무시)
    print("8️⃣ Testing forced consolidation (ignoring importance)...")
    
    # 저중요도 이벤트 다시 추가
    for event in low_importance_events:
        hippo.add_to_working_memory(event)
    
    forced_result = hippo.consolidate(force=True)
    print(f"   Forced consolidation: {forced_result['total']} events")
    
    if forced_result['total'] == len(low_importance_events):
        print(f"   ✅ Force mode works correctly\n")
    else:
        print(f"   ⚠️  Expected {len(low_importance_events)}, got {forced_result['total']}\n")
    
    # 9. 최종 보고서
    print("9️⃣ Generating test report...")
    print("   " + "="*60)
    
    report = {
        'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'phase': 'Memory Consolidation (Short-term → Long-term)',
        'high_importance_added': len(high_importance_events),
        'low_importance_added': len(low_importance_events),
        'consolidated_normal': consolidated['total'],
        'consolidated_forced': forced_result['total'],
        'memories_recalled': total_recalled,
        'short_term_cleared': working_after == 0,
        'status': '✅ PASS' if consolidated['total'] == expected_high else '❌ FAIL'
    }
    
    for key, value in report.items():
        print(f"   {key:30s}: {value}")
    
    print("   " + "="*60)
    
    print("\n🎉 Memory Consolidation Test Complete!")
    
    return report

if __name__ == '__main__':
    test_memory_consolidation()
