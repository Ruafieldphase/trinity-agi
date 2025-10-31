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

# Get task_ids with evidence_gate
eg_task_ids = set(e['task_id'] for e in windowed_events if e.get('event') == 'evidence_gate_triggered' and e.get('task_id'))

# For each evidence_gate task, check if it has valid symmetry (synthesis_end before evidence_gate)
task_timestamps = {}
for e in windowed_events:
    tid = e.get('task_id')
    if not tid:
        continue
    if tid not in task_timestamps:
        task_timestamps[tid] = {}
    
    et = e.get('event')
    ts_val = e.get('ts') or e.get('timestamp')
    
    if et == 'synthesis_end':
        task_timestamps[tid]['synthesis_end'] = ts_val
    elif et == 'evidence_gate_triggered':
        task_timestamps[tid]['evidence_gate'] = ts_val

# Check which tasks have valid symmetry (synthesis_end < evidence_gate)
valid_symmetry_tasks = set()
for tid in eg_task_ids:
    ts_map = task_timestamps.get(tid, {})
    s_end = ts_map.get('synthesis_end')
    eg_time = ts_map.get('evidence_gate')
    
    if s_end and eg_time:
        if eg_time >= s_end:  # Valid order
            valid_symmetry_tasks.add(tid)

print(f"Evidence gate triggered: {len(eg_task_ids)}")
print(f"With valid symmetry (synthesis_end < evidence_gate): {len(valid_symmetry_tasks)}")

# Get second_pass events
sp_task_ids = set(e['task_id'] for e in windowed_events if e.get('event') == 'second_pass' and e.get('task_id'))

# Check overlap
overlap_all_eg = eg_task_ids.intersection(sp_task_ids)
overlap_valid_sym = valid_symmetry_tasks.intersection(sp_task_ids)

print(f"\nSecond pass in all evidence_gate tasks: {len(overlap_all_eg)} ({100*len(overlap_all_eg)/len(eg_task_ids):.1f}%)")
print(f"Second pass in valid symmetry tasks: {len(overlap_valid_sym)} ({100*len(overlap_valid_sym)/len(valid_symmetry_tasks):.1f}% if {len(valid_symmetry_tasks)}))")
