#!/usr/bin/env python3
"""
Daily Health Check - 일일 AGI 시스템 건강 체크

매일 자동 실행하여 시스템 상태 점검:
- Replan rate
- Quality metrics
- Evidence gate 정상 작동
- Corrections enabled 확인
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

# Repo root 경로 추가
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def load_ledger(hours: float = 24) -> List[Dict[str, Any]]:
    """최근 N시간 레저 로드"""
    ledger_path = repo_root / "memory" / "resonance_ledger.jsonl"
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp()

    events = []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    evt = json.loads(line)
                    if evt.get('ts', 0) > cutoff:
                        events.append(evt)
                except json.JSONDecodeError:
                    continue
    return events


def analyze_health(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """시스템 건강 분석"""

    # Task 수집
    tasks = {}
    for evt in events:
        task_id = evt.get('task_id')
        if not task_id:
            continue

        if task_id not in tasks:
            tasks[task_id] = {
                'task_id': task_id,
                'corrections_enabled': None,
                'quality': None,
                'evidence_ok': None,
                'replan': None,
                'evidence_correction': False
            }

        event_type = evt.get('event')

        if event_type == 'run_config':
            tasks[task_id]['corrections_enabled'] = evt.get('corrections', {}).get('enabled')
        elif event_type == 'eval' and tasks[task_id]['quality'] is None:
            tasks[task_id]['quality'] = evt.get('quality')
            tasks[task_id]['evidence_ok'] = evt.get('evidence_ok')
        elif event_type == 'rune' and tasks[task_id]['replan'] is None:
            tasks[task_id]['replan'] = evt.get('rune', {}).get('replan')
        elif event_type == 'evidence_correction':
            tasks[task_id]['evidence_correction'] = evt.get('attempted', False)

    # 완료된 task만 분석 (quality 있는 것)
    completed_tasks = [t for t in tasks.values() if t['quality'] is not None]

    if not completed_tasks:
        return {
            'status': 'NO_DATA',
            'message': 'No completed tasks in the last 24h',
            'total_tasks': 0
        }

    # 통계
    total = len(completed_tasks)
    corrections_enabled_count = sum(1 for t in completed_tasks if t['corrections_enabled'] is True)
    high_quality_count = sum(1 for t in completed_tasks if t['quality'] >= 0.6)
    evidence_ok_count = sum(1 for t in completed_tasks if t['evidence_ok'] is True)
    replan_count = sum(1 for t in completed_tasks if t['replan'] is True)
    evidence_correction_count = sum(1 for t in completed_tasks if t['evidence_correction'] is True)

    # 평균
    avg_quality = sum(t['quality'] for t in completed_tasks) / total

    # 건강 상태 판정
    health_score = 0
    issues = []

    # 1. Corrections enabled 체크 (25점)
    corrections_rate = corrections_enabled_count / total
    if corrections_rate >= 0.95:
        health_score += 25
    elif corrections_rate >= 0.8:
        health_score += 15
        issues.append(f"Corrections enabled rate: {corrections_rate*100:.1f}% (target: >= 95%)")
    else:
        issues.append(f"CRITICAL: Corrections enabled rate: {corrections_rate*100:.1f}% (target: >= 95%)")

    # 2. Replan rate 체크 (25점)
    replan_rate = replan_count / total
    if replan_rate <= 0.10:
        health_score += 25
    elif replan_rate <= 0.20:
        health_score += 15
        issues.append(f"Replan rate: {replan_rate*100:.1f}% (target: <= 10%)")
    else:
        issues.append(f"CRITICAL: Replan rate: {replan_rate*100:.1f}% (target: <= 10%)")

    # 3. Quality 체크 (25점)
    if avg_quality >= 0.7:
        health_score += 25
    elif avg_quality >= 0.6:
        health_score += 15
        issues.append(f"Avg quality: {avg_quality:.2f} (target: >= 0.7)")
    else:
        issues.append(f"CRITICAL: Avg quality: {avg_quality:.2f} (target: >= 0.6)")

    # 4. Evidence OK rate 체크 (25점)
    evidence_ok_rate = evidence_ok_count / total
    if evidence_ok_rate >= 0.9:
        health_score += 25
    elif evidence_ok_rate >= 0.7:
        health_score += 15
        issues.append(f"Evidence OK rate: {evidence_ok_rate*100:.1f}% (target: >= 90%)")
    else:
        issues.append(f"CRITICAL: Evidence OK rate: {evidence_ok_rate*100:.1f}% (target: >= 70%)")

    # 상태 결정
    if health_score >= 90:
        status = 'HEALTHY'
    elif health_score >= 70:
        status = 'WARNING'
    else:
        status = 'CRITICAL'

    return {
        'status': status,
        'health_score': health_score,
        'total_tasks': total,
        'metrics': {
            'corrections_enabled_rate': corrections_rate,
            'replan_rate': replan_rate,
            'avg_quality': avg_quality,
            'evidence_ok_rate': evidence_ok_rate,
            'high_quality_rate': high_quality_count / total
        },
        'counts': {
            'corrections_enabled': corrections_enabled_count,
            'replan': replan_count,
            'evidence_correction': evidence_correction_count,
            'high_quality': high_quality_count,
            'evidence_ok': evidence_ok_count
        },
        'issues': issues
    }


def print_report(health: Dict[str, Any]):
    """건강 보고서 출력"""
    print("="*60)
    print("AGI DAILY HEALTH CHECK")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Period: Last 24 hours\n")

    if health['status'] == 'NO_DATA':
        print(f"Status: {health['message']}")
        return

    # 상태 표시
    status_emoji = {
        'HEALTHY': 'PASS',
        'WARNING': 'WARNING',
        'CRITICAL': 'CRITICAL'
    }
    print(f"Status: {status_emoji[health['status']]} - Health Score: {health['health_score']}/100")
    print(f"Total tasks: {health['total_tasks']}\n")

    # 메트릭
    m = health['metrics']
    c = health['counts']
    print("Key Metrics:")
    print(f"  Corrections enabled: {c['corrections_enabled']}/{health['total_tasks']} ({m['corrections_enabled_rate']*100:.1f}%)")
    print(f"  Replan rate: {c['replan']}/{health['total_tasks']} ({m['replan_rate']*100:.1f}%)")
    print(f"  Avg quality: {m['avg_quality']:.3f}")
    print(f"  Evidence OK: {c['evidence_ok']}/{health['total_tasks']} ({m['evidence_ok_rate']*100:.1f}%)")
    print(f"  Evidence corrections: {c['evidence_correction']}")

    # 이슈
    if health['issues']:
        print("\nIssues:")
        for issue in health['issues']:
            if 'CRITICAL' in issue:
                print(f"  CRITICAL {issue}")
            else:
                print(f"  WARNING {issue}")
    else:
        print("\nNo issues detected")

    # 권장사항
    print("\nRecommendations:")
    if health['status'] == 'HEALTHY':
        print("  System is healthy. Continue monitoring.")
    elif health['status'] == 'WARNING':
        print("  Some metrics need attention. Review issues above.")
    else:
        print("  URGENT: System requires immediate investigation!")
        print("  1. Check recent task failures")
        print("  2. Verify config settings (corrections_enabled)")
        print("  3. Review evidence gate performance")


def save_report(health: Dict[str, Any]):
    """보고서 저장"""
    output_dir = repo_root / "outputs"
    output_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    report_file = output_dir / f"health_check_{date_str}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'health': health
        }, f, indent=2, ensure_ascii=False)

    return report_file


def main():
    """메인 실행"""
    try:
        # 레저 로드 (24시간)
        events = load_ledger(hours=24)

        # 건강 분석
        health = analyze_health(events)

        # 보고서 출력
        print_report(health)

        # 보고서 저장
        report_file = save_report(health)
        print(f"\nReport saved: {report_file}")

        # 종료 코드
        if health['status'] == 'HEALTHY':
            return 0
        elif health['status'] == 'WARNING':
            return 1
        else:
            return 2

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())
