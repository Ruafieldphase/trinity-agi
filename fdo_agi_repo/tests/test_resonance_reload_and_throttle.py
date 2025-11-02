import json
import time
import tempfile
from pathlib import Path


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def test_resonance_config_mtime_reload(monkeypatch):
    from fdo_agi_repo.orchestrator import resonance_bridge as rb

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "resonance.json"
        write_json(
            p,
            {
                "active_mode": "observe",
                "active_policy": "quality-first",
                "policies": {
                    "quality-first": {"min_quality": 0.8, "require_evidence": True, "max_latency_ms": 8000}
                },
                "closed_loop_snapshot_period_sec": 2,
            },
        )

        monkeypatch.setenv("RESONANCE_CONFIG", str(p))

        # First load
        cfg1 = rb.load_resonance_config(force_reload=True)
        assert cfg1.get("active_mode") == "observe"
        assert rb.get_active_policy_name() == "quality-first"
        assert rb.get_closed_loop_period_sec() == 2

        # Ensure mtime changes on Windows (coarse mtime resolution)
        time.sleep(2.2)

        # Modify active policy and period
        write_json(
            p,
            {
                "active_mode": "enforce",
                "active_policy": "latency-first",
                "policies": {
                    "quality-first": {"min_quality": 0.8, "require_evidence": True, "max_latency_ms": 8000},
                    "latency-first": {"min_quality": 0.5, "require_evidence": False, "max_latency_ms": 1500},
                },
                "closed_loop_snapshot_period_sec": 3,
            },
        )
        # Force filesystem to record a fresh mtime
        import os as _os
        _os.utime(p, None)

        cfg2 = rb.load_resonance_config()
        assert cfg2.get("active_mode") == "enforce"
        assert rb.get_active_mode() == "enforce"
        assert rb.get_active_policy_name() == "latency-first"
        assert rb.get_closed_loop_period_sec() == 3


def test_should_emit_closed_loop_throttle(monkeypatch):
    from fdo_agi_repo.orchestrator import resonance_bridge as rb

    # Reset last snapshot timestamp
    monkeypatch.setattr(rb, "_LAST_SNAPSHOT_TS", None, raising=False)

    # First call should emit
    assert rb.should_emit_closed_loop(period_sec=1) is True
    # Immediate second call within 1s should not emit
    assert rb.should_emit_closed_loop(period_sec=1) is False

    # After ~1s it should emit again
    time.sleep(1.1)
    assert rb.should_emit_closed_loop(period_sec=1) is True
