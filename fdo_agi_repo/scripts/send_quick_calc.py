#!/usr/bin/env python3
"""
코멧에게 간단한 계산 작업 보내기 (즉시 실행)

사용법:
    python scripts/send_quick_calc.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared_task_queue import TaskQueue

def send_calc_task():
    """간단한 계산 작업 전송"""
    
    queue = TaskQueue()
    
    # 실용적인 작업: 모니터링 성공률 계산
    task_id = queue.push_task(
        task_type="calculation",
        data={
            "operation": "multiply",
            "numbers": [847, 1000]  # 성공 847건 / 전체 1000건
        },
        requester="copilot"
    )
    
    print(f"✅ 작업 전송 완료!")
    print(f"🆔 Task ID: {task_id}")
    print(f"📋 타입: calculation (곱셈)")
    print(f"🔢 계산: 847 × 1000 = 847000")
    print(f"\n⏳ 코멧이 5초 내 처리 예상...")
    print(f"\n💡 결과 확인 (8초 후):")
    print(f"   Get-Content d:\\nas_backup\\fdo_agi_repo\\outputs\\task_queue\\results\\{task_id}.json | ConvertFrom-Json")
    
    return task_id

if __name__ == "__main__":
    task_id = send_calc_task()
