"""
ShionOperator with Continuous Vision
항상 열린 눈 + Vision Feedback Loop 통합

Author: Sena & Shion
Date: 2025-12-24
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Add workspace to path
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from body.continuous_vision import ContinuousVision
from body.shion_operator import ShionOperator

logger = logging.getLogger("ShionWithVision")


class ShionWithContinuousVision:
    """
    ShionOperator + Continuous Vision 통합

    인간의 눈처럼:
    - 항상 화면을 보고 있음 (Continuous Vision)
    - 변화를 감지하면 맥락을 업데이트
    - 필요할 때 정밀 분석 (ShionOperator Vision Feedback)
    """

    def __init__(
        self,
        operator_mode: str = "DRY_RUN",
        obs_source: str = "Display Capture",
        vision_fps: int = 1
    ):
        # 1. Continuous Vision (항상 열린 눈)
        self.vision = ContinuousVision(
            source_name=obs_source,
            base_fps=vision_fps
        )

        # 2. ShionOperator (정밀 분석 + 행동)
        self.operator = ShionOperator(mode=operator_mode)

        # 3. Visual Context (최근 화면 기억)
        self.visual_memory: list[Dict[str, Any]] = []
        self.max_memory = 10  # 최근 10개 변화 기억

        # 4. Register change callback
        self.vision.on_change(self._on_screen_change)

    def _on_screen_change(self, frame):
        """화면 변화 감지 시 자동 호출"""
        logger.info("👁️ Screen changed - Visual context updated")

        # 최근 변화를 메모리에 저장
        self.visual_memory.append({
            "timestamp": time.time(),
            "frame_size": frame.size,
            "change_detected": True
        })

        # 메모리 크기 제한
        if len(self.visual_memory) > self.max_memory:
            self.visual_memory.pop(0)

    def start_vision(self):
        """연속 시각 시스템 시작 (눈 뜨기)"""
        self.vision.start()
        logger.info("👁️ Continuous Vision Started - Eyes are now OPEN")

    def stop_vision(self):
        """연속 시각 시스템 중지 (눈 감기)"""
        self.vision.stop()
        logger.info("💤 Continuous Vision Stopped - Eyes CLOSED")

    def sense_and_act_with_context(self, goal: str) -> Dict[str, Any]:
        """
        맥락을 유지하면서 행동

        인간처럼:
        1. 항상 화면을 보고 있음 (Continuous Vision)
        2. 최근 변화를 기억하고 있음 (Visual Memory)
        3. 목표가 주어지면 정밀 분석 + 행동 (ShionOperator)
        """

        # 1. 현재 시각 맥락 확인
        context = self.vision.get_visual_context()
        logger.info(f"Visual Context: {context}")

        # 2. 최근 화면 변화 요약
        recent_changes = len(self.visual_memory)
        logger.info(f"Recent screen changes: {recent_changes}")

        # 3. ShionOperator로 정밀 분석 + 행동
        # (현재는 PyAutoGUI 스크린샷 사용, 나중에 OBS 프레임 사용 가능)
        result = self.operator.sense_and_act(goal)

        return {
            "operator_result": result,
            "visual_context": context,
            "recent_changes": recent_changes,
            "visual_memory": self.visual_memory[-3:]  # 최근 3개 변화
        }

    def get_current_view(self):
        """현재 보고 있는 화면 (인간의 시야)"""
        return self.vision.get_current_frame()


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    print("=" * 60)
    print("ShionOperator with Continuous Vision Test")
    print("인간의 눈처럼 항상 열려있는 AGI")
    print("=" * 60)
    print()

    # 1. Create integrated system
    shion = ShionWithContinuousVision(
        operator_mode="DRY_RUN",
        obs_source="Display Capture",  # OBS 설정에 맞게 수정
        vision_fps=1  # 1초에 1프레임
    )

    # 2. Start continuous vision (눈 뜨기)
    shion.start_vision()

    try:
        # 3. 10초간 화면 변화 감지
        print("\n👁️ Watching screen for 10 seconds...")
        print("(Try changing windows or moving things around)\n")

        for i in range(10):
            time.sleep(1)
            context = shion.vision.get_visual_context()
            print(f"[{i+1}s] Frames: {context['frame_count']}, "
                  f"Last change: {context['last_change_seconds_ago']:.1f}s ago")

        # 4. 맥락을 유지하면서 작업 수행
        print("\n🎯 Performing task with visual context...\n")

        result = shion.sense_and_act_with_context(
            "현재 화면에서 브라우저를 찾아주세요"
        )

        print("\n📊 Result:")
        print(f"  Operator Success: {result['operator_result'].get('success')}")
        print(f"  Total Frames Captured: {result['visual_context']['frame_count']}")
        print(f"  Recent Changes: {result['recent_changes']}")

    except KeyboardInterrupt:
        print("\n\nStopped by user")

    finally:
        # 5. Stop vision (눈 감기)
        shion.stop_vision()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
