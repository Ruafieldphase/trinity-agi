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

# Get a sample task with second_pass and evidence_gate
eg_and_sp_tasks = []
for tid in set(e.get('task_id') for e in windowed_events if e.get('task_id')):
    task_events = [e for e in windowed_events if e.get('task_id') == tid]
    has_eg = any(e.get('event') == 'evidence_gate_triggered' for e in task_events)
    has_sp = any(e.get('event') == 'second_pass' for e in task_events)
    if has_eg and has_sp:
        eg_and_sp_tasks.append(tid)

if eg_and_sp_tasks:
    sample_task = eg_and_sp_tasks[0]
    print(f"Sample task with both evidence_gate and second_pass: {sample_task}\n")
    
    task_events = [e for e in windowed_events if e.get('task_id') == sample_task]
    # Sort by timestamp
    task_events.sort(key=lambda e: e.get('ts') or 0)
    
    print("Event sequence:")
    for e in task_events:
        evt = e.get('event')
        ts = e.get('ts')
        if evt in ('synthesis_start', 'synthesis_end', 'evidence_gate_triggered', 'second_pass'):
            print(f"  {ts:.3f}: {evt}")
else:
    print("No tasks found with both evidence_gate and second_pass")
