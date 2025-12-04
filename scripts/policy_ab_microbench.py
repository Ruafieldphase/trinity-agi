"""
Policy A/B Micro-Benchmark (synthetic replay)

Re-evaluates recent tasks from resonance_ledger.jsonl under multiple policies
using their recorded quality/evidence and observed latency, without re-running
the pipeline. Useful for fast comparison between 'quality-first' and
'latency-first' (or any policies present in configs/resonance_config.json).

Outputs JSON summary to outputs/policy_ab_synthetic_latest.json and prints a
concise summary.

Usage:
  python scripts/policy_ab_microbench.py --lines 50000 \
      --out outputs/policy_ab_synthetic_latest.json \
      --policies quality-first latency-first
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Dict, Any

LEDGER_PATH = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")
CONFIG_PATH = Path("configs/resonance_config.json")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--lines", type=int, default=50000, help="Tail N lines from ledger")
    p.add_argument("--out", type=str, default="outputs/policy_ab_synthetic_latest.json")
    p.add_argument("--policies", nargs="*", default=["quality-first", "latency-first"], help="Policy names to compare")
    return p.parse_args()


def tail_lines(path: Path, n: int) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-n:] if n > 0 and len(lines) > n else lines


def load_config(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def evaluate(policy: Dict[str, Any], quality: float, evidence_ok: bool, latency_ms: float) -> Dict[str, Any]:
    min_q = float(policy.get("min_quality", 0.8))
    req_ev = bool(policy.get("require_evidence", True))
    max_lat = float(policy.get("max_latency_ms", 8000))
    reasons = []
    if quality < min_q:
        reasons.append(f"quality {quality:.2f} < min_quality {min_q:.2f}")
    if req_ev and not evidence_ok:
        reasons.append("evidence_required_but_missing")
    if latency_ms > max_lat:
        reasons.append(f"latency {latency_ms:.0f}ms > max_latency_ms {max_lat:.0f}ms")
    action = "allow" if not reasons else "warn"
    return {
        "action": action,
        "reasons": reasons,
    }


def main():
    args = parse_args()
    cfg = load_config(CONFIG_PATH)
    policies: Dict[str, Dict[str, Any]] = cfg.get("policies", {})

    # Collect last eval per task and observed latency
    lines = tail_lines(LEDGER_PATH, args.lines)
    eval_by_task: Dict[str, Dict[str, Any]] = {}
    latency_by_task: Dict[str, float] = {}

    for line in lines:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("event") == "eval":
            tid = str(obj.get("task_id"))
            ev = obj.get("eval") or {}
            # Keep last
            eval_by_task[tid] = {
                "quality": float((ev or {}).get("quality") or obj.get("quality") or 0.0),
                "evidence_ok": bool((ev or {}).get("evidence_ok") if ev else obj.get("evidence_ok", False)),
            }
        elif obj.get("event") == "resonance_policy":
            tid = str(obj.get("task_id"))
            ob = obj.get("observed") or {}
            try:
                latency_by_task[tid] = float(ob.get("latency_ms") or 0.0)
            except Exception:
                pass

    # Join tasks having both eval and latency
    tasks: list[Dict[str, Any]] = []
    for tid, ev in eval_by_task.items():
        lat = latency_by_task.get(tid)
        if lat is None:
            continue
        tasks.append({"task_id": tid, **ev, "latency_ms": lat})

    if not tasks:
        print("No tasks with both eval and latency found.")
        return

    # Evaluate under requested policies
    summary: Dict[str, Dict[str, Any]] = {}
    for pol_name in args.policies:
        pol = policies.get(pol_name) or {}
        counts = {"allow": 0, "warn": 0, "block": 0}
        latencies: list[float] = []
        for t in tasks:
            r = evaluate(pol, t["quality"], t["evidence_ok"], t["latency_ms"])
            action = r["action"]
            counts[action] = counts.get(action, 0) + 1
            latencies.append(t["latency_ms"])
        avg_lat = sum(latencies)/len(latencies) if latencies else 0.0
        lat_sorted = sorted(latencies)
        p95 = lat_sorted[int(round(0.95*(len(lat_sorted)-1)))] if lat_sorted else 0.0
        summary[pol_name] = {
            "samples": len(tasks),
            **counts,
            "avg_latency_ms": float(avg_lat),
            "p95_latency_ms": float(p95),
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_obj = {"tasks": len(tasks), "policies": summary}
    out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Synthetic A/B summary written: {out_path}")
    for name, s in summary.items():
        print(f"- {name}: n={s['samples']} allow={s['allow']} warn={s['warn']} avg={s['avg_latency_ms']:.0f}ms p95={s['p95_latency_ms']:.0f}ms")


if __name__ == "__main__":
    main()

