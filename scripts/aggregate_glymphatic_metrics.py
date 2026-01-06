"""
Glymphatic telemetry aggregator.

Reads JSONL ledger written by AdaptiveGlymphaticSystem and summarizes the
last N hours of operation into a compact JSON summary.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_LEDGER = Path("fdo_agi_repo/memory/glymphatic_ledger.jsonl")
DEFAULT_SUMMARY = Path("outputs/glymphatic_metrics_latest.json")


def _load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _to_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, (int, float)):
        # assume unix seconds
        try:
            return datetime.fromtimestamp(float(value))
        except Exception:
            return None
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None
    return None


def summarize(entries: Iterable[Dict[str, Any]], hours: int) -> Dict[str, Any]:
    cutoff = datetime.now() - timedelta(hours=hours)
    items: List[Dict[str, Any]] = []
    for e in entries:
        ts = _to_dt(e.get("timestamp")) or _to_dt(e.get("ts"))
        if ts is None or ts < cutoff:
            continue
        items.append(e)

    summary: Dict[str, Any] = {
        "hours": hours,
        "events": len(items),
        "decisions": 0,
        "cleanup_start": 0,
        "cleanup_end": 0,
        "cleanup_success": 0,
        "avg_cleanup_duration_sec": None,
        "avg_workload_percent": None,
        "avg_fatigue_level": None,
        "avg_adjusted_fatigue": None,
        "decisions_by_action": {},
        "last_activity": None,
    }

    if not items:
        return summary

    # Sort by ts for last_activity
    def _get_ts(obj: Dict[str, Any]) -> float:
        ts = obj.get("ts")
        if isinstance(ts, (int, float)):
            return float(ts)
        dt = _to_dt(obj.get("timestamp"))
        return dt.timestamp() if dt else 0.0

    items.sort(key=_get_ts)
    last_dt = _to_dt(items[-1].get("timestamp")) or _to_dt(items[-1].get("ts"))
    if last_dt:
        summary["last_activity"] = last_dt.isoformat()

    # Accumulators
    durations: List[float] = []
    workloads: List[float] = []
    fatigues: List[float] = []
    adjusted_fatigues: List[float] = []

    for e in items:
        ev = e.get("event")
        if ev == "decision":
            summary["decisions"] += 1
            payload = e.get("payload", {})
            action = str(payload.get("decision_action", "unknown"))
            summary["decisions_by_action"][action] = (
                summary["decisions_by_action"].get(action, 0) + 1
            )
            try:
                wp = float(payload.get("workload_percent"))
                workloads.append(wp)
            except Exception:
                pass
            try:
                fl = float(payload.get("fatigue_level"))
                fatigues.append(fl)
            except Exception:
                pass
            try:
                afl = float(payload.get("adjusted_fatigue"))
                adjusted_fatigues.append(afl)
            except Exception:
                pass
        elif ev == "cleanup_start":
            summary["cleanup_start"] += 1
        elif ev == "cleanup_end":
            summary["cleanup_end"] += 1
            payload = e.get("payload", {})
            if payload.get("success") is True:
                summary["cleanup_success"] += 1
            try:
                dur = float(payload.get("duration"))
                durations.append(dur)
            except Exception:
                pass

    def _avg(values: List[float]) -> Optional[float]:
        return round(sum(values) / len(values), 3) if values else None

    summary["avg_cleanup_duration_sec"] = _avg(durations)
    summary["avg_workload_percent"] = _avg(workloads)
    summary["avg_fatigue_level"] = _avg(fatigues)
    summary["avg_adjusted_fatigue"] = _avg(adjusted_fatigues)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate glymphatic telemetry")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--json", action="store_true", help="print JSON summary to stdout")
    args = parser.parse_args()

    entries = list(_load_jsonl(args.ledger))
    summary = summarize(entries, args.hours)

    args.summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(args.summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        # brief human-readable output
        print(
            f"Glymphatic Summary (last {summary['hours']}h): events={summary['events']} decisions={summary['decisions']} "
            f"cleanup_success={summary['cleanup_success']}/{summary['cleanup_end']} avg_dur={summary['avg_cleanup_duration_sec']}s"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

