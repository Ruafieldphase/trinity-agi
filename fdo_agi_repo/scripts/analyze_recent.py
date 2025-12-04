#!/usr/bin/env python3
"""
Quick analysis of recent ledger entries
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

print(f"Total ledger entries: {len(entries)}")

# Recent 100
recent = entries[-100:]
with_quality = [e for e in recent if 'quality' in e and e['quality'] is not None]

print(f"\n📊 Recent 100 entries:")
print(f"  With quality: {len(with_quality)}")
if with_quality:
    avg = sum(e['quality'] for e in with_quality) / len(with_quality)
    print(f"  Average quality: {avg:.3f}")
    low = [e for e in with_quality if e['quality'] < 0.65]
    print(f"  Low quality (<0.65): {len(low)} / {len(with_quality)} ({100*len(low)/len(with_quality):.1f}%)")

# Recent 20
recent_20 = entries[-20:]
with_q_20 = [e for e in recent_20 if 'quality' in e and e['quality'] is not None]

print(f"\n📊 Recent 20 entries:")
print(f"  With quality: {len(with_q_20)}")
if with_q_20:
    avg_20 = sum(e['quality'] for e in with_q_20) / len(with_q_20)
    print(f"  Average quality: {avg_20:.3f}")

# Lowest examples
print(f"\n📉 Lowest 5 quality (from recent 100):")
for i, e in enumerate(sorted(with_quality, key=lambda x: x['quality'])[:5], 1):
    goal = e.get('goal', 'N/A')
    if len(goal) > 50:
        goal = goal[:47] + "..."
    print(f"  {i}. Q={e['quality']:.3f}, goal={goal}")
