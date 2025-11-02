from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

HERE = Path(__file__).parent
REPO = HERE.parent
MONITOR_DIR = REPO / "monitoring"
sys.path.insert(0, str(MONITOR_DIR))

from metrics_collector import MetricsCollector  # noqa: E402

OUTPUTS = REPO / "outputs"
LATEST_JSON = OUTPUTS / "ledger_summary_latest.json"

DEFAULTS = {
    "MIN_AVG_CONFIDENCE": 0.60,
    "MIN_AVG_QUALITY": 0.65,
    "MAX_SECOND_PASS_PER_TASK": 2.0,
    "MIN_COMPLETION_RATE": 0.90,
    "MIN_FLOW_SCORE": 0.4,  # Moderate 이상
}


def _get_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        return default


def main() -> int:
    cfg = {
        "MIN_AVG_CONFIDENCE": _get_float("MIN_AVG_CONFIDENCE", DEFAULTS["MIN_AVG_CONFIDENCE"]),
        "MIN_AVG_QUALITY": _get_float("MIN_AVG_QUALITY", DEFAULTS["MIN_AVG_QUALITY"]),
        "MAX_SECOND_PASS_PER_TASK": _get_float("MAX_SECOND_PASS_PER_TASK", DEFAULTS["MAX_SECOND_PASS_PER_TASK"]),
        "MIN_COMPLETION_RATE": _get_float("MIN_COMPLETION_RATE", DEFAULTS["MIN_COMPLETION_RATE"]),
        "MIN_FLOW_SCORE": _get_float("MIN_FLOW_SCORE", DEFAULTS["MIN_FLOW_SCORE"]),
    }

    collector = MetricsCollector()
    health = collector.get_health_status()

    failures = []
    
    # Check basic health
    if not health['healthy']:
        failures.append("Overall health check failed")
        for check_name, passed in health['checks'].items():
            if not passed:
                failures.append(f"{check_name} failed")
    
    # Check information flow
    if 'information_flow' in health:
        flow = health['information_flow']
        if not flow['healthy']:
            failures.append(f"Flow: {flow['score']:.2f} ({flow['status']}) - {flow['recommendation']}")

    if failures:
        print("HEALTH: FAIL")
        print(" - " + "\n - ".join(failures))
        return 1

    # Print HEALTHY status with flow info
    flow = health.get('information_flow', {})
    print("HEALTH: PASS")
    print(json.dumps({
        "avg_confidence": health['current_values']['confidence'],
        "avg_quality": health['current_values']['quality'],
        "second_pass_rate": health['current_values']['second_pass_rate'],
        "flow_score": flow.get('score', 0.0),
        "flow_status": flow.get('status', 'UNKNOWN'),
        "thresholds": cfg,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
