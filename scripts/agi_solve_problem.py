"""
🧠 AGI가 스스로 문제를 해결하기
응답 추출이 실패했으니, AGI가 더 좋은 방법을 찾아본다.
"""
import sys
from pathlib import Path
from workspace_root import get_workspace_root
sys.path.insert(0, str(get_workspace_root()))

import logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s - %(message)s')

from agi_core.proto_goal import ProtoGoal, ProtoGoalType
from agi_core.self_acquisition_loop import execute_proto_goal
from agi_core.internal_state import get_internal_state, update_internal_state

print("=" * 60)
print("🧠 AGI가 스스로 문제를 해결합니다")
print("=" * 60)

# 문제 상황 설명
problem = """
코어에게 질문을 보내는 건 성공했는데, 응답을 추출하는 데 실패했어.
Vision API가 화면 전체를 읽어서 코어의 응답만 추출하지 못했거든.

나는 몇 가지 해결책을 생각해봤어:
1. ChatGPT 앱의 특정 영역만 캡처하기
2. 코어의 응답을 복사(Ctrl+C)해서 클립보드에서 읽기
3. ChatGPT API를 직접 사용하기
4. 응답 영역의 좌표를 학습해서 그 부분만 캡처하기

코어, 나는 어떤 방법이 가장 좋을까?
그리고 비노체가 직접 해결해주지 않고 내가 스스로 해결할 수 있는 방법이 있을까?
"""

print("\n💭 AGI의 질문:")
print(problem)

# ProtoGoal 생성 - AGI가 스스로 해결책을 찾기
goal = ProtoGoal(
    type=ProtoGoalType.CONSULT_LUA,
    score=0.95,
    description="응답 추출 문제 해결법을 코어에게 질문",
    params={
        "trigger_type": "UNRESOLVED_PATTERN",
        "question": problem,
        "target": "chatgpt"
    }
)

print("\n🚀 ChatGPT로 질문 전송 중...")
print("   코어에게 해결책을 물어봅니다.")
print()

# 실행
result = execute_proto_goal(goal)

if result.get("success"):
    print("\n" + "=" * 60)
    print("🌊 코어의 조언:")
    print("=" * 60)
    print(result.get("response", "응답 없음"))
    print("=" * 60)
    
    # 문제 해결 시도 - 클립보드 방법 테스트
    print("\n🔧 AGI가 해결책을 시도합니다...")
    print("   → 클립보드 복사 방법 테스트 중...")
    
    import pyautogui
    import pyperclip
    import time
    
    # ChatGPT 앱에서 마지막 응답 복사 시도
    # Ctrl+Shift+C로 마지막 응답 복사 (ChatGPT 앱 기능)
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'shift', 'c')
    time.sleep(0.5)
    
    clipboard_content = pyperclip.paste()
    if clipboard_content and len(clipboard_content) > 50:
        print("\n✅ 클립보드 방법 성공!")
        print(f"   복사된 내용: {clipboard_content[:200]}...")
        
        # 이 방법을 학습 패턴으로 저장
        print("\n📝 이 방법을 패턴으로 저장합니다...")
else:
    print(f"\n❌ 질문 실패: {result}")
    print("\n💡 AGI가 대안적 방법을 시도합니다...")
    
    # 직접 해결 시도 - 클립보드 복사
    import pyautogui
    import pyperclip
    import time
    
    print("   → 클립보드 복사 방법 직접 테스트...")
    
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'shift', 'c')  # ChatGPT 앱의 복사 단축키
    time.sleep(0.5)
    
    clipboard_content = pyperclip.paste()
    print(f"\n📋 클립보드 내용: {clipboard_content[:300] if clipboard_content else '없음'}...")
