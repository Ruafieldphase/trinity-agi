"""
Action Runner for Orchestrator System

Executes actions planned by the Orchestrator intent router.
Bridges natural language commands to actual PowerShell script execution.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestrator.intent_router import Plan, PlannedAction

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Script paths
SCRIPTS_DIR = Path(__file__).parent / "scripts"
PROJECT_ID = "naeda-genesis"


@dataclass
class ActionResult:
    """Result of executing an action"""

    action_kind: str
    action_args: Dict[str, Any]
    success: bool
    output: str
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class ExecutionReport:
    """Complete execution report for a plan"""

    plan_summary: str
    start_time: str
    end_time: str
    total_duration_seconds: float
    action_results: List[ActionResult]
    overall_success: bool


class ActionRunner:
    """Executes actions from Orchestrator plans"""

    def __init__(self, project_id: str = PROJECT_ID, scripts_dir: Path = SCRIPTS_DIR):
        self.project_id = project_id
        self.scripts_dir = scripts_dir
        self.dry_run = False

    def set_dry_run(self, enabled: bool):
        """Enable or disable dry-run mode (no actual execution)"""
        self.dry_run = enabled
        logger.info(f"Dry-run mode: {'ENABLED' if enabled else 'DISABLED'}")

    def execute_plan(self, plan: Plan) -> ExecutionReport:
        """Execute all actions in a plan"""
        logger.info(f"Executing plan: {plan.summary}")
        logger.info(f"Actions to execute: {len(plan.actions)}")

        start_time = datetime.now()
        results: List[ActionResult] = []

        for idx, action in enumerate(plan.actions, 1):
            logger.info(f"[{idx}/{len(plan.actions)}] Executing: {action.kind}")
            result = self._execute_action(action)
            results.append(result)

            if not result.success:
                logger.error(
                    f"Action {action.kind} failed: {result.error}. Stopping execution."
                )
                break

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        report = ExecutionReport(
            plan_summary=plan.summary,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_duration_seconds=duration,
            action_results=results,
            overall_success=all(r.success for r in results),
        )

        logger.info(
            f"Plan execution completed. Success: {report.overall_success}, Duration: {duration:.2f}s"
        )
        return report

    def _execute_action(self, action: PlannedAction) -> ActionResult:
        """Execute a single action"""
        start_time = datetime.now()

        try:
            if action.kind == "deploy_canary":
                result = self._deploy_canary(action.args)
            elif action.kind == "rollback_canary":
                result = self._rollback_canary(action.args)
            elif action.kind == "start_monitor_loop":
                result = self._start_monitor_loop(action.args)
            elif action.kind == "stop_monitor_loops":
                result = self._stop_monitor_loops(action.args)
            elif action.kind == "probe":
                result = self._probe(action.args)
            elif action.kind == "run_tests":
                result = self._run_tests(action.args)
            elif action.kind == "load_test":
                result = self._load_test(action.args)
            elif action.kind == "check_status":
                result = self._check_status(action.args)
            else:
                result = ActionResult(
                    action_kind=action.kind,
                    action_args=action.args,
                    success=False,
                    output="",
                    error=f"Unknown action kind: {action.kind}",
                )

            duration = (datetime.now() - start_time).total_seconds()
            result.duration_seconds = duration
            return result

        except Exception as e:
            logger.exception(f"Error executing action {action.kind}")
            duration = (datetime.now() - start_time).total_seconds()
            return ActionResult(
                action_kind=action.kind,
                action_args=action.args,
                success=False,
                output="",
                error=str(e),
                duration_seconds=duration,
            )

    def _run_powershell(
        self, script_path: Path, args: List[str], timeout: int = 300
    ) -> tuple[bool, str, str]:
        """Run a PowerShell script with arguments"""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would execute: {script_path} {' '.join(args)}")
            return True, f"[DRY-RUN] {script_path.name} with args {args}", ""

        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ] + args

        logger.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, cwd=script_path.parent
            )
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Script execution timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)

    def _deploy_canary(self, args: Dict[str, Any]) -> ActionResult:
        """Execute canary deployment"""
        percentage = args.get("percentage", 5)
        script = self.scripts_dir / "deploy_phase4_canary.ps1"

        ps_args = [
            "-ProjectId",
            self.project_id,
            "-CanaryPercentage",
            str(percentage),
        ]

        success, stdout, stderr = self._run_powershell(script, ps_args, timeout=600)

        return ActionResult(
            action_kind="deploy_canary",
            action_args=args,
            success=success,
            output=stdout,
            error=stderr if stderr else None,
        )

    def _rollback_canary(self, args: Dict[str, Any]) -> ActionResult:
        """Execute canary rollback"""
        script = self.scripts_dir / "rollback_phase4_canary.ps1"

        ps_args = ["-ProjectId", self.project_id, "-AutoApprove"]

        success, stdout, stderr = self._run_powershell(script, ps_args, timeout=600)

        return ActionResult(
            action_kind="rollback_canary",
            action_args=args,
            success=success,
            output=stdout,
            error=stderr if stderr else None,
        )

    def _start_monitor_loop(self, args: Dict[str, Any]) -> ActionResult:
        """Start monitoring loop"""
        profile = args.get("profile", "with_probe")
        script = (
            self.scripts_dir / "start_monitor_loop_with_probe.ps1"
            if profile == "with_probe"
            else self.scripts_dir / "start_monitor_loop.ps1"
        )

        ps_args = [
            "-KillExisting",
            "-IntervalSeconds",
            "1800",
            "-DurationMinutes",
            "1440",
        ]

        success, stdout, stderr = self._run_powershell(script, ps_args)

        return ActionResult(
            action_kind="start_monitor_loop",
            action_args=args,
            success=success,
            output=stdout,
            error=stderr if stderr else None,
        )

    def _stop_monitor_loops(self, args: Dict[str, Any]) -> ActionResult:
        """Stop all monitoring loops"""
        script = self.scripts_dir / "start_monitor_loop.ps1"
        ps_args = ["-KillExisting", "-StopOnly"]

        success, stdout, stderr = self._run_powershell(script, ps_args)

        return ActionResult(
            action_kind="stop_monitor_loops",
            action_args=args,
            success=success,
            output=stdout,
            error=stderr if stderr else None,
        )

    def _probe(self, args: Dict[str, Any]) -> ActionResult:
        """Execute rate limit probe"""
        profile = args.get("profile", "safe")
        script = self.scripts_dir / "rate_limit_probe.ps1"

        # Map profile to probe parameters
        probe_params = {
            "gentle": ["-RequestsPerSide", "3", "-DelayMsBetweenRequests", "2000"],
            "safe": ["-RequestsPerSide", "10", "-DelayMsBetweenRequests", "500"],
            "normal": ["-RequestsPerSide", "10", "-DelayMsBetweenRequests", "1000"],
            "aggressive": ["-RequestsPerSide", "25", "-DelayMsBetweenRequests", "500"],
        }

        ps_args = probe_params.get(profile, probe_params["safe"])

        success, stdout, stderr = self._run_powershell(script, ps_args)

        return ActionResult(
            action_kind="probe",
            action_args=args,
            success=success,
            output=stdout,
            error=stderr if stderr else None,
        )

    def _run_tests(self, args: Dict[str, Any]) -> ActionResult:
        """Run tests"""
        script = self.scripts_dir.parent / ".venv" / "Scripts" / "python.exe"
        test_args = ["-m", "pytest", "-q"]

        # For simplicity, we'll use subprocess directly
        if self.dry_run:
            return ActionResult(
                action_kind="run_tests",
                action_args=args,
                success=True,
                output="[DRY-RUN] Would run pytest",
            )

        try:
            result = subprocess.run(
                [str(script)] + test_args,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=self.scripts_dir.parent,
            )
            success = result.returncode == 0
            return ActionResult(
                action_kind="run_tests",
                action_args=args,
                success=success,
                output=result.stdout,
                error=result.stderr if result.stderr else None,
            )
        except Exception as e:
            return ActionResult(
                action_kind="run_tests",
                action_args=args,
                success=False,
                output="",
                error=str(e),
            )

    def _load_test(self, args: Dict[str, Any]) -> ActionResult:
        """Run load tests"""
        profile = args.get("profile", "light")
        script = self.scripts_dir / "run_all_load_tests.ps1"

        ps_args = ["-ScenarioProfile", profile, "-OverrideRunTime", "10s"]

        success, stdout, stderr = self._run_powershell(script, ps_args, timeout=600)

        return ActionResult(
            action_kind="load_test",
            action_args=args,
            success=success,
            output=stdout,
            error=stderr if stderr else None,
        )

    def _check_status(self, args: Dict[str, Any]) -> ActionResult:
        """Check deployment status"""
        script = self.scripts_dir / "check_monitoring_status.ps1"

        success, stdout, stderr = self._run_powershell(script, [])

        return ActionResult(
            action_kind="check_status",
            action_args=args,
            success=success,
            output=stdout,
            error=stderr if stderr else None,
        )


def save_report(report: ExecutionReport, output_path: Path):
    """Save execution report to JSON file"""
    report_dict = {
        "plan_summary": report.plan_summary,
        "start_time": report.start_time,
        "end_time": report.end_time,
        "total_duration_seconds": report.total_duration_seconds,
        "overall_success": report.overall_success,
        "action_results": [asdict(r) for r in report.action_results],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2, ensure_ascii=False)

    logger.info(f"Report saved to: {output_path}")


def main():
    """CLI for testing action runner"""
    if len(sys.argv) < 2:
        print("Usage: python action_runner.py '<natural language command>' [--dry-run]")
        print("\nExamples:")
        print('  python action_runner.py "5% 카나리 배포"')
        print('  python action_runner.py "Deploy 25% canary and start monitoring" --dry-run')
        print('  python action_runner.py "모니터링 중지하고 롤백"')
        sys.exit(1)

    # Import here to avoid circular dependency
    from orchestrator.intent_router import plan_from_prompt

    command = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    # Parse command
    print(f"\n{'='*60}")
    print(f"Command: {command}")
    print(f"{'='*60}\n")

    plan = plan_from_prompt(command)
    print(f"Plan: {plan.summary}")
    print(f"Actions: {len(plan.actions)}")
    for idx, action in enumerate(plan.actions, 1):
        print(f"  {idx}. {action.kind}: {action.args}")
    print()

    # Execute
    runner = ActionRunner()
    runner.set_dry_run(dry_run)

    report = runner.execute_plan(plan)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Execution Report")
    print(f"{'='*60}")
    print(f"Overall Success: {'✅' if report.overall_success else '❌'}")
    print(f"Duration: {report.total_duration_seconds:.2f}s")
    print(f"\nAction Results:")
    for idx, result in enumerate(report.action_results, 1):
        status = "✅" if result.success else "❌"
        print(f"  {idx}. {status} {result.action_kind} ({result.duration_seconds:.2f}s)")
        if result.error:
            print(f"     Error: {result.error}")

    # Save report
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"action_runner_report_{timestamp}.json"
    save_report(report, report_path)

    sys.exit(0 if report.overall_success else 1)


if __name__ == "__main__":
    main()
