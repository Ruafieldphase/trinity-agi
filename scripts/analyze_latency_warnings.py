#!/usr/bin/env python3
"""
Analyze latency behaviour and resonance optimization effects from the orchestrator ledger.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Optional, Union, Dict


def _safe_iso(ts: Optional[Union[float, int]]) -> str:
    if not ts:
        return "Unknown timestamp"
    try:
        return datetime.fromtimestamp(float(ts)).isoformat()
    except Exception:
        return f"Invalid timestamp ({ts})"


def _safe_avg(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def _percentile(sorted_vals, pct: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    idx = int(len(sorted_vals) * pct)
    idx = max(0, min(len(sorted_vals) - 1, idx))
    return sorted_vals[idx]


def analyze_latency():
    ledger_path = Path("fdo_agi_repo/memory/resonance_ledger.jsonl")

    if not ledger_path.exists():
        print(f"Error: {ledger_path} not found")
        return 1

    warnings = []
    latency_by_task = defaultdict(list)
    policy_events = []
    optimization_by_task: Dict[str, dict] = {}
    preferred_channel_primary = Counter()
    throttle_adjustments = 0

    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = entry.get("event")
            if event_type == "resonance_optimization":
                task_id = entry.get("task_id")
                if not task_id:
                    continue
                optimization_by_task[task_id] = entry
                channels = entry.get("preferred_channels")
                if isinstance(channels, list) and channels:
                    preferred_channel_primary[str(channels[0])] += 1
                if entry.get("should_throttle_offpeak"):
                    throttle_adjustments += 1
                continue

            if event_type != "resonance_policy":
                continue

            task_id = entry.get("task_id", "unknown")
            observed = entry.get("observed", {}) or {}
            latency_ms = float(observed.get("latency_ms", 0.0) or 0.0)
            action = entry.get("action", "allow")

            opt_info = optimization_by_task.get(task_id)
            policy_events.append(
                {
                    "task_id": task_id,
                    "action": action,
                    "latency_ms": latency_ms,
                    "quality": observed.get("quality"),
                    "evidence_ok": observed.get("evidence_ok"),
                    "ts": entry.get("ts"),
                    "optimization": opt_info,
                }
            )

            latency_by_task[task_id].append(latency_ms)
            if action == "warn":
                warnings.append(entry)

    print("\n=== Latency Warning Analysis ===")
    print(f"Total warnings: {len(warnings)}")
    print(f"Unique tasks with warnings: {len(latency_by_task)}")

    if warnings:
        print("\n=== Warnings by Task ===")
        for task_id, latencies in sorted(latency_by_task.items(), key=lambda x: max(x[1]), reverse=True):
            avg_lat = _safe_avg(latencies)
            max_lat = max(latencies)
            print(f"\nTask: {task_id}")
            print(f"  Count: {len(latencies)}")
            print(f"  Avg: {avg_lat:.1f}ms ({avg_lat/1000:.1f}s)")
            print(f"  Max: {max_lat:.1f}ms ({max_lat/1000:.1f}s)")

        print("\n=== Recent Warnings (last 10) ===")
        for w in warnings[-10:]:
            observed = w.get("observed", {}) or {}
            latency_ms = float(observed.get("latency_ms", 0.0) or 0.0)
            quality = observed.get("quality")
            evidence_ok = observed.get("evidence_ok")
            print(f"\n{_safe_iso(w.get('ts'))}")
            print(f"  Task: {w.get('task_id', 'unknown')}")
            print(f"  Latency: {latency_ms:.1f}ms ({latency_ms/1000:.1f}s)")
            print(f"  Quality: {quality if quality is not None else 'N/A'}, Evidence: {evidence_ok}")
    else:
        print("\nNo latency warnings found")

    all_latencies = [p["latency_ms"] for p in policy_events if p["latency_ms"] > 0]
    if all_latencies:
        print("\n=== Overall Policy Event Statistics ===")
        sorted_lats = sorted(all_latencies)
        avg_all = _safe_avg(all_latencies)
        print(f"Count: {len(all_latencies)}")
        print(f"Min: {sorted_lats[0]:.1f}ms ({sorted_lats[0]/1000:.1f}s)")
        print(f"Max: {sorted_lats[-1]:.1f}ms ({sorted_lats[-1]/1000:.1f}s)")
        print(f"Avg: {avg_all:.1f}ms ({avg_all/1000:.1f}s)")
        p50 = _percentile(sorted_lats, 0.5)
        p95 = _percentile(sorted_lats, 0.95)
        print(f"P50: {p50:.1f}ms ({p50/1000:.1f}s)")
        print(f"P95: {p95:.1f}ms ({p95/1000:.1f}s)")

    print("\n=== Resonance Optimization Context ===")
    tasks_with_opt = sum(1 for p in policy_events if p["optimization"])
    print(f"Optimization-tagged policy events: {tasks_with_opt}/{len(policy_events)}")
    print(f"Off-peak throttle adjustments: {throttle_adjustments}")
    if preferred_channel_primary:
        print("Primary preferred channel counts:")
        for channel, count in preferred_channel_primary.most_common():
            print(f"  {channel}: {count}")

    window_groups = defaultdict(list)
    for event in policy_events:
        opt = event["optimization"]
        if not opt:
            window_groups["unknown"].append(event)
            continue
        window_groups["peak" if opt.get("is_peak_now") else "offpeak"].append(event)

    for window, events in window_groups.items():
        if not events:
            continue
        latencies = [e["latency_ms"] for e in events if e["latency_ms"] > 0]
        avg_lat = _safe_avg(latencies)
        warn_count = sum(1 for e in events if e["action"] == "warn")
        allow_count = sum(1 for e in events if e["action"] == "allow")
        total = len(events)
        qualities = [e["quality"] for e in events if isinstance(e["quality"], (int, float))]
        avg_quality = _safe_avg(qualities)
        print(f"\n[{window.upper()}] events: {total}")
        print(f"  Allows/Warns: {allow_count}/{warn_count}")
        if latencies:
            print(f"  Avg latency: {avg_lat:.1f}ms ({avg_lat/1000:.1f}s)")
            print(f"  P95 latency: {_percentile(sorted(latencies), 0.95):.1f}ms")
        if qualities:
            print(f"  Avg quality: {avg_quality:.2f}")

    print("\n=== Recommendations ===")
    if all_latencies and max(all_latencies) > 30000:
        print("- HIGH: Latency >30s detected. Inspect network paths, model cold starts, or rate limits.")
    if all_latencies and _safe_avg(all_latencies) > 15000:
        print("- MEDIUM: Avg latency >15s. Consider caching, async handling, or revised timeout thresholds.")
    if window_groups.get("offpeak") and throttle_adjustments == 0:
        print("- NOTE: Off-peak windows detected but no throttling recorded; confirm optimization config.")

    return 0


if __name__ == "__main__":
    sys.exit(analyze_latency())
