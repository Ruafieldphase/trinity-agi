"""
Execution Verifier
Phase 2.5 Week 2 Day 12

RPA 액션 실행 전후 검증
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
import logging
import json

from PIL import Image

from .screenshot_capture import ScreenshotCapture, ScreenRegion
from .image_comparator import ImageComparator, ComparisonResult
from .actions.base import ActionResult

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """검증 결과"""
    action_name: str                      # 액션 이름
    action_type: str                      # 액션 타입
    success: bool                         # 검증 성공 여부
    screenshot_before: Optional[str]      # 실행 전 스크린샷 경로
    screenshot_after: Optional[str]       # 실행 후 스크린샷 경로
    comparison: Optional[ComparisonResult] # 이미지 비교 결과
    execution_time: float                 # 실행 시간 (초)
    timestamp: float = field(default_factory=time.time)
    error_message: Optional[str] = None   # 에러 메시지
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환 (JSON serializable)"""
        return {
            "action_name": self.action_name,
            "action_type": self.action_type,
            "success": bool(self.success),  # numpy bool → Python bool
            "screenshot_before": str(self.screenshot_before) if self.screenshot_before else None,
            "screenshot_after": str(self.screenshot_after) if self.screenshot_after else None,
            "comparison": {
                "method": self.comparison.method,
                "similarity": float(self.comparison.similarity),  # numpy float → Python float
                "difference": float(self.comparison.difference),
                "is_similar": bool(self.comparison.is_similar),  # numpy bool → Python bool
                "threshold": float(self.comparison.threshold)
            } if self.comparison else None,
            "execution_time": float(self.execution_time),
            "timestamp": self.timestamp,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


class ExecutionVerifier:
    """
    RPA 액션 실행 검증기
    
    Features:
    - 실행 전후 스크린샷 캡처
    - 이미지 비교 (변화 감지)
    - 검증 리포트 생성
    - 실패 시 롤백 지원
    
    Workflow:
    1. Before: 실행 전 스크린샷 캡처
    2. Execute: 액션 실행
    3. After: 실행 후 스크린샷 캡처
    4. Compare: 이미지 비교 (변화 감지)
    5. Verify: 기대 결과와 비교
    """
    
    def __init__(
        self,
        output_dir: Path,
        enable_screenshots: bool = True,
        enable_comparison: bool = True,
        comparison_method: str = "SSIM",
        similarity_threshold: float = 0.85
    ):
        """
        Args:
            output_dir: 스크린샷 저장 디렉토리
            enable_screenshots: 스크린샷 캡처 활성화
            enable_comparison: 이미지 비교 활성화
            comparison_method: 비교 방법 (SSIM, MSE, HISTOGRAM)
            similarity_threshold: 유사도 임계값
        """
        self.output_dir = output_dir
        self.enable_screenshots = enable_screenshots
        self.enable_comparison = enable_comparison
        self.comparison_method = comparison_method
        
        # 하위 디렉토리 생성
        self.screenshots_dir = output_dir / "screenshots"
        self.reports_dir = output_dir / "reports"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 유틸리티 초기화
        if enable_screenshots:
            self.capturer = ScreenshotCapture(output_dir=self.screenshots_dir)
        else:
            self.capturer = None
        
        if enable_comparison:
            if comparison_method.upper() == "SSIM":
                self.comparator = ImageComparator(ssim_threshold=similarity_threshold)
            elif comparison_method.upper() == "MSE":
                self.comparator = ImageComparator(mse_threshold=similarity_threshold)
            else:
                self.comparator = ImageComparator(histogram_threshold=similarity_threshold)
        else:
            self.comparator = None
        
        # 검증 기록
        self.verification_history: List[VerificationResult] = []
        
        logger.info(
            f"ExecutionVerifier initialized: "
            f"screenshots={enable_screenshots}, "
            f"comparison={enable_comparison} ({comparison_method})"
        )
    
    def capture_before(
        self,
        action_name: str,
        region: Optional[ScreenRegion] = None
    ) -> Optional[str]:
        """
        액션 실행 전 스크린샷 캡처
        
        Args:
            action_name: 액션 이름 (파일명에 사용)
            region: 캡처할 영역 (None이면 전체 화면)
        
        Returns:
            스크린샷 파일 경로 (None if disabled)
        """
        if not self.enable_screenshots:
            return None
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{action_name}_before_{timestamp}.png"
        
        try:
            if region:
                img = self.capturer.capture_region(region, filename=filename)
            else:
                img = self.capturer.capture_full_screen(filename=filename)
            
            filepath = self.screenshots_dir / filename
            logger.debug(f"Before screenshot captured: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Failed to capture before screenshot: {e}")
            return None
    
    def capture_after(
        self,
        action_name: str,
        region: Optional[ScreenRegion] = None,
        delay: float = 0.5
    ) -> Optional[str]:
        """
        액션 실행 후 스크린샷 캡처
        
        Args:
            action_name: 액션 이름
            region: 캡처할 영역
            delay: 캡처 전 대기 시간 (UI 변화 반영 대기)
        
        Returns:
            스크린샷 파일 경로
        """
        if not self.enable_screenshots:
            return None
        
        # UI 변화가 반영될 때까지 대기
        time.sleep(delay)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{action_name}_after_{timestamp}.png"
        
        try:
            if region:
                img = self.capturer.capture_region(region, filename=filename)
            else:
                img = self.capturer.capture_full_screen(filename=filename)
            
            filepath = self.screenshots_dir / filename
            logger.debug(f"After screenshot captured: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Failed to capture after screenshot: {e}")
            return None
    
    def compare_screenshots(
        self,
        before_path: str,
        after_path: str
    ) -> Optional[ComparisonResult]:
        """
        실행 전후 스크린샷 비교
        
        Args:
            before_path: 실행 전 스크린샷 경로
            after_path: 실행 후 스크린샷 경로
        
        Returns:
            ComparisonResult (None if disabled or error)
        """
        if not self.enable_comparison or not self.comparator:
            return None
        
        try:
            if self.comparison_method.upper() == "SSIM":
                result = self.comparator.compare_ssim(before_path, after_path)
            elif self.comparison_method.upper() == "MSE":
                result = self.comparator.compare_mse(before_path, after_path)
            elif self.comparison_method.upper() == "HISTOGRAM":
                result = self.comparator.compare_histogram(before_path, after_path)
            else:
                logger.error(f"Unknown comparison method: {self.comparison_method}")
                return None
            
            logger.debug(f"Screenshot comparison: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to compare screenshots: {e}")
            return None
    
    def verify_action(
        self,
        action_result: ActionResult,
        before_screenshot: Optional[str],
        after_screenshot: Optional[str],
        expect_change: bool = True
    ) -> VerificationResult:
        """
        액션 실행 결과 검증
        
        Args:
            action_result: 액션 실행 결과
            before_screenshot: 실행 전 스크린샷
            after_screenshot: 실행 후 스크린샷
            expect_change: 변화를 기대하는지 (True: 달라야 함, False: 같아야 함)
        
        Returns:
            VerificationResult
        """
        logger.info(f"Verifying action: {action_result.action_name}")
        
        # 이미지 비교
        comparison = None
        if before_screenshot and after_screenshot:
            comparison = self.compare_screenshots(before_screenshot, after_screenshot)
        
        # 검증 로직
        success = action_result.success
        error_message = action_result.error_message
        
        if success and comparison:
            # 변화 검증
            if expect_change:
                # 변화가 있어야 하는데 없으면 실패
                if comparison.is_similar:
                    success = False
                    error_message = (
                        f"Expected screen change but screens are similar "
                        f"(similarity={comparison.similarity:.4f})"
                    )
            else:
                # 변화가 없어야 하는데 있으면 실패
                if not comparison.is_similar:
                    success = False
                    error_message = (
                        f"Expected no change but screens differ "
                        f"(similarity={comparison.similarity:.4f})"
                    )
        
        # 결과 생성
        result = VerificationResult(
            action_name=action_result.action_name,
            action_type=action_result.action_type,
            success=success,
            screenshot_before=before_screenshot,
            screenshot_after=after_screenshot,
            comparison=comparison,
            execution_time=action_result.execution_time,
            error_message=error_message,
            metadata={
                "expect_change": expect_change,
                "dry_run": action_result.metadata.get("dry_run", False)
            }
        )
        
        # 기록
        self.verification_history.append(result)
        
        logger.info(
            f"Verification result: "
            f"{'✅ PASS' if success else '❌ FAIL'} "
            f"({action_result.action_name})"
        )
        
        return result
    
    def generate_report(
        self,
        output_file: Optional[Path] = None
    ) -> dict:
        """
        검증 리포트 생성
        
        Args:
            output_file: 리포트 저장 경로 (None이면 저장 안함)
        
        Returns:
            리포트 딕셔너리
        """
        total = len(self.verification_history)
        passed = sum(1 for r in self.verification_history if r.success)
        failed = total - passed
        
        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": passed / total if total > 0 else 0.0,
                "total_time": sum(r.execution_time for r in self.verification_history)
            },
            "verifications": [r.to_dict() for r in self.verification_history],
            "config": {
                "screenshots_enabled": self.enable_screenshots,
                "comparison_enabled": self.enable_comparison,
                "comparison_method": self.comparison_method
            }
        }
        
        # 저장
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Verification report saved: {output_file}")
        
        return report
    
    def print_summary(self):
        """검증 결과 요약 출력"""
        total = len(self.verification_history)
        passed = sum(1 for r in self.verification_history if r.success)
        failed = total - passed
        
        print("\n" + "="*60)
        print("  Verification Summary")
        print("="*60)
        print(f"  Total:  {total}")
        print(f"  Passed: {passed} ✅")
        print(f"  Failed: {failed} ❌")
        print(f"  Pass Rate: {passed/total*100:.1f}%" if total > 0 else "  Pass Rate: N/A")
        print("="*60 + "\n")
        
        if failed > 0:
            print("Failed verifications:")
            for r in self.verification_history:
                if not r.success:
                    print(f"  ❌ {r.action_name}: {r.error_message}")
            print()
    
    def reset(self):
        """검증 기록 초기화"""
        self.verification_history.clear()
        logger.info("Verification history reset")


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 간단한 테스트
    output_dir = Path("outputs/verification_test")
    verifier = ExecutionVerifier(
        output_dir=output_dir,
        enable_screenshots=True,
        enable_comparison=True,
        comparison_method="SSIM"
    )
    
    print("\n" + "="*60)
    print("  Execution Verifier Test")
    print("="*60 + "\n")
    
    # 가상의 액션 결과
    action_result = ActionResult(
        action_name="test_click",
        action_type="CLICK",
        success=True,
        execution_time=0.5
    )
    
    # 스크린샷 캡처 테스트
    print("[Test 1] Screenshot capture")
    before = verifier.capture_before("test_action")
    print(f"  Before: {before}")
    
    time.sleep(1)  # 변화 시뮬레이션
    
    after = verifier.capture_after("test_action")
    print(f"  After: {after}")
    
    # 검증
    print("\n[Test 2] Verification")
    result = verifier.verify_action(
        action_result=action_result,
        before_screenshot=before,
        after_screenshot=after,
        expect_change=False  # 변화가 없어야 (같은 화면)
    )
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    
    # 리포트
    print("\n[Test 3] Report generation")
    report_file = output_dir / "reports" / "test_report.json"
    report = verifier.generate_report(output_file=report_file)
    print(f"  Report saved: {report_file}")
    
    # 요약
    verifier.print_summary()
    
    print("="*60 + "\n")
