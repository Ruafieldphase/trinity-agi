#!/usr/bin/env python3
import json
from pathlib import Path

ledger_path = Path(r"c:\workspace\agi\fdo_agi_repo\memory\resonance_ledger.jsonl")

with open(ledger_path, 'r', encoding='utf-8') as f:
    lines = [json.loads(l) for l in f if l.strip()]

events_with_task = [e for e in lines if e.get('task_id')]

# Find events with thesis/antithesis/synthesis
thesis_events = [e for e in events_with_task if 'thesis' in e.get('event', '')]
antithesis_events = [e for e in events_with_task if 'antithesis' in e.get('event', '')]
synthesis_events = [e for e in events_with_task if 'synthesis' in e.get('event', '')]

print(f"Total events: {len(lines)}")
print(f"Events with task_id: {len(events_with_task)}")
print(f"Thesis events: {len(thesis_events)}")
print(f"Antithesis events: {len(antithesis_events)}")
print(f"Synthesis events: {len(synthesis_events)}")

print("\nSample thesis events:")
for e in thesis_events[:5]:
    print(f"  {e.get('event')} - task_id={e.get('task_id')[:40]} - ts={e.get('timestamp')}")

print("\nSample antithesis events:")
for e in antithesis_events[:5]:
    print(f"  {e.get('event')} - task_id={e.get('task_id')[:40]} - ts={e.get('timestamp')}")

print("\nSample synthesis events:")
for e in synthesis_events[:5]:
    print(f"  {e.get('event')} - task_id={e.get('task_id')[:40]} - ts={e.get('timestamp')}")
