"""
Live Frame Analyzer
실시간 프레임 분석 - Gemini Vision 활용

비노체의 화면 활동을 분석하여 패턴을 추출
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timezone

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

from .frame_queue import get_queue, VisionFrame
from .vision_event_router import VisionEventRouter

logger = logging.getLogger("LiveFrameAnalyzer")

# Vertex AI 설정 (vision_motor_bridge.py 참조)
PROJECT_ID = "naeda-genesis"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.0-flash-exp"

# 분석 결과 저장 경로
VISION_LOG_PATH = Path(__file__).parent.parent.parent / "memory" / "vision_events.jsonl"


class LiveFrameAnalyzer:
    """실시간 프레임 분석기"""
    
    def __init__(self, analysis_interval: float = 5.0):
        """
        Args:
            analysis_interval: 분석 주기 (초) - 매 프레임이 아닌 주기적 분석
        """
        self.analysis_interval = analysis_interval
        self.model: Optional[GenerativeModel] = None
        self._running = False
        self._analyzed_count = 0
        
        if VERTEX_AVAILABLE:
            try:
                vertexai.init(project=PROJECT_ID, location=LOCATION)
                self.model = GenerativeModel(MODEL_NAME)
                logger.info(f"✅ Gemini Vision initialized: {MODEL_NAME}")
            except Exception as e:
                logger.warning(f"Vertex AI 초기화 실패: {e}")
    
    async def analyze_frame(self, frame: VisionFrame) -> Dict[str, Any]:
        """
        단일 프레임 분석
        
        Returns:
            분석 결과 (actions, objects, patterns, summary)
        """
        if not self.model:
            return {"error": "Gemini model not available", "frame_id": frame.frame_id}
        
        prompt = """
        분석 중인 화면 스크린샷에서 주요 UI 요소들의 정보를 추출해주세요.
        결과는 반드시 다음 구조의 JSON만 반환해야 합니다:
        {
            "summary": "화면 상황 요약 (한국어)",
            "current_app": "활성 애플리케이션 이름",
            "user_actions": ["감지된 사용자 행동"],
            "ui_elements": [
                {
                    "name": "요소 이름 (예: 로그인 버튼, 검색창)",
                    "type": "button | input | icon | text",
                    "rect_normalized": [ymin, xmin, ymax, xmax],  // 0.0-1.0 사이의 정규화된 좌표
                    "description": "요소에 대한 짧은 묘사"
                }
            ],
            "activity_type": "작업 유형 (coding, browsing, communication, media, other)",
            "focus_level": 0.0-1.0
        }
        중요: rect_normalized는 [ymin, xmin, ymax, xmax] 순서이며, 각 값은 0에서 1 사이의 실수여야 합니다.
        
        try:
            image_part = Part.from_data(data=frame.data, mime_type="image/jpeg")
            response = await asyncio.to_thread(
                self.model.generate_content,
                [image_part, prompt]
            )
            
            text = response.text.replace("```json", "").replace("```", "").strip()
            result = json.loads(text)
            result["frame_id"] = frame.frame_id
            result["timestamp"] = frame.timestamp.isoformat()
            
            self._analyzed_count += 1
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 실패: {e}")
            return {"error": "JSON parse error", "frame_id": frame.frame_id, "raw": response.text[:200]}
        except Exception as e:
            logger.error(f"분석 실패: {e}")
            return {"error": str(e), "frame_id": frame.frame_id}
    
    def _save_result(self, result: Dict[str, Any]) -> None:
        """분석 결과를 JSONL 파일에 저장"""
        try:
            VISION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(VISION_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"결과 저장 실패: {e}")
    
    async def run(self) -> None:
        """메인 분석 루프"""
        queue = get_queue()
        self._running = True
        
        logger.info(f"🔬 Live Frame Analyzer started (interval: {self.analysis_interval}s)")
        
        while self._running:
            try:
                # 최신 프레임 획득 (타임아웃 대기)
                frame = await queue.get(timeout=self.analysis_interval)
                
                if frame:
                    logger.info(f"📷 Analyzing frame #{frame.frame_id}...")
                    result = await self.analyze_frame(frame)
                    
                    if "error" not in result:
                        # 결과 저장 및 라우팅
                        self._save_result(result)
                        VisionEventRouter.route(result)
                        logger.info(f"✅ Frame #{frame.frame_id}: {result.get('summary', 'N/A')[:50]}...")
                    else:
                        logger.warning(f"⚠️ Frame #{frame.frame_id} error: {result.get('error')}")
                
                # 분석 주기 대기
                await asyncio.sleep(self.analysis_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"분석 루프 오류: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"🛑 Live Frame Analyzer stopped. Analyzed {self._analyzed_count} frames.")
    
    def stop(self) -> None:
        """분석기 중지"""
        self._running = False
    
    @property
    def analyzed_count(self) -> int:
        return self._analyzed_count


async def run_live_vision(analysis_interval: float = 5.0) -> None:
    """Live Vision 분석 시작 (편의 함수)"""
    analyzer = LiveFrameAnalyzer(analysis_interval=analysis_interval)
    await analyzer.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    asyncio.run(run_live_vision())
