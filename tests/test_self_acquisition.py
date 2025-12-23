"""
Self-Acquisition System 테스트
"""
import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestSelfTrigger:
    """self_trigger.py 테스트"""
    
    def test_trigger_type_enum(self):
        from agi_core.self_trigger import TriggerType
        
        assert TriggerType.UNRESOLVED_PATTERN.value == "UNRESOLVED_PATTERN"
        assert TriggerType.BOREDOM.value == "BOREDOM"
        assert TriggerType.CURIOSITY_CONFLICT.value == "CURIOSITY_CONFLICT"
        assert TriggerType.MODEL_DRIFT.value == "MODEL_DRIFT"
    
    def test_trigger_event_dataclass(self):
        from agi_core.self_trigger import TriggerEvent, TriggerType
        
        event = TriggerEvent(
            type=TriggerType.BOREDOM,
            score=0.8,
            reason="Test reason",
            payload={"key": "value"}
        )
        
        assert event.type == TriggerType.BOREDOM
        assert event.score == 0.8
        assert event.reason == "Test reason"
        
        d = event.to_dict()
        assert d["type"] == "BOREDOM"
        assert d["score"] == 0.8
    
    def test_compute_unresolved_pattern_trigger(self):
        from agi_core.self_trigger import compute_unresolved_pattern_trigger
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # 60% 실패 비율 (threshold 이상)
            for i in range(6):
                f.write(json.dumps({"status": "failed", "event": "test"}) + "\n")
            for i in range(4):
                f.write(json.dumps({"status": "completed", "event": "test"}) + "\n")
            f.flush()
            
            trigger = compute_unresolved_pattern_trigger(f.name, threshold=0.5)
            assert trigger is not None
            assert trigger.type.value == "UNRESOLVED_PATTERN"
            assert trigger.score >= 0.5
            
        os.unlink(f.name)
    
    def test_compute_boredom_trigger_empty_log(self):
        from agi_core.self_trigger import compute_boredom_trigger
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # 빈 파일
            f.flush()
            
            trigger = compute_boredom_trigger(f.name, min_idle_seconds=60)
            assert trigger is not None
            assert trigger.type.value == "BOREDOM"
            assert trigger.score == 1.0  # 완전한 휴면 상태
            
        os.unlink(f.name)
    
    def test_compute_boredom_trigger_recent_activity(self):
        from agi_core.self_trigger import compute_boredom_trigger
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # 방금 전 활동
            now = datetime.now(timezone.utc).isoformat()
            f.write(json.dumps({"timestamp": now, "status": "recorded"}) + "\n")
            f.flush()
            
            trigger = compute_boredom_trigger(f.name, min_idle_seconds=1800)
            assert trigger is None  # 최근 활동이 있으므로 트리거 없음
            
        os.unlink(f.name)
    
    def test_compute_self_trigger_integration(self):
        from agi_core.self_trigger import compute_self_trigger
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "paths": {
                    "resonance_ledger": os.path.join(tmpdir, "resonance.jsonl"),
                    "learning_log": os.path.join(tmpdir, "learning.jsonl"),
                    "learned_patterns": os.path.join(tmpdir, "patterns.json"),
                },
                "thresholds": {
                    "unresolved_pattern": 0.6,
                    "boredom_idle_seconds": 60,
                    "curiosity_conflict": 0.5,
                    "model_drift": 0.7,
                }
            }
            
            # 빈 상태에서도 BOREDOM 트리거가 발생해야 함
            trigger = compute_self_trigger(config)
            assert trigger is not None
            assert trigger.type.value == "BOREDOM"


class TestProtoGoal:
    """proto_goal.py 테스트"""
    
    def test_proto_goal_type_enum(self):
        from agi_core.proto_goal import ProtoGoalType
        
        assert ProtoGoalType.SANDBOX_EXPERIMENT.value == "SANDBOX_EXPERIMENT"
        assert ProtoGoalType.YOUTUBE_LEARNING.value == "YOUTUBE_LEARNING"
        assert ProtoGoalType.PATTERN_MINING.value == "PATTERN_MINING"
    
    def test_proto_goal_dataclass(self):
        from agi_core.proto_goal import ProtoGoal, ProtoGoalType
        
        goal = ProtoGoal(
            type=ProtoGoalType.SANDBOX_EXPERIMENT,
            score=0.9,
            description="Test experiment",
            params={"hint": "test"}
        )
        
        assert goal.type == ProtoGoalType.SANDBOX_EXPERIMENT
        assert goal.score == 0.9
        
        d = goal.to_dict()
        assert d["type"] == "SANDBOX_EXPERIMENT"
    
    def test_generate_proto_goals_from_boredom_trigger(self):
        from agi_core.self_trigger import TriggerEvent, TriggerType
        from agi_core.proto_goal import generate_proto_goals_from_trigger, ProtoGoalType
        
        trigger = TriggerEvent(
            type=TriggerType.BOREDOM,
            score=0.8,
            reason="Test boredom",
            payload={}
        )
        
        goals = generate_proto_goals_from_trigger(trigger)
        
        assert len(goals) >= 1
        goal_types = [g.type for g in goals]
        # BOREDOM → YOUTUBE_LEARNING 또는 SANDBOX_EXPERIMENT
        assert ProtoGoalType.YOUTUBE_LEARNING in goal_types or ProtoGoalType.SANDBOX_EXPERIMENT in goal_types
    
    def test_generate_proto_goals_from_unresolved_pattern_trigger(self):
        from agi_core.self_trigger import TriggerEvent, TriggerType
        from agi_core.proto_goal import generate_proto_goals_from_trigger, ProtoGoalType
        
        trigger = TriggerEvent(
            type=TriggerType.UNRESOLVED_PATTERN,
            score=0.7,
            reason="Test unresolved",
            payload={"failed_count": 5}
        )
        
        goals = generate_proto_goals_from_trigger(trigger)
        
        assert len(goals) >= 1
        goal_types = [g.type for g in goals]
        assert ProtoGoalType.PATTERN_MINING in goal_types


class TestSelfAcquisitionLoop:
    """self_acquisition_loop.py 테스트"""
    
    def test_config_default(self):
        from agi_core.self_acquisition_loop import SelfAcquisitionConfig
        
        config = SelfAcquisitionConfig.default()
        
        assert config.loop_interval_seconds == 300
        assert config.max_actions_per_cycle == 1
    
    def test_select_best_proto_goal(self):
        from agi_core.self_acquisition_loop import select_best_proto_goal
        from agi_core.proto_goal import ProtoGoal, ProtoGoalType
        
        goals = [
            ProtoGoal(type=ProtoGoalType.SANDBOX_EXPERIMENT, score=0.5, description="A"),
            ProtoGoal(type=ProtoGoalType.PATTERN_MINING, score=0.9, description="B"),
            ProtoGoal(type=ProtoGoalType.YOUTUBE_LEARNING, score=0.7, description="C"),
        ]
        
        best = select_best_proto_goal(goals)
        
        assert best is not None
        assert best.score == 0.9
        assert best.type == ProtoGoalType.PATTERN_MINING
    
    def test_select_best_proto_goal_empty(self):
        from agi_core.self_acquisition_loop import select_best_proto_goal
        
        best = select_best_proto_goal([])
        assert best is None
    
    def test_execute_proto_goal_blender_not_implemented(self):
        from agi_core.self_acquisition_loop import execute_proto_goal
        from agi_core.proto_goal import ProtoGoal, ProtoGoalType
        
        goal = ProtoGoal(
            type=ProtoGoalType.BLENDER_VISUALIZATION,
            score=0.5,
            description="Test blender"
        )
        
        result = execute_proto_goal(goal)
        
        assert result["success"] is False
        assert "BLENDER_NOT_IMPLEMENTED" in result.get("reason", "")
    
    @patch("agi_core.self_acquisition_loop.compute_self_trigger")
    def test_run_self_acquisition_cycle_no_trigger(self, mock_trigger):
        from agi_core.self_acquisition_loop import run_self_acquisition_cycle, SelfAcquisitionConfig
        
        mock_trigger.return_value = None
        
        config = SelfAcquisitionConfig.default()
        result = run_self_acquisition_cycle(config)
        
        assert result is None
    
    @patch("agi_core.self_acquisition_loop.execute_proto_goal")
    @patch("agi_core.self_acquisition_loop.generate_proto_goals_from_trigger")
    @patch("agi_core.self_acquisition_loop.compute_self_trigger")
    def test_run_self_acquisition_cycle_with_trigger(
        self, mock_trigger, mock_goals, mock_execute
    ):
        from agi_core.self_acquisition_loop import run_self_acquisition_cycle, SelfAcquisitionConfig
        from agi_core.self_trigger import TriggerEvent, TriggerType
        from agi_core.proto_goal import ProtoGoal, ProtoGoalType
        
        mock_trigger.return_value = TriggerEvent(
            type=TriggerType.BOREDOM,
            score=0.8,
            reason="Test",
            payload={}
        )
        
        mock_goals.return_value = [
            ProtoGoal(
                type=ProtoGoalType.YOUTUBE_LEARNING,
                score=0.8,
                description="Test learning"
            )
        ]
        
        mock_execute.return_value = {"success": True, "action_type": "youtube_learning"}
        
        config = SelfAcquisitionConfig.default()
        result = run_self_acquisition_cycle(config)
        
        assert result is not None
        assert result["trigger"]["type"] == "BOREDOM"
        assert result["selected_goal"]["type"] == "YOUTUBE_LEARNING"
        assert result["result"]["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
