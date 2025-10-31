import json

with open('c:/workspace/agi/fdo_agi_repo/memory/resonance_ledger.jsonl', 'r', encoding='utf-8') as f:
    events = [json.loads(line) for line in f]

sp_events = [e for e in events if e.get('event') == 'second_pass']
eg_events = [e for e in events if e.get('event') == 'evidence_gate_triggered']

print(f"second_pass events: {len(sp_events)}")
print(f"  With task_id: {len([e for e in sp_events if e.get('task_id')])}")
if sp_events:
    print(f"  Sample: {sp_events[0]}")

print(f"\nevidence_gate_triggered events: {len(eg_events)}")
print(f"  With task_id: {len([e for e in eg_events if e.get('task_id')])}")
if eg_events:
    print(f"  Sample: {eg_events[0]}")
