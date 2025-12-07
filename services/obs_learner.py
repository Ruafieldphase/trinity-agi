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

# Ari Engine 연동
from services.ari_engine import get_ari_engine, ParsedGoal, TaskType

logger = logging.getLogger(__name__)

class OBSLearner:
    """
    OBS 비디오 학습기
    """
    
    def __init__(self, obs_dir: str = "C:/workspace/agi/obs_recode"):
        self.obs_dir = Path(obs_dir)
        self.processed_files_log = self.obs_dir / "processed_videos.json"
        self.processed_files = self._load_processed_log()
        self.ari_engine = get_ari_engine()
        
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
        """새로운 비디오 파일 탐색"""
        if not self.obs_dir.exists():
            logger.warning(f"OBS directory not found: {self.obs_dir}")
            return []
            
        videos = list(self.obs_dir.glob("*.mp4"))
        new_videos = [v for v in videos if v.name not in self.processed_files]
        
        # 최신 순 정렬
        new_videos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return new_videos

    async def analyze_video(self, video_path: Path) -> Optional[Dict[str, Any]]:
        """
        Gemini Vision으로 비디오 분석
        """
        logger.info(f"Analyzing video: {video_path.name}...")
        
        try:
            # 1. 파일 업로드
            video_file = genai.upload_file(path=str(video_path))
            logger.info(f"Uploaded video: {video_file.name}")
            
            # 2. 처리 대기
            while video_file.state.name == "PROCESSING":
                logger.info("Waiting for video processing...")
                await asyncio.sleep(5)
                video_file = genai.get_file(video_file.name)
                
            if video_file.state.name == "FAILED":
                logger.error("Video processing failed on Google side.")
                return None
                
            # 3. 분석 요청
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            
            prompt = """
            Analyze the user's desktop actions in this video to teach an AI automation agent.
            
            1. Identify the high-level **GOAL** of the user (e.g., "Write a report in Notepad", "Search specifically for Python tutorials").
            2. Breakdown the actions into granular **STEPS**.
            3. For each step, identify the **Action** (CLICK, TYPE, OPEN_APP, SCROLL, etc.) and **Target** (App name, UI element text).
            
            Format the output strictly as JSON:
            {
                "goal": "...",
                "task_type": "ui_task",
                "target_app": "...",
                "action_verb": "...",
                "steps": [
                    {"step_index": 1, "action": "OPEN_APP", "target": "Chrome", "reason": "..."},
                    {"step_index": 2, "action": "CLICK", "target": "SearchBar", "parameters": {"x": 0, "y": 0}},
                    {"step_index": 3, "action": "TYPE", "target": "SearchBar", "parameters": {"content": "..."}}
                ]
            }
            """
            
            response = model.generate_content(
                [prompt, video_file],
                generation_config={"response_mime_type": "application/json"}
            )
            
            # 4. 결과 파싱
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
    logging.basicConfig(level=logging.INFO)
    learner = OBSLearner()
    asyncio.run(learner.process_new_videos())
