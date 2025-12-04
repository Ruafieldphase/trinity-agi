#!/usr/bin/env python3
"""Check ensemble_decision events in ledger"""
import json
from datetime import datetime, timedelta
from pathlib import Path

ledger_path = Path(__file__).parent.parent / "memory" / "resonance_ledger.jsonl"

events = []
with open(ledger_path, encoding='utf-8') as f:
    for line in f:
        if line.strip():
            events.append(json.loads(line))

# All ensemble events
ens_events = [e for e in events 
              if e.get('type') == 'binoche_decision' 
              and 'ensemble_decision' in e]

print(f"전체 ensemble_decision 이벤트: {len(ens_events)}개")
if ens_events:
    first_ts = ens_events[0].get('timestamp', 0)
    last_ts = ens_events[-1].get('timestamp', 0)
    first_dt = datetime.fromtimestamp(first_ts).strftime('%Y-%m-%d %H:%M:%S')
    last_dt = datetime.fromtimestamp(last_ts).strftime('%Y-%m-%d %H:%M:%S')
    print(f"첫 이벤트: {first_dt}")
    print(f"마지막 이벤트: {last_dt}")
    
    # Recent 24h
    cutoff = (datetime.now() - timedelta(hours=24)).timestamp()
    recent = [e for e in ens_events if e.get('timestamp', 0) > cutoff]
    print(f"\n24h 내 이벤트: {len(recent)}개")
    
    # Show sample
    print("\n샘플 5개:")
    for e in ens_events[:5]:
        tid = e.get('task_id', '')
        ens = e.get('ensemble_decision', {})
        outcome = e.get('final_outcome', '')
        print(f"  {tid} - decision={ens.get('decision')} conf={ens.get('confidence'):.2f} - outcome={outcome}")
