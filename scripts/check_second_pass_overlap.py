import json
from datetime import datetime, timedelta

with open('c:/workspace/agi/fdo_agi_repo/memory/resonance_ledger.jsonl', 'r', encoding='utf-8') as f:
    events = [json.loads(line) for line in f]

now = datetime.now()
since = now - timedelta(hours=168)

# Filter by time window
windowed_events = []
for e in events:
    ts_val = e.get('ts') or e.get('timestamp')
    if not ts_val:
        continue
    try:
        if isinstance(ts_val, (int, float)):
            evt_dt = datetime.fromtimestamp(ts_val)
        else:
            evt_dt = datetime.fromisoformat(str(ts_val).replace('Z', '+00:00'))
        
        if evt_dt >= since:
            windowed_events.append(e)
    except:
        continue

print(f"Total events in 7-day window: {len(windowed_events)}")

# Get task_ids with complete loops (evidence_gate_triggered)
complete_task_ids = set(e['task_id'] for e in windowed_events if e.get('event') == 'evidence_gate_triggered' and e.get('task_id'))
print(f"Tasks with evidence_gate_triggered: {len(complete_task_ids)}")

# Get second_pass events in window
sp_events = [e for e in windowed_events if e.get('event') == 'second_pass']
sp_task_ids = set(e['task_id'] for e in sp_events if e.get('task_id'))
print(f"second_pass events in window: {len(sp_events)}")
print(f"Unique task_ids with second_pass: {len(sp_task_ids)}")

# Check overlap
overlap = complete_task_ids.intersection(sp_task_ids)
print(f"\nTasks with both evidence_gate AND second_pass: {len(overlap)}")

# Show sample task_ids
print(f"\nSample complete task_ids (first 3): {list(complete_task_ids)[:3]}")
print(f"Sample second_pass task_ids (first 3): {list(sp_task_ids)[:3]}")
