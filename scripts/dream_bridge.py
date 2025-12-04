#!/usr/bin/env python3
"""
Dream Bridge: ingest dreams.jsonl from Dream Mode and append salient entries to resonance_ledger.jsonl.

Usage:
  python scripts/dream_bridge.py \
    --dreams-path outputs/dreams.jsonl \
    --ledger-path fdo_agi_repo/memory/resonance_ledger.jsonl \
    --max-entries 50 \
    --min-delta 0.25
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Set


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Bridge dream logs into resonance ledger")
    p.add_argument("--workspace", default="C:/workspace/agi", help="Workspace root")
    p.add_argument("--dreams-path", default="outputs/dreams.jsonl", help="Relative path to dreams jsonl")
    p.add_argument("--ledger-path", default="fdo_agi_repo/memory/resonance_ledger.jsonl", help="Relative path to resonance ledger")
    p.add_argument("--max-entries", type=int, default=50, help="How many dream lines to consider from the tail")
    p.add_argument("--min-delta", type=float, default=0.25, help="Minimum avg_delta to treat as salient")
    p.add_argument("--tag", type=str, default="", help="Optional tag to attach to dream events")
    return p.parse_args()


def tail_lines(path: Path, max_lines: int) -> List[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if max_lines and max_lines > 0:
        return lines[-max_lines:]
    return lines


def load_existing_ids(ledger_path: Path) -> Set[str]:
    ids: Set[str] = set()
    if not ledger_path.exists():
        return ids
    for line in ledger_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        did = obj.get("dream_id")
        if isinstance(did, str):
            ids.add(did)
    return ids


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace)
    dreams_path = workspace / args.dreams_path
    ledger_path = workspace / args.ledger_path

    tail = tail_lines(dreams_path, args.max_entries)
    if not tail:
        print(f"[WARN] No dreams found at {dreams_path}")
        return 0

    existing_ids = load_existing_ids(ledger_path)

    appended = 0
    entries: List[str] = []
    for line in tail:
        try:
            obj: Dict[str, Any] = json.loads(line)
        except Exception:
            continue
        did = obj.get("dream_id")
        if not isinstance(did, str):
            continue
        if did in existing_ids:
            continue

        avg_delta = float(obj.get("avg_delta") or 0.0)
        interesting = bool(obj.get("interesting"))
        if not interesting and avg_delta < args.min_delta:
            continue

        event = {
            "event": "dream_episode",
            "dream_id": did,
            "timestamp": obj.get("timestamp"),
            "narrative": obj.get("narrative"),
            "recombinations": obj.get("recombinations"),
            "patterns": obj.get("patterns"),
            "avg_delta": avg_delta,
            "interesting": interesting,
            "params": obj.get("params"),
        }
        if args.tag:
            event["tag"] = args.tag
        entries.append(json.dumps(event, ensure_ascii=False))
        appended += 1

    if appended == 0:
        print("[INFO] No new dream episodes appended (filtered or already present).")
        return 0

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as f:
        for line in entries:
            f.write(line + "\n")

    print(f"[OK] Appended {appended} dream episode(s) to {ledger_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
