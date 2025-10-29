"""
Integrated Deployment Controller

Combines Orchestrator + Action Runner for complete automation.
Can be used from command line, Slack bot, or web API.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from action_runner import ActionRunner, ExecutionReport, save_report
from orchestrator.intent_router import plan_from_prompt

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DeploymentController:
    """High-level controller for deployment operations"""

    def __init__(self, dry_run: bool = False, save_reports: bool = True):
        self.runner = ActionRunner()
        self.runner.set_dry_run(dry_run)
        self.save_reports = save_reports
        self.reports_dir = Path(__file__).parent / "outputs" / "deployment_reports"
        if self.save_reports:
            self.reports_dir.mkdir(parents=True, exist_ok=True)

    def execute_command(
        self, command: str, user_id: Optional[str] = None
    ) -> ExecutionReport:
        """
        Execute a natural language deployment command.

        Args:
            command: Natural language command (KO/EN)
            user_id: Optional user identifier for logging

        Returns:
            ExecutionReport with execution details
        """
        logger.info(f"Processing command from user {user_id or 'unknown'}: {command}")

        # Parse command with Orchestrator
        plan = plan_from_prompt(command)
        logger.info(f"Plan created: {plan.summary} ({len(plan.actions)} actions)")

        # Execute plan
        report = self.runner.execute_plan(plan)

        # Save report if enabled
        if self.save_reports:
            self._save_report(report, user_id, command)

        return report

    def _save_report(
        self, report: ExecutionReport, user_id: Optional[str], command: str
    ):
        """Save execution report with metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_suffix = f"_{user_id}" if user_id else ""
        filename = f"deployment_{timestamp}{user_suffix}.json"
        filepath = self.reports_dir / filename

        # Add metadata
        report_dict = {
            "command": command,
            "user_id": user_id,
            "plan_summary": report.plan_summary,
            "start_time": report.start_time,
            "end_time": report.end_time,
            "total_duration_seconds": report.total_duration_seconds,
            "overall_success": report.overall_success,
            "action_results": [
                {
                    "action_kind": r.action_kind,
                    "action_args": r.action_args,
                    "success": r.success,
                    "duration_seconds": r.duration_seconds,
                    "output": r.output[:500] if r.output else "",  # Truncate long output
                    "error": r.error,
                }
                for r in report.action_results
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Report saved to: {filepath}")

    def format_report_for_slack(self, report: ExecutionReport, command: str) -> str:
        """Format execution report for Slack message"""
        status_emoji = "✅" if report.overall_success else "❌"
        duration = report.total_duration_seconds

        message = f"{status_emoji} *Command Execution Complete*\n\n"
        message += f"*Command:* `{command}`\n"
        message += f"*Plan:* {report.plan_summary}\n"
        message += f"*Duration:* {duration:.2f}s\n"
        message += f"*Status:* {'Success' if report.overall_success else 'Failed'}\n\n"

        message += "*Actions:*\n"
        for idx, result in enumerate(report.action_results, 1):
            action_status = "✅" if result.success else "❌"
            message += f"{idx}. {action_status} `{result.action_kind}` ({result.duration_seconds:.2f}s)\n"
            if result.error:
                # Truncate error for Slack
                error_preview = result.error[:200] + "..." if len(result.error) > 200 else result.error
                message += f"   ⚠️ {error_preview}\n"

        return message

    def format_report_for_console(self, report: ExecutionReport, command: str) -> str:
        """Format execution report for console output"""
        lines = []
        lines.append("=" * 70)
        lines.append("DEPLOYMENT EXECUTION REPORT")
        lines.append("=" * 70)
        lines.append(f"Command: {command}")
        lines.append(f"Plan: {report.plan_summary}")
        lines.append(f"Duration: {report.total_duration_seconds:.2f}s")
        lines.append(
            f"Status: {'✅ SUCCESS' if report.overall_success else '❌ FAILED'}"
        )
        lines.append("")
        lines.append("Actions:")
        for idx, result in enumerate(report.action_results, 1):
            status = "✅" if result.success else "❌"
            lines.append(
                f"  {idx}. {status} {result.action_kind} ({result.duration_seconds:.2f}s)"
            )
            if result.action_args:
                lines.append(f"     Args: {result.action_args}")
            if result.error:
                lines.append(f"     Error: {result.error}")
        lines.append("=" * 70)
        return "\n".join(lines)


def main():
    """CLI interface for deployment controller"""
    parser = argparse.ArgumentParser(
        description="Integrated Deployment Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy canary (dry-run)
  python deployment_controller.py "5% 카나리 배포" --dry-run

  # Deploy and monitor (actual execution)
  python deployment_controller.py "Deploy 25% canary and start monitoring"

  # Check status with user tracking
  python deployment_controller.py "상태 확인" --user alice

  # Rollback (actual execution)
  python deployment_controller.py "롤백해줘"

Supported commands:
  - Canary deployment: "5% 배포", "Deploy 10% canary"
  - Monitoring: "모니터링 시작", "Start monitoring", "모니터링 중지"
  - Testing: "테스트 실행", "Run load test"
  - Status: "상태 확인", "Check status"
  - Rollback: "롤백", "Rollback canary"
  - Probe: "Probe gentle/normal/aggressive"
        """,
    )

    parser.add_argument("command", help="Natural language deployment command")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode (no actual execution)"
    )
    parser.add_argument("--user", help="User ID for tracking")
    parser.add_argument(
        "--no-save", action="store_true", help="Don't save execution report"
    )
    parser.add_argument(
        "--slack-format", action="store_true", help="Output in Slack message format"
    )

    args = parser.parse_args()

    # Create controller
    controller = DeploymentController(
        dry_run=args.dry_run, save_reports=not args.no_save
    )

    # Execute command
    try:
        report = controller.execute_command(args.command, args.user)

        # Format output
        if args.slack_format:
            print(controller.format_report_for_slack(report, args.command))
        else:
            print(controller.format_report_for_console(report, args.command))

        # Exit with appropriate code
        sys.exit(0 if report.overall_success else 1)

    except Exception as e:
        logger.exception("Error executing command")
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
