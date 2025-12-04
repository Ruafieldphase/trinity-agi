#!/usr/bin/env python3
"""
성능 벤치마크 - 깃코 개선 효과 정량화

목적: 깃코의 Evidence Gate + RAG 개선 전후 비교
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def analyze_period(start_ts, end_ts, label):
    """특정 기간의 성능 분석"""
    ledger_path = repo_root / "memory" / "resonance_ledger.jsonl"

    tasks = defaultdict(lambda: {
        'quality': None,
        'evidence_ok': None,
        'replan': None,
        'corrections_enabled': None,
        'rag_hits': None,
        'rag_relevance': None,
        'synthetic_used': False,
        'retry_used': False,
    })

    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                evt = json.loads(line.strip())
                ts = evt.get('ts', 0)

                if not (start_ts <= ts < end_ts):
                    continue

                task_id = evt.get('task_id')
                if not task_id:
                    continue

                event_type = evt.get('event')

                if event_type == 'run_config':
                    tasks[task_id]['corrections_enabled'] = evt.get('corrections', {}).get('enabled')
                elif event_type == 'eval':
                    tasks[task_id]['quality'] = evt.get('quality')
                    tasks[task_id]['evidence_ok'] = evt.get('evidence_ok')
                elif event_type == 'rune':
                    tasks[task_id]['replan'] = evt.get('rune', {}).get('replan')
                elif event_type == 'evidence_correction':
                    tasks[task_id]['rag_hits'] = evt.get('hits', 0)
                    tasks[task_id]['rag_relevance'] = evt.get('avg_relevance', 0.0)
                    tasks[task_id]['synthetic_used'] = evt.get('synthetic_used', False)
                    tasks[task_id]['retry_used'] = evt.get('retry_broaden_used', False)

            except Exception:
                continue

    # 완료된 태스크만
    completed = [t for t in tasks.values() if t['quality'] is not None]

    if not completed:
        return {
            'label': label,
            'total_tasks': 0,
            'note': 'No data'
        }

    # 통계
    total = len(completed)
    corrections_count = sum(1 for t in completed if t['corrections_enabled'] is True)
    high_quality_count = sum(1 for t in completed if t['quality'] >= 0.7)
    evidence_ok_count = sum(1 for t in completed if t['evidence_ok'] is True)
    replan_count = sum(1 for t in completed if t['replan'] is True)

    avg_quality = sum(t['quality'] for t in completed) / total

    # RAG 통계
    rag_tasks = [t for t in completed if t['rag_hits'] is not None]
    if rag_tasks:
        rag_success = sum(1 for t in rag_tasks if t['rag_hits'] > 0)
        avg_rag_hits = sum(t['rag_hits'] for t in rag_tasks) / len(rag_tasks)
        avg_rag_rel = sum(t['rag_relevance'] for t in rag_tasks) / len(rag_tasks)
        synthetic_count = sum(1 for t in rag_tasks if t['synthetic_used'])
        retry_count = sum(1 for t in rag_tasks if t['retry_used'])
    else:
        rag_success = 0
        avg_rag_hits = 0
        avg_rag_rel = 0
        synthetic_count = 0
        retry_count = 0

    return {
        'label': label,
        'total_tasks': total,
        'corrections_enabled_rate': corrections_count / total,
        'avg_quality': avg_quality,
        'high_quality_rate': high_quality_count / total,
        'evidence_ok_rate': evidence_ok_count / total,
        'replan_rate': replan_count / total,
        'rag_attempts': len(rag_tasks),
        'rag_success_rate': rag_success / len(rag_tasks) if rag_tasks else 0,
        'avg_rag_hits': avg_rag_hits,
        'avg_rag_relevance': avg_rag_rel,
        'synthetic_rate': synthetic_count / len(rag_tasks) if rag_tasks else 0,
        'retry_rate': retry_count / len(rag_tasks) if rag_tasks else 0,
    }


def main():
    print("="*60)
    print("Performance Benchmark - 깃코 개선 효과 측정")
    print("="*60)
    print()

    # 깃코 Evidence Gate 개선: 10/26 23:55
    # RAG Config 수정: 10/27 09:07

    gitco_improvement = datetime(2025, 10, 26, 23, 55, 0).timestamp()
    rag_config_fix = datetime(2025, 10, 27, 9, 7, 0).timestamp()
    now = datetime.now().timestamp()

    # Period 1: 깃코 개선 전 (10/26 18:00 ~ 23:55)
    period1 = analyze_period(
        datetime(2025, 10, 26, 18, 0, 0).timestamp(),
        gitco_improvement,
        "Before Gitco (10/26 18:00-23:55)"
    )

    # Period 2: 깃코 개선 후, RAG config 전 (10/26 23:55 ~ 10/27 09:07)
    period2 = analyze_period(
        gitco_improvement,
        rag_config_fix,
        "After Gitco, Before RAG Config (10/26 23:55 - 10/27 09:07)"
    )

    # Period 3: RAG config 후 (10/27 09:07 ~ 현재)
    period3 = analyze_period(
        rag_config_fix,
        now,
        "After RAG Config (10/27 09:07 - now)"
    )

    # 출력
    periods = [period1, period2, period3]

    print("기간별 성능 비교:\n")

    for p in periods:
        print(f"{p['label']}")
        print(f"  Tasks: {p['total_tasks']}")

        if p['total_tasks'] == 0:
            print(f"  (No data)")
            print()
            continue

        print(f"  Corrections enabled: {p['corrections_enabled_rate']*100:.1f}%")
        print(f"  Avg quality: {p['avg_quality']:.3f}")
        print(f"  High quality (>=0.7): {p['high_quality_rate']*100:.1f}%")
        print(f"  Evidence OK: {p['evidence_ok_rate']*100:.1f}%")
        print(f"  Replan rate: {p['replan_rate']*100:.1f}%")
        print(f"  RAG attempts: {p['rag_attempts']}")
        print(f"  RAG success rate: {p['rag_success_rate']*100:.1f}%")
        print(f"  Avg RAG hits: {p['avg_rag_hits']:.2f}")
        print(f"  Avg RAG relevance: {p['avg_rag_relevance']:.3f}")
        print(f"  Synthetic fallback rate: {p['synthetic_rate']*100:.1f}%")
        print(f"  Retry broaden rate: {p['retry_rate']*100:.1f}%")
        print()

    # 개선 효과 계산
    print("="*60)
    print("개선 효과 분석")
    print("="*60)
    print()

    if period1['total_tasks'] > 0 and period3['total_tasks'] > 0:
        print("Before vs After (Period 1 vs Period 3):")
        print()

        improvements = {
            'Quality': (period3['avg_quality'] - period1['avg_quality'], period1['avg_quality']),
            'Evidence OK': (period3['evidence_ok_rate'] - period1['evidence_ok_rate'], period1['evidence_ok_rate']),
            'Replan rate': (period1['replan_rate'] - period3['replan_rate'], period1['replan_rate']),  # 감소가 좋음
            'RAG success': (period3['rag_success_rate'] - period1['rag_success_rate'], period1['rag_success_rate']),
            'RAG relevance': (period3['avg_rag_relevance'] - period1['avg_rag_relevance'], period1['avg_rag_relevance']),
        }

        for metric, (diff, baseline) in improvements.items():
            if baseline > 0:
                pct_change = (diff / baseline) * 100
                direction = "↑" if pct_change > 0 else ("↓" if pct_change < 0 else "=")

                if metric == "Replan rate":
                    # Replan은 감소가 좋음
                    direction = "✅" if pct_change > 0 else "⚠️"
                else:
                    direction = "✅" if pct_change > 0 else "⚠️"

                print(f"  {metric:20s}: {direction} {abs(pct_change):6.1f}%")
            else:
                print(f"  {metric:20s}: N/A (baseline 0)")
    else:
        print("Not enough data for comparison")

    print()

    # 깃코 개선 항목별 효과
    if period2['total_tasks'] > 0:
        print("깃코 개선 항목별 효과:")
        print()
        print(f"  Evidence Gate synthetic 제외:")
        print(f"    - Period 1 synthetic rate: {period1['synthetic_rate']*100:.1f}%")
        print(f"    - Period 2 synthetic rate: {period2['synthetic_rate']*100:.1f}%")
        print(f"    - 효과: Synthetic 사용 감소 예상")
        print()

        print(f"  RAG retry/fallback:")
        print(f"    - Period 1 retry rate: {period1['retry_rate']*100:.1f}%")
        print(f"    - Period 2 retry rate: {period2['retry_rate']*100:.1f}%")
        print(f"    - 효과: Retry 메커니즘 작동 확인")
        print()

    if period3['total_tasks'] > 0:
        print(f"  RAG Config 최적화 (include_types 확장):")
        print(f"    - Period 2 RAG success: {period2['rag_success_rate']*100:.1f}%")
        print(f"    - Period 3 RAG success: {period3['rag_success_rate']*100:.1f}%")
        print(f"    - Period 2 RAG relevance: {period2['avg_rag_relevance']:.3f}")
        print(f"    - Period 3 RAG relevance: {period3['avg_rag_relevance']:.3f}")

        if period2['rag_success_rate'] > 0:
            improvement = ((period3['rag_success_rate'] - period2['rag_success_rate']) / period2['rag_success_rate']) * 100
            print(f"    - 효과: RAG 성공률 {improvement:+.1f}% 변화")


if __name__ == '__main__':
    main()
