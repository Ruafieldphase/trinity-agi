from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from workspace_root import get_workspace_root


def _repo_root() -> Path:
    return get_workspace_root()


def _add_repo_to_path():
    root = _repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _load_json_lines(path: Path, max_lines: int = 2000) -> list[Dict[str, Any]]:
    out: list[Dict[str, Any]] = []
    if not path.exists():
        return out
    try:
        with path.open("r", encoding="utf-8") as f:
            # Read from tail-ish by collecting; file is small in our usage
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    # Some ledgers may use ISO ts JSON; try forgiving
                    try:
                        obj = json.loads(line.replace("'", '"'))
                    except Exception:
                        continue
                if isinstance(obj, dict):
                    out.append(obj)
                if len(out) >= max_lines:
                    out = out[-max_lines:]
        return out
    except Exception:
        return out


def _find_ledger() -> Optional[Path]:
    # Try common locations
    candidates = [
        _repo_root() / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl",
        _repo_root() / "memory" / "resonance_ledger.jsonl",
        Path("fdo_agi_repo/memory/resonance_ledger.jsonl").resolve(),
        Path("memory/resonance_ledger.jsonl").resolve(),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _last_task_latency_ms(events: list[Dict[str, Any]]) -> tuple[Optional[float], Optional[Dict[str, Any]]]:
    # Prefer resonance_policy event (has observed.latency_ms)
    for obj in reversed(events):
        if obj.get("event") == "resonance_policy":
            observed = obj.get("observed") or {}
            try:
                lat = float(observed.get("latency_ms"))
                return lat, obj
            except Exception:
                pass
    # Fallback: any event with duration or duration_sec
    for obj in reversed(events):
        for key in ("duration_ms", "duration_sec", "duration"):
            if key in obj:
                try:
                    val = float(obj[key])
                    if key.endswith("_sec") or key == "duration":
                        return val * 1000.0, obj
                    return val, obj
                except Exception:
                    continue
    return None, None


def _build_summary() -> Dict[str, Any]:
    _add_repo_to_path()
    # Import config/policy helpers (best-effort)
    active_mode = "observe"
    active_policy = "quality-first"
    max_latency_ms: Optional[float] = None
    min_quality: Optional[float] = None
    reasons: Optional[list[str]] = None

    try:
        from fdo_agi_repo.orchestrator.resonance_bridge import (
            get_active_mode,
            get_active_policy_name,
            get_active_policy,
        )

        active_mode = get_active_mode()
        active_policy = get_active_policy_name()
        pol = get_active_policy() or {}
        try:
            max_latency_ms = float(pol.get("max_latency_ms"))
        except Exception:
            max_latency_ms = None
    except Exception:
        pass

    try:
        from fdo_agi_repo.orchestrator.config import get_evaluation_config

        ev = get_evaluation_config() or {}
        if "min_quality" in ev:
            min_quality = float(ev["min_quality"])  # type: ignore[assignment]
    except Exception:
        pass

    ledger_path = _find_ledger()
    events: list[Dict[str, Any]] = _load_json_lines(ledger_path) if ledger_path else []
    lat_ms, src = _last_task_latency_ms(events)
    if src and src.get("event") == "resonance_policy":
        try:
            reasons = list(src.get("reasons") or [])
        except Exception:
            reasons = None

    # Also peek monitoring metrics if present
    metrics_path = _repo_root() / "outputs" / "monitoring_metrics_latest.json"
    agi_avg_ms: Optional[float] = None
    try:
        if metrics_path.exists():
            m = json.loads(metrics_path.read_text(encoding="utf-8"))
            agi = m.get("AGI", {})
            avg_dur = agi.get("AvgDuration")
            if avg_dur is None:
                avg_dur = agi.get("AvgDurationSec")
                if avg_dur is not None:
                    agi_avg_ms = float(avg_dur) * 1000.0
            else:
                agi_avg_ms = float(avg_dur)
    except Exception:
        pass

    print("=== Last Task Latency Summary ===")
    print(f"Configured Mode    : {active_mode}")
    print(f"Configured Policy  : {active_policy}")
    if max_latency_ms is not None:
        print(f"Max Latency (ms)   : {int(max_latency_ms)}")
    if min_quality is not None:
        print(f"Eval min_quality   : {min_quality}")

    if lat_ms is not None:
        status = "OK"
        if max_latency_ms is not None and lat_ms > max_latency_ms:
            status = f"SLOW by +{int(lat_ms - max_latency_ms)}ms"
        print(f"Last Task Latency  : {int(lat_ms)}ms  ({status})")
    else:
        print("Last Task Latency  : n/a (no recent entries)")

    return {
        "configured_mode": active_mode,
        "configured_policy": active_policy,
        "max_latency_ms": max_latency_ms,
        "min_quality": min_quality,
        "last_task_latency_ms": lat_ms,
        "window_avg_latency_ms": agi_avg_ms,
        "last_policy_reasons": reasons or [],
    }


def main():
    parser = argparse.ArgumentParser(description="Summarize last task latency from ledger/metrics.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text")
    args = parser.parse_args()

    summary = _build_summary()

    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
        return

    print("=== Last Task Latency Summary ===")
    print(f"Configured Mode    : {summary['configured_mode']}")
    print(f"Configured Policy  : {summary['configured_policy']}")
    if summary.get("max_latency_ms") is not None:
        print(f"Max Latency (ms)   : {int(summary['max_latency_ms'])}")
    if summary.get("min_quality") is not None:
        print(f"Eval min_quality   : {summary['min_quality']}")

    lat_ms = summary.get("last_task_latency_ms")
    max_lat = summary.get("max_latency_ms")
    if lat_ms is not None:
        status = "OK"
        if max_lat is not None and lat_ms > max_lat:
            status = f"SLOW by +{int(lat_ms - max_lat)}ms"
        print(f"Last Task Latency  : {int(lat_ms)}ms  ({status})")
    else:
        print("Last Task Latency  : n/a (no recent entries)")

    if summary.get("window_avg_latency_ms") is not None:
        print(f"Window Avg Latency : {int(summary['window_avg_latency_ms'])}ms (AGI.AvgDuration)")
    reasons = summary.get("last_policy_reasons") or []
    if reasons:
        print("Last Reasons       : " + ", ".join(reasons))


if __name__ == "__main__":
    main()
