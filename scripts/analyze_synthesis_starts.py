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

# Get second_pass tasks
sp_tasks = set(e.get('task_id') for e in windowed_events if e.get('event') == 'second_pass' and e.get('task_id'))

if sp_tasks:
    sample_task = list(sp_tasks)[0]
    print(f"Sample second_pass task: {sample_task}\n")
    
    task_events = [e for e in windowed_events if e.get('task_id') == sample_task]
    task_events.sort(key=lambda e: e.get('ts') or 0)
    
    print("Event sequence (synthesis and antithesis only):")
    for e in task_events:
        evt = e.get('event')
        ts = e.get('ts')
        if 'synthesis' in evt or 'antithesis' in evt or evt in ('evidence_gate_triggered', 'second_pass'):
            print(f"  {ts:.3f}: {evt}")
