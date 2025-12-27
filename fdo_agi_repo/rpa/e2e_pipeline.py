"""
Phase 2.5 E2E Integration Pipeline
YouTube Learning → RPA Execution → Resonance Ledger Feedback Loop

Architecture:
1. YouTube Learner: 영상 분석 및 절차 추출
2. RPA Core: 화면 자동화 실행
3. Trial-Error Engine: 실패 시 재시도 및 학습
4. Resonance Ledger: 모든 이벤트 기록
5. Task Queue: 비동기 작업 처리

Flow:
  YouTube URL → Analyze → Extract Steps → Execute → Learn → Log
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from rpa.youtube_learner import YouTubeLearner, YouTubeLearnerConfig, VideoAnalysis
from rpa.core import RPACore, RPACoreConfig
from rpa.trial_error_engine import TrialErrorEngine, TrialErrorConfig


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class E2EConfig:
    """E2E 통합 설정"""
    output_dir: Path = Path("outputs/e2e_integration")
    ledger_path: Path = Path("memory/resonance_ledger.jsonl")
    
    # 모듈별 설정
    youtube_config: Optional[YouTubeLearnerConfig] = None
    rpa_config: Optional[RPACoreConfig] = None
    trial_error_config: Optional[TrialErrorConfig] = None
    
    # 통합 설정
    enable_auto_execution: bool = False  # 자동 실행 (위험할 수 있음)
    max_steps: int = 20  # 최대 실행 스텝 수
    
    log_level: str = "INFO"


@dataclass
class LearningTask:
    """학습 작업"""
    task_id: str
    youtube_url: str
    video_analysis: Optional[VideoAnalysis] = None
    execution_steps: Optional[List[Dict[str, Any]]] = None
    execution_results: Optional[List[Dict[str, Any]]] = None
    status: str = "pending"  # pending, analyzing, executing, completed, failed
    created_at: Optional[str] = None
    
    def __post_init__(self):
        if self.task_id is None:
            self.task_id = str(uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.execution_steps is None:
            self.execution_steps = []
        if self.execution_results is None:
            self.execution_results = []


# ============================================================================
# E2E Integration Pipeline
# ============================================================================

class E2EPipeline:
    """Phase 2.5 End-to-End Integration Pipeline"""
    
    def __init__(self, config: Optional[E2EConfig] = None):
        self.config = config or E2EConfig()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.config.log_level)
        
        # Output 디렉토리 생성
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 모듈 초기화
        self.youtube_learner = YouTubeLearner(
            self.config.youtube_config or YouTubeLearnerConfig()
        )
        self.rpa_core = RPACore(
            self.config.rpa_config or RPACoreConfig()
        )
        self.trial_error_engine = TrialErrorEngine(
            self.config.trial_error_config or TrialErrorConfig()
        )
        
        self.logger.info("E2E Pipeline initialized")
    
    async def run_learning_task(self, youtube_url: str) -> LearningTask:
        """
        YouTube 영상 학습 작업 실행 (전체 파이프라인)
        
        Steps:
        1. YouTube 영상 분석
        2. 실행 절차 추출
        3. RPA 자동화 실행 (옵션)
        4. Resonance Ledger 기록
        """
        task = LearningTask(
            task_id=str(uuid4()),
            youtube_url=youtube_url
        )
        
        self.logger.info(f"Starting learning task: {task.task_id}")
        await self._log_event("task_start", task)
        
        try:
            # Step 1: YouTube 영상 분석
            task.status = "analyzing"
            self.logger.info("Step 1: Analyzing YouTube video...")
            
            video_analysis = await self.youtube_learner.analyze_video(youtube_url)
            task.video_analysis = video_analysis
            
            await self._log_event("video_analyzed", task, {
                "video_id": video_analysis.video_id,
                "title": video_analysis.title,
                "duration": video_analysis.duration,
                "subtitles_count": len(video_analysis.subtitles),
                "keywords": video_analysis.keywords
            })
            
            # Step 2: 실행 절차 추출
            self.logger.info("Step 2: Extracting execution steps...")
            
            execution_steps = self._extract_steps_from_analysis(video_analysis)
            task.execution_steps = execution_steps
            
            await self._log_event("steps_extracted", task, {
                "steps_count": len(execution_steps)
            })
            
            # Step 3: RPA 실행 (옵션)
            if self.config.enable_auto_execution and execution_steps:
                task.status = "executing"
                self.logger.info("Step 3: Executing RPA automation...")
                
                execution_results = await self._execute_steps(execution_steps)
                task.execution_results = execution_results
                
                await self._log_event("execution_completed", task, {
                    "success_count": sum(1 for r in execution_results if r.get("success")),
                    "failure_count": sum(1 for r in execution_results if not r.get("success"))
                })
            else:
                self.logger.info("Step 3: Skipping execution (auto_execution disabled)")
                await self._log_event("execution_skipped", task)
            
            # Step 4: 완료
            task.status = "completed"
            await self._log_event("task_completed", task)
            
            self.logger.info(f"✅ Learning task completed: {task.task_id}")
            
            # 결과 저장
            await self._save_task_result(task)
            
            return task
        
        except Exception as e:
            task.status = "failed"
            error_msg = str(e)
            
            self.logger.error(f"❌ Learning task failed: {error_msg}")
            await self._log_event("task_failed", task, {"error": error_msg})
            
            raise
    
    def _extract_steps_from_analysis(
        self,
        video_analysis: VideoAnalysis
    ) -> List[Dict[str, Any]]:
        """
        영상 분석 결과에서 실행 절차 추출
        
        Strategy:
        1. 자막에서 명령어 패턴 추출 (예: "click", "type", "open")
        2. 프레임 분석으로 UI 요소 식별
        3. 순서대로 실행 스텝 생성
        """
        steps = []
        
        # 간단한 휴리스틱: 자막에서 액션 키워드 추출
        action_keywords = {
            "click": "click",
            "type": "type",
            "open": "open",
            "press": "press",
            "drag": "drag",
            "move": "move"
        }
        
        for subtitle in video_analysis.subtitles:
            text_lower = subtitle.text.lower()
            
            for keyword, action in action_keywords.items():
                if keyword in text_lower:
                    steps.append({
                        "action": action,
                        "timestamp": subtitle.start,
                        "description": subtitle.text,
                        "params": {}
                    })
                    
                    if len(steps) >= self.config.max_steps:
                        break
            
            if len(steps) >= self.config.max_steps:
                break
        
        self.logger.info(f"Extracted {len(steps)} execution steps")
        return steps
    
    async def _execute_steps(
        self,
        steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """RPA로 실행 스텝 실행"""
        results = []
        
        for i, step in enumerate(steps):
            self.logger.info(f"Executing step {i+1}/{len(steps)}: {step['action']}")
            
            try:
                # Trial-and-Error 방식으로 실행
                success, trial_results = await self.trial_error_engine.execute_with_retry(
                    task_fn=self._execute_single_step,
                    task_name=step['action'],
                    initial_params={**step['params'], "action": step['action'], "description": step['description']},
                    state={"step_index": i, "description": step['description']}
                )
                
                results.append({
                    "step_index": i,
                    "action": step['action'],
                    "success": success,
                    "trials": len(trial_results),
                    "description": step['description']
                })
            
            except Exception as e:
                self.logger.error(f"Step {i+1} failed: {e}")
                results.append({
                    "step_index": i,
                    "action": step['action'],
                    "success": False,
                    "error": str(e),
                    "description": step['description']
                })
        
        return results
    
    async def _execute_single_step(self, **params) -> bool:
        """단일 스텝 실행 (RPACore 활용)"""
        action = params.get("action")
        value = params.get("value", "")
        desc = params.get("description", "")
        
        self.logger.info(f"🎬 Executing action: {action} ({desc})")
        
        try:
            if action == "click":
                # 좌표가 있으면 클릭, 없으면 텍스트나 템플릿 검색 (여기선 단순화)
                x, y = params.get("x"), params.get("y")
                if x is not None and y is not None:
                    await self.rpa_core.click(x, y)
                else:
                    self.logger.warning("Click requested without coordinates.")
                    return False
            elif action == "type":
                await self.rpa_core.type_text(value)
            elif action == "press":
                await self.rpa_core.press_key(value)
            elif action == "open":
                # URL 열기 (브라우저나 쉘 사용)
                import webbrowser
                webbrowser.open(value)
            elif action == "wait":
                wait_time = float(value) if value else 1.0
                await asyncio.sleep(wait_time)
            else:
                self.logger.info(f"Unknown action type: {action}. Simulating success.")
                await asyncio.sleep(0.5)
            
            return True
        except Exception as e:
            self.logger.error(f"Action failed: {e}")
            return False
    
    async def _log_event(
        self,
        event_type: str,
        task: LearningTask,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Resonance Ledger에 이벤트 기록"""
        event = {
            "ts": datetime.utcnow().isoformat() + "+00:00",
            "event": f"e2e_{event_type}",
            "task_id": task.task_id,
            "youtube_url": task.youtube_url,
            "status": task.status,
            **(metadata or {})
        }
        # Ensure ledger directory exists
        ledger_dir = self.config.ledger_path.parent
        try:
            ledger_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # 디렉토리 생성 실패 시에도 최대한 진행 (직후 파일 열기에서 에러 발생 시 상위에서 처리)
            pass

        with open(self.config.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        self.logger.debug(f"Logged event: {event_type}")
    
    async def _save_task_result(self, task: LearningTask):
        """작업 결과 저장"""
        output_file = self.config.output_dir / f"task_{task.task_id}.json"
        
        # JSON 직렬화 가능한 형식으로 변환
        task_data = {
            "task_id": task.task_id,
            "youtube_url": task.youtube_url,
            "status": task.status,
            "created_at": task.created_at,
            "video_analysis": {
                "video_id": task.video_analysis.video_id if task.video_analysis else None,
                "title": task.video_analysis.title if task.video_analysis else None,
                "keywords": task.video_analysis.keywords if task.video_analysis else [],
                "summary": task.video_analysis.summary if task.video_analysis else None
            } if task.video_analysis else None,
            "execution_steps_count": len(task.execution_steps) if task.execution_steps else 0,
            "execution_results_count": len(task.execution_results) if task.execution_results else 0,
            "execution_steps": task.execution_steps or [],
            "execution_results": task.execution_results or []
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Task result saved: {output_file}")


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """CLI 인터페이스"""
    import argparse
    
    parser = argparse.ArgumentParser(description="E2E Learning Pipeline - YouTube to RPA")
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no execution)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Set logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level)
    
    pipeline = E2EPipeline()
    
    print(f"\n🚀 Starting E2E Learning Task")
    print(f"   URL: {args.url}")
    if args.dry_run:
        print(f"   Mode: DRY RUN")
    
    task = await pipeline.run_learning_task(args.url)
    
    print(f"\n✅ Task Completed:")
    print(f"   Task ID: {task.task_id}")
    print(f"   Status: {task.status}")
    print(f"   Steps Extracted: {len(task.execution_steps) if task.execution_steps else 0}")
    print(f"   Steps Executed: {len(task.execution_results) if task.execution_results else 0}")


if __name__ == "__main__":
    asyncio.run(main())
