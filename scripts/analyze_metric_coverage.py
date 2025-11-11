#!/usr/bin/env python3
"""
메트릭 커버리지 분석 도구
"""
import json
from pathlib import Path
from collections import Counter

def analyze_coverage():
    ledger = Path('fdo_agi_repo/memory/resonance_ledger.jsonl')
    if not ledger.exists():
        print("Ledger not found")
        return
    
    lines = ledger.read_text(encoding='utf-8').strip().split('\n')[-1000:]
    events = [json.loads(l) for l in lines if l.strip()]
    
    total = len(events)
    with_quality = sum(1 for e in events if 'quality' in e)
    with_latency = sum(1 for e in events if 'latency_ms' in e)
    with_both = sum(1 for e in events if 'quality' in e and 'latency_ms' in e)
    
    print(f"=== 최근 1000 이벤트 메트릭 커버리지 ===")
    print(f"총 이벤트: {total}")
    print(f"품질 메트릭: {with_quality} ({with_quality/total*100:.1f}%)")
    print(f"레이턴시: {with_latency} ({with_latency/total*100:.1f}%)")
    print(f"둘 다: {with_both} ({with_both/total*100:.1f}%)")
    print(f"\n루멘 목표: 80%+ (현재: {max(with_quality, with_latency)/total*100:.1f}%)")
    
    # 메트릭 누락 이벤트 분석
    no_metrics = [e for e in events if 'quality' not in e and 'latency_ms' not in e]
    types = Counter(e.get('event_type', 'unknown') for e in no_metrics)
    
    print(f"\n=== 메트릭 누락 이벤트 Top 10 ===")
    for etype, count in types.most_common(10):
        pct = count / len(no_metrics) * 100 if no_metrics else 0
        print(f"  {etype}: {count}회 ({pct:.1f}%)")
    
    print(f"\n총 {len(no_metrics)}개 이벤트가 메트릭 누락 ({len(no_metrics)/total*100:.1f}%)")
    
    # 자동 enrichment 후보 식별
    print(f"\n=== 자동 enrichment 후보 (start/end 패턴) ===")
    start_events = Counter(e.get('event_type', '') for e in events if e.get('event_type', '').endswith('_start'))
    end_events = Counter(e.get('event_type', '') for e in events if e.get('event_type', '').endswith('_end') or e.get('event_type', '').endswith('_completed'))
    
    for start_type, count in start_events.most_common(5):
        base = start_type[:-6]  # Remove '_start'
        end_type = f"{base}_end"
        completed_type = f"{base}_completed"
        end_count = end_events.get(end_type, 0) + end_events.get(completed_type, 0)
        print(f"  {base}: {count} starts, {end_count} ends")

if __name__ == '__main__':
    analyze_coverage()
