#!/usr/bin/env python3
"""
Analyze Quality metrics from resonance ledger
"""
import json
from pathlib import Path

ledger_path = Path(__file__).parent.parent / "memory" / "resonance_ledger.jsonl"

entries = []
with open(ledger_path, encoding='utf-8') as f:
    for line in f:
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

# Filter entries with quality
with_quality = [e for e in entries if 'quality' in e and e['quality'] is not None]

print(f"Total entries with quality: {len(with_quality)}")

# Low quality
low_quality = [e for e in with_quality if e['quality'] < 0.65]
print(f"Low quality (<0.65): {len(low_quality)} ({100 * len(low_quality) / len(with_quality):.1f}%)")

# Lowest 10
print(f"\n📉 Lowest 10 quality entries:")
for i, e in enumerate(sorted(with_quality, key=lambda x: x['quality'])[:10], 1):
    title = e.get('task_title', 'N/A')
    if len(title) > 60:
        title = title[:57] + "..."
    print(f"  {i:2d}. Quality={e['quality']:.3f} - {title}")

# Average by event_type
from collections import defaultdict
by_type = defaultdict(list)
for e in with_quality:
    event_type = e.get('event_type', 'unknown')
    by_type[event_type].append(e['quality'])

print(f"\n📊 Average quality by event type:")
for event_type, qualities in sorted(by_type.items(), key=lambda x: sum(x[1])/len(x[1])):
    avg = sum(qualities) / len(qualities)
    print(f"  {event_type:20s}: {avg:.3f} (n={len(qualities)})")

# Recent 20
recent_20 = with_quality[-20:]
avg_recent = sum(e['quality'] for e in recent_20) / len(recent_20) if recent_20 else 0
print(f"\n⏰ Recent 20 avg quality: {avg_recent:.3f}")
