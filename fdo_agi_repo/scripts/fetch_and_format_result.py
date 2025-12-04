#!/usr/bin/env python3
"""
Comet 작업 결과 조회 및 포맷팅

사용법:
    python scripts/fetch_and_format_result.py <task_id>
    python scripts/fetch_and_format_result.py abc123 --format table
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared_task_queue import TaskQueue


def fetch_result(task_id, timeout=10, format_type="json"):
    """작업 결과 조회 및 포맷팅
    
    Args:
        task_id: 조회할 작업 ID
        timeout: 대기 시간 (초)
        format_type: 출력 형식 (json, table, markdown)
    """
    
    queue = TaskQueue()
    
    print(f"🔍 작업 결과 조회 중...")
    print(f"🆔 Task ID: {task_id}")
    
    # 결과 대기
    result = queue.get_result(task_id, timeout=timeout)
    
    if not result:
        print(f"\n❌ {timeout}초 내에 결과를 받지 못했습니다.")
        print(f"\n💡 직접 확인:")
        print(f"   Get-Content outputs\\task_queue\\results\\{task_id}.json")
        return None
    
    print(f"\n✅ 결과 받음!")
    print(f"   Worker: {result.worker}")
    print(f"   Status: {result.status}")
    print(f"   완료: {result.completed_at}")
    
    if result.status == "error":
        print(f"\n❌ 에러 발생:")
        print(f"   {result.error_message}")
        return None
    
    # 포맷팅 출력
    print(f"\n📊 결과 데이터:")
    
    if format_type == "json":
        print(json.dumps(result.data, indent=2, ensure_ascii=False))
    
    elif format_type == "table":
        print("\n" + "=" * 60)
        if isinstance(result.data, dict):
            for key, value in result.data.items():
                print(f"  {key:20s}: {value}")
        else:
            print(f"  {result.data}")
        print("=" * 60)
    
    elif format_type == "markdown":
        print("\n## 작업 결과\n")
        if isinstance(result.data, dict):
            print("| 항목 | 값 |")
            print("|------|-----|")
            for key, value in result.data.items():
                print(f"| {key} | {value} |")
        else:
            print(f"- 결과: {result.data}")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="작업 결과 조회")
    parser.add_argument("task_id", help="조회할 작업 ID")
    parser.add_argument("--timeout", type=int, default=10, help="대기 시간 (초)")
    parser.add_argument("--format", choices=["json", "table", "markdown"], 
                       default="table", help="출력 형식")
    
    args = parser.parse_args()
    
    fetch_result(args.task_id, timeout=args.timeout, format_type=args.format)
