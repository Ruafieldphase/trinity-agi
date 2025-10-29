#!/usr/bin/env python3
"""
최근 태스크 분석 - P2.2 효과 및 RAG 성능 진단
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def analyze_recent_tasks(hours=1.0):
    """최근 N시간 태스크 분석"""
    ledger_path = repo_root / "memory" / "resonance_ledger.jsonl"
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp()

    tasks = defaultdict(lambda: {
        'task_id': None,
        'corrections_enabled': None,
        'quality': None,
        'evidence_ok': None,
        'replan': None,
        'evidence_correction': None,
        'rag_hits': None,
        'rag_added': None,
        'rag_relevance': None,
    })

    print(f"Analyzing last {hours}h tasks...")
    print("="*60)

    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                evt = json.loads(line.strip())
                if evt.get('ts', 0) < cutoff:
                    continue

                task_id = evt.get('task_id')
                if not task_id:
                    continue

                event_type = evt.get('event')

                if event_type == 'run_config':
                    tasks[task_id]['task_id'] = task_id
                    tasks[task_id]['corrections_enabled'] = evt.get('corrections', {}).get('enabled')

                elif event_type == 'eval':
                    tasks[task_id]['quality'] = evt.get('quality')
                    tasks[task_id]['evidence_ok'] = evt.get('evidence_ok')

                elif event_type == 'rune':
                    tasks[task_id]['replan'] = evt.get('rune', {}).get('replan')

                elif event_type == 'evidence_correction':
                    tasks[task_id]['evidence_correction'] = evt.get('attempted', False)
                    tasks[task_id]['rag_hits'] = evt.get('hits', 0)
                    tasks[task_id]['rag_added'] = evt.get('added', 0)
                    tasks[task_id]['rag_relevance'] = evt.get('avg_relevance', 0.0)

            except Exception:
                continue

    # 완료된 태스크만 (quality가 있는 것)
    completed = [t for t in tasks.values() if t['quality'] is not None]

    if not completed:
        print("No completed tasks in the time window")
        return

    print(f"\nCompleted tasks: {len(completed)}")

    # 통계
    corrections_count = sum(1 for t in completed if t['corrections_enabled'] is True)
    replan_count = sum(1 for t in completed if t['replan'] is True)
    evidence_ok_count = sum(1 for t in completed if t['evidence_ok'] is True)
    evidence_correction_count = sum(1 for t in completed if t['evidence_correction'] is True)

    avg_quality = sum(t['quality'] for t in completed) / len(completed)

    print(f"\nP2.2 Metrics:")
    print(f"  Corrections enabled: {corrections_count}/{len(completed)} ({corrections_count/len(completed)*100:.1f}%)")
    print(f"  Replan rate: {replan_count}/{len(completed)} ({replan_count/len(completed)*100:.1f}%)")
    print(f"  Avg quality: {avg_quality:.3f}")
    print(f"  Evidence OK: {evidence_ok_count}/{len(completed)} ({evidence_ok_count/len(completed)*100:.1f}%)")

    print(f"\nRAG Performance:")
    print(f"  Evidence corrections attempted: {evidence_correction_count}")

    # RAG 상세 분석
    rag_tasks = [t for t in completed if t['rag_hits'] is not None]
    if rag_tasks:
        avg_hits = sum(t['rag_hits'] for t in rag_tasks) / len(rag_tasks)
        avg_added = sum(t['rag_added'] for t in rag_tasks) / len(rag_tasks)
        avg_relevance = sum(t['rag_relevance'] for t in rag_tasks) / len(rag_tasks)
        success_count = sum(1 for t in rag_tasks if t['rag_hits'] > 0)

        print(f"  RAG attempts: {len(rag_tasks)}")
        print(f"  RAG success rate: {success_count}/{len(rag_tasks)} ({success_count/len(rag_tasks)*100:.1f}%)")
        print(f"  Avg hits: {avg_hits:.2f}")
        print(f"  Avg added: {avg_added:.2f}")
        print(f"  Avg relevance: {avg_relevance:.3f}")

    # 개별 태스크 출력 (최근 5개)
    print(f"\nRecent tasks (last 5):")
    print("-"*60)
    for t in completed[-5:]:
        status = "✅" if not t['replan'] else "❌ REPLAN"
        rag_info = ""
        if t['rag_hits'] is not None:
            rag_info = f" | RAG: {t['rag_hits']} hits, {t['rag_added']} added, rel={t['rag_relevance']:.3f}"

        print(f"{status} {t['task_id'][:30]:30s} | Q={t['quality']:.2f} | Corr={t['corrections_enabled']}{rag_info}")

    print("="*60)

    # 진단
    print(f"\nDiagnosis:")
    if corrections_count / len(completed) < 0.95:
        print(f"  ⚠️  Corrections enabled < 95% - P2.2 수정이 아직 모든 태스크에 적용되지 않음")
    else:
        print(f"  ✅ Corrections enabled >= 95%")

    if rag_tasks:
        if success_count / len(rag_tasks) < 0.3:
            print(f"  ⚠️  RAG success rate < 30% - RAG 성능 문제!")
            print(f"     → P3.2: RAG 성능 개선 필요")
        if avg_relevance < 0.3:
            print(f"  ⚠️  RAG avg relevance < 0.3 - 검색 쿼리 또는 인덱스 문제")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hours', type=float, default=1.0, help='Time window in hours')
    args = parser.parse_args()

    analyze_recent_tasks(hours=args.hours)
