"""
test_orchestrator_resonance.py
오케스트레이터 파이프라인과 Universal Resonance 통합 테스트.
"""
import pytest
from pathlib import Path
from datetime import datetime, timezone
import tempfile
import os

from fdo_agi_repo.universal.resonance import ResonanceStore, ResonanceEvent
from fdo_agi_repo.orchestrator.resonance_bridge import init_resonance_store, record_task_resonance


def test_record_task_resonance_basic():
    """Test basic resonance recording from orchestrator."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "test_events.jsonl"
        init_resonance_store(store_path)
        
        # Simulate orchestrator task completion
        eval_report = {
            "quality": 0.85,
            "evidence_ok": True,
        }
        
        record_task_resonance(
            task_id="test-task-001",
            task_goal="Analyze codebase structure",
            eval_report=eval_report,
            bqi_coord={"Binoche_Observer": 0.75, "quality": 0.9, "intent": 0.6},
            duration_sec=2.5,
        )
        
        # Verify event recorded
        store = ResonanceStore(store_path)
        event = store.latest()
        
        assert event is not None
        assert event.task_id == "test-task-001"
        assert event.resonance_key == "orchestrator:reason:binoche_high"
        assert event.metrics["quality"] == 0.85
        assert event.metrics["evidence"] == 1.0
        assert event.metrics["latency_ms"] == 2500.0
        assert "bqi_binoche" in event.tags


def test_record_task_resonance_no_bqi():
    """Test resonance recording without BQI coordinates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "test_events_no_bqi.jsonl"
        init_resonance_store(store_path)
        
        eval_report = {
            "quality": 0.60,
            "evidence_ok": False,
        }
        
        record_task_resonance(
            task_id="test-task-002",
            task_goal="Write documentation",
            eval_report=eval_report,
            bqi_coord=None,
            duration_sec=None,
        )
        
        store = ResonanceStore(store_path)
        event = store.latest()
        
        assert event is not None
        assert event.resonance_key == "orchestrator:reason"  # no subdomain
        assert event.metrics["quality"] == 0.60
        assert event.metrics["evidence"] == 0.0
        assert "latency_ms" not in event.metrics  # duration was None


def test_record_task_resonance_silent_on_no_init():
    """Test that recording silently skips if store not initialized."""
    # Reset global store (simulate no init)
    from fdo_agi_repo.orchestrator import resonance_bridge
    resonance_bridge._RESONANCE_STORE = None
    
    # Should not raise exception
    record_task_resonance(
        task_id="test-task-003",
        task_goal="Test silent fallback",
        eval_report={"quality": 0.5, "evidence_ok": True},
    )
    # No assertion needed; test passes if no exception raised


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
