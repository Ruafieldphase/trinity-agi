#!/usr/bin/env python3
"""
Self-Managing Agent - AI가 스스로 자신과 의존성을 관리하는 자율 에이전트

핵심 원칙:
1. AI는 자신의 건강 상태를 스스로 모니터링
2. 필요한 의존성(서버/워커/워치독)을 자동 등록/시작/복구
3. 권한 문제 시에만 사용자에게 최소한의 승인 요청
4. 모든 작업을 로그로 남기고 투명하게 공개
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
SCRIPTS_DIR = WORKSPACE_ROOT / "scripts"

DEPENDENCIES = {
    "task_queue_server": {
        "check_pattern": "task_queue_server.py",
        "start_script": "ensure_task_queue_server.ps1",
        "health_url": "http://127.0.0.1:8091/api/health",
        "scheduled_task": "AGI_Task_Queue_Server",
        "register_script": "register_task_queue_server.ps1",
        "critical": True
    },
    "rpa_worker": {
        "check_pattern": "rpa_worker.py",
        "start_script": "ensure_rpa_worker.ps1",
        "scheduled_task": None,  # No scheduled task (started by server)
        "critical": True
    },
    "watchdog": {
        "check_pattern": "task_watchdog.py",
        "start_script": None,  # Started via tasks.json
        "scheduled_task": "AgiWatchdog",
        "register_script": "register_watchdog_task.ps1",
        "critical": True
    },
    "task_watchdog": {
        "check_pattern": "task_watchdog.py",
        "start_script": None,  # Background job
        "scheduled_task": "AGI_TaskWatchdog",
        "register_script": "register_task_watchdog_scheduled_task.ps1",
        "critical": True,
        "monitors": "Stuck tasks in queue"
    },
    "meta_observer": {
        "check_pattern": "meta_observer_daemon.ps1",
        "start_script": None,  # OS-level scheduled task
        "scheduled_task": "AGI_MetaLayerObserver",
        "register_script": "register_meta_observer_task.ps1",
        "critical": True,
        "layer": "meta",
        "monitors": "ALL AGI processes (OS-level)"
    },
    "master_orchestrator": {
        "check_pattern": "master_orchestrator.ps1",
        "scheduled_task": "AGI_Master_Orchestrator",
        "register_script": "register_master_orchestrator.ps1",
        "critical": True
    },
    "monitoring_collector": {
        "scheduled_task": "MonitoringCollector",
        "register_script": "register_monitoring_collector_task.ps1",
        "critical": False
    }
}


class SelfManagingAgent:
    """AI 자율 관리 에이전트"""
    
    def __init__(self, auto_fix: bool = True, verbose: bool = True):
        self.auto_fix = auto_fix
        self.verbose = verbose
        self.status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dependencies": {},
            "actions_taken": [],
            "errors": [],
            "needs_human_approval": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """로그 출력"""
        if self.verbose:
            prefix = {
                "INFO": "ℹ️",
                "SUCCESS": "✅",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "ACTION": "🔧"
            }.get(level, "ℹ️")
            print(f"{prefix} {message}")
    
    def check_process_running(self, pattern: str) -> bool:
        """프로세스 실행 중인지 확인"""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"Get-Process | Where-Object {{ $_.CommandLine -like '*{pattern}*' }} | Measure-Object | Select-Object -ExpandProperty Count"],
                capture_output=True,
                text=True,
                timeout=5
            )
            count = int(result.stdout.strip() or "0")
            return count > 0
        except Exception as e:
            self.log(f"Failed to check process {pattern}: {e}", "ERROR")
            return False
    
    def check_scheduled_task(self, task_name: str) -> Tuple[bool, Optional[str]]:
        """예약 작업 등록 여부 및 상태 확인"""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"$t = Get-ScheduledTask -TaskName '{task_name}' -ErrorAction SilentlyContinue; if ($t) {{ $t.State }} else {{ 'NotFound' }}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            state = result.stdout.strip()
            if state == "NotFound":
                return False, None
            return True, state
        except Exception as e:
            self.log(f"Failed to check scheduled task {task_name}: {e}", "ERROR")
            return False, None
    
    def check_http_health(self, url: str, timeout: int = 3) -> bool:
        """HTTP 헬스 체크"""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"try {{ $r = Invoke-WebRequest -Uri '{url}' -TimeoutSec {timeout} -UseBasicParsing; $r.StatusCode }} catch {{ 0 }}"],
                capture_output=True,
                text=True,
                timeout=timeout + 2
            )
            status_code = int(result.stdout.strip() or "0")
            return status_code == 200
        except Exception:
            return False
    
    def register_scheduled_task(self, dep_name: str, register_script: str) -> bool:
        """예약 작업 등록 시도"""
        script_path = SCRIPTS_DIR / register_script
        if not script_path.exists():
            self.log(f"Register script not found: {script_path}", "ERROR")
            self.status["errors"].append(f"Missing register script: {register_script}")
            return False
        
        self.log(f"Attempting to register {dep_name}...", "ACTION")
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(script_path), "-Register"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log(f"Successfully registered {dep_name}", "SUCCESS")
                self.status["actions_taken"].append({
                    "action": "register_scheduled_task",
                    "target": dep_name,
                    "script": register_script,
                    "success": True
                })
                return True
            else:
                # 권한 부족 가능성 확인
                if "Access" in result.stderr or "권한" in result.stderr or "denied" in result.stderr.lower():
                    self.log(f"Permission denied for {dep_name} - needs admin rights", "WARNING")
                    self.status["needs_human_approval"].append({
                        "task": "register_scheduled_task",
                        "target": dep_name,
                        "reason": "Administrator privileges required",
                        "manual_command": f"powershell -NoProfile -ExecutionPolicy Bypass -File '{script_path}' -Register"
                    })
                else:
                    self.log(f"Failed to register {dep_name}: {result.stderr[:200]}", "ERROR")
                    self.status["errors"].append(f"Failed to register {dep_name}: {result.stderr[:200]}")
                return False
        except Exception as e:
            self.log(f"Exception during registration of {dep_name}: {e}", "ERROR")
            self.status["errors"].append(f"Exception registering {dep_name}: {str(e)}")
            return False
    
    def start_dependency(self, dep_name: str, start_script: str) -> bool:
        """의존성 시작"""
        script_path = SCRIPTS_DIR / start_script
        if not script_path.exists():
            self.log(f"Start script not found: {script_path}", "ERROR")
            return False
        
        self.log(f"Starting {dep_name}...", "ACTION")
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(script_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log(f"Successfully started {dep_name}", "SUCCESS")
                self.status["actions_taken"].append({
                    "action": "start_dependency",
                    "target": dep_name,
                    "script": start_script,
                    "success": True
                })
                return True
            else:
                self.log(f"Failed to start {dep_name}: {result.stderr[:200]}", "ERROR")
                self.status["errors"].append(f"Failed to start {dep_name}")
                return False
        except Exception as e:
            self.log(f"Exception starting {dep_name}: {e}", "ERROR")
            return False
    
    def check_and_fix_dependency(self, dep_name: str, config: Dict) -> Dict:
        """의존성 체크 및 자동 수정"""
        dep_status = {
            "name": dep_name,
            "critical": config.get("critical", False),
            "process_running": False,
            "scheduled_task_registered": False,
            "scheduled_task_state": None,
            "health_ok": False,
            "auto_fixed": False
        }
        
        # 1. 프로세스 실행 확인
        if "check_pattern" in config:
            dep_status["process_running"] = self.check_process_running(config["check_pattern"])
        
        # 2. 예약 작업 확인
        if "scheduled_task" in config and config["scheduled_task"]:
            registered, state = self.check_scheduled_task(config["scheduled_task"])
            dep_status["scheduled_task_registered"] = registered
            dep_status["scheduled_task_state"] = state
        
        # 3. HTTP 헬스 체크
        if "health_url" in config:
            dep_status["health_ok"] = self.check_http_health(config["health_url"])
        
        # 4. 자동 수정 시도
        # 4. 자동 수정 시도
        if self.auto_fix and dep_status["critical"]:
            # 예약 작업 미등록 시 등록 시도
            if "scheduled_task" in config and config["scheduled_task"]:
                if not dep_status["scheduled_task_registered"]:
                    if "register_script" in config:
                        success = self.register_scheduled_task(dep_name, config["register_script"])
                        if success:
                            dep_status["scheduled_task_registered"] = True
                            dep_status["auto_fixed"] = True
                
                # 예약 작업이 비활성화된 경우 활성화 시도
                elif dep_status["scheduled_task_state"] == "Disabled":
                    self.log(f"Enabling disabled task {config['scheduled_task']}...", "ACTION")
                    try:
                        subprocess.run(
                            ["powershell", "-NoProfile", "-Command", 
                             f"Enable-ScheduledTask -TaskName '{config['scheduled_task']}'"],
                            check=True
                        )
                        self.log(f"Successfully enabled {config['scheduled_task']}", "SUCCESS")
                        dep_status["scheduled_task_state"] = "Ready"
                        dep_status["auto_fixed"] = True
                    except Exception as e:
                        self.log(f"Failed to enable task {config['scheduled_task']}: {e}", "ERROR")

            # 프로세스 미실행 시 시작 시도
            if "start_script" in config and config["start_script"] and not dep_status["process_running"]:
                success = self.start_dependency(dep_name, config["start_script"])
                if success:
                    time.sleep(3)  # 안정화 대기
                    dep_status["process_running"] = self.check_process_running(config["check_pattern"])
                    dep_status["auto_fixed"] = True
        
        return dep_status
    
    def generate_report(self) -> str:
        """리포트 생성"""
        lines = []
        lines.append("# Self-Managing Agent Report")
        lines.append(f"\n**Timestamp**: {self.status['timestamp']}")
        lines.append(f"**Auto-Fix**: {'Enabled' if self.auto_fix else 'Disabled'}")
        
        lines.append("\n## Dependencies Status")
        for dep_name, dep_status in self.status["dependencies"].items():
            critical_mark = "🔴" if dep_status["critical"] else "🟡"
            lines.append(f"\n### {critical_mark} {dep_name}")
            lines.append(f"- Process Running: {'✅' if dep_status['process_running'] else '❌'}")
            if dep_status["scheduled_task_state"] is not None:
                lines.append(f"- Scheduled Task: {'✅' if dep_status['scheduled_task_registered'] else '❌'} ({dep_status['scheduled_task_state']})")
            if "health_ok" in dep_status and dep_status["health_ok"] is not None:
                lines.append(f"- Health Check: {'✅' if dep_status['health_ok'] else '❌'}")
            if dep_status.get("auto_fixed"):
                lines.append(f"- Auto-Fixed: ✅")
        
        if self.status["actions_taken"]:
            lines.append("\n## Actions Taken")
            for action in self.status["actions_taken"]:
                lines.append(f"- {action['action']}: {action['target']} ({'✅' if action['success'] else '❌'})")
        
        if self.status["needs_human_approval"]:
            lines.append("\n## ⚠️ Needs Human Approval (Administrator Privileges)")
            for item in self.status["needs_human_approval"]:
                lines.append(f"\n### {item['target']}")
                lines.append(f"- Task: {item['task']}")
                lines.append(f"- Reason: {item['reason']}")
                lines.append(f"- Manual Command:")
                lines.append(f"  ```powershell")
                lines.append(f"  {item['manual_command']}")
                lines.append(f"  ```")
        
        if self.status["errors"]:
            lines.append("\n## Errors")
            for error in self.status["errors"]:
                lines.append(f"- {error}")
        
        return "\n".join(lines)
    
    def run(self) -> int:
        """메인 실행"""
        self.log("Self-Managing Agent started", "INFO")
        self.log(f"Auto-Fix: {'Enabled' if self.auto_fix else 'Disabled'}", "INFO")
        
        # 모든 의존성 체크
        for dep_name, config in DEPENDENCIES.items():
            self.log(f"\nChecking {dep_name}...", "INFO")
            dep_status = self.check_and_fix_dependency(dep_name, config)
            self.status["dependencies"][dep_name] = dep_status
        
        # 리포트 생성 및 저장
        report_md = self.generate_report()
        report_path = OUTPUTS_DIR / "self_managing_agent_latest.md"
        report_path.write_text(report_md, encoding="utf-8")
        self.log(f"\nReport saved: {report_path}", "SUCCESS")
        
        # JSON 저장
        json_path = OUTPUTS_DIR / "self_managing_agent_latest.json"
        json_path.write_text(json.dumps(self.status, indent=2, ensure_ascii=False), encoding="utf-8")
        
        # 결과 요약
        critical_issues = [
            name for name, status in self.status["dependencies"].items()
            if status["critical"] and not (status.get("process_running") or status.get("scheduled_task_registered"))
        ]
        
        if critical_issues:
            self.log(f"\n⚠️ Critical issues found: {', '.join(critical_issues)}", "WARNING")
            if self.status["needs_human_approval"]:
                self.log(f"\n🙋 Human approval needed for {len(self.status['needs_human_approval'])} items", "WARNING")
                self.log("See report for details", "INFO")
            return 1
        else:
            self.log("\n✅ All critical dependencies are healthy", "SUCCESS")
            return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Self-Managing Agent - AI autonomous system manager")
    parser.add_argument("--no-auto-fix", action="store_true", help="Disable auto-fix (check only)")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()
    
    agent = SelfManagingAgent(auto_fix=not args.no_auto_fix, verbose=not args.quiet)
    return agent.run()


if __name__ == "__main__":
    sys.exit(main())
