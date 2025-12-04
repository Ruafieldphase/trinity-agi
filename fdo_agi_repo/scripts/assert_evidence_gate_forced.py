#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Assert that forced evidence_correction events occurred recently and added > 0.
- Scans the resonance_ledger.jsonl for evidence_correction events within --last-hours
- By default requires forced=true and at least --min-added citations added
- Prints a concise summary and exits with non-zero code on failure
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_LEDGER = Path(__file__).resolve().parent.parent / "memory" / "resonance_ledger.jsonl"

def load_events(ledger_path: Path) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    if not ledger_path.exists():
        print(f"ERROR: Ledger not found: {ledger_path}")
        return events
    try:
        with ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    events.append(obj)
                except json.JSONDecodeError:
                    # skip malformed line
                    continue
    except Exception as e:
        print(f"ERROR: Failed to read ledger: {type(e).__name__}: {e}")
    return events


def summarize_forced_evidence(
    events: List[Dict[str, Any]], *,
    last_hours: float = 24.0,
    min_added: int = 1,
    require_forced: bool = True,
    print_samples: int = 3,
) -> int:
    now = time.time()
    cutoff = now - last_hours * 3600.0

    evs = [e for e in events if e.get("event") == "evidence_correction" and float(e.get("ts", 0)) >= cutoff]
    if require_forced:
        evs = [e for e in evs if bool(e.get("forced"))]

    attempts = len(evs)
    successes = sum(1 for e in evs if int(e.get("added", 0)) >= min_added)
    avg_hits = (sum(float(e.get("hits", 0)) for e in evs) / attempts) if attempts else 0.0
    avg_added = (sum(float(e.get("added", 0)) for e in evs) / attempts) if attempts else 0.0
    success_rate = (successes / attempts) if attempts else 0.0

    print("--- Forced Evidence Gate Assertion ---")
    print(f"Window       : last {last_hours}h (cutoff ts={cutoff:.0f})")
    print(f"Filter       : require_forced={require_forced}, min_added={min_added}")
    print(f"Attempts     : {attempts}")
    print(f"Successes    : {successes}")
    print(f"Success Rate : {success_rate:.3f}")
    print(f"Avg Hits     : {avg_hits:.2f}")
    print(f"Avg Added    : {avg_added:.2f}")

    if print_samples and evs:
        print("Samples:")
        for e in evs[-print_samples:]:
            tid = e.get("task_id", "?")
            hits = e.get("hits")
            added = e.get("added")
            forced = e.get("forced")
            rtot = e.get("rag_total_found")
            ts = e.get("ts")
            print(f"  - task_id={tid} forced={forced} hits={hits} added={added} rag_total_found={rtot} ts={ts}")

    if successes > 0:
        print("STATUS: PASS (found at least one forced evidence_correction with added >= min_added)")
        return 0
    if attempts == 0:
        print("STATUS: FAIL (no forced evidence_correction attempts in window)")
    else:
        print("STATUS: FAIL (attempts present but none added enough citations)")
    return 1


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description="Assert forced evidence_correction presence in ledger")
    p.add_argument("--ledger-path", type=str, default=str(DEFAULT_LEDGER), help="Path to resonance_ledger.jsonl")
    p.add_argument("--last-hours", type=float, default=24.0, help="Time window to scan")
    p.add_argument("--min-added", type=int, default=1, help="Minimum added citations to count as success")
    p.add_argument("--no-require-forced", action="store_true", help="Do not require forced=true")
    p.add_argument("--print-samples", type=int, default=3, help="Number of sample events to print")
    args = p.parse_args(argv)

    ledger_path = Path(args.ledger_path)
    events = load_events(ledger_path)
    code = summarize_forced_evidence(
        events,
        last_hours=args.last_hours,
        min_added=args.min_added,
        require_forced=(not args.no_require_forced),
        print_samples=args.print_samples,
    )
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
