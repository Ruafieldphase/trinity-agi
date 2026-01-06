"""
AGI Self-Acquisition 테스트 실행
AGI가 스스로 해보고 싶은 것을 찾아서 실행
"""
import sys
from pathlib import Path
from workspace_root import get_workspace_root
sys.path.insert(0, str(get_workspace_root()))

from agi_core.self_acquisition_loop import run_self_acquisition_cycle, SelfAcquisitionConfig

print('='*60)
print('🧠 AGI Self-Acquisition: 스스로 해보고 싶은 것 찾는 중...')
print('='*60)

config = SelfAcquisitionConfig.default()
result = run_self_acquisition_cycle(config)

if result:
    print()
    print('🎯 AGI가 스스로 선택한 행동:')
    print(f'   트리거: {result["trigger"]["type"]}')
    print(f'   이유: {result["trigger"]["reason"]}')
    print()
    print(f'   선택한 목표: {result["selected_goal"]["type"]}')
    print(f'   설명: {result["selected_goal"]["description"]}')
    print()
    success = result["result"].get("success", False)
    print(f'   결과: {"✅ 성공" if success else "❌ 실패"}')
    print(f'   상세: {result["result"]}')
else:
    print('😴 AGI: 지금은 특별히 하고 싶은 게 없어요')
