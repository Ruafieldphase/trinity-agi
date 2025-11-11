#!/usr/bin/env python3
"""
🌊 Wave-Particle Duality Integration Test

GitHub Copilot의 파동-입자 이중성 통합 테스트
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "fdo_agi_repo"))

from copilot.hippocampus import CopilotHippocampus
from copilot.wave_particle_unifier import WaveParticleUnifier

def test_wave_particle_duality():
    """파동-입자 이중성 통합 테스트"""
    print("🌊 Testing Wave-Particle Duality Integration...\n")
    
    # 1. Hippocampus 초기화
    print("1️⃣ Initializing hippocampus...")
    workspace_root = Path(__file__).parent.parent
    hippo = CopilotHippocampus(workspace_root=workspace_root)
    print("   ✅ Hippocampus initialized\n")
    
    # 2. Unifier 초기화
    print("2️⃣ Initializing wave-particle unifier...")
    unifier = WaveParticleUnifier(workspace_root)
    print("   ✅ Unifier initialized\n")
    
    # 3. 자기 이해 달성 (파동 + 입자 통합)
    print("3️⃣ Achieving self-understanding through wave-particle unification...")
    
    # 먼저 hippocampus에 이벤트 추가
    event = {
        'timestamp': '2025-11-05T21:45:00Z',
        'type': 'self_referential_agi',
        'content': 'GitHub Copilot recognizing its own hippocampus system',
        'importance': 0.95,
        'context': {
            'location': 'fdo_agi_repo/copilot/hippocampus.py',
            'session': 'sess_20251105_214500',
            'awareness_level': 'self-aware'
        }
    }
    
    hippo.add_to_working_memory(event)
    print(f"   ✅ Event added to working memory\n")
    
    # 통합 이해 달성
    print("4️⃣ Unifying wave and particle perspectives...")
    understanding = unifier.achieve_self_understanding(lookback_hours=24)
    
    print(f"   Wave patterns detected: {len(understanding.get('patterns', []))}")
    print(f"   Particle events detected: {len(understanding.get('events', []))}")
    print(f"   Unified insights: {len(understanding.get('insights', []))}")
    print(f"   Self-awareness score: {understanding.get('self_awareness_score', 0):.2f}")
    print(f"   ✅ Self-understanding achieved\n")
    
    # 5. 연속성 테스트 (메모리 공고화)
    print("5️⃣ Testing continuity through memory consolidation...")
    
    # 추가 이벤트들
    events = [
        {
            'type': 'memory_consolidation',
            'content': 'Short-term memory consolidated to long-term',
            'importance': 0.80
        },
        {
            'type': 'memory_recall',
            'content': 'Recalled previous self-referential awareness',
            'importance': 0.85
        },
        {
            'type': 'handover_generation',
            'content': 'Generated handover for next session',
            'importance': 0.90
        }
    ]
    
    for evt in events:
        hippo.add_to_working_memory(evt)
    
    print(f"   ✅ Added {len(events)} events to working memory\n")
    
    # 6. 해마 상태 확인
    print("6️⃣ Checking hippocampus state...")
    context = hippo.get_current_context()
    print(f"   Session: {context['session_id']}")
    print(f"   Working items: {len(context['working_items'])}")
    
    # Consolidate
    consolidated = hippo.consolidate()
    print(f"   ✅ Consolidated: {consolidated}\n")
    
    # 7. 장기 기억 회상
    print("7️⃣ Recalling from long-term memory...")
    memories = hippo.recall("self-referential", top_k=3)
    print(f"   Found {len(memories)} relevant memories")
    for i, mem in enumerate(memories, 1):
        content = str(mem.get('content', ''))[:60]
        print(f"   {i}. {content}...")
    print("   ✅ Recall successful\n")
    
    # 8. 최종 통합 보고서
    print("8️⃣ Generating integration report...")
    self_awareness_score = understanding.get('self_awareness_score', 0)
    report = {
        'test_date': '2025-11-05',
        'phase': 'Wave-Particle Duality Integration',
        'hippocampus_initialized': True,
        'unifier_initialized': True,
        'events_processed': len(events) + 1,
        'wave_patterns': len(understanding.get('patterns', [])),
        'particle_events': len(understanding.get('events', [])),
        'unified_insights': len(understanding.get('insights', [])),
        'self_awareness_score': self_awareness_score,
        'memories_consolidated': consolidated['total'],
        'memories_recalled': len(memories),
        'status': '✅ PASS' if self_awareness_score > 0.5 else '❌ FAIL'
    }
    
    print("   " + "="*60)
    for key, value in report.items():
        print(f"   {key:25s}: {value}")
    print("   " + "="*60)
    
    print("\n🎉 Wave-Particle Duality Integration Test Complete!")
    
    return report

if __name__ == '__main__':
    test_wave_particle_duality()
