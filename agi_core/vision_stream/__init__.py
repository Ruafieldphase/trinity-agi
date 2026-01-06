"""
Vision Stream Package
OBS → WebSocket → Frame Queue → Vision Analysis → Self-Acquisition Loop

실시간 비전 입력을 통한 AGI 학습 시스템
"""

from .frame_queue import VisionFrameQueue
from .vision_event_router import VisionEventRouter

__all__ = [
    "VisionFrameQueue",
    "VisionEventRouter",
]
