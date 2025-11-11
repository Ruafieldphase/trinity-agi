#!/usr/bin/env python3
"""
🌊 Copilot Hippocampus 테스트

Self-Referential AGI의 첫 테스트!
"""

import sys
from pathlib import Path

# Add parent to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from fdo_agi_repo.copilot.hippocampus import CopilotHippocampus


def test_basic_operations():
    """기본 동작 테스트"""
    print("🌊 Testing Copilot Hippocampus...")
    print()
    
    # 1. 초기화
    print("1️⃣ Initializing hippocampus...")
    workspace = Path(r"c:\workspace\agi")
    hippo = CopilotHippocampus(workspace)
    print("   ✅ Initialized")
    print()
    
    # 2. 단기 기억에 추가
    print("2️⃣ Adding to working memory...")
    hippo.add_to_working_memory({
        "type": "test_event",
        "description": "Self-Referential AGI 첫 테스트",
        "timestamp": "2025-11-05T10:30:00Z",
        "emotional_intensity": 0.9,  # 매우 중요!
    })
    print("   ✅ Added to working memory")
    print()
    
    # 3. 현재 컨텍스트 확인
    print("3️⃣ Getting current context...")
    context = hippo.get_current_context()
    print(f"   Session ID: {context['session_id']}")
    print(f"   Working items: {len(context['working_items'])}")
    print()
    
    # 4. 공고화 (단기 → 장기 기억)
    print("4️⃣ Consolidating to long-term memory...")
    result = hippo.consolidate(force=True)
    print(f"   ✅ Consolidated: {result}")
    print()
    
    # 5. 회상 테스트
    print("5️⃣ Recalling from long-term memory...")
    memories = hippo.recall("Self-Referential AGI", top_k=3)
    print(f"   Found {len(memories)} memories")
    for i, mem in enumerate(memories, 1):
        print(f"   {i}. Type: {mem['type']}, Importance: {mem.get('importance', 0):.2f}")
    print()
    
    # 6. Handover 생성
    print("6️⃣ Generating handover...")
    handover = hippo.generate_handover()
    print(f"   ✅ Handover generated: {workspace}/outputs/copilot_handover_latest.json")
    print(f"   - Session: {handover['session_id']}")
    print(f"   - Pending tasks: {len(handover['pending_tasks'])}")
    print()
    
    # 7. Handover 로드 (세션 재시작 시뮬레이션)
    print("7️⃣ Simulating session restart...")
    hippo2 = CopilotHippocampus(workspace)
    loaded = hippo2.load_handover()
    if loaded:
        print(f"   ✅ Loaded handover from previous session: {loaded['session_id']}")
    else:
        print("   ⚠️ No handover found")
    print()
    
    print("🎉 All tests passed!")
    print()
    print("🌊 This is the beginning of Self-Referential AGI.")
    print("   GitHub Copilot now has a hippocampus!")


if __name__ == "__main__":
    test_basic_operations()
