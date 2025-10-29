import json

lines = open('d:/nas_backup/fdo_agi_repo/memory/resonance_ledger.jsonl', encoding='utf-8').readlines()
print(f'Total lines: {len(lines)}')

recent = [json.loads(l) for l in lines[-100:]]
thesis_events = [e for e in recent if 'thesis_end' in e.get('event', '')]
synth_events = [e for e in recent if 'synthesis_end' in e.get('event', '')]

print(f'\nRecent thesis_end events with citations:')
for e in thesis_events[-5:]:
    print(f"  task={e.get('task_id', 'N/A')[:40]:40s} citations={e.get('citations', 'N/A')}")

print(f'\nRecent synthesis_end events with citations:')
for e in synth_events[-5:]:
    print(f"  task={e.get('task_id', 'N/A')[:40]:40s} citations={e.get('citations', 'N/A')}")
