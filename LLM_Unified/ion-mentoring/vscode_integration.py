from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

VS_CODE_VERSION = "2.0.0"


@dataclass
class TaskSpec:
    label: str
    command: str
    args: List[str]
    group: Optional[str] = None
    isBackground: Optional[bool] = None
    problemMatcher: Optional[List[str]] = None
    options: Optional[Dict[str, Any]] = None

    def to_tasks_json(self) -> Dict[str, Any]:
        task: Dict[str, Any] = {
            "label": self.label,
            "type": "shell",
            "command": self.command,
            "args": self.args,
        }
        if self.group:
            task["group"] = self.group
        if self.isBackground is not None:
            task["isBackground"] = self.isBackground
        if self.problemMatcher:
            task["problemMatcher"] = self.problemMatcher
        if self.options:
            task["options"] = self.options
        return task


def _pwsh_args(script_path: str, *extra: str) -> List[str]:
    args = [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        script_path,
    ]
    args.extend(extra)
    return args


def _pwsh_command() -> str:
    return "powershell"


def default_repo_tasks(workspace_folder_var: str = "${workspaceFolder}") -> List[TaskSpec]:
    """
    Repository-friendly default tasks that mirror the commonly used operations.
    These are derived from the project's operational scripts and current workspace tasks.
    """
    ws = workspace_folder_var
    scripts_root = f"{ws}/LLM_Unified/ion-mentoring/scripts"

    tasks: List[TaskSpec] = []

    def t(
        label: str,
        script_rel: str,
        *extra_args: str,
        group: Optional[str] = None,
        is_bg: Optional[bool] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> TaskSpec:
        return TaskSpec(
            label=label,
            command=_pwsh_command(),
            args=_pwsh_args(f"{scripts_root}/{script_rel}", *extra_args),
            group=group,
            isBackground=is_bg,
            options={"env": env} if env else None,
        )

    # Monitoring tasks
    # Live status watcher (uses extension_api)
    tasks.append(
        TaskSpec(
            label="VS Code: Watch Orchestrator Status",
            command=_pwsh_command(),
            args=[
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                (
                    f"{ws}/LLM_Unified/.venv/Scripts/python.exe "
                    f"{ws}/LLM_Unified/ion-mentoring/extension_api.py watch-status "
                    f"--state-file {ws}/LLM_Unified/ion-mentoring/outputs/orchestrator_state.json --interval 1.0"
                ),
            ],
            group="test",
            isBackground=True,
        )
    )
    tasks.append(
        t(
            "Monitoring: Start Canary Loop (30m, with probe)",
            "start_monitor_loop_with_probe.ps1",
            "-KillExisting",
            "-IntervalSeconds",
            "1800",
            "-DurationMinutes",
            "1440",
            group="test",
            is_bg=True,
        )
    )
    tasks.append(
        t(
            "Monitoring: Start Canary Loop (30m)",
            "start_monitor_loop.ps1",
            "-KillExisting",
            "-IntervalSeconds",
            "1800",
            "-DurationMinutes",
            "1440",
            group="test",
            is_bg=True,
        )
    )
    tasks.append(
        t(
            "Monitoring: Stop All Canary Loops",
            "start_monitor_loop.ps1",
            "-KillExisting",
            "-StopOnly",
            group="test",
        )
    )
    tasks.append(
        t(
            "Monitoring: Rate Limit Probe (safe)",
            "rate_limit_probe.ps1",
            "-RequestsPerSide",
            "10",
            "-DelayMsBetweenRequests",
            "500",
            group="test",
        )
    )
    tasks.append(
        t(
            "Monitoring: One-shot Probe",
            "rate_limit_probe.ps1",
            "-RequestsPerSide",
            "5",
            "-DelayMsBetweenRequests",
            "500",
            "-OutJson",
            f"{ws}/rate_limit_probe_once.json",
            group="test",
        )
    )
    tasks.append(
        t(
            "Monitoring: Check Canary Status",
            "check_monitoring_status.ps1",
            group="test",
        )
    )
    tasks.append(
        t(
            "Monitoring: Create Canary Dashboard",
            # Use gcloud create via inline -Command; keep env to disable prompts
            # We wrap it by using PowerShell -Command from VS Code task consumer
            # Here, we call gcloud directly through -Command in options by using command args style
            # For parity with workspace tasks, we provide it as a separate task via direct command
            # Implementation note: We'll keep this mirrored in extension_api.generate_commands_json()
            # For tasks.json, we replicate using -Command string.
            # We'll still route through powershell -Command with the same content.
            # Keeping script_rel as placeholder; it will not be used, we pass -Command instead below.
            "check_monitoring_status.ps1",
            group="build",
            env={"CLOUDSDK_CORE_DISABLE_PROMPTS": "1"},
        )
    )

    # Luon pipeline utilities
    tasks.append(
        TaskSpec(
            label="Luon: Start Watch",
            command=_pwsh_command(),
            args=_pwsh_args(f"{ws}/scripts/start_luon_watch.ps1", "-IntervalSeconds", "15"),
        )
    )
    tasks.append(
        TaskSpec(
            label="Luon: Kill and Restart Watch",
            command=_pwsh_command(),
            args=_pwsh_args(
                f"{ws}/scripts/start_luon_watch.ps1", "-KillExisting", "-IntervalSeconds", "15"
            ),
            group="build",
        )
    )
    tasks.append(
        TaskSpec(
            label="Luon: Run Pipeline Once",
            command=_pwsh_command(),
            args=_pwsh_args(f"{ws}/scripts/run_luon_pipeline.ps1"),
            group="test",
        )
    )

    # Python tests (repo venv)
    tasks.append(
        TaskSpec(
            label="Python: Run All Tests (repo venv)",
            command=_pwsh_command(),
            args=[
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"{ws}/LLM_Unified/.venv/Scripts/python.exe -m pytest -q",
            ],
            group="test",
        )
    )
    tasks.append(
        TaskSpec(
            label="Python: Run Vertex AI Test (repo venv)",
            command=_pwsh_command(),
            args=[
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                f"{ws}/LLM_Unified/.venv/Scripts/python.exe -m pytest -q LLM_Unified/ion-mentoring/tests/test_ion_first_vertex_ai.py",
            ],
            group="test",
        )
    )

    # Load testing
    tasks.append(
        t(
            "Load Test: Run All Scenarios",
            "run_all_load_tests.ps1",
            group="test",
        )
    )
    tasks.append(
        t(
            "Load Test: Light Smoke (10s)",
            "run_all_load_tests.ps1",
            "-ScenarioProfile",
            "light",
            "-OverrideRunTime",
            "10s",
            group="test",
        )
    )
    tasks.append(
        t(
            "Load Testing: Summarize Locust Results (Latest)",
            "summarize_locust_results.ps1",
            group="test",
        )
    )
    tasks.append(
        t(
            "Load Testing: Summarize Locust Results (All CSVs)",
            "summarize_locust_results.ps1",
            "-InputGlob",
            "outputs/*.csv",
            group="test",
        )
    )

    # Canary deploy/rollback
    tasks.append(
        t(
            "Dry-Run: Phase4 Canary Deploy",
            "deploy_phase4_canary.ps1",
            "-ProjectId",
            "naeda-genesis",
            "-DryRun",
            group="build",
            env={"CLOUDSDK_CORE_DISABLE_PROMPTS": "1"},
        )
    )
    for pct in (5, 10, 25, 50, 100):
        tasks.append(
            t(
                f"Phase4: Canary Deploy ({pct}%)",
                "deploy_phase4_canary.ps1",
                "-ProjectId",
                "naeda-genesis",
                "-CanaryPercentage",
                str(pct),
                group="build",
                env={"CLOUDSDK_CORE_DISABLE_PROMPTS": "1"},
            )
        )
    tasks.append(
        t(
            "Phase4: Rollback Canary (to 0%)",
            "rollback_phase4_canary.ps1",
            "-ProjectId",
            "naeda-genesis",
            "-AutoApprove",
            group="build",
            env={"CLOUDSDK_CORE_DISABLE_PROMPTS": "1"},
        )
    )
    tasks.append(
        t(
            "Emergency: Rollback Canary (Interactive)",
            "emergency_rollback.ps1",
            group="build",
        )
    )
    tasks.append(
        t(
            "Emergency: Force Rollback Canary (Skip Confirmation)",
            "emergency_rollback.ps1",
            "-Force",
            "-SkipConfirmation",
            group="build",
        )
    )

    # Quick compare and one-off utilities
    tasks.append(
        t(
            "One-off: Balanced Warmup",
            "balanced_warmup.ps1",
            "-CanaryUrl",
            "https://ion-api-canary-64076350717.us-central1.run.app",
            "-LegacyUrl",
            "https://ion-api-64076350717.us-central1.run.app",
            "-CountPerSide",
            "25",
            group="test",
        )
    )
    tasks.append(
        t(
            "Quick: POST compare personalized vs legacy chat",
            "compare_canary_vs_legacy.ps1",
            "-Method",
            "POST",
            "-RequestsPerSide",
            "10",
            "-Retries",
            "0",
            "-DelayMsBetweenRequests",
            "50",
            "-CanaryEndpointPath",
            "/api/v2/recommend/personalized",
            "-LegacyEndpointPath",
            "/chat",
            "-CanaryBodyJson",
            '{"user_id":"test-123","query":"Explain AI concepts in a concise style","options":{"style":"concise","depth":"overview"}}',
            "-LegacyBodyJson",
            '{"message":"Explain AI concepts in a concise style"}',
            "-MinSuccessRatePercent",
            "80",
        )
    )
    tasks.append(
        t(
            "Quick: POST compare (debug, save JSON)",
            "compare_canary_vs_legacy.ps1",
            "-Method",
            "POST",
            "-RequestsPerSide",
            "10",
            "-Retries",
            "2",
            "-DelayMsBetweenRequests",
            "50",
            "-CanaryEndpointPath",
            "/api/v2/recommend/personalized",
            "-LegacyEndpointPath",
            "/chat",
            "-CanaryBodyJson",
            '{"user_id":"test-123","query":"Explain AI concepts in a concise style"}',
            "-LegacyBodyJson",
            '{"message":"Explain AI concepts in a concise style"}',
            "-MinSuccessRatePercent",
            "80",
            "-OutJson",
            f"{ws}/compare_quick_out.json",
            group="test",
        )
    )

    # Log utilities
    tasks.append(
        t(
            "Monitoring: Filter Logs (Last 1 Hour)",
            "filter_logs_by_time.ps1",
            "-Last",
            "1h",
            "-ShowSummary",
            group="test",
        )
    )
    tasks.append(
        t(
            "Monitoring: Filter Logs (Last 24 Hours)",
            "filter_logs_by_time.ps1",
            "-Last",
            "24h",
            "-ShowSummary",
            group="test",
        )
    )
    tasks.append(
        t(
            "Operations: Generate Daily Report",
            "generate_daily_report.ps1",
            "-Hours",
            "24",
            group="test",
        )
    )
    tasks.append(
        t(
            "Operations: Cleanup Old Logs (7 days, DryRun)",
            "cleanup_old_logs.ps1",
            "-KeepDays",
            "7",
            "-DryRun",
            "-Verbose",
            group="test",
        )
    )
    tasks.append(
        t(
            "Operations: Cleanup Old Logs (7 days, Execute)",
            "cleanup_old_logs.ps1",
            "-KeepDays",
            "7",
            group="build",
        )
    )

    # Probe intensity presets
    tasks.append(
        t(
            "Probe: Gentle (3 req, 2s delay)",
            "rate_limit_probe.ps1",
            "-RequestsPerSide",
            "3",
            "-DelayMsBetweenRequests",
            "2000",
            group="test",
        )
    )
    tasks.append(
        t(
            "Probe: Normal (10 req, 1s delay)",
            "rate_limit_probe.ps1",
            "-RequestsPerSide",
            "10",
            "-DelayMsBetweenRequests",
            "1000",
            group="test",
        )
    )
    tasks.append(
        t(
            "Probe: Aggressive (25 req, 500ms delay)",
            "rate_limit_probe.ps1",
            "-RequestsPerSide",
            "25",
            "-DelayMsBetweenRequests",
            "500",
            group="test",
        )
    )

    # Inbox watcher (production readiness)
    tasks.append(
        t(
            "Inbox Watcher: Register (At logon)",
            "register_inbox_watcher.ps1",
            "-TaskName",
            "IonInboxWatcher",
            "-Agents",
            "all",
            "-Force",
            group="build",
        )
    )
    tasks.append(
        t(
            "Inbox Watcher: Unregister",
            "unregister_inbox_watcher.ps1",
            "-TaskName",
            "IonInboxWatcher",
            "-Force",
            group="build",
        )
    )
    tasks.append(
        t(
            "Inbox Watcher: Stop (Scheduled Task)",
            "stop_inbox_watcher.ps1",
            "-TaskName",
            "IonInboxWatcher",
            group="build",
        )
    )
    tasks.append(
        t(
            "Inbox Watcher: Status",
            "status_inbox_watcher.ps1",
            "-TaskName",
            "IonInboxWatcher",
            group="test",
        )
    )
    tasks.append(
        t(
            "Inbox Watcher: Show Log (tail 200)",
            "show_inbox_watcher_log.ps1",
            "-Tail",
            "200",
            group="test",
        )
    )
    tasks.append(
        t(
            "Inbox Watcher: Follow Log",
            "show_inbox_watcher_log.ps1",
            "-Tail",
            "100",
            "-Follow",
            group="test",
        )
    )
    tasks.append(
        t(
            "Inbox Watcher: Run Now (foreground)",
            "run_inbox_watcher.ps1",
            "-Agents",
            "all",
            group="test",
        )
    )

    # Direct runner (no hidden process) for debugging
    tasks.append(
        TaskSpec(
            label="Inbox Watcher: Run Now (direct)",
            command=_pwsh_command(),
            args=[
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                (
                    f"{ws}/LLM_Unified/.venv/Scripts/python.exe "
                    f"{ws}/LLM_Unified/ion-mentoring/inbox_watcher_runner.py "
                    f"--agents all --duration-seconds 10 --status-file {ws}/LLM_Unified/ion-mentoring/outputs/inbox_watcher_status.json --status-interval-seconds 1"
                ),
            ],
            group="test",
        )
    )

    # VS Code watcher for inbox watcher status
    tasks.append(
        TaskSpec(
            label="VS Code: Watch Inbox Watcher Status",
            command=_pwsh_command(),
            args=[
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                (
                    f"{ws}/LLM_Unified/.venv/Scripts/python.exe "
                    f"{ws}/LLM_Unified/ion-mentoring/extension_api.py watch-status "
                    f"--state-file {ws}/LLM_Unified/ion-mentoring/outputs/inbox_watcher_status.json --interval 1.0"
                ),
            ],
            group="test",
            isBackground=True,
        )
    )

    return tasks


def write_tasks_json(vscode_dir: Path, tasks: List[TaskSpec]) -> Path:
    vscode_dir.mkdir(parents=True, exist_ok=True)
    out_path = vscode_dir / "tasks.json"
    payload = {
        "version": VS_CODE_VERSION,
        "tasks": [t.to_tasks_json() for t in tasks],
    }
    new_text = json.dumps(payload, ensure_ascii=False, indent=2)
    # If exists and different, back up
    if out_path.exists():
        try:
            current_text = out_path.read_text(encoding="utf-8")
        except Exception:
            current_text = ""
        if current_text.strip() != new_text.strip():
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = out_path.with_suffix(f".json.bak.{ts}")
            try:
                out_path.replace(backup)
            except Exception:
                # Fallback: write backup separately without replacing original first
                backup.write_text(current_text, encoding="utf-8")
        # After backup (or if identical), write new
    out_path.write_text(new_text, encoding="utf-8")
    return out_path


def generate_commands_json(vscode_dir: Path, tasks: List[TaskSpec]) -> Path:
    """
    Create a lightweight commands.json for internal reference or custom tooling.
    VS Code does not natively consume this file, but it can be used by scripts or custom extensions.
    """
    vscode_dir.mkdir(parents=True, exist_ok=True)
    out_path = vscode_dir / "commands.json"
    commands = []
    for t in tasks:
        cmd_id = "task.run." + t.label.lower().replace(" ", "-")
        commands.append(
            {
                "id": cmd_id,
                "title": f"Run: {t.label}",
                "taskLabel": t.label,
            }
        )
    new_text = json.dumps({"commands": commands}, ensure_ascii=False, indent=2)
    if out_path.exists():
        try:
            current_text = out_path.read_text(encoding="utf-8")
        except Exception:
            current_text = ""
        if current_text.strip() != new_text.strip():
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup = out_path.with_suffix(f".json.bak.{ts}")
            try:
                out_path.replace(backup)
            except Exception:
                backup.write_text(current_text, encoding="utf-8")
    out_path.write_text(new_text, encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate VS Code tasks.json and commands.json")
    parser.add_argument(
        "--workspace-dir",
        default=str(Path(__file__).resolve().parents[2]),
        help="Workspace root directory (default: repo root)",
    )
    parser.add_argument(
        "--vscode-dir",
        default=".vscode",
        help="Relative path under workspace for VS Code config directory",
    )
    args = parser.parse_args()

    # Sanitize in case a poweshell inline comment was appended to the same token
    ws_arg = args.workspace_dir
    if "#" in ws_arg:
        ws_arg = ws_arg.split("#", 1)[0].strip()
    workspace_dir = Path(ws_arg).resolve()
    vscode_dir = (workspace_dir / args.vscode_dir).resolve()

    tasks = default_repo_tasks(workspace_folder_var="${workspaceFolder}")
    tasks_path = write_tasks_json(vscode_dir, tasks)
    cmds_path = generate_commands_json(vscode_dir, tasks)

    print(f"Generated: {tasks_path}")
    print(f"Generated: {cmds_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
