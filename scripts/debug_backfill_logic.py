#!/usr/bin/env python3
"""
Debug backfill logic by checking timestamp extraction and phase estimation
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict

LEDGER_PATH = Path(r"c:\workspace\agi\fdo_agi_repo\memory\resonance_ledger.jsonl")

def parse_timestamp(ts_val: Any) -> datetime:
    if isinstance(ts_val, (int, float)):
        return datetime.fromtimestamp(ts_val)
    else:
        return datetime.fromisoformat(str(ts_val).replace("Z", "+00:00"))

with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
    events = [json.loads(l) for l in f if l.strip()]

# Filter to last 7 days
now = datetime.now()
since = now - timedelta(hours=168)

recent_events = []
for ev in events:
    ts_val = ev.get("timestamp") or ev.get("ts")
    if ts_val:
        try:
            dt = parse_timestamp(ts_val)
            if dt >= since:
                recent_events.append(ev)
        except:
            pass

print(f"Total events: {len(events)}")
print(f"Recent events (last 7 days): {len(recent_events)}")

# Find a task with thesis/antithesis/synthesis events
task_events = {}
for ev in recent_events:
    tid = ev.get('task_id')
    event_type = ev.get('event')
    if tid and event_type in ('thesis_start', 'thesis_end', 'antithesis_start', 'antithesis_end', 
                                'synthesis_start', 'synthesis_end'):
        if tid not in task_events:
            task_events[tid] = []
        task_events[tid].append((event_type, ev.get('timestamp') or ev.get('ts')))

print(f"\nTasks with dialectic events: {len(task_events)}")

# Show one complete example
for tid, evs in list(task_events.items())[:3]:
    print(f"\nTask {tid[:40]}:")
    for event_type, ts in evs:
        print(f"  {event_type}: {ts}")
    
    # Try to extract timestamps
    ts_map = {et: ts for et, ts in evs}
    
    if 'thesis_start' in ts_map and 'thesis_end' in ts_map:
        try:
            t_start = parse_timestamp(ts_map['thesis_start'])
            t_end = parse_timestamp(ts_map['thesis_end'])
            duration = (t_end - t_start).total_seconds()
            print(f"  -> Folding duration: {duration:.3f} sec")
        except Exception as e:
            print(f"  -> Folding calculation failed: {e}")
