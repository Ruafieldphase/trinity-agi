#!/usr/bin/env python3
"""
Summarize dream episodes from resonance_ledger.jsonl.

Usage:
  python scripts/summarize_dream_episodes.py \
    --workspace <workspace_root> \
    --ledger fdo_agi_repo/memory/resonance_ledger.jsonl \
    --out outputs/dream_episodes_latest.json \
    --hours 72 \
    --limit 50
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from workspace_root import get_workspace_root


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize dream episodes from resonance ledger")
    p.add_argument("--workspace", default=str(get_workspace_root()), help="Workspace root")
    p.add_argument("--ledger", default="fdo_agi_repo/memory/resonance_ledger.jsonl", help="Relative path to resonance ledger")
    p.add_argument("--out", default="outputs/dream_episodes_latest.json", help="Output summary JSON")
    p.add_argument("--hours", type=int, default=72, help="Lookback window in hours")
    p.add_argument("--limit", type=int, default=50, help="Maximum episodes to include")
    return p.parse_args()


def load_dreams(ledger_path: Path, since: datetime, limit: int) -> List[Dict[str, Any]]:
    dreams: List[Dict[str, Any]] = []
    if not ledger_path.exists():
        return dreams
    for line in ledger_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("event") != "dream_episode":
            continue
        ts_raw = obj.get("timestamp")
        try:
            ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
        except Exception:
            continue
        if ts < since:
            continue
        dreams.append(obj)
    dreams.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return dreams[:limit]


def summarize(dreams: List[Dict[str, Any]]) -> Dict[str, Any]:
    tags = {}
    max_delta = 0.0
    for d in dreams:
        tag = d.get("tag") or "untagged"
        tags[tag] = tags.get(tag, 0) + 1
        try:
            max_delta = max(max_delta, float(d.get("avg_delta") or 0.0))
        except Exception:
            pass
    return {
        "count": len(dreams),
        "tags": tags,
        "max_avg_delta": max_delta,
        "latest_timestamp": dreams[0].get("timestamp") if dreams else None,
    }


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace)
    ledger_path = workspace / args.ledger
    out_path = workspace / args.out

    since = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    dreams = load_dreams(ledger_path, since, args.limit)
    summary = summarize(dreams)
    summary["window_hours"] = args.hours
    summary["limit"] = args.limit
    summary["dreams"] = dreams

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Wrote {len(dreams)} dream episodes to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
