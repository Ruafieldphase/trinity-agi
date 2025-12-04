#!/usr/bin/env python3
"""
Utility to replay historical health snapshots against prospective alert thresholds.

This helps tune the confidence/quality/second-pass guardrails before changing live values.
"""
from __future__ import annotations

import argparse
import json
import os
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from monitor.metrics_collector import MetricsCollector


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _parse_range(spec: str | None, default_value: float) -> List[float]:
    if spec is None:
        return [default_value]
    spec = spec.strip()
    if not spec:
        return [default_value]
    if ":" in spec:
        parts = spec.split(":")
        if len(parts) != 3:
            raise ValueError(f"Range '{spec}' must use start:end:step format.")
        start, end, step = (float(part) for part in parts)
        if step <= 0:
            raise ValueError(f"Step must be positive, got {step}.")
        values: List[float] = []
        current = start
        # Extend a tiny epsilon to counter floating point drift.
        limit = end + (step / 10.0)
        while current <= limit:
            values.append(round(current, 4))
            current += step
        return values
    return [float(spec)]


def _load_alert_log_samples(repo_root: Path) -> List[Dict[str, Any]]:
    alert_path = repo_root / "outputs" / "health_alerts.jsonl"
    samples: List[Dict[str, Any]] = []
    if not alert_path.exists():
        return samples

    with open(alert_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            metrics = payload.get("metrics") or {}
            samples.append(
                {
                    "timestamp": payload.get("timestamp"),
                    "confidence": float(metrics.get("confidence", 0.0)),
                    "quality": float(metrics.get("quality", 0.0)),
                    "second_pass_rate": float(metrics.get("second_pass_rate", 0.0)),
                    "source": "alert_log",
                }
            )
    return samples


def _load_ledger_samples(repo_root: Path, hours: float, interval_minutes: int) -> List[Dict[str, Any]]:
    collector = MetricsCollector(repo_root=repo_root)
    timeline = collector.get_timeline_data(hours=hours, interval_minutes=interval_minutes)
    samples: List[Dict[str, Any]] = []
    for slot in timeline:
        if slot.get("avg_confidence") is None or slot.get("avg_quality") is None:
            continue
        samples.append(
            {
                "timestamp": slot["timestamp"],
                "confidence": float(slot.get("avg_confidence", 0.0)),
                "quality": float(slot.get("avg_quality", 0.0)),
                "second_pass_rate": float(slot.get("second_pass_rate", 0.0)),
                "source": "ledger_timeline",
            }
        )
    return samples


def _evaluate_thresholds(
    samples: Iterable[Dict[str, Any]],
    min_confidence: float,
    min_quality: float,
    max_second_pass_rate: float,
) -> Dict[str, Any]:
    total = 0
    triggered = 0
    metric_hits = {"confidence": 0, "quality": 0, "second_pass_rate": 0}
    timeline_hits: List[Tuple[str | None, Dict[str, bool]]] = []

    for sample in samples:
        total += 1
        confidence = sample["confidence"]
        quality = sample["quality"]
        second_pass = sample["second_pass_rate"]
        hit_flags = {
            "confidence": confidence < min_confidence,
            "quality": quality < min_quality,
            "second_pass_rate": second_pass > max_second_pass_rate,
        }
        if any(hit_flags.values()):
            triggered += 1
            for metric, hit in hit_flags.items():
                if hit:
                    metric_hits[metric] += 1
            timeline_hits.append((sample.get("timestamp"), hit_flags))

    return {
        "min_confidence": min_confidence,
        "min_quality": min_quality,
        "max_second_pass_rate": max_second_pass_rate,
        "total_samples": total,
        "alerts": triggered,
        "alert_rate": (triggered / total) if total else 0.0,
        "metric_hits": metric_hits,
        "timeline_hits": timeline_hits,
    }


def main() -> None:
    default_conf = float(os.getenv("AGI_MIN_CONFIDENCE", "0.60"))
    default_quality = float(os.getenv("AGI_MIN_QUALITY", "0.65"))
    default_second = float(os.getenv("AGI_MAX_SECOND_PASS_RATE", "2.0"))

    parser = argparse.ArgumentParser(
        description="Simulate health alerts for different threshold settings."
    )
    parser.add_argument(
        "--source",
        choices=["alert_log", "ledger"],
        default="alert_log",
        help="Data source for simulation. Defaults to alert_log (outputs/health_alerts.jsonl).",
    )
    parser.add_argument("--hours", type=float, default=24.0, help="Lookback window when using ledger data.")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Timeline interval in minutes when using ledger data.",
    )
    parser.add_argument("--min-confidence", type=float, help="Single confidence threshold to evaluate.")
    parser.add_argument("--min-quality", type=float, help="Single quality threshold to evaluate.")
    parser.add_argument("--max-second-pass", type=float, help="Single second-pass rate ceiling to evaluate.")
    parser.add_argument("--confidence-grid", type=str, help="Range for min confidence formatted as start:end:step.")
    parser.add_argument("--quality-grid", type=str, help="Range for min quality formatted as start:end:step.")
    parser.add_argument("--second-pass-grid", type=str, help="Range for max second-pass rate formatted as start:end:step.")
    parser.add_argument(
        "--show-timeline",
        action="store_true",
        help="Print timestamps where alerts would fire for each configuration.",
    )
    args = parser.parse_args()

    repo_root = _repo_root()
    if args.source == "alert_log":
        samples = _load_alert_log_samples(repo_root)
    else:
        samples = _load_ledger_samples(repo_root, hours=args.hours, interval_minutes=args.interval)

    if not samples:
        print("No samples available for simulation. Try switching --source or extending --hours.")
        return

    confidence_values = _parse_range(args.confidence_grid, args.min_confidence or default_conf)
    quality_values = _parse_range(args.quality_grid, args.min_quality or default_quality)
    second_pass_values = _parse_range(args.second_pass_grid, args.max_second_pass or default_second)

    print(f"Simulating {len(confidence_values) * len(quality_values) * len(second_pass_values)} configurations across {len(samples)} samples.")
    print("Thresholds -> alerts/total (rate) | hits by metric")

    results = []
    for conf, qual, second in product(confidence_values, quality_values, second_pass_values):
        evaluation = _evaluate_thresholds(samples, conf, qual, second)
        results.append(evaluation)

    # Sort by alert rate ascending to highlight calmer configurations first.
    results.sort(key=lambda item: item["alert_rate"])

    for entry in results:
        metric_hits = entry["metric_hits"]
        breakdown = ", ".join(f"{name}:{metric_hits[name]}" for name in ("confidence", "quality", "second_pass_rate"))
        print(
            f"conf>={entry['min_confidence']:.2f}, quality>={entry['min_quality']:.2f}, 2nd<={entry['max_second_pass_rate']:.2f} "
            f"-> {entry['alerts']}/{entry['total_samples']} ({entry['alert_rate']:.1%}) [{breakdown}]"
        )
        if args.show_timeline and entry["timeline_hits"]:
            for ts, flags in entry["timeline_hits"]:
                hit_metrics = ", ".join(name for name, fired in flags.items() if fired)
                print(f"  - {ts or 'unknown'} :: {hit_metrics}")


if __name__ == "__main__":
    main()
