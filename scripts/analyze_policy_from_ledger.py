"""
Analyze resonance policy outcomes from resonance_ledger.jsonl

Produces per-policy counts and latency statistics without running the pipeline.

Usage:
  python scripts/analyze_policy_from_ledger.py [--lines 10000] [--out outputs/policy_ab_summary_latest.json]
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from statistics import mean

LEDGER_PATH = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--lines", type=int, default=20000, help="Tail N lines to analyze")
    p.add_argument("--out", type=str, default="outputs/policy_ab_summary_latest.json", help="Output JSON path")
    return p.parse_args()


def tail_lines(path: Path, n: int) -> list[str]:
    if not path.exists():
        return []
    # Efficient tail: read all if small, else read and slice
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if n <= 0 or len(lines) <= n:
        return lines
    return lines[-n:]


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = int(round(0.95 * (len(s) - 1)))
    return float(s[idx])


def main():
    args = parse_args()
    lines = tail_lines(LEDGER_PATH, args.lines)
    if not lines:
        print("No ledger lines found.")
        return

    by_policy: dict[str, dict] = {}
    for line in lines:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("event") != "resonance_policy":
            continue
        pol = str(obj.get("policy") or "unknown")
        observed = obj.get("observed") or {}
        lat_ms = float(observed.get("latency_ms") or 0.0)
        action = str(obj.get("action") or "").lower()

        rec = by_policy.setdefault(pol, {
            "count": 0,
            "allow": 0,
            "warn": 0,
            "block": 0,
            "latencies_ms": [],
        })
        rec["count"] += 1
        if action in ("allow", "warn", "block"):
            rec[action] += 1
        if lat_ms > 0:
            rec["latencies_ms"].append(lat_ms)

    # Aggregate stats
    summary: dict[str, dict] = {}
    for pol, rec in by_policy.items():
        lats = rec["latencies_ms"]
        summary[pol] = {
            "count": rec["count"],
            "allow": rec["allow"],
            "warn": rec["warn"],
            "block": rec["block"],
            "avg_latency_ms": float(mean(lats)) if lats else 0.0,
            "p95_latency_ms": float(p95(lats)) if lats else 0.0,
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "source": str(LEDGER_PATH),
        "analyzed_lines": len(lines),
        "policies": summary,
    }
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Summary written: {out_path}")
    # Also print concise text for quick glance
    for pol, s in summary.items():
        print(f"- {pol}: count={s['count']} allow={s['allow']} warn={s['warn']} block={s['block']} avg={s['avg_latency_ms']:.0f}ms p95={s['p95_latency_ms']:.0f}ms")


if __name__ == "__main__":
    main()

