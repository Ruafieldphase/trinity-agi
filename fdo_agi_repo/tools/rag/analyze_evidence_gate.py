#!/usr/bin/env python3
"""Analyze recent evidence_correction events and their task flows"""
import json
from pathlib import Path

from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from workspace_utils import find_fdo_root

fdo_root = find_fdo_root(Path(__file__).parent)
ledger = fdo_root / "memory" / "resonance_ledger.jsonl"
if not ledger.exists():
    print("Ledger not found")
    exit(1)

# Find last 3 evidence_correction events
evidence_events = []
with open(ledger, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            event = json.loads(line.strip())
            if event.get("event") == "evidence_correction":
                evidence_events.append(event)
        except:
            continue

recent = evidence_events[-3:] if len(evidence_events) >= 3 else evidence_events

for ev in recent:
    task_id = ev.get("task_id")
    print(f"\n{'='*70}")
    print(f"Task ID: {task_id}")
    print(f"Evidence Correction: hits={ev.get('hits')}, added={ev.get('added')}, fallback={ev.get('fallback_used')}")
    print(f"  rag_initial_total_found: {ev.get('rag_initial_total_found')}")
    print(f"  rag_total_found: {ev.get('rag_total_found')}")
    
    # Get all events for this task
    task_events = []
    with open(ledger, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                e = json.loads(line.strip())
                if e.get("task_id") == task_id:
                    task_events.append(e)
            except:
                continue
    
    print(f"\nTask Flow ({len(task_events)} events):")
    for e in task_events:
        evt = e.get("event")
        if evt == "eval":
            print(f"  [{evt}] evidence_ok={e.get('evidence_ok')}, quality={e.get('quality')}")
        elif evt == "synthesis_end":
            # Can't see citations count here, but thesis would have added them
            print(f"  [{evt}]")
        elif evt == "persona_llm_run" and e.get("persona") == "thesis":
            print(f"  [thesis_llm_run] ok={e.get('ok')}")
        elif evt == "evidence_correction":
            print(f"  [{evt}] hits={e.get('hits')}, added={e.get('added')}")
        elif evt in ["task_start", "thesis_start", "thesis_end", "synthesis_start"]:
            print(f"  [{evt}]")
