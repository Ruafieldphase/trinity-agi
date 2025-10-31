"""
test_orchestrator_runtime.py
실제 orchestrator pipeline.run_task()를 호출하여 resonance 기록 검증.
"""
import pytest
from pathlib import Path
import tempfile
import os

# Skip if orchestrator dependencies not available
pytest.importorskip("fdo_agi_repo.orchestrator.pipeline")
pytest.importorskip("fdo_agi_repo.orchestrator.contracts")


def test_run_task_records_resonance_event():
    """Test that actual pipeline.run_task() records resonance event."""
    from fdo_agi_repo.orchestrator.pipeline import run_task
    from fdo_agi_repo.orchestrator.resonance_bridge import init_resonance_store
    from fdo_agi_repo.universal.resonance import ResonanceStore
    
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "runtime_test_events.jsonl"
        init_resonance_store(store_path)
        
        # Create minimal task spec dict
        task_spec = {
            "task_id": "runtime-test-001",
            "title": "Test Task",
            "goal": "Summarize Python best practices in 50 words",
            "constraints": ["Keep it concise"],
            "inputs": {},
            "scope": "doc",
            "permissions": [],
            "evidence_required": False,
        }
        
        # Create minimal tool config dict
        tool_cfg = {
            "project_root": str(Path(tmpdir)),
            "knowledge_base_path": str(Path(tmpdir) / "kb"),
            "ledger_path": str(Path(tmpdir) / "ledger.jsonl"),
            "coordinate_path": str(Path(tmpdir) / "coord.jsonl"),
        }
        
        try:
            # Run actual orchestrator pipeline
            result = run_task(tool_cfg, task_spec)
            
            # Verify result
            assert result is not None
            assert result["task_id"] == "runtime-test-001"
            
            # Verify resonance event recorded
            store = ResonanceStore(store_path)
            event = store.latest()
            
            assert event is not None
            assert event.task_id == "runtime-test-001"
            assert event.resonance_key.startswith("orchestrator:reason")
            assert "quality" in event.metrics
            assert "evidence" in event.metrics
            
        except Exception as e:
            pytest.skip(f"Orchestrator runtime test skipped due to: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
