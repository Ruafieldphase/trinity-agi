import json

events = [json.loads(line) for line in open('d:/nas_backup/fdo_agi_repo/memory/resonance_ledger.jsonl', encoding='utf-8') if line.strip()]
runes = [e for e in events if e.get('event') == 'rune']
real_runes = [r for r in runes if 'batch_val' not in r.get('task_id', '') and 'test_' not in r.get('task_id', '')]
replans = [r for r in real_runes if r.get('replan') is True]

print(f'Total RUNE: {len(runes)}')
print(f'Real RUNE: {len(real_runes)}')
print(f'Real Replans: {len(replans)} ({len(replans)/len(real_runes)*100:.1f}%)')

if real_runes:
    print(f'\nSample real task_ids:')
    for r in real_runes[:5]:
        print(f"  {r.get('task_id')}: replan={r.get('replan')}, quality={r.get('quality', 'N/A')}")
