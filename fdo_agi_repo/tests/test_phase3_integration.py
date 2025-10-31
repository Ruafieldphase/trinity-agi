"""
Phase 3 Integration Test
Day 12 - Verification & Failsafe Test

스크린샷 캡처, 이미지 비교, 검증, Failsafe 통합 테스트
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa.screenshot_capture import ScreenshotCapture, ScreenRegion
from rpa.image_comparator import ImageComparator, ComparisonResult
from rpa.verifier import ExecutionVerifier, VerificationResult
from rpa.failsafe import Failsafe, FailsafeConfig
from rpa.actions.base import ActionResult


def test_screenshot_capture():
    """스크린샷 캡처 테스트"""
    print("\n" + "="*60)
    print("  [Test 1] Screenshot Capture")
    print("="*60)
    
    output_dir = Path("outputs/phase3_test/screenshots")
    capturer = ScreenshotCapture(output_dir=output_dir)
    
    # 전체 화면
    print("\n1-1. Full screen capture")
    img = capturer.capture_full_screen(filename="test_full.png")
    print(f"  ✅ Captured: {img.size}")
    
    # 영역 캡처
    print("\n1-2. Region capture (200x200 at 100,100)")
    region = ScreenRegion(left=100, top=100, width=200, height=200)
    img = capturer.capture_region(region, filename="test_region.png")
    print(f"  ✅ Captured: {img.size}")
    
    # 연속 캡처
    print("\n1-3. Sequence capture (3 shots, 0.5s interval)")
    imgs = capturer.capture_sequence(count=3, interval=0.5, prefix="test_seq")
    print(f"  ✅ Captured {len(imgs)} screenshots")
    
    return True


def test_image_comparison():
    """이미지 비교 테스트"""
    print("\n" + "="*60)
    print("  [Test 2] Image Comparison")
    print("="*60)
    
    # 테스트용 이미지 생성
    from PIL import Image, ImageDraw
    import numpy as np
    
    output_dir = Path("outputs/phase3_test/comparison")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 이미지 1: 빨간 원
    img1 = Image.new('RGB', (200, 200), 'white')
    draw1 = ImageDraw.Draw(img1)
    draw1.ellipse([50, 50, 150, 150], fill='red')
    img1_path = output_dir / "img1_red_circle.png"
    img1.save(img1_path)
    
    # 이미지 2: 약간 다른 빨간 원 (위치 살짝 이동)
    img2 = Image.new('RGB', (200, 200), 'white')
    draw2 = ImageDraw.Draw(img2)
    draw2.ellipse([55, 55, 155, 155], fill='red')
    img2_path = output_dir / "img2_red_circle_moved.png"
    img2.save(img2_path)
    
    # 이미지 3: 파란 원 (완전히 다름)
    img3 = Image.new('RGB', (200, 200), 'white')
    draw3 = ImageDraw.Draw(img3)
    draw3.ellipse([50, 50, 150, 150], fill='blue')
    img3_path = output_dir / "img3_blue_circle.png"
    img3.save(img3_path)
    
    comparator = ImageComparator(ssim_threshold=0.95)
    
    # 테스트 2-1: 유사한 이미지
    print("\n2-1. Similar images (img1 vs img2)")
    result = comparator.compare_ssim(img1_path, img2_path)
    print(f"  Similarity: {result.similarity:.4f}")
    print(f"  Is similar: {result.is_similar}")
    
    # 테스트 2-2: 다른 이미지
    print("\n2-2. Different images (img1 vs img3)")
    result = comparator.compare_ssim(img1_path, img3_path)
    print(f"  Similarity: {result.similarity:.4f}")
    print(f"  Is similar: {result.is_similar}")
    
    # 테스트 2-3: 모든 방법
    print("\n2-3. All comparison methods (img1 vs img2)")
    results = comparator.compare_all(img1_path, img2_path)
    for method, result in results.items():
        print(f"  {method}: similarity={result.similarity:.4f}, is_similar={result.is_similar}")
    
    return True


def test_execution_verifier():
    """실행 검증 테스트"""
    print("\n" + "="*60)
    print("  [Test 3] Execution Verifier")
    print("="*60)
    
    output_dir = Path("outputs/phase3_test/verification")
    verifier = ExecutionVerifier(
        output_dir=output_dir,
        enable_screenshots=True,
        enable_comparison=True,
        comparison_method="SSIM"
    )
    
    # 가상의 액션 시뮬레이션
    print("\n3-1. Simulating action execution...")
    
    # Before screenshot
    before = verifier.capture_before("test_action")
    print(f"  Before: {before}")
    
    # 액션 실행 (시뮬레이션)
    action_result = ActionResult(
        action_name="test_click",
        action_type="CLICK",
        success=True,
        execution_time=0.5,
        metadata={"x": 100, "y": 100}
    )
    
    # After screenshot
    time.sleep(0.5)  # 변화 대기
    after = verifier.capture_after("test_action")
    print(f"  After: {after}")
    
    # 검증
    print("\n3-2. Verifying execution...")
    result = verifier.verify_action(
        action_result=action_result,
        before_screenshot=before,
        after_screenshot=after,
        expect_change=False  # 변화 없을 것으로 예상
    )
    
    print(f"  Success: {result.success}")
    if result.comparison:
        print(f"  Similarity: {result.comparison.similarity:.4f}")
    
    # 리포트 생성
    print("\n3-3. Generating report...")
    report_file = output_dir / "reports" / "test_report.json"
    report = verifier.generate_report(output_file=report_file)
    print(f"  Report saved: {report_file}")
    print(f"  Pass rate: {report['summary']['pass_rate']*100:.1f}%")
    
    return True


def test_failsafe():
    """Failsafe 테스트"""
    print("\n" + "="*60)
    print("  [Test 4] Failsafe Mechanism")
    print("="*60)
    
    config = FailsafeConfig(
        enable_pyautogui_failsafe=True,
        pause_between_actions=0.1,
        enable_timeout=True,
        action_timeout=2.0,
        enable_auto_retry=True,
        max_retries=2
    )
    
    failsafe = Failsafe(config=config)
    
    # 테스트 4-1: 정상 실행
    print("\n4-1. Normal execution")
    def normal_func():
        time.sleep(0.3)
        return "OK"
    
    result = failsafe.safe_execute(normal_func)
    print(f"  ✅ Result: {result}")
    
    # 테스트 4-2: 재시도
    print("\n4-2. Retry mechanism")
    attempt = [0]
    def flaky_func():
        attempt[0] += 1
        if attempt[0] < 2:
            raise ValueError("Simulated error")
        return "OK after retry"
    
    try:
        result = failsafe.safe_execute(flaky_func, max_retries=2)
        print(f"  ✅ Result: {result} (attempts: {attempt[0]})")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
    
    # 테스트 4-3: 타임아웃
    print("\n4-3. Timeout (should fail)")
    def slow_func():
        time.sleep(5.0)
        return "Should not reach here"
    
    try:
        result = failsafe.safe_execute(slow_func, timeout=1.0)
        print(f"  ❌ Should have timed out!")
    except Exception as e:
        print(f"  ✅ Timed out as expected: {type(e).__name__}")
    
    # 테스트 4-4: 스냅샷
    print("\n4-4. Snapshot & Rollback")
    failsafe.take_snapshot("state1", {"counter": 0})
    failsafe.take_snapshot("state2", {"counter": 1})
    
    latest = failsafe.get_latest_snapshot()
    print(f"  Latest snapshot: {latest}")
    
    state1 = failsafe.get_snapshot("state1")
    print(f"  State1 snapshot: {state1}")
    
    return True


def test_integrated_workflow():
    """통합 워크플로우 테스트"""
    print("\n" + "="*60)
    print("  [Test 5] Integrated Workflow")
    print("="*60)
    
    output_dir = Path("outputs/phase3_test/integrated")
    
    # Verifier + Failsafe 통합
    verifier = ExecutionVerifier(
        output_dir=output_dir,
        enable_screenshots=True,
        enable_comparison=True
    )
    
    config = FailsafeConfig(
        enable_timeout=True,
        action_timeout=30.0,
        enable_auto_retry=True,
        max_retries=2
    )
    failsafe = Failsafe(config=config)
    
    print("\n5-1. Executing action with verification and failsafe...")
    
    def execute_with_verification():
        # Before
        before = verifier.capture_before("integrated_test")
        
        # Execute action
        action_result = ActionResult(
            action_name="integrated_test",
            action_type="TEST",
            success=True,
            execution_time=0.5
        )
        
        # After
        time.sleep(0.5)
        after = verifier.capture_after("integrated_test")
        
        # Verify
        result = verifier.verify_action(
            action_result=action_result,
            before_screenshot=before,
            after_screenshot=after,
            expect_change=False
        )
        
        return result
    
    # Failsafe로 감싸서 실행
    result = failsafe.safe_execute(execute_with_verification)
    
    print(f"  ✅ Verification result: {'PASS' if result.success else 'FAIL'}")
    
    # 최종 리포트
    verifier.print_summary()
    
    return True


def main():
    """메인 테스트 함수"""
    print("\n" + "="*70)
    print("  Phase 3 Integration Test - Day 12")
    print("  Screenshot Capture | Image Comparison | Verifier | Failsafe")
    print("="*70)
    
    tests = [
        ("Screenshot Capture", test_screenshot_capture),
        ("Image Comparison", test_image_comparison),
        ("Execution Verifier", test_execution_verifier),
        ("Failsafe Mechanism", test_failsafe),
        ("Integrated Workflow", test_integrated_workflow)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
            print(f"\n✅ {name}: PASS\n")
        except Exception as e:
            print(f"\n❌ {name}: FAIL ({e})\n")
            results.append((name, False))
            import traceback
            traceback.print_exc()
    
    # 최종 요약
    print("\n" + "="*70)
    print("  Test Summary")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}  {name}")
    
    print("="*70)
    print(f"  Total: {total}  |  Passed: {passed}  |  Failed: {total - passed}")
    print(f"  Pass Rate: {passed/total*100:.1f}%")
    print("="*70 + "\n")
    
    return passed == total


if __name__ == '__main__':
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    success = main()
    sys.exit(0 if success else 1)
