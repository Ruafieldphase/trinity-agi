"""
Phase injection engine tests.

The tests focus on prompt decoration and state transitions rather than the
exact numeric values (which are intentionally heuristic).
"""

from phase_injection import PhaseInjectionEngine


def test_inject_phase_decorates_prompt():
    engine = PhaseInjectionEngine()
    base_prompt = "사용자의 요청을 정리하고 실행 전략을 제안하세요."

    decorated = engine.inject_phase(base_prompt)
    snapshot = engine.get_last_snapshot()

    assert base_prompt in decorated
    assert snapshot is not None
    assert "bqi" in snapshot
    assert snapshot["phase_index"] == 0


def test_phase_rotation_when_interval_elapsed():
    engine = PhaseInjectionEngine(interval_seconds=0)

    engine.inject_phase("첫 번째 요청")
    first_snapshot = engine.get_last_snapshot()
    assert first_snapshot is not None
    first_phase = first_snapshot["phase_index"]

    engine.inject_phase("두 번째 요청")
    second_phase = engine.get_last_snapshot()["phase_index"]

    assert second_phase != first_phase
    assert second_phase in {0, 1, 2}


def test_phase_reset_returns_to_initial_state():
    engine = PhaseInjectionEngine(interval_seconds=0)
    engine.inject_phase("테스트 요청")
    engine.reset()

    assert engine.get_last_snapshot() is None
    prompt = engine.inject_phase("리셋 이후 요청")
    assert "Phase 1" in prompt
