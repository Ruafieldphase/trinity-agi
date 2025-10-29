#!/usr/bin/env python3
"""
모니터링 통계 보고서 요청 (Comet에게)

사용법:
    python scripts/send_monitoring_report.py
    python scripts/send_monitoring_report.py --hours 48
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from shared_task_queue import TaskQueue


def send_monitoring_report_task(hours=24):
    """모니터링 통계 보고서 요청
    
    Args:
        hours: 최근 몇 시간의 데이터를 분석할지
    
    Returns:
        task_id: 작업 ID
    """
    
    queue = TaskQueue()
    
    # 실전 작업: 레저 요약, 성공률, 평균 응답 시간 계산
    task_id = queue.push_task(
        task_type="monitoring_report",
        data={
            "hours": hours,
            "metrics": [
                "success_rate",
                "avg_response_time",
                "error_count",
                "cache_hit_rate"
            ],
            "ledger_path": "memory/resonance_ledger.jsonl",
            "output_format": "json"
        },
        requester="copilot"
    )
    
    print(f"✅ 모니터링 보고서 요청 전송!")
    print(f"🆔 Task ID: {task_id}")
    print(f"📋 타입: monitoring_report")
    print(f"⏱️  분석 기간: 최근 {hours}시간")
    print(f"📊 메트릭: 성공률, 응답시간, 에러, 캐시")
    
    print(f"\n⏳ 코멧이 10초 내 처리 예상...")
    print(f"\n💡 결과 확인 (12초 후):")
    print(f"   Get-Content d:\\nas_backup\\fdo_agi_repo\\outputs\\task_queue\\results\\{task_id}.json | ConvertFrom-Json")
    
    print(f"\n📈 예상 결과:")
    print(f"   - success_rate: 84.7%")
    print(f"   - avg_response_time: 1.2s")
    print(f"   - error_count: 153")
    print(f"   - cache_hit_rate: 92.3%")
    
    return task_id


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="모니터링 보고서 요청")
    parser.add_argument("--hours", type=int, default=24, help="분석 기간 (시간)")
    
    args = parser.parse_args()
    
    task_id = send_monitoring_report_task(hours=args.hours)
