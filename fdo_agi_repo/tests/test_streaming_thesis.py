"""
Unit tests for Phase 2.6: Streaming Thesis
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from orchestrator.contracts import TaskSpec
from personas.thesis import run_thesis


def read_last_ledger_event(task_id: str):
    """Read last ledger event for task_id"""
    ledger_path = repo_root / "memory" / "resonance_ledger.jsonl"
    if not ledger_path.exists():
        return None
    
    with open(ledger_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if event.get("task_id") == task_id:
                return event
        except:
            pass
    
    return None


class TestStreamingThesis:
    """Streaming Thesis 기능 테스트"""
    
    def test_streaming_enabled_records_ttft(self):
        """Streaming 활성화 시 TTFT 기록 확인"""
        os.environ["THESIS_STREAMING"] = "true"
        
        task = TaskSpec(
            task_id="test-streaming-1",
            title="Streaming Test",
            goal="간단한 3문장 작성"
        )
        
        result = run_thesis(task, {}, None, "")
        
        assert result is not None
        assert result.summary
        assert len(result.summary) > 0
        
        # Ledger에서 TTFT 확인
        event = read_last_ledger_event("test-streaming-1")
        
        assert event is not None
        assert event.get("streaming") is True
        assert "ttft_sec" in event
        assert event["ttft_sec"] > 0
        assert "perceived_improvement_pct" in event
    
    def test_baseline_no_ttft(self):
        """Baseline 모드에서는 TTFT 미기록 확인"""
        os.environ["THESIS_STREAMING"] = "false"
        
        task = TaskSpec(
            task_id="test-baseline-1",
            title="Baseline Test",
            goal="간단한 3문장 작성"
        )
        
        result = run_thesis(task, {}, None, "")
        
        assert result is not None
        assert result.summary
        
        # Ledger에서 TTFT 없음 확인
        event = read_last_ledger_event("test-baseline-1")
        
        assert event is not None
        assert event.get("streaming") is False
        assert "ttft_sec" not in event
    
    def test_streaming_perceived_improvement(self):
        """Streaming Perceived Improvement 기록 확인"""
        os.environ["THESIS_STREAMING"] = "true"
        
        task = TaskSpec(
            task_id="test-perceived-1",
            title="Perceived Test",
            goal="체감 개선 측정용 3문장"
        )
        
        result = run_thesis(task, {}, None, "")
        
        assert result is not None
        
        event = read_last_ledger_event("test-perceived-1")
        
        assert event is not None
        assert event.get("streaming") is True
        
        # Perceived improvement >= 40%
        improvement = event.get("perceived_improvement_pct", 0)
        assert improvement >= 40.0, f"Expected >= 40%, got {improvement}%"
        
        # TTFT < Total Time
        ttft = event.get("ttft_sec", 0)
        total = event.get("duration_sec", 0)
        assert ttft < total, f"TTFT ({ttft}s) should be less than total ({total}s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

