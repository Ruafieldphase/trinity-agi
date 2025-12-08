"""
OBS Behavioral Learner - 행동 학습 모듈
======================================
Gemini Vision을 사용하여 OBS 녹화 영상을 분석하고,
사용자의 행동 패턴을 Ari Engine의 학습 버퍼에 주입합니다.
"""
import os
import time
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import sys

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Ari Engine 연동
from services.ari_engine import get_ari_engine, ParsedGoal, TaskType

logger = logging.getLogger(__name__)

class OBSLearner:
    """
    OBS 비디오 학습기
    """
    
    def __init__(self, obs_dir: str = "C:/workspace/agi/input/obs_recode"):
        self.obs_dir = Path(obs_dir)
        self.processed_files_log = self.obs_dir / "processed_videos.json"
        self.processed_files = self._load_processed_log()
        self.ari_engine = get_ari_engine()
        self.size_limit_mb = 1024 # 1GB limit for "small" files
        
        # API Key 설정 (환경변수 또는 하드코딩된 값 확인)
        # 실제 환경에서는 os.environ["GOOGLE_API_KEY"]가 설정되어 있어야 함
        
    def _load_processed_log(self) -> List[str]:
        """처리된 파일 목록 로드"""
        if self.processed_files_log.exists():
            try:
                with open(self.processed_files_log, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_processed_log(self):
        """처리된 파일 목록 저장"""
        try:
            with open(self.processed_files_log, 'w', encoding='utf-8') as f:
                json.dump(self.processed_files, f)
        except Exception as e:
            logger.error(f"Failed to save processed log: {e}")

    def get_new_videos(self) -> List[Path]:
        """새로운 비디오 파일 탐색 (용량 제한 적용)"""
        if not self.obs_dir.exists():
            logger.warning(f"OBS directory not found: {self.obs_dir}")
            return []
            
        videos = list(self.obs_dir.glob("*.mp4"))
        new_videos = []
        
        for v in videos:
            if v.name in self.processed_files:
                continue
                
            size_mb = v.stat().st_size / (1024 * 1024)
            if size_mb > self.size_limit_mb:
                logger.info(f"Skipping large video: {v.name} ({size_mb:.2f} MB)")
                continue
                
            new_videos.append(v)
        
        # 최신 순 정렬
        new_videos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return new_videos

    async def analyze_video(self, video_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract frames and analyze with Gemini Vision (no file upload).
        """
        logger.info(f"Analyzing video via frame extraction: {video_path.name}...")
        
        try:
            import cv2
            from PIL import Image
            
            # 1. Extract frames at intervals
            FRAME_INTERVAL_SEC = 10  # Extract 1 frame every 10 seconds
            MAX_FRAMES = 30  # Limit frames to fit in context
            
            cam = cv2.VideoCapture(str(video_path))
            fps = cam.get(cv2.CAP_PROP_FPS)
            total_frames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            frames = []
            current_time = 0
            
            while current_time < duration and len(frames) < MAX_FRAMES:
                cam.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
                ret, frame = cam.read()
                if ret:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb_frame)
                    pil_img.thumbnail((640, 640))
                    frames.append(pil_img)
                current_time += FRAME_INTERVAL_SEC
                
            cam.release()
            logger.info(f"Extracted {len(frames)} frames from {video_path.name}")
            
            if not frames:
                logger.warning("No frames extracted.")
                return None
            
            # 2. Send frames to Gemini
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = """
            Analyze the user's desktop actions in these screenshots to teach an AI automation agent.
            
            1. Identify the high-level **GOAL** of the user.
            2. Breakdown the actions into granular **STEPS**.
            
            Format the output strictly as JSON:
            {
                "goal": "...",
                "task_type": "ui_task",
                "target_app": "...",
                "steps": [
                    {"step_index": 1, "action": "OPEN_APP", "target": "..."},
                    {"step_index": 2, "action": "CLICK", "target": "..."}
                ]
            }
            """
            
            content = [prompt] + frames
            
            response = model.generate_content(
                content,
                generation_config={"response_mime_type": "application/json"}
            )
            
            result_json = json.loads(response.text)
            logger.info(f"Analysis complete: {result_json.get('goal')}")
            
            return result_json
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return None
            
    def inject_knowledge(self, analysis_result: Dict[str, Any]):
        """
        Ari Learning Buffer에 지식 주입
        """
        if not analysis_result:
            return
            
        # Ari Engine의 Learning Buffer에 직접 주입
        # LearningBuffer는 ExecutionPlan과 성공 여부를 받지만,
        # 여기서는 외부 데이터 주입용 메소드가 필요하거나, 
        # 수동으로 딕셔너리를 구성해서 append 해야 함.
        
        # LearningBuffer의 experiences 리스트에 직접 접근하여 추가 (임시)
        # TODO: LearningBuffer에 inject_experience 메소드 추가 권장
        
        experience = {
            "goal": analysis_result.get("goal", "Unknown Goal"),
            "task_type": analysis_result.get("task_type", "ui_task"),
            "target": analysis_result.get("target_app", "Unknown App"),
            "action": analysis_result.get("action_verb", "execute"),
            "steps": [
                {
                    "action": s.get("action"),
                    "status": "success", # 성공한 것으로 간주
                    "retry_count": 0,
                    "reason": s.get("reason")
                }
                for s in analysis_result.get("steps", [])
            ],
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "source": "obs_learning" # 출처 표시
        }
        
        self.ari_engine.learning.experiences.append(experience)
        self.ari_engine.learning._save_buffer()
        logger.info(f"Injected knowledge: {experience['goal']}")
        
    async def process_new_videos(self):
        """새로운 비디오 처리 루프"""
        new_videos = self.get_new_videos()
        if not new_videos:
            logger.info("No new videos found.")
            return
            
        logger.info(f"Found {len(new_videos)} new videos.")
        
        for video in new_videos:
            result = await self.analyze_video(video)
            if result:
                self.inject_knowledge(result)
                self.processed_files.append(video.name)
                self._save_processed_log()
            
            # API 제한 고려 대기
            await asyncio.sleep(5)

# 단독 실행 테스트용
if __name__ == "__main__":
    # Ensure logs directory exists
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        filename=log_dir / "obs_learner.log",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    learner = OBSLearner()
    # Create event loop for async run
    import asyncio
    try:
        logging.info("Starting OBS Learner Loop...")
        asyncio.run(learner.process_new_videos())
    except Exception as e:
        logging.error(f"Fatal error: {e}")
