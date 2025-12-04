#!/usr/bin/env python3
"""
코멧에게 지원되는 작업 보내기 (data_transform)

사용법:
    python scripts/send_comet_data_task.py
"""

import json
from pathlib import Path
from datetime import datetime

def send_data_transform_task():
    """코멧이 지원하는 data_transform 작업 전송"""
    
    base = Path(__file__).parent.parent
    inbox = base / "outputs" / "task_queue" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    
    # 실제로 유용한 작업: 문자열 변환 (로그 정리 등에 활용)
    task = {
        "id": f"data-transform-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "task_type": "data_transform",
        "data": {
            "operation": "uppercase",
            "text": "ledger event types: task_completed, error, warning, cache_hit"
        },
        "metadata": {
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "note": "코멧 데이터 변환 테스트 - 실제 협업 준비"
        }
    }
    
    task_file = inbox / f"{task['id']}.json"
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 작업 전송 완료!")
    print(f"🆔 Task ID: {task['id']}")
    print(f"📋 타입: {task['task_type']} (지원됨 ✅)")
    print(f"🔄 작업: {task['data']['operation']}")
    print(f"\n⏳ 코멧이 5초 내 처리 예상...")
    
    return task['id']

if __name__ == "__main__":
    task_id = send_data_transform_task()
    
    print(f"\n💡 8초 후 결과 확인:")
    print(f"   Get-Content d:\\nas_backup\\fdo_agi_repo\\outputs\\task_queue\\results\\{task_id}.json")
