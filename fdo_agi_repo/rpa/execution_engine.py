"""
RPA Execution Engine - Phase 3 Live Execution
전체 파이프라인 통합: Extractor → Mapper → Executor → Verifier

Author: Gitko AGI Team
Date: 2025-10-31
Phase: 2.5 Week 2 Day 13
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .step_extractor import StepExtractor
from .action_mapper import ActionMapper
from .executor import RPAExecutor
from .verifier import ExecutionVerifier
from .failsafe import Failsafe, enable_failsafe
from .core import RPACore

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """실행 모드"""
    DRY_RUN = "dry_run"      # 시뮬레이션만
    LIVE = "live"            # 실제 실행
    VERIFY_ONLY = "verify"   # 검증만


@dataclass
class ExecutionConfig:
    """실행 설정"""
    mode: ExecutionMode = ExecutionMode.DRY_RUN
    enable_verification: bool = True
    enable_screenshots: bool = True
    enable_failsafe: bool = True
    confirmation_required: bool = True  # Live 모드 시 확인 프롬프트
    
    # Verifier 설정
    similarity_threshold: float = 0.95
    comparison_method: str = "SSIM"
    
    # Failsafe 설정
    timeout: Optional[float] = 30.0
    max_retries: int = 3
    
    # 출력 디렉토리
    output_dir: Path = Path("outputs/execution")


@dataclass
class ExecutionResult:
    """실행 결과"""
    success: bool
    mode: ExecutionMode
    tutorial_name: str
    total_actions: int
    executed_actions: int
    verified_actions: int
    failed_actions: int
    execution_time: float
    
    # 상세 결과
    action_results: List[Dict[str, Any]]
    verification_results: List[Dict[str, Any]]
    
    # 에러
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "success": self.success,
            "mode": self.mode.value,
            "tutorial_name": self.tutorial_name,
            "total_actions": self.total_actions,
            "executed_actions": self.executed_actions,
            "verified_actions": self.verified_actions,
            "failed_actions": self.failed_actions,
            "execution_time": self.execution_time,
            "action_results": self.action_results,
            "verification_results": self.verification_results,
            "errors": self.errors
        }


class ExecutionEngine:
    """
    RPA 실행 엔진
    
    전체 파이프라인:
    1. Extract: 튜토리얼 텍스트 → 단계 추출
    2. Map: 단계 → RPA 액션 매핑
    3. Execute: 액션 실행 (Dry-run or Live)
    4. Verify: 실행 검증 (스크린샷 비교)
    
    Features:
    - Dry-run 모드 (안전한 테스트)
    - Live 모드 (실제 실행)
    - 자동 검증
    - Failsafe (긴급 중단, 재시도, 타임아웃)
    - 상세 리포트 생성
    """
    
    def __init__(self, config: ExecutionConfig):
        """
        Args:
            config: 실행 설정
        """
        self.config = config
        
        # 출력 디렉토리 생성
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 컴포넌트 초기화
        self.extractor = StepExtractor()
        self.mapper = ActionMapper()
        self.executor = RPAExecutor(dry_run=(config.mode == ExecutionMode.DRY_RUN))
        
        if config.enable_verification:
            self.verifier = ExecutionVerifier(
                output_dir=config.output_dir / "verification",
                enable_screenshots=config.enable_screenshots,
                enable_comparison=True,
                comparison_method=config.comparison_method,
                similarity_threshold=config.similarity_threshold
            )
        else:
            self.verifier = None
        
        if config.enable_failsafe:
            self.failsafe = Failsafe()
            enable_failsafe()  # 함수 호출
        else:
            self.failsafe = None
        
        self.rpa_core = RPACore()
        
        logger.info(f"ExecutionEngine initialized: mode={config.mode.value}, "
                   f"verification={config.enable_verification}, "
                   f"failsafe={config.enable_failsafe}")
    
    def execute_tutorial(
        self,
        tutorial_text: str,
        tutorial_name: str = "tutorial"
    ) -> ExecutionResult:
        """
        튜토리얼 실행
        
        Args:
            tutorial_text: 튜토리얼 텍스트
            tutorial_name: 튜토리얼 이름
        
        Returns:
            ExecutionResult
        """
        import time
        start_time = time.time()

        # Prepare containers for partial-progress safe returns
        steps: List[Dict[str, Any]] = []
        actions: List[Dict[str, Any]] = []
        action_results: List[Dict[str, Any]] = []
        verification_results: List[Dict[str, Any]] = []
        failed_count: int = 0
        
        logger.info(f"Starting tutorial execution: {tutorial_name} (mode={self.config.mode.value})")
        
        # Live 모드면 확인 프롬프트
        if self.config.mode == ExecutionMode.LIVE and self.config.confirmation_required:
            if not self._confirm_live_execution(tutorial_name):
                logger.warning("Live execution cancelled by user")
                return ExecutionResult(
                    success=False,
                    mode=self.config.mode,
                    tutorial_name=tutorial_name,
                    total_actions=0,
                    executed_actions=0,
                    verified_actions=0,
                    failed_actions=0,
                    execution_time=0.0,
                    action_results=[],
                    verification_results=[],
                    errors=["Cancelled by user"]
                )
        
        try:
            # 1. Extract: 튜토리얼 → 단계
            logger.info("Step 1: Extracting steps from tutorial...")
            
            # 간단한 텍스트 파싱 (줄 단위)
            step_num = 0
            for line in tutorial_text.strip().split('\n'):
                line = line.strip()
                # 숫자로 시작하는 줄을 단계로 인식
                if line and (line[0].isdigit() or line.startswith('-')):
                    step_num += 1
                    
                    # instruction에서 action 추출 (간단한 키워드 매칭)
                    instruction_lower = line.lower()
                    action = "CLICK"  # 기본값
                    
                    if "type" in instruction_lower or "입력" in instruction_lower:
                        action = "TYPE"
                    elif "click" in instruction_lower or "클릭" in instruction_lower:
                        action = "CLICK"
                    elif "install" in instruction_lower or "설치" in instruction_lower:
                        action = "INSTALL"
                    elif "open" in instruction_lower or "실행" in instruction_lower or "열기" in instruction_lower:
                        action = "CLICK"  # 실행도 click으로
                    
                    steps.append({
                        "step": step_num,
                        "action": action,
                        "instruction": line,
                        "confidence": 1.0
                    })
            
            logger.info(f"Extracted {len(steps)} steps")
            
            if not steps:
                raise ValueError("No steps extracted from tutorial")
            
            # 2. Map: 단계 → 액션  
            logger.info("Step 2: Mapping steps to actions...")
            # ActionMapper가 Action 객체를 반환하므로, 각 Action의 step dict 사용
            action_objects = self.mapper.map_steps(steps)
            actions = [action_obj.step for action_obj in action_objects]
            logger.info(f"Mapped {len(actions)} actions")
            
            if not actions:
                raise ValueError("No actions mapped from steps")
            
            # 3. Execute: 액션 실행 (RPAExecutor는 steps dict 리스트를 받음)
            logger.info(f"Step 3: Executing {len(actions)} actions...")

            if self.config.mode != ExecutionMode.VERIFY_ONLY:
                # RPAExecutor.execute_steps 사용
                execution_report = self.executor.execute_steps(actions)
                for i, step_result in enumerate(execution_report.results, 1):
                    result_dict = step_result.get("result", {})
                    action_results.append({
                        "action_index": i,
                        "action_type": step_result.get("action", "unknown"),
                        "success": result_dict.get("success", False),
                        "duration": result_dict.get("duration", 0.0),
                        "error": result_dict.get("error")
                    })
                
                # ExecutionReport에서 failed 카운트 가져오기
                failed_count = execution_report.failed

                # BQI Phase 6 Integration (best-effort; never fail the run)
                try:
                    logger.info("Step 4: Evaluating execution with Binoche...")
                    rpa_result_for_bqi = {
                        "success": execution_report.success,
                        "output_path": None,
                        "error": execution_report.results[-1].get("result", {}).get("error") if not execution_report.success else None
                    }
                    bqi_coord_for_bqi = {"priority": 1, "emotion": "neutral", "rhythm": "execution"}

                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    bqi_decision = loop.run_until_complete(
                        self.rpa_core.evaluate_and_decide(tutorial_name, rpa_result_for_bqi, bqi_coord_for_bqi)
                    )
                    logger.info(f"Binoche decision: {bqi_decision}")
                except Exception as bqi_err:
                    # Log and continue; do not let BQI failures zero-out results
                    logger.warning(f"Binoche evaluation skipped due to error: {bqi_err}")
            else:
                failed_count = 0
            
            # 실행 완료
            execution_time = time.time() - start_time
            
            result = ExecutionResult(
                success=(failed_count == 0),
                mode=self.config.mode,
                tutorial_name=tutorial_name,
                total_actions=len(actions),
                executed_actions=len(action_results),
                verified_actions=len(verification_results),
                failed_actions=failed_count,
                execution_time=execution_time,
                action_results=action_results,
                verification_results=verification_results,
                errors=[]
            )
            
            logger.info(f"Tutorial execution complete: {result.executed_actions}/{result.total_actions} "
                       f"actions executed, {result.failed_actions} failed, "
                       f"time={execution_time:.2f}s")
            
            return result
        
        except Exception as e:
            # Preserve partial progress if available
            logger.error(f"Tutorial execution failed: {e}")
            execution_time = time.time() - start_time

            return ExecutionResult(
                success=False,
                mode=self.config.mode,
                tutorial_name=tutorial_name,
                total_actions=len(actions) if actions is not None else 0,
                executed_actions=len(action_results) if action_results is not None else 0,
                verified_actions=len(verification_results) if verification_results is not None else 0,
                failed_actions=failed_count if isinstance(failed_count, int) else 0,
                execution_time=execution_time,
                action_results=action_results or [],
                verification_results=verification_results or [],
                errors=[str(e)]
            )
    
    def _confirm_live_execution(self, tutorial_name: str) -> bool:
        """
        Live 실행 확인 프롬프트
        
        Args:
            tutorial_name: 튜토리얼 이름
        
        Returns:
            True면 실행, False면 취소
        """
        print("\n" + "="*60)
        print("  ⚠️  LIVE EXECUTION WARNING  ⚠️")
        print("="*60)
        print(f"  Tutorial: {tutorial_name}")
        print(f"  Mode: LIVE (실제 실행)")
        print("  ")
        print("  This will execute REAL actions on your system:")
        print("  - Mouse clicks")
        print("  - Keyboard input")
        print("  - Application launches")
        print("  ")
        print("  Emergency stop: Move mouse to screen corner")
        print("="*60)
        
        response = input("  Continue? (yes/no): ").strip().lower()
        
        if response in ["yes", "y"]:
            print("  ✅ Starting live execution...\n")
            return True
        else:
            print("  ❌ Cancelled\n")
            return False
    
    def generate_report(self, result: ExecutionResult, output_file: Path):
        """
        실행 리포트 생성
        
        Args:
            result: 실행 결과
            output_file: 출력 파일 경로
        """
        import json
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Execution report saved: {output_file}")
    
    def print_summary(self, result: ExecutionResult):
        """
        실행 결과 요약 출력
        
        Args:
            result: 실행 결과
        """
        print("\n" + "="*60)
        print("  Execution Summary")
        print("="*60)
        print(f"  Tutorial: {result.tutorial_name}")
        print(f"  Mode: {result.mode.value}")
        print(f"  Status: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
        print(f"  ")
        print(f"  Total Actions: {result.total_actions}")
        print(f"  Executed: {result.executed_actions}")
        print(f"  Verified: {result.verified_actions}")
        print(f"  Failed: {result.failed_actions}")
        print(f"  ")
        print(f"  Execution Time: {result.execution_time:.2f}s")
        
        if result.errors:
            print(f"  ")
            print(f"  Errors:")
            for error in result.errors:
                print(f"    - {error}")
        
        print("="*60 + "\n")
