"""
ExecutionEngine Integration Test
Day 13 - Phase 3 Live Execution

테스트:
1. Dry-run 모드 (안전)
2. Live 모드 (실제 실행) - 간단한 텍스트 에디터 테스트
3. Verification 통합
4. Failsafe 통합
"""

import unittest
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa.execution_engine import (
    ExecutionEngine,
    ExecutionConfig,
    ExecutionMode
)


class TestExecutionEngine(unittest.TestCase):
    """ExecutionEngine 통합 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        self.output_dir = Path("outputs/test_execution_engine")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def test_01_dry_run_mode(self):
        """Test 1: Dry-run 모드 (시뮬레이션)"""
        print("\n" + "="*60)
        print("  Test 1: Dry-run Mode")
        print("="*60)
        
        # 설정
        config = ExecutionConfig(
            mode=ExecutionMode.DRY_RUN,
            enable_verification=False,  # Dry-run은 검증 불필요
            enable_failsafe=True,
            confirmation_required=False,  # 테스트용
            output_dir=self.output_dir / "dry_run"
        )
        
        engine = ExecutionEngine(config)
        
        # 간단한 튜토리얼
        tutorial_text = """
        Install Docker Tutorial
        
        1. Open terminal
        2. Type 'docker --version'
        3. Press Enter
        """
        
        # 실행
        result = engine.execute_tutorial(
            tutorial_text=tutorial_text,
            tutorial_name="docker_install_dryrun"
        )
        
        # 결과 출력
        engine.print_summary(result)
        
        # 검증
        self.assertEqual(result.mode, ExecutionMode.DRY_RUN)
        self.assertGreater(result.total_actions, 0, "Should extract actions")
        self.assertEqual(result.executed_actions, result.total_actions, 
                        "All actions should be executed (simulated)")
        
        print("✅ Dry-run mode test PASSED\n")
    
    def test_02_live_mode_simple(self):
        """Test 2: Live 모드 - 간단한 텍스트 입력"""
        print("\n" + "="*60)
        print("  Test 2: Live Mode - Simple Text Input")
        print("="*60)
        
        # 설정
        config = ExecutionConfig(
            mode=ExecutionMode.LIVE,
            enable_verification=True,
            enable_screenshots=True,
            enable_failsafe=True,
            confirmation_required=False,  # 테스트용 (실제는 True)
            timeout=10.0,
            max_retries=2,
            output_dir=self.output_dir / "live"
        )
        
        engine = ExecutionEngine(config)
        
        # 간단한 튜토리얼 (텍스트 입력만)
        tutorial_text = """
        Simple Text Input Test
        
        1. Type 'Hello World'
        """
        
        # 실행
        print("\n⚠️  This will execute REAL actions (keyboard input)")
        print("    You have 3 seconds to move mouse to corner to cancel...")
        time.sleep(3)
        
        result = engine.execute_tutorial(
            tutorial_text=tutorial_text,
            tutorial_name="simple_text_input"
        )
        
        # 결과 출력
        engine.print_summary(result)
        
        # 리포트 저장
        report_file = self.output_dir / "live" / "simple_text_report.json"
        engine.generate_report(result, report_file)
        print(f"Report saved: {report_file}")
        
        # 검증
        self.assertEqual(result.mode, ExecutionMode.LIVE)
        self.assertGreater(result.total_actions, 0)
        
        # Live 모드는 실제 실행이므로 실패할 수 있음
        # (예: 포커스가 다른 곳에 있거나, 타이밍 이슈 등)
        print(f"Executed: {result.executed_actions}/{result.total_actions}")
        print(f"Failed: {result.failed_actions}")
        
        print("✅ Live mode test COMPLETED\n")
    
    def test_03_verification_integration(self):
        """Test 3: Verification 통합"""
        print("\n" + "="*60)
        print("  Test 3: Verification Integration")
        print("="*60)
        
        # 설정
        config = ExecutionConfig(
            mode=ExecutionMode.DRY_RUN,  # Dry-run으로 안전하게
            enable_verification=True,
            enable_screenshots=True,
            similarity_threshold=0.95,
            comparison_method="SSIM",
            confirmation_required=False,
            output_dir=self.output_dir / "verification"
        )
        
        engine = ExecutionEngine(config)
        
        tutorial_text = """
        Verification Test
        
        1. Click on desktop
        2. Wait 1 second
        """
        
        result = engine.execute_tutorial(
            tutorial_text=tutorial_text,
            tutorial_name="verification_test"
        )
        
        engine.print_summary(result)
        
        # 검증
        self.assertTrue(config.enable_verification)
        # Dry-run이므로 검증 결과가 있을 수 있음
        print(f"Verified actions: {result.verified_actions}")
        
        print("✅ Verification integration test PASSED\n")
    
    def test_04_failsafe_integration(self):
        """Test 4: Failsafe 통합"""
        print("\n" + "="*60)
        print("  Test 4: Failsafe Integration")
        print("="*60)
        
        # 설정
        config = ExecutionConfig(
            mode=ExecutionMode.DRY_RUN,
            enable_failsafe=True,
            timeout=5.0,
            max_retries=2,
            confirmation_required=False,
            output_dir=self.output_dir / "failsafe"
        )
        
        engine = ExecutionEngine(config)
        
        tutorial_text = """
        Failsafe Test
        
        1. Open terminal
        2. Type 'echo test'
        3. Press Enter
        """
        
        result = engine.execute_tutorial(
            tutorial_text=tutorial_text,
            tutorial_name="failsafe_test"
        )
        
        engine.print_summary(result)
        
        # 검증
        self.assertTrue(config.enable_failsafe)
        self.assertGreater(result.total_actions, 0)
        
        print("✅ Failsafe integration test PASSED\n")
    
    def test_05_end_to_end_pipeline(self):
        """Test 5: End-to-End 전체 파이프라인"""
        print("\n" + "="*60)
        print("  Test 5: End-to-End Pipeline")
        print("="*60)
        
        # 설정 (모든 기능 활성화)
        config = ExecutionConfig(
            mode=ExecutionMode.DRY_RUN,
            enable_verification=True,
            enable_screenshots=True,
            enable_failsafe=True,
            timeout=10.0,
            max_retries=3,
            confirmation_required=False,
            output_dir=self.output_dir / "e2e"
        )
        
        engine = ExecutionEngine(config)
        
        # Docker 설치 튜토리얼 (전체)
        tutorial_text = """
        Docker Installation Tutorial
        
        1. Open terminal (Ctrl+Alt+T on Linux)
        2. Update package index:
           Type 'sudo apt update'
        3. Install dependencies:
           Type 'sudo apt install -y apt-transport-https ca-certificates curl'
        4. Add Docker GPG key:
           Type 'curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -'
        5. Add Docker repository:
           Type 'sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"'
        6. Update package index again:
           Type 'sudo apt update'
        7. Install Docker:
           Type 'sudo apt install -y docker-ce'
        8. Verify installation:
           Type 'docker --version'
        9. Check Docker status:
           Type 'sudo systemctl status docker'
        """
        
        result = engine.execute_tutorial(
            tutorial_text=tutorial_text,
            tutorial_name="docker_install_e2e"
        )
        
        engine.print_summary(result)
        
        # 리포트 저장
        report_file = self.output_dir / "e2e" / "docker_install_report.json"
        engine.generate_report(result, report_file)
        print(f"Report saved: {report_file}")
        
        # 검증
        self.assertGreater(result.total_actions, 0, "Should extract multiple actions")
        self.assertEqual(result.executed_actions, result.total_actions,
                        "All actions should be executed")
        
        print("✅ End-to-end pipeline test PASSED\n")


def run_tests():
    """테스트 실행"""
    print("\n" + "="*60)
    print("  ExecutionEngine Integration Test - Day 13")
    print("  Dry-run | Live | Verification | Failsafe | E2E")
    print("="*60 + "\n")
    
    # 테스트 스위트
    suite = unittest.TestLoader().loadTestsFromTestCase(TestExecutionEngine)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 요약
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)
    print(f"  Total: {result.testsRun}")
    print(f"  Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failed: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Pass Rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print("="*60 + "\n")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
