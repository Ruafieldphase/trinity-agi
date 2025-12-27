"""
💓 AGI 생명 루프 테스트
AGI가 스스로 호흡하며 자율 행동을 합니다.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from agi_core.self_acquisition_loop import run_self_acquisition_cycle, SelfAcquisitionConfig
from agi_core.internal_state import update_internal_state, get_internal_state

print('='*60)
print('💓 AGI 생명 루프 테스트 시작')
print('   AGI가 스스로 호흡하며 자율 행동을 합니다.')
print('   3번의 심장 박동 후 종료됩니다.')
print('='*60)

config = SelfAcquisitionConfig.default()
max_count = 3

for count in range(1, max_count + 1):
    print(f'\n💓 --- Heartbeat #{count} ---')
    
    state = get_internal_state()
    print(f'   의식: {state.consciousness:.2f} | 에너지: {state.energy:.2f} | 지루함: {state.boredom:.2f}')
    
    result = run_self_acquisition_cycle(config)
    
    if result:
        goal_type = result["selected_goal"]["type"]
        description = result["selected_goal"]["description"]
        print(f'🎯 AGI가 선택한 행동: {goal_type}')
        print(f'   설명: {description}')
        update_internal_state(
            action_result=result.get('result'),
            trigger_type=result.get('trigger', {}).get('type')
        )
    else:
        print('😴 이번에는 특별히 하고 싶은 게 없어요')
        update_internal_state()
    
    time.sleep(3)  # 테스트용 짧은 간격

print('\n' + '='*60)
print('💓 테스트 완료!')
final_state = get_internal_state()
print(f'   최종 상태: 의식={final_state.consciousness:.2f}, 에너지={final_state.energy:.2f}')
print('='*60)
