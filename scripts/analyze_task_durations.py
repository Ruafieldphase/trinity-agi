#!/usr/bin/env python3
"""
Analyze task duration breakdown
"""
import json
from pathlib import Path

ledger_path = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")

target_tasks = ['runtime-test-001', 'test-ledger']
events = []

with open(ledger_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            e = json.loads(line)
            task_id = e.get('task_id', '')
            if any(t in task_id for t in target_tasks):
                events.append(e)
        except:
            pass

print(f"Found {len(events)} events for target tasks")

# Group by task_id and analyze durations
from collections import defaultdict
by_task = defaultdict(list)

for e in events:
    if 'duration_sec' in e:
        task_id = e.get('task_id', 'unknown')
        event_type = e.get('event', 'unknown')
        duration = e.get('duration_sec', 0)
        by_task[task_id].append((event_type, duration))

print(f"\nTask count: {len(by_task)}")

for task_id, durations in list(by_task.items())[:5]:
    print(f"\n=== {task_id} ===")
    for event_type, duration in durations:
        print(f"  {event_type}: {duration:.2f}s")
    total = sum(d for _, d in durations)
    print(f"  TOTAL: {total:.2f}s")
