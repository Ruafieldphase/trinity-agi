import json
from collections import Counter

with open('c:/workspace/agi/fdo_agi_repo/memory/resonance_ledger.jsonl', 'r', encoding='utf-8') as f:
    events = [json.loads(line) for line in f]

event_types = Counter(e.get('event') for e in events)

print("Event types in ledger:")
for event_type, count in event_types.most_common():
    print(f"  {event_type}: {count}")

# Check for completion-related events
completion_events = [e for e in events if 'complete' in e.get('event', '').lower() or 'finish' in e.get('event', '').lower() or 'done' in e.get('event', '').lower()]
print(f"\nCompletion-related events: {len(completion_events)}")

# Check for evidence_gate events
eg_events = [e for e in events if e.get('event') == 'evidence_gate']
print(f"evidence_gate events: {len(eg_events)}")
if eg_events:
    print(f"Sample evidence_gate event: {eg_events[0]}")
