#!/usr/bin/env python3
"""
Complete Deployment Demo - ION Mentoring System

이 스크립트는 전체 자동화 파이프라인의 실제 사용 시나리오를 시연합니다.
자연어 명령 → Orchestrator → Action Runner → PowerShell 실행 흐름을 확인할 수 있습니다.

시나리오:
1. 현재 배포 상태 확인
2. 5% 카나리 배포
3. 모니터링 시작 (프로브 포함)
4. Rate Limit 프로브 실행
5. 상태 재확인
6. 25% 카나리 배포
7. 통합 테스트 실행
8. 롤백 시나리오 (긴급 상황 시)

기본값: --dry-run (실제 실행 없음, 안전)
실제 실행: --execute 플래그 추가 (주의!)

Usage:
    python complete_deployment_demo.py                    # Dry-run demo
    python complete_deployment_demo.py --execute          # Real execution (확인 필요)
    python complete_deployment_demo.py --scenario 1       # 특정 시나리오만 실행
"""

import sys
import time
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from deployment_controller import DeploymentController
from action_runner import ExecutionReport


# ANSI 색상 코드
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """헤더 출력"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_step(step_num: int, description: str):
    """단계 출력"""
    print(f"{Colors.OKBLUE}{Colors.BOLD}[Step {step_num}]{Colors.ENDC} {description}")


def print_command(command: str):
    """실행할 명령 출력"""
    print(f"{Colors.OKCYAN}  Command: {Colors.BOLD}\"{command}\"{Colors.ENDC}")


def print_success(message: str):
    """성공 메시지"""
    print(f"{Colors.OKGREEN}  ✅ {message}{Colors.ENDC}")


def print_warning(message: str):
    """경고 메시지"""
    print(f"{Colors.WARNING}  ⚠️  {message}{Colors.ENDC}")


def print_fail(message: str):
    """실패 메시지"""
    print(f"{Colors.FAIL}  ❌ {message}{Colors.ENDC}")


def print_report_summary(report: ExecutionReport):
    """실행 보고서 요약 출력"""
    status_icon = "✅" if report.overall_success else "❌"
    status_text = "SUCCESS" if report.overall_success else "FAILED"
    
    print(f"\n  {Colors.BOLD}Report Summary:{Colors.ENDC}")
    print(f"    Status: {status_icon} {status_text}")
    print(f"    Duration: {report.total_duration_seconds:.2f}s")
    print(f"    Actions: {len(report.action_results)}")
    
    for idx, result in enumerate(report.action_results, 1):
        result_icon = "✅" if result.success else "❌"
        print(f"      {idx}. {result_icon} {result.action_kind} ({result.duration_seconds:.2f}s)")
        if not result.success and result.error:
            print(f"         Error: {result.error}")


def pause_between_steps(seconds: int = 2):
    """단계 사이 일시정지"""
    time.sleep(seconds)


def run_scenario_1(controller: DeploymentController, dry_run: bool, user_id: str):
    """
    Scenario 1: 기본 배포 흐름
    - 상태 확인 → 5% 배포 → 모니터링 시작
    """
    print_header("SCENARIO 1: Basic Deployment Flow")
    
    # Step 1: 상태 확인
    print_step(1, "현재 배포 상태 확인")
    print_command("현재 상태 확인해줘")
    report = controller.execute_command("현재 상태 확인해줘", user_id)
    print_report_summary(report)
    pause_between_steps()
    
    # Step 2: 5% 카나리 배포
    print_step(2, "5% 카나리 배포 시작")
    print_command("5% 카나리 배포해줘")
    report = controller.execute_command("5% 카나리 배포해줘", user_id)
    print_report_summary(report)
    pause_between_steps()
    
    # Step 3: 모니터링 시작
    print_step(3, "모니터링 시스템 시작 (프로브 포함)")
    print_command("모니터링 시작해줘")
    report = controller.execute_command("모니터링 시작해줘", user_id)
    print_report_summary(report)
    
    print_success("Scenario 1 완료!")


def run_scenario_2(controller: DeploymentController, dry_run: bool, user_id: str):
    """
    Scenario 2: 점진적 롤아웃
    - 25% 배포 → 테스트 → 50% 배포 → 확인
    """
    print_header("SCENARIO 2: Gradual Rollout")
    
    # Step 1: 25% 배포
    print_step(1, "25% 카나리 배포 (점진적 확대)")
    print_command("Deploy 25% canary")
    report = controller.execute_command("Deploy 25% canary", user_id)
    print_report_summary(report)
    pause_between_steps()
    
    # Step 2: 통합 테스트 실행
    print_step(2, "통합 테스트 실행")
    print_command("Run all tests")
    report = controller.execute_command("Run all tests", user_id)
    print_report_summary(report)
    pause_between_steps()
    
    # Step 3: 50% 배포
    print_step(3, "50% 카나리 배포 (절반 확대)")
    print_command("50% 배포해줘")
    report = controller.execute_command("50% 배포해줘", user_id)
    print_report_summary(report)
    pause_between_steps()
    
    # Step 4: 상태 재확인
    print_step(4, "배포 후 상태 확인")
    print_command("Check deployment status")
    report = controller.execute_command("Check deployment status", user_id)
    print_report_summary(report)
    
    print_success("Scenario 2 완료!")


def run_scenario_3(controller: DeploymentController, dry_run: bool, user_id: str):
    """
    Scenario 3: 모니터링 및 프로브
    - Rate limit 프로브 → 로드 테스트 → 상태 확인
    """
    print_header("SCENARIO 3: Monitoring & Probing")
    
    # Step 1: Rate limit 프로브 (safe)
    print_step(1, "Rate Limit 프로브 실행 (안전 모드)")
    print_command("Run safe probe")
    report = controller.execute_command("Run safe probe", user_id)
    print_report_summary(report)
    pause_between_steps()
    
    # Step 2: 로드 테스트
    print_step(2, "로드 테스트 실행")
    print_command("Run load test")
    report = controller.execute_command("Run load test", user_id)
    print_report_summary(report)
    pause_between_steps()
    
    # Step 3: 모니터링 상태 확인
    print_step(3, "모니터링 시스템 상태 확인")
    print_command("모니터링 상태 확인")
    report = controller.execute_command("모니터링 상태 확인", user_id)
    print_report_summary(report)
    
    print_success("Scenario 3 완료!")


def run_scenario_4(controller: DeploymentController, dry_run: bool, user_id: str):
    """
    Scenario 4: 긴급 롤백
    - 모니터링 중지 → 롤백 → 상태 확인
    """
    print_header("SCENARIO 4: Emergency Rollback")
    
    print_warning("긴급 상황 시나리오: 문제 발견, 즉시 롤백 필요")
    pause_between_steps(1)
    
    # Step 1: 모니터링 중지
    print_step(1, "모니터링 시스템 중지")
    print_command("Stop all monitoring")
    report = controller.execute_command("Stop all monitoring", user_id)
    print_report_summary(report)
    pause_between_steps()
    
    # Step 2: 카나리 롤백
    print_step(2, "카나리 배포 롤백 (0%로 복귀)")
    print_command("Rollback canary deployment")
    report = controller.execute_command("Rollback canary deployment", user_id)
    print_report_summary(report)
    pause_between_steps()
    
    # Step 3: 롤백 후 상태 확인
    print_step(3, "롤백 완료 확인")
    print_command("Check status")
    report = controller.execute_command("Check status", user_id)
    print_report_summary(report)
    
    print_success("Scenario 4 완료! 안전하게 롤백되었습니다.")


def run_scenario_5(controller: DeploymentController, dry_run: bool, user_id: str):
    """
    Scenario 5: 완전한 배포 사이클 (Full Workflow)
    - 상태 → 5% → 모니터링 → 프로브 → 25% → 테스트 → 50% → 100% → 모니터링 종료
    """
    print_header("SCENARIO 5: Complete Deployment Cycle")
    
    print_warning("전체 배포 사이클 시연 (8단계)")
    pause_between_steps(1)
    
    steps = [
        ("상태 확인", "Check initial status"),
        ("5% 배포", "Deploy 5% canary and start monitoring"),
        ("프로브 실행", "Run safe probe"),
        ("25% 배포", "Deploy 25% canary"),
        ("테스트 실행", "Run all tests"),
        ("50% 배포", "Deploy 50% canary"),
        ("100% 배포", "Deploy 100% canary"),
        ("모니터링 종료", "Stop monitoring"),
    ]
    
    for idx, (desc, command) in enumerate(steps, 1):
        print_step(idx, desc)
        print_command(command)
        report = controller.execute_command(command, user_id)
        print_report_summary(report)
        
        if not report.overall_success:
            print_fail(f"Step {idx} 실패! 다음 단계로 계속 진행합니다.")
        
        pause_between_steps()
    
    print_success("Scenario 5 완료! 전체 배포 사이클이 완료되었습니다.")


def main():
    parser = argparse.ArgumentParser(
        description="ION Mentoring Complete Deployment Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 모든 시나리오 dry-run (안전)
  python complete_deployment_demo.py
  
  # 특정 시나리오만 실행
  python complete_deployment_demo.py --scenario 1
  python complete_deployment_demo.py --scenario 5
  
  # 실제 실행 (주의!)
  python complete_deployment_demo.py --execute --scenario 1
  
  # 사용자 지정
  python complete_deployment_demo.py --user alice --scenario 3

Scenarios:
  1: Basic Deployment Flow (상태 → 5% → 모니터링)
  2: Gradual Rollout (25% → 테스트 → 50%)
  3: Monitoring & Probing (프로브 → 로드테스트 → 상태)
  4: Emergency Rollback (중지 → 롤백 → 확인)
  5: Complete Cycle (전체 배포 사이클, 8단계)
        """
    )
    
    parser.add_argument(
        "--execute",
        action="store_true",
        help="실제 실행 모드 (기본값: dry-run)"
    )
    
    parser.add_argument(
        "--scenario",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="실행할 시나리오 번호 (기본값: 모두 실행)"
    )
    
    parser.add_argument(
        "--user",
        type=str,
        default="demo-user",
        help="사용자 ID (기본값: demo-user)"
    )
    
    parser.add_argument(
        "--no-pause",
        action="store_true",
        help="단계 사이 일시정지 생략"
    )
    
    args = parser.parse_args()
    
    # 설정 출력
    print_header("ION Mentoring Deployment Demo")
    
    dry_run = not args.execute
    mode_text = "DRY-RUN (안전 모드)" if dry_run else "REAL EXECUTION (실제 실행)"
    mode_color = Colors.OKGREEN if dry_run else Colors.WARNING
    
    print(f"{mode_color}{Colors.BOLD}Mode: {mode_text}{Colors.ENDC}")
    print(f"{Colors.BOLD}User: {args.user}{Colors.ENDC}")
    
    if args.scenario:
        print(f"{Colors.BOLD}Scenario: {args.scenario}{Colors.ENDC}")
    else:
        print(f"{Colors.BOLD}Scenario: All (1-5){Colors.ENDC}")
    
    # 실제 실행 시 확인
    if not dry_run:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  WARNING: 실제 실행 모드입니다!{Colors.ENDC}")
        print(f"{Colors.WARNING}GCP Cloud Run에 실제 배포가 수행됩니다.{Colors.ENDC}")
        response = input(f"{Colors.WARNING}계속하시겠습니까? (yes/no): {Colors.ENDC}")
        if response.lower() != "yes":
            print("중단되었습니다.")
            return
    
    # Controller 초기화
    controller = DeploymentController(dry_run=dry_run, save_reports=True)
    
    # Pause 설정
    if args.no_pause:
        global pause_between_steps
        pause_between_steps = lambda x=0: None
    
    # 시나리오 실행
    scenarios = {
        1: run_scenario_1,
        2: run_scenario_2,
        3: run_scenario_3,
        4: run_scenario_4,
        5: run_scenario_5,
    }
    
    try:
        if args.scenario:
            # 특정 시나리오만 실행
            scenarios[args.scenario](controller, dry_run, args.user)
        else:
            # 모든 시나리오 실행
            for scenario_num, scenario_func in scenarios.items():
                scenario_func(controller, dry_run, args.user)
                pause_between_steps(3)
        
        # 최종 요약
        print_header("DEMO COMPLETE")
        print_success("모든 시나리오가 성공적으로 완료되었습니다!")
        print(f"\n{Colors.BOLD}생성된 보고서:{Colors.ENDC}")
        reports_dir = Path(__file__).parent.parent / "outputs" / "deployment_reports"
        print(f"  {reports_dir}")
        print(f"\n{Colors.OKBLUE}다음 단계:{Colors.ENDC}")
        print("  1. outputs/deployment_reports/ 에서 JSON 보고서 확인")
        print("  2. README.md 에서 상세 사용법 확인")
        print("  3. --execute 플래그로 실제 배포 실행 (프로덕션 환경)")
        
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}사용자에 의해 중단되었습니다.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_fail(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
