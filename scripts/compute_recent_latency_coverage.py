#!/usr/bin/env python3
import json, pathlib, sys
from workspace_root import get_workspace_root
from statistics import mean

LEDGER = get_workspace_root() / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
COUNT = 50
if not LEDGER.exists():
    print('Ledger not found:', LEDGER)
    sys.exit(1)
lines = [json.loads(l) for l in LEDGER.read_text(encoding='utf-8').splitlines()[-COUNT:] if l.strip()]
lat_present = [o for o in lines if 'latency_ms' in o]
coverage = (len(lat_present)/len(lines)*100) if lines else 0.0
avg_latency = mean([o['latency_ms'] for o in lat_present if isinstance(o.get('latency_ms'), (int,float))]) if lat_present else 0.0
print(f'Last {len(lines)} entries: latency_ms present {len(lat_present)} ({coverage:.1f}%), avg_latency_ms={avg_latency:.1f}')
