"""
RPA Executor
Phase 2.5 Week 2 Day 11

RPA 실행 엔진
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import time
import logging
from pathlib import Path

from .action_mapper import ActionMapper
from .actions import Action, ActionResult

logger = logging.getLogger(__name__)


@dataclass
class ExecutionReport:
    """실행 리포트"""
    total_steps: int
    successful: int
    failed: int
    skipped: int
    duration: float
    dry_run: bool
    results: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'total_steps': self.total_steps,
            'successful': self.successful,
            'failed': self.failed,
            'skipped': self.skipped,
            'duration': self.duration,
            'dry_run': self.dry_run,
            'success_rate': f"{self.successful / self.total_steps * 100:.1f}%" if self.total_steps > 0 else "0%",
            'results': self.results
        }
    
    def print_summary(self):
        """요약 출력"""
        print("\n" + "="*60)
        print(f"  RPA Execution Report ({'DRY-RUN' if self.dry_run else 'LIVE'})")
        print("="*60)
        print(f"Total Steps:   {self.total_steps}")
        print(f"Successful:    {self.successful} ✅")
        print(f"Failed:        {self.failed} ❌")
        print(f"Skipped:       {self.skipped} ⏭️")
        print(f"Duration:      {self.duration:.2f}s")
        
        if self.total_steps > 0:
            success_rate = self.successful / self.total_steps * 100
            print(f"Success Rate:  {success_rate:.1f}%")
        
        print("="*60 + "\n")


class RPAExecutor:
    """RPA 실행 엔진"""
    
    def __init__(self, dry_run: bool = True, verbose: bool = False):
        """
        Args:
            dry_run: True면 시뮬레이션만, False면 실제 실행
            verbose: 상세 로그 출력
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.mapper = ActionMapper()
        
        # 로깅 설정
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
    
    def execute_steps(self, steps: List[Dict[str, Any]]) -> ExecutionReport:
        """
        Step 리스트 실행
        
        Args:
            steps: Step Extractor/Refiner에서 생성된 단계 리스트
        
        Returns:
            ExecutionReport
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"  Starting RPA Execution ({'DRY-RUN' if self.dry_run else 'LIVE'})")
        logger.info(f"  Total Steps: {len(steps)}")
        logger.info(f"{'='*60}\n")
        
        start_time = time.time()
        results = []
        successful = 0
        failed = 0
        skipped = 0
        
        # Step → Action 변환
        actions = self.mapper.map_steps(steps)
        
        # 각 액션 실행
        for i, (step, action) in enumerate(zip(steps, actions), 1):
            logger.info(f"\n--- Step {i}/{len(steps)} ---")
            logger.info(f"Action: {action.action_type}")
            logger.info(f"Target: {action.target}")
            logger.info(f"Description: {action.description}")
            
            # 액션 실행
            result = action.execute(dry_run=self.dry_run)
            
            # 결과 기록
            if result.success:
                successful += 1
                logger.info(f"✅ Success ({result.duration:.2f}s)")
            else:
                failed += 1
                logger.error(f"❌ Failed: {result.error}")
            
            results.append({
                'step_number': i,
                'step': step,
                'action': action.action_type,
                'result': result.to_dict()
            })
            
            # 짧은 대기 (시뮬레이션 속도 조절)
            if self.dry_run:
                time.sleep(0.1)
            else:
                time.sleep(0.5)
        
        duration = time.time() - start_time
        
        # 리포트 생성
        report = ExecutionReport(
            total_steps=len(steps),
            successful=successful,
            failed=failed,
            skipped=skipped,
            duration=duration,
            dry_run=self.dry_run,
            results=results
        )
        
        report.print_summary()
        
        return report
    
    def execute_from_file(self, input_file: str, output_file: Optional[str] = None) -> ExecutionReport:
        """
        JSON 파일에서 Step을 읽어 실행
        
        Args:
            input_file: Step JSON 파일 경로
            output_file: 결과 저장 경로 (선택)
        
        Returns:
            ExecutionReport
        """
        logger.info(f"Loading steps from: {input_file}")
        
        # JSON 로드
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Step 추출 (Step Extractor 또는 Step Refiner 출력)
        if 'steps' in data:
            steps = data['steps']
        elif 'refined_steps' in data:
            steps = data['refined_steps']
        elif isinstance(data, list):
            steps = data
        else:
            raise ValueError(f"Unknown JSON format in {input_file}")
        
        logger.info(f"Loaded {len(steps)} steps")
        
        # 실행
        report = self.execute_steps(steps)
        
        # 결과 저장
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"\n✅ Report saved to: {output_file}")
        
        return report


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='RPA Executor')
    parser.add_argument('--input', required=True, help='Input JSON file (steps)')
    parser.add_argument('--output', help='Output JSON file (results)')
    parser.add_argument('--mode', choices=['dry-run', 'live'], default='dry-run', 
                        help='Execution mode (default: dry-run)')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    dry_run = (args.mode == 'dry-run')
    
    executor = RPAExecutor(dry_run=dry_run, verbose=args.verbose)
    executor.execute_from_file(args.input, args.output)
