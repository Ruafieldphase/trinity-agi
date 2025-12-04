from scripts import summarize_last_task_latency as sl


def test_last_task_latency_prefers_resonance_policy():
    events = [
        {"event": "task_completed", "duration_ms": 1200},
        {
            "event": "resonance_policy",
            "observed": {"latency_ms": 3456},
            "reasons": ["latency 3456ms > max_latency_ms 3000ms"],
        },
    ]
    lat, src = sl._last_task_latency_ms(events)
    assert lat == 3456
    assert src and src["event"] == "resonance_policy"


def test_last_task_latency_fallback_duration_seconds():
    events = [
        {"event": "task_completed", "duration_sec": 2.5},
    ]
    lat, src = sl._last_task_latency_ms(events)
    assert int(lat) == 2500
    assert src and src["event"] == "task_completed"


def test_build_summary_shape():
    s = sl._build_summary()
    # Keys should exist even when values may be None
    for k in (
        "configured_mode",
        "configured_policy",
        "max_latency_ms",
        "min_quality",
        "last_task_latency_ms",
        "window_avg_latency_ms",
        "last_policy_reasons",
    ):
        assert k in s

