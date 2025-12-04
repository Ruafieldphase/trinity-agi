#!/usr/bin/env python3
"""
코멧에게 텍스트 변환 작업 보내기

사용법:
    python scripts/send_text_transform.py
    
    # 또는 커스텀 텍스트:
    python scripts/send_text_transform.py "YOUR TEXT HERE"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared_task_queue import TaskQueue


def send_transform_task(text=None, operation="uppercase"):
    """텍스트 변환 작업 전송"""
    
    if text is None:
        text = "ledger event types: task_completed, error, warning, cache_hit"
    
    queue = TaskQueue()
    
    task_id = queue.push_task(
        task_type="data_transform",
        data={
            "operation": operation,  # uppercase, lowercase, reverse
            "text": text
        },
        requester="copilot"
    )
    
    print(f"✅ 텍스트 변환 작업 전송!")
    print(f"🆔 Task ID: {task_id}")
    print(f"📋 작업: {operation}")
    print(f"📝 입력: {text}")
    print(f"\n⏳ 코멧이 5초 내 처리 예상...")
    print(f"\n💡 결과 확인 (8초 후):")
    print(f"   Get-Content d:\\nas_backup\\fdo_agi_repo\\outputs\\task_queue\\results\\{task_id}.json | ConvertFrom-Json")
    
    return task_id


if __name__ == "__main__":
    custom_text = sys.argv[1] if len(sys.argv) > 1 else None
    operation = sys.argv[2] if len(sys.argv) > 2 else "uppercase"
    
    task_id = send_transform_task(custom_text, operation)
