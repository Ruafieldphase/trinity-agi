#!/usr/bin/env python3
"""
Analyze timeline drop in Quality (11:09 period)
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

ledger_path = Path(__file__).parent.parent / "memory" / "resonance_ledger.jsonl"

# Target time: 11:09 (10:39 - 11:39 window)
target_start = datetime.now().replace(hour=10, minute=39, second=0, microsecond=0)
target_end = datetime.now().replace(hour=11, minute=39, second=0, microsecond=0)

entries = []
with open(ledger_path, encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

# Filter by time
time_filtered = []
for e in entries:
    if 'timestamp' not in e:
        continue
    try:
        ts = datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00'))
        if target_start <= ts <= target_end:
            time_filtered.append(e)
    except:
        continue

print(f"Entries in 10:39-11:39 window: {len(time_filtered)}")

# Quality analysis
with_quality = [e for e in time_filtered if 'quality' in e and e['quality'] is not None]
print(f"With quality: {len(with_quality)}")

if with_quality:
    avg_q = sum(e['quality'] for e in with_quality) / len(with_quality)
    print(f"Average quality: {avg_q:.3f}")
    
    low_q = [e for e in with_quality if e['quality'] < 0.65]
    print(f"Low quality (<0.65): {len(low_q)} ({100*len(low_q)/len(with_quality):.1f}%)")
    
    # Sample low quality entries
    print(f"\n📉 Sample low quality entries:")
    for e in sorted(with_quality, key=lambda x: x['quality'])[:5]:
        print(f"  Q={e['quality']:.3f}, goal={e.get('goal', 'N/A')[:50]}...")
        print(f"    event={e.get('event_type', 'N/A')}, personas={len(e.get('persona_weights', {}))}")

# Event type distribution
from collections import Counter
event_types = Counter(e.get('event_type', 'unknown') for e in time_filtered)
print(f"\n📊 Event type distribution:")
for event_type, count in event_types.most_common():
    print(f"  {event_type:20s}: {count}")
