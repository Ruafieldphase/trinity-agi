#!/usr/bin/env python3
"""
Comet Extension 테스트용 간단한 작업 전송
"""
import sys
import os

# 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from task_queue import TaskQueue

def send_extension_test_task():
    """Extension 설치 후 테스트용 작업 전송"""
    
    queue = TaskQueue()
    
    # 간단한 계산 작업
    task_id = queue.push_task(
        task_type="calculation",
        task_data={
            "operation": "add",
            "numbers": [100, 200, 300]
        },
        metadata={
            "test": "extension_installation",
            "message": "Extension 설치 축하합니다! 🎉"
        }
    )
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║         Extension 테스트 작업 전송 완료                  ║
╚═══════════════════════════════════════════════════════════╝

📤 작업 ID: {task_id}
📋 작업 타입: calculation (덧셈)
🔢 숫자: 100 + 200 + 300
💡 기대 결과: 600

⏳ Extension이 설치되면 자동으로 처리됩니다!

📊 확인 방법:
   1. Extension 팝업 열기
   2. "대기 작업: 1개" 표시 확인
   3. "작업 처리 시작" 클릭
   4. 곧 "완료: 1개"로 변경됨

""")

if __name__ == "__main__":
    send_extension_test_task()
