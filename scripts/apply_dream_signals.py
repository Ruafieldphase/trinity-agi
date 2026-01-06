#!/usr/bin/env python3
"""
Apply dream signals from dream episodes and emit a lightweight risk/creativity summary.

Reads:
  - outputs/dream_episodes_latest.json (or resonance_ledger.jsonl fallback)
Writes:
  - outputs/dream_signal_latest.json

Usage:
  python scripts/apply_dream_signals.py \
    --workspace <workspace_root> \
    --episodes outputs/dream_episodes_latest.json \
    --out outputs/dream_signal_latest.json \
    --high-threshold 1e9 \
    --medium-threshold 1e6
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from workspace_root import get_workspace_root


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Apply dream signals to produce risk/creativity summary")
    p.add_argument("--workspace", default=str(get_workspace_root()), help="Workspace root")
    p.add_argument("--episodes", default="outputs/dream_episodes_latest.json", help="Path to dream episodes summary JSON")
    p.add_argument("--out", default="outputs/dream_signal_latest.json", help="Output path for dream signal")
    p.add_argument("--high-threshold", type=float, default=1e9, help="High risk/energy threshold for avg_delta")
    p.add_argument("--medium-threshold", type=float, default=1e6, help="Medium risk/energy threshold for avg_delta")
    return p.parse_args()


def load_episodes(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def classify(max_delta: float, high: float, medium: float) -> str:
    if max_delta >= high:
        return "high"
    if max_delta >= medium:
        return "medium"
    return "low"


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace)
    episodes_path = workspace / args.episodes
    out_path = workspace / args.out

    episodes = load_episodes(episodes_path)
    dreams: List[Dict[str, Any]] = episodes.get("dreams") or []
    max_delta = float(episodes.get("max_avg_delta") or 0.0)
    signal_level = classify(max_delta, args.high_threshold, args.medium_threshold)

    signal = {
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": str(episodes_path),
        "count": len(dreams),
        "max_avg_delta": max_delta,
        "signal_level": signal_level,
        "tags": episodes.get("tags") or {},
        "latest_timestamp": episodes.get("latest_timestamp"),
        "window_hours": episodes.get("window_hours"),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(signal, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Dream signal written → {out_path} (level={signal_level}, max_delta={max_delta})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
