"""
Continuous Vision System - AGI's Always-On Eyes
인간의 눈처럼 항상 열려있는 시각 시스템

OBS WebSocket을 사용해 연속적으로 화면을 모니터링하고
변화를 감지하며 맥락을 유지합니다.

Author: Sena & Shion
Date: 2025-12-24
"""

import os
import sys
import logging
import time
import json
import base64
import io
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from queue import Queue
from PIL import Image

# Add workspace to path
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.internal_state import get_internal_state

logger = logging.getLogger("ContinuousVision")


class ContinuousVision:
    """
    AGI의 항상 열린 눈 (Human-like Continuous Vision)

    Features:
    - OBS WebSocket으로 연속 화면 캡처
    - 변화 감지 (Scene Change Detection)
    - 맥락 유지 (Visual Context Memory)
    - 에너지 기반 프레임레이트 조절
    """

    def __init__(
        self,
        obs_host: str = "127.0.0.1",
        obs_port: int = 4455,
        obs_password: str = "",
        source_name: str = "Display Capture",  # OBS Source 이름
        base_fps: int = 1,  # 기본 1fps (에너지 절약)
    ):
        self.obs_host = obs_host
        self.obs_port = obs_port
        self.obs_password = obs_password
        self.source_name = source_name
        self.base_fps = base_fps

        # OBS 연결 (lazy)
        self.obs_client = None
        self.is_running = False

        # Visual Context (최근 프레임 메모리)
        self.current_frame: Optional[Image.Image] = None
        self.previous_frame: Optional[Image.Image] = None
        self.frame_count = 0

        # Change Detection
        self.change_threshold = 0.05  # 5% 이상 변화 감지
        self.last_change_time = time.time()

        # Callbacks
        self.on_change_callbacks: list[Callable] = []

        # Thread
        self.vision_thread: Optional[threading.Thread] = None
        self.frame_queue = Queue(maxsize=10)

    def connect_obs(self):
        """OBS WebSocket 연결"""
        try:
            import obsws_python as obs
            self.obs_client = obs.ReqClient(
                host=self.obs_host,
                port=self.obs_port,
                password=self.obs_password,
                timeout=5.0
            )
            logger.info(f"✅ OBS Connected: {self.obs_host}:{self.obs_port}")
            return True
        except Exception as e:
            logger.error(f"❌ OBS Connection Failed: {e}")
            return False

    def start(self):
        """연속 시각 시스템 시작 (인간의 눈 뜨기)"""
        if self.is_running:
            logger.warning("Vision already running")
            return

        if not self.obs_client and not self.connect_obs():
            logger.error("Cannot start vision without OBS connection")
            return

        self.is_running = True
        self.vision_thread = threading.Thread(target=self._vision_loop, daemon=True)
        self.vision_thread.start()
        logger.info("👁️ Continuous Vision Started (Eyes Open)")

    def stop(self):
        """연속 시각 시스템 중지 (눈 감기)"""
        self.is_running = False
        if self.vision_thread:
            self.vision_thread.join(timeout=2.0)
        logger.info("💤 Continuous Vision Stopped (Eyes Closed)")

    def _vision_loop(self):
        """메인 시각 루프 (인간의 눈이 끊임없이 보듯)"""
        while self.is_running:
            try:
                # 1. 현재 에너지 상태 확인
                state = get_internal_state()

                # 2. 에너지 기반 프레임레이트 조절
                if state.energy < 0.3:
                    # 에너지 낮음 → 느린 프레임레이트 (휴식 모드)
                    fps = self.base_fps * 0.5
                elif state.energy > 0.7:
                    # 에너지 높음 → 빠른 프레임레이트 (집중 모드)
                    fps = self.base_fps * 2
                else:
                    # 정상 에너지
                    fps = self.base_fps

                interval = 1.0 / fps

                # 3. OBS에서 현재 화면 캡처
                frame = self._capture_current_frame()

                if frame:
                    # 4. 변화 감지
                    change_detected = self._detect_change(frame)

                    # 5. 프레임 저장
                    self.previous_frame = self.current_frame
                    self.current_frame = frame
                    self.frame_count += 1

                    # 6. 변화 발생 시 콜백 실행
                    if change_detected:
                        self._trigger_change_callbacks(frame)

                    # 7. 프레임을 큐에 추가 (다른 모듈에서 사용 가능)
                    if not self.frame_queue.full():
                        self.frame_queue.put(frame)

                # 8. 리듬에 맞춰 대기
                time.sleep(interval)

            except Exception as e:
                logger.error(f"Vision loop error: {e}")
                time.sleep(1.0)

    def _capture_current_frame(self) -> Optional[Image.Image]:
        """OBS에서 현재 프레임 캡처"""
        try:
            # OBS source screenshot 가져오기
            response = self.obs_client.get_source_screenshot(
                name=self.source_name,
                img_format="png",
                width=1280,  # 해상도 조절 (성능 vs 품질)
                height=720,
                quality=85  # 압축 품질
            )

            # Base64 디코딩
            if hasattr(response, 'image_data'):
                img_data = response.image_data
            elif isinstance(response, dict):
                img_data = response.get('imageData')
            else:
                return None

            # data:image/png;base64, 제거
            if img_data and img_data.startswith('data:'):
                img_data = img_data.split(',', 1)[1]

            # PIL Image로 변환
            img_bytes = base64.b64decode(img_data)
            image = Image.open(io.BytesIO(img_bytes))

            return image

        except Exception as e:
            logger.debug(f"Frame capture error: {e}")
            return None

    def _detect_change(self, new_frame: Image.Image) -> bool:
        """화면 변화 감지 (간단한 픽셀 차이)"""
        if self.current_frame is None:
            return True  # 첫 프레임은 항상 변화

        try:
            # 두 프레임을 비교 (간단한 방법: 해시 비교)
            import hashlib

            current_hash = hashlib.md5(self.current_frame.tobytes()).hexdigest()
            new_hash = hashlib.md5(new_frame.tobytes()).hexdigest()

            if current_hash != new_hash:
                self.last_change_time = time.time()
                return True

            return False

        except Exception as e:
            logger.debug(f"Change detection error: {e}")
            return False

    def on_change(self, callback: Callable[[Image.Image], None]):
        """화면 변화 시 실행할 콜백 등록"""
        self.on_change_callbacks.append(callback)

    def _trigger_change_callbacks(self, frame: Image.Image):
        """변화 감지 시 콜백 실행"""
        for callback in self.on_change_callbacks:
            try:
                callback(frame)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def get_current_frame(self) -> Optional[Image.Image]:
        """현재 프레임 가져오기 (다른 모듈에서 사용)"""
        return self.current_frame

    def get_visual_context(self) -> Dict[str, Any]:
        """현재 시각 맥락 정보"""
        return {
            "frame_count": self.frame_count,
            "has_current_frame": self.current_frame is not None,
            "last_change_seconds_ago": time.time() - self.last_change_time,
            "is_running": self.is_running,
        }


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Continuous Vision Test ===\n")

    # 1. Create vision system
    vision = ContinuousVision(
        source_name="Display Capture",  # OBS Source 이름 (설정에 맞게 수정)
        base_fps=1  # 1초에 1프레임
    )

    # 2. Register change callback
    def on_screen_change(frame: Image.Image):
        print(f"📸 Screen changed! Frame size: {frame.size}")

    vision.on_change(on_screen_change)

    # 3. Start vision (눈 뜨기)
    vision.start()

    try:
        # 4. Run for 30 seconds
        for i in range(30):
            time.sleep(1)
            context = vision.get_visual_context()
            print(f"[{i+1}s] Frames: {context['frame_count']}, "
                  f"Last change: {context['last_change_seconds_ago']:.1f}s ago")

    except KeyboardInterrupt:
        print("\nStopped by user")

    finally:
        # 5. Stop vision (눈 감기)
        vision.stop()

    print("\n=== Test Complete ===")
