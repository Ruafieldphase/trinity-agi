#!/usr/bin/env python3
"""
코멧에게 간단한 집계 작업 보내기

사용법:
    python scripts/push_simple_aggregate_task.py
"""

import json
import os
from pathlib import Path
from datetime import datetime

def push_aggregate_task():
    """간단한 JSONL 집계 작업을 코멧에게 보냅니다."""
    
    # Task Queue 경로
    base = Path(__file__).parent.parent
    inbox = base / "outputs" / "task_queue" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    
    # 작업 생성
    task = {
        "id": f"aggregate-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "task_type": "json_process",
        "data": {
            "operation": "count_by_type",
            "description": "레저 파일에서 최근 이벤트 타입별 카운트",
            "note": "코멧 첫 실전 작업 - JSONL 집계 테스트"
        },
        "metadata": {
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "created_by": "copilot",
            "expected_worker": "comet-extension"
        }
    }
    
    # 파일 저장
    task_file = inbox / f"{task['id']}.json"
    with open(task_file, 'w', encoding='utf-8') as f:
        json.dump(task, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 작업 생성 완료!")
    print(f"📁 파일: {task_file}")
    print(f"🆔 Task ID: {task['id']}")
    print(f"📋 타입: {task['task_type']}")
    print(f"\n⏳ 코멧이 처리할 때까지 대기 중...")
    print(f"📊 결과는 outputs/task_queue/results/{task['id']}.json 에 저장됩니다")
    
    return task['id']

if __name__ == "__main__":
    task_id = push_aggregate_task()
    
    print(f"\n💡 결과 확인:")
    print(f"   Get-Content d:\\nas_backup\\fdo_agi_repo\\outputs\\task_queue\\results\\{task_id}.json | ConvertFrom-Json")
