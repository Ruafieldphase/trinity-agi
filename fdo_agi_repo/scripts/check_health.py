from __future__ import annotations
import json
import os
import sys
from pathlib import Path
import argparse
import time
from typing import Any, Dict, Optional, Callable
import threading

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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AGI System Health Check")
    parser.add_argument("--window-seconds", type=int, default=3600, help="Stats window in seconds (default: 3600)")
    parser.add_argument("--fast", action="store_true", help="Fast path: compute health from basic stats only (skip flow)")
    parser.add_argument("--min-snapshots", type=int, default=1, help="Minimum snapshots required to evaluate (default: 1)")
    parser.add_argument("--json-only", action="store_true", help="Output JSON only (no human-readable lines)")
    parser.add_argument("--max-duration", type=float, default=15.0, help="Max seconds allowed for health computation (soft timeout)")
    parser.add_argument("--hard-timeout", type=float, default=None, help="Hard timeout in seconds (interrupt computation and return TIMEOUT)")
    return parser.parse_args()


def _run_with_timeout(func: Callable[[], Any], timeout: float) -> tuple[bool, Optional[Any], Optional[str]]:
    """Run a callable with a hard timeout using a worker thread.

    Returns: (finished, result, error_msg)
    """
    result: dict[str, Any] | None = None  # type: ignore[assignment]
    error: Optional[str] = None

    def _target():
        nonlocal result, error
        try:
            result = func()
        except Exception as e:  # Defensive: surface internal errors without hanging
            error = f"{type(e).__name__}: {e}"

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return (False, None, None)
    if error is not None:
        return (True, None, error)
    return (True, result, None)


def main() -> int:
    args = _parse_args()

    cfg = {
        "MIN_AVG_CONFIDENCE": _get_float("MIN_AVG_CONFIDENCE", DEFAULTS["MIN_AVG_CONFIDENCE"]),
        "MIN_AVG_QUALITY": _get_float("MIN_AVG_QUALITY", DEFAULTS["MIN_AVG_QUALITY"]),
        "MAX_SECOND_PASS_PER_TASK": _get_float("MAX_SECOND_PASS_PER_TASK", DEFAULTS["MAX_SECOND_PASS_PER_TASK"]),
        "MIN_COMPLETION_RATE": _get_float("MIN_COMPLETION_RATE", DEFAULTS["MIN_COMPLETION_RATE"]),
        "MIN_FLOW_SCORE": _get_float("MIN_FLOW_SCORE", DEFAULTS["MIN_FLOW_SCORE"]),
    }

    start_ts = time.time()
    collector = MetricsCollector()

    # Fast path: compute health from stats only and skip flow calculations
    if args.fast:
        stats = collector.get_statistics(window_seconds=args.window_seconds)
        # If not enough data, return PASS with informative payload (non-blocking)
        if stats.get("count", 0) < args.min_snapshots:
            payload = {
                "healthy": True,
                "checks": {
                    "success_rate": True,
                    "error_rate": True,
                    "response_time": True,
                },
                "current_values": {
                    "confidence": (stats.get("avg_success_rate", 0.0) / 100.0),
                    "quality": 1.0 - (stats.get("avg_error_rate", 0.0) / 100.0),
                    "second_pass_rate": 0.0,
                },
                "information_flow": {
                    "score": 0.0,
                    "status": "UNKNOWN",
                    "healthy": True,
                    "recommendation": "Fast mode: flow skipped",
                },
                "timestamp": time.time(),
                "mode": "fast",
            }
            if not args.json_only:
                print("HEALTH: PASS (FAST, NO-DATA)")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        # Evaluate basic checks against defaults (mapped to percentage-based)
        MIN_SUCCESS = 90.0
        MAX_ERROR = 10.0
        MAX_RESPONSE_TIME = 5000.0
        checks = {
            "success_rate": stats.get("avg_success_rate", 0.0) >= MIN_SUCCESS,
            "error_rate": stats.get("avg_error_rate", 0.0) <= MAX_ERROR,
            "response_time": stats.get("avg_response_time_ms", 0.0) <= MAX_RESPONSE_TIME,
        }
        healthy = all(checks.values())
        payload = {
            "healthy": healthy,
            "checks": checks,
            "current_values": {
                "confidence": (stats.get("avg_success_rate", 0.0) / 100.0),
                "quality": 1.0 - (stats.get("avg_error_rate", 0.0) / 100.0),
                "second_pass_rate": 0.0,
            },
            "information_flow": {
                "score": 0.0,
                "status": "SKIPPED",
                "healthy": True,
                "recommendation": "Fast mode: flow skipped",
            },
            "timestamp": time.time(),
            "mode": "fast",
        }
        if not args.json_only:
            print("HEALTH:", "PASS" if healthy else "FAIL")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if healthy else 1

    # Normal path with hard/soft timeout guard
    # Prefer hard-timeout (thread join) if provided, else fall back to soft check
    hard_timeout = float(args.hard_timeout) if args.hard_timeout is not None else float(args.max_duration)
    finished, health, err = _run_with_timeout(lambda: collector.get_health_status(), hard_timeout)
    if not finished:
        if not args.json_only:
            print("HEALTH: FAIL (TIMEOUT)")
        print(json.dumps({
            "healthy": False,
            "checks": {"timeout": True},
            "reason": f"Health computation exceeded {hard_timeout:.1f}s",
            "timestamp": time.time(),
            "mode": "normal",
        }, ensure_ascii=False, indent=2))
        return 2
    if err is not None:
        if not args.json_only:
            print("HEALTH: FAIL (ERROR)")
        print(json.dumps({
            "healthy": False,
            "checks": {"exception": True},
            "reason": err,
            "timestamp": time.time(),
            "mode": "normal",
        }, ensure_ascii=False, indent=2))
        return 3
    if not isinstance(health, dict):
        if not args.json_only:
            print("HEALTH: FAIL (INVALID RESULT)")
        print(json.dumps({
            "healthy": False,
            "checks": {"invalid": True},
            "reason": "Collector returned no data",
            "timestamp": time.time(),
            "mode": "normal",
        }, ensure_ascii=False, indent=2))
        return 3
    # Extra soft timeout check in case health computation itself was long but returned
    elapsed = time.time() - start_ts
    if elapsed > args.max_duration:
        if not args.json_only:
            print("HEALTH: FAIL (TIMEOUT)")
        print(json.dumps({
            "healthy": False,
            "checks": {"timeout": True},
            "reason": f"Health computation exceeded {args.max_duration:.1f}s",
            "timestamp": time.time(),
            "mode": "normal",
        }, ensure_ascii=False, indent=2))
        return 2

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
        if not args.json_only:
            print("HEALTH: FAIL")
            print(" - " + "\n - ".join(failures))
        print(json.dumps({
            "healthy": False,
            "failures": failures,
            "thresholds": cfg,
            "timestamp": time.time(),
            "mode": "normal",
        }, ensure_ascii=False, indent=2))
        return 1

    # Print HEALTHY status with flow info
    flow = health.get('information_flow', {})
    if not args.json_only:
        print("HEALTH: PASS")
    print(json.dumps({
        "avg_confidence": health['current_values']['confidence'],
        "avg_quality": health['current_values']['quality'],
        "second_pass_rate": health['current_values']['second_pass_rate'],
        "flow_score": flow.get('score', 0.0),
        "flow_status": flow.get('status', 'UNKNOWN'),
        "thresholds": cfg,
        "timestamp": time.time(),
        "mode": "normal",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
