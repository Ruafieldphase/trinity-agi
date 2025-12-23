"""
Vision Stream 테스트
"""
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone


class TestVisionFrameQueue:
    """frame_queue.py 테스트"""
    
    def setup_method(self):
        """각 테스트 전 큐 초기화"""
        from agi_core.vision_stream.frame_queue import VisionFrameQueue
        VisionFrameQueue.reset()
    
    @pytest.mark.asyncio
    async def test_frame_queue_put_get(self):
        """기본 put/get 동작"""
        from agi_core.vision_stream.frame_queue import VisionFrameQueue
        
        queue = VisionFrameQueue(maxsize=5)
        test_data = b"test_frame_data"
        
        await queue.put(test_data)
        assert queue.size == 1
        assert queue.total_frames == 1
        
        frame = await queue.get(timeout=1.0)
        assert frame is not None
        assert frame.data == test_data
        assert queue.size == 0
    
    @pytest.mark.asyncio
    async def test_frame_queue_overflow(self):
        """큐 오버플로우 시 오래된 프레임 드롭"""
        from agi_core.vision_stream.frame_queue import VisionFrameQueue
        
        queue = VisionFrameQueue(maxsize=3)
        
        # 5개 프레임 추가 (maxsize 3 초과)
        for i in range(5):
            await queue.put(f"frame_{i}".encode())
        
        # 마지막 3개만 남아있어야 함
        assert queue.size == 3
        assert queue.dropped_frames == 2
    
    def test_frame_queue_stats(self):
        """통계 확인"""
        from agi_core.vision_stream.frame_queue import VisionFrameQueue
        
        queue = VisionFrameQueue(maxsize=5)
        stats = queue.stats()
        
        assert "current_size" in stats
        assert "total_frames" in stats
        assert "dropped_frames" in stats
        assert "drop_rate" in stats


class TestVisionEventRouter:
    """vision_event_router.py 테스트"""
    
    def setup_method(self):
        from agi_core.vision_stream.vision_event_router import VisionEventRouter
        VisionEventRouter.clear()
    
    def test_route_event(self):
        """이벤트 라우팅"""
        from agi_core.vision_stream.vision_event_router import VisionEventRouter
        
        test_result = {"summary": "test", "activity_type": "coding"}
        VisionEventRouter.route(test_result)
        
        events = VisionEventRouter.get_pending_events()
        assert len(events) == 1
        assert events[0]["source"] == "vision"
        assert events[0]["data"] == test_result
    
    def test_consume_events(self):
        """이벤트 소비"""
        from agi_core.vision_stream.vision_event_router import VisionEventRouter
        
        VisionEventRouter.route({"test": 1})
        VisionEventRouter.route({"test": 2})
        
        events = VisionEventRouter.consume_events()
        assert len(events) == 2
        
        # 소비 후 비어있어야 함
        remaining = VisionEventRouter.get_pending_events()
        assert len(remaining) == 0


class TestSelfAcquisitionIntegration:
    """Self-Acquisition Loop 통합 테스트"""
    
    def setup_method(self):
        from agi_core.self_acquisition_loop import consume_external_events
        consume_external_events()  # 큐 비우기
    
    def test_register_external_event(self):
        """외부 이벤트 등록"""
        from agi_core.self_acquisition_loop import (
            register_external_event,
            consume_external_events
        )
        
        event = {"source": "vision", "data": {"test": True}}
        register_external_event(event)
        
        events = consume_external_events()
        assert len(events) == 1
        assert events[0]["source"] == "vision"
    
    def test_vision_learning_proto_goal_type(self):
        """VISION_LEARNING ProtoGoalType 존재 확인"""
        from agi_core.proto_goal import ProtoGoalType
        
        assert hasattr(ProtoGoalType, "VISION_LEARNING")
        assert ProtoGoalType.VISION_LEARNING.value == "VISION_LEARNING"
    
    def test_run_vision_learning(self):
        """run_vision_learning 함수 테스트"""
        from agi_core.self_acquisition_loop import run_vision_learning
        
        params = {
            "vision_data": {
                "activity_type": "coding",
                "user_actions": ["typing", "scrolling"],
                "summary": "테스트 활동"
            }
        }
        
        result = run_vision_learning(params)
        assert result["success"] is True
        assert result["action_type"] == "vision_learning"
        assert result["activity_type"] == "coding"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
