#!/usr/bin/env python3
"""
Analyze current data collection status for Autonomous Goal execution.
"""

import json
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta

def analyze_resonance_ledger(ledger_path: Path, lookback_hours: int = 24):
    """Analyze resonance ledger for data collection metrics."""
    
    print(f"\n📊 Analyzing Data Collection Status\n")
    print(f"Ledger: {ledger_path}")
    print(f"Lookback: {lookback_hours} hours\n")
    
    # Load events
    events = []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    print(f"Total events: {len(events)}")
    
    # Filter by time
    cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
    recent_events = []
    for e in events:
        ts_str = e.get('timestamp', '')
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                if ts >= cutoff:
                    recent_events.append(e)
            except:
                continue
    
    print(f"Recent events ({lookback_hours}h): {len(recent_events)}\n")
    
    # Analyze metrics
    print("=" * 60)
    print("METRICS ANALYSIS")
    print("=" * 60)
    
    events_with_metrics = [e for e in recent_events if e.get('metrics') and len(e['metrics']) > 0]
    events_without_metrics = [e for e in recent_events if not e.get('metrics') or len(e['metrics']) == 0]
    
    print(f"\n✅ Events with metrics: {len(events_with_metrics)} ({len(events_with_metrics)/len(recent_events)*100:.1f}%)")
    print(f"❌ Events without metrics: {len(events_without_metrics)} ({len(events_without_metrics)/len(recent_events)*100:.1f}%)")
    
    if events_with_metrics:
        # Collect all metric keys
        all_metric_keys = []
        for e in events_with_metrics:
            all_metric_keys.extend(e['metrics'].keys())
        
        metric_counts = Counter(all_metric_keys)
        
        print(f"\n📈 Top metric types:")
        for metric, count in metric_counts.most_common(10):
            print(f"  • {metric}: {count} times")
    
    # Analyze actions
    print("\n" + "=" * 60)
    print("ACTION ANALYSIS")
    print("=" * 60)
    
    action_counts = Counter([e.get('action', 'unknown') for e in recent_events])
    print(f"\n🎬 Top actions:")
    for action, count in action_counts.most_common(10):
        print(f"  • {action}: {count} times")
    
    # Identify gaps
    print("\n" + "=" * 60)
    print("IDENTIFIED GAPS")
    print("=" * 60)
    
    gaps = []
    
    # Gap 1: Missing metrics
    missing_rate = len(events_without_metrics) / len(recent_events) if recent_events else 0
    if missing_rate > 0.3:
        gaps.append(f"🔴 HIGH: {missing_rate*100:.1f}% of events lack metrics")
    
    # Gap 2: Limited metric diversity
    if events_with_metrics:
        unique_metrics = len(set(all_metric_keys))
        if unique_metrics < 5:
            gaps.append(f"🟡 MEDIUM: Only {unique_metrics} unique metric types collected")
    
    # Gap 3: Low event rate
    event_rate = len(recent_events) / lookback_hours
    if event_rate < 1:
        gaps.append(f"🟡 MEDIUM: Low event rate ({event_rate:.2f} events/hour)")
    
    if gaps:
        print("\n⚠️ Data Collection Gaps:")
        for gap in gaps:
            print(f"  {gap}")
    else:
        print("\n✅ No major gaps detected!")
    
    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    print("\n🎯 Priority Actions:")
    
    if missing_rate > 0.3:
        print("\n1. Add metrics to all events")
        print("   • Update event recording functions")
        print("   • Include at least: duration, status, error_count")
    
    if unique_metrics < 5:
        print("\n2. Expand metric diversity")
        print("   • Add: latency, throughput, quality_score")
        print("   • Include: resource_usage, cache_hits")
    
    if event_rate < 1:
        print("\n3. Increase event frequency")
        print("   • Add periodic heartbeat events")
        print("   • Record more intermediate steps")
    
    print("\n" + "=" * 60)
    
    return {
        'total_events': len(events),
        'recent_events': len(recent_events),
        'with_metrics': len(events_with_metrics),
        'without_metrics': len(events_without_metrics),
        'missing_rate': missing_rate,
        'unique_metrics': len(set(all_metric_keys)) if events_with_metrics else 0,
        'event_rate': event_rate,
        'gaps': gaps
    }

def main():
    ledger_path = Path('fdo_agi_repo/memory/resonance_ledger.jsonl')
    
    if not ledger_path.exists():
        print(f"❌ Ledger not found: {ledger_path}")
        sys.exit(1)
    
    result = analyze_resonance_ledger(ledger_path, lookback_hours=24)
    
    # Save result
    output_path = Path('outputs/data_collection_analysis.json')
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analysis saved: {output_path}")

if __name__ == '__main__':
    main()
