#!/usr/bin/env python3
"""
배치 계산 요청 (여러 계산을 한 번에)

사용법:
    python scripts/send_batch_calc.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared_task_queue import TaskQueue


def send_batch_calculation_task():
    """배치 계산 요청
    
    실전 시나리오:
    - 성공률: 847/1000 * 100
    - 에러율: 153/1000 * 100
    - 평균 응답 시간: (1.2 + 1.5 + 0.9) / 3
    - 캐시 히트율: 923/1000 * 100
    """
    
    queue = TaskQueue()
    
    calculations = [
        {"id": "success_rate", "operation": "divide", "numbers": [847, 1000], "multiply_by": 100},
        {"id": "error_rate", "operation": "divide", "numbers": [153, 1000], "multiply_by": 100},
        {"id": "avg_response", "operation": "average", "numbers": [1.2, 1.5, 0.9]},
        {"id": "cache_hit", "operation": "divide", "numbers": [923, 1000], "multiply_by": 100}
    ]
    
    task_id = queue.push_task(
        task_type="batch_calculation",
        data={
            "calculations": calculations,
            "output_format": "json"
        },
        requester="copilot"
    )
    
    print(f"✅ 배치 계산 요청 전송!")
    print(f"🆔 Task ID: {task_id}")
    print(f"📋 타입: batch_calculation")
    print(f"🔢 계산 개수: {len(calculations)}개")
    
    print(f"\n📊 요청한 계산:")
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from workspace_utils import find_fdo_root
    
    fdo_root = find_fdo_root(Path(__file__).parent)
    
    for calc in calculations:
        print(f"   - {calc['id']}: {calc['operation']}")
    
    print(f"\n⏳ 코멧이 10초 내 처리 예상...")
    print(f"\n💡 결과 확인 (12초 후):")
    print(f"   Get-Content {fdo_root}\\\\outputs\\\\task_queue\\\\results\\\\{task_id}.json | ConvertFrom-Json")
    
    print(f"\n📈 예상 결과:")
    print(f"   - success_rate: 84.7%")
    print(f"   - error_rate: 15.3%")
    print(f"   - avg_response: 1.2")
    print(f"   - cache_hit: 92.3%")
    
    return task_id


if __name__ == "__main__":
    task_id = send_batch_calculation_task()
