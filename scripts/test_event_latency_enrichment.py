#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test: Event latency auto-enrichment

- Emits thesis_start -> thesis_end with ~100ms sleep
- Emits task_started -> task_completed with ~150ms sleep
- Emits synthesis_start -> synthesis_end using context manager

Prints the last few ledger records and checks for latency_ms presence.
"""
import json
import os
import sys
import time
from pathlib import Path

# Ensure repo root in sys.path for import
REPO_ROOT = Path(__file__).resolve().parents[1]
FDO_ROOT = REPO_ROOT / 'fdo_agi_repo'
if str(FDO_ROOT) not in sys.path:
    sys.path.insert(0, str(FDO_ROOT))

from orchestrator.event_emitter import emit_event, timed_event  # type: ignore

LEDGER_PATH = FDO_ROOT / 'memory' / 'resonance_ledger.jsonl'


def tail_ledger(n=6):
    if not LEDGER_PATH.exists():
        return []
    # Efficient tail read
    lines = LEDGER_PATH.read_text(encoding='utf-8').strip().splitlines()
    return lines[-n:]


def main():
    print(f"Ledger: {LEDGER_PATH}")

    # 1) Pair: thesis
    emit_event('thesis_start', { 'component': 'test_enrichment', 'case': 'thesis_pair' }, task_id='t-enrich-1')
    time.sleep(0.10)
    emit_event('thesis_end',   { 'component': 'test_enrichment', 'case': 'thesis_pair' }, task_id='t-enrich-1')

    # 2) Pair: task
    emit_event('task_started', { 'component': 'test_enrichment', 'case': 'task_pair' }, task_id='t-enrich-2')
    time.sleep(0.15)
    emit_event('task_completed', { 'component': 'test_enrichment', 'case': 'task_pair' }, task_id='t-enrich-2')

    # 3) Context manager: synthesis
    with timed_event('synthesis', task_id='t-enrich-3', payload={ 'component': 'test_enrichment', 'case': 'ctx_manager' }):
        time.sleep(0.05)

    print("\nLast 6 ledger entries:")
    for line in tail_ledger(6):
        try:
            obj = json.loads(line)
        except Exception:
            print(line)
            continue
        subset = {
            'ts': obj.get('ts'),
            'event_type': obj.get('event_type'),
            'task_id': obj.get('task_id'),
            'latency_ms': obj.get('latency_ms'),
            'component': obj.get('component'),
            'case': obj.get('case'),
        }
        print(json.dumps(subset, ensure_ascii=False))


if __name__ == '__main__':
    main()
