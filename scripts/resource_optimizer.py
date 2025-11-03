#!/usr/bin/env python3
"""
Resource Optimizer Stub
-----------------------

Reads the latest performance metrics to compare against a configurable
resource budget. Outputs recommendations (dry-run by default) for actions
such as scaling workers, reducing task throughput, or scheduling maintenance.
"""

from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Any, Dict, List

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = WORKSPACE_ROOT / "configs" / "resource_budget.json"
METRICS_PATH = WORKSPACE_ROOT / "outputs" / "performance_metrics_latest.json"
SUMMARY_PATH = WORKSPACE_ROOT / "outputs" / "resource_optimizer_summary.md"


def load_json(path: Path, fallback: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[WARN] Failed to load {path}: {exc}")
    return fallback


def evaluate(metrics: Dict[str, Any], budget: Dict[str, Any]) -> List[str]:
    recs: List[str] = []
    cpu_budget = float(budget.get("cpu_budget_percent", 80))
    mem_budget = float(budget.get("memory_budget_percent", 80))
    queue_budget = float(budget.get("queue_latency_ms", 2000))

    cpu_usage = float(metrics.get("cpu_usage_percent", 0))
    mem_usage = float(metrics.get("memory_usage_percent", 0))
    queue_latency = float(metrics.get("queue_latency_ms", 0))

    if cpu_usage > cpu_budget:
        recs.append(f"CPU usage {cpu_usage:.1f}% exceeds budget {cpu_budget}%. Consider throttling tasks.")
    if mem_usage > mem_budget:
        recs.append(f"Memory usage {mem_usage:.1f}% exceeds budget {mem_budget}%. Consider cache cleanup.")
    if queue_latency > queue_budget:
        recs.append(f"Queue latency {queue_latency:.0f}ms exceeds budget {queue_budget}ms. Consider adding worker.")

    if not recs:
        recs.append("All metrics within budget thresholds.")
    return recs


def main() -> None:
    parser = argparse.ArgumentParser(description="Resource Optimizer Stub")
    parser.add_argument("--dry-run", action="store_true", help="Preview recommendations without executing actions.")
    parser.add_argument("--config", type=str, default=str(CONFIG_PATH))
    parser.add_argument("--metrics", type=str, default=str(METRICS_PATH))
    parser.add_argument("--summary", type=str, default=str(SUMMARY_PATH))
    args = parser.parse_args()

    budget = load_json(Path(args.config), {})
    metrics = load_json(Path(args.metrics), {})

    recs = evaluate(metrics, budget)

    summary_lines = [
        "# Resource Optimizer Summary",
        "",
        f"**Dry Run**: {args.dry_run}",
        f"**Budget Config**: {args.config}",
        f"**Metrics Source**: {args.metrics}",
        "",
        "## Recommendations",
    ]
    summary_lines.extend([f"- {r}" for r in recs])

    Path(args.summary).write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"Summary written: {args.summary}")
    for rec in recs:
        print(f"> {rec}")


if __name__ == "__main__":
    main()
