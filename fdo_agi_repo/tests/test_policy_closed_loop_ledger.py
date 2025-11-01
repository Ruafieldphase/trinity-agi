import json
import time
from datetime import datetime
from pathlib import Path


LEDGER_PATH = Path(__file__).resolve().parents[2] / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"


def _to_epoch_seconds(ts_val):
    try:
        if isinstance(ts_val, (int, float)):
            return float(ts_val)
        if isinstance(ts_val, str):
            # Handle ISO8601 with optional Z
            s = ts_val.replace("Z", "+00:00")
            return datetime.fromisoformat(s).timestamp()
    except Exception:
        return 0.0
    return 0.0


def _read_new_events(since_ts: float):
    if not LEDGER_PATH.exists():
        return []
    out = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        try:
            obj = json.loads(line)
        except Exception:
            continue
        ts = _to_epoch_seconds(obj.get("ts", 0))
        if ts >= since_ts:
            out.append(obj)
    return out


def test_policy_and_closed_loop_throttle():
    # Arrange: mark start time
    start_ts = time.time()

    # Minimal task spec
    spec = {
        "task_id": f"test-ledger-{int(start_ts)}",
        "title": "Ledger policy+closed-loop test",
        "goal": "quick run for ledger events",
        "constraints": [],
        "inputs": {},
        "scope": "analysis",
        "permissions": ["READ"],
        "evidence_required": False,
    }

    # Act: run twice quickly to exercise throttle
    from fdo_agi_repo.orchestrator.pipeline import run_task
    run_task({}, spec)
    # second run with different id to ensure separate task
    spec2 = dict(spec)
    spec2["task_id"] = spec["task_id"] + "-2"
    run_task({}, spec2)

    # Assert: read new events only
    events = _read_new_events(start_ts)
    pol = [e for e in events if e.get("event") == "resonance_policy"]
    cls = [e for e in events if e.get("event") == "closed_loop_snapshot"]

    assert len(pol) >= 2, "Expected at least 2 policy evaluations across two runs"
    assert len(cls) <= 1, "Closed-loop snapshot should be throttled to max 1 in quick succession"
