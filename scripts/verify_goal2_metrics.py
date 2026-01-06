"""
Phase 1 Goal #2 Verification: Check metrics coverage
"""
import json
import sys
from pathlib import Path

ledger_path = Path("c:/workspace/agi/fdo_agi_repo/memory/resonance_ledger.jsonl")

if not ledger_path.exists():
    print(f"❌ Ledger not found: {ledger_path}")
    sys.exit(1)

events = []
errors = 0

with open(ledger_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as e:
            errors += 1
            if errors <= 3:  # Show first 3 errors only
                print(f"⚠️ Line {i}: {e}")

print(f"\n📊 Ledger Stats:")
print(f"Total events: {len(events)}")
print(f"Parse errors: {errors}")

# Check recent 20 events
recent = events[-20:]
with_metrics = sum(1 for e in recent if 'metrics' in e and e.get('metrics'))

print(f"\n🎯 Recent 20 Events:")
print(f"With metrics: {with_metrics}/{len(recent)} ({with_metrics/len(recent)*100:.1f}%)")

# Show sample metrics
if with_metrics > 0:
    sample = next(e for e in reversed(recent) if 'metrics' in e and e.get('metrics'))
    print(f"\n📋 Sample Metrics:")
    print(f"Event: {sample.get('event', 'N/A')}")
    print(f"Action: {sample.get('action', 'N/A')}")
    print(f"Metrics keys: {list(sample['metrics'].keys())}")
    
    # Calculate improvement
    all_with_metrics = sum(1 for e in events if 'metrics' in e and e.get('metrics'))
    print(f"\n🚀 Overall Coverage:")
    print(f"With metrics: {all_with_metrics}/{len(events)} ({all_with_metrics/len(events)*100:.1f}%)")
