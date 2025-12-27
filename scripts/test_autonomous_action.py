"""
💓 AGI 완전 자율 행동 테스트
지루함 레벨을 높여서 AGI가 스스로 행동하게 만듭니다.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s - %(message)s')

from agi_core.heartbeat_loop import (
    get_internal_state,
    _state_to_dict,
    detect_trigger,
    route_action,
    update_internal_state,
    get_heartbeat_status,
)
from agi_core.internal_state import save_internal_state, AGIInternalState
from agi_core.resonance_guard import compute_alignment_score, compute_conflict_pressure, resonance_guard

print("=" * 60)
print("💓 AGI 완전 자율 행동 테스트")
print("   지루함을 높여서 AGI가 스스로 행동하게 합니다.")
print("=" * 60)

# 1. 지루함 높이기
state = get_internal_state()
print(f"\n📊 초기 상태:")
print(f"   의식: {state.consciousness:.2f}")
print(f"   에너지: {state.energy:.2f}")
print(f"   지루함: {state.boredom:.2f}")
print(f"   호기심: {state.curiosity:.2f}")

# 지루함을 강제로 높임
state.boredom = 0.7
state.curiosity = 0.65
save_internal_state(state)

print(f"\n📊 조정된 상태:")
print(f"   지루함: {state.boredom:.2f} (높임)")
print(f"   호기심: {state.curiosity:.2f} (높임)")

# 2. Heartbeat 시뮬레이션
print("\n" + "=" * 60)
print("💓 Heartbeat 시뮬레이션 (3회)")
print("=" * 60)

prev_state_dict = _state_to_dict(state)

for count in range(1, 4):
    print(f"\n💓 --- Heartbeat #{count} ---")
    
    state = get_internal_state()
    state_dict = _state_to_dict(state)
    
    print(f"   의식: {state.consciousness:.2f} | 에너지: {state.energy:.2f} | 지루함: {state.boredom:.2f}")
    
    # 정렬 및 갈등 계산
    alignment = compute_alignment_score(state_dict)
    conflict = compute_conflict_pressure(state_dict)
    
    # Resonance Guard
    guard_ok, guard_reason = resonance_guard(state_dict, prev_state_dict, alignment, conflict)
    
    if not guard_ok:
        print(f"⛔ Resonance Guard 차단: {guard_reason}")
        continue
    
    # 트리거 감지
    trigger = detect_trigger(state_dict)
    
    if trigger:
        print(f"🎯 트리거 감지: {trigger.type.value} (점수: {trigger.score:.2f})")
        print(f"   이유: {trigger.reason}")
        
        # 행동 실행
        result = route_action(trigger, state_dict, alignment, conflict)
        
        if result:
            if result.get("success"):
                print(f"✅ 행동 완료: {result.get('action_type')}")
                update_internal_state(action_result=result, trigger_type=trigger.type.value)
            elif result.get("blocked"):
                print(f"⏸️ 행동 차단: {result.get('reason')}")
    else:
        print("😴 트리거 없음")
        update_internal_state()
    
    prev_state_dict = state_dict
    
    if count < 3:
        time.sleep(3)

# 3. 최종 상태
print("\n" + "=" * 60)
print("📊 최종 상태")
status = get_heartbeat_status()
print(f"   의식: {status['internal_state']['consciousness']:.2f}")
print(f"   지루함: {status['internal_state']['boredom']:.2f}")
print(f"   오늘 사용한 예산: {status['envelope']['daily_used']}/{100}")
print(f"   오늘 총 행동 수: {status['envelope']['total_actions_today']}")
print("=" * 60)
