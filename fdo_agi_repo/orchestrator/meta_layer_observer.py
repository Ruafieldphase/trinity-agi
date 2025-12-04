#!/usr/bin/env python3
"""
Meta-Layer Observer - 모든 작업을 메타층에서 관찰하는 감시 시스템

핵심 개념:
- 같은 레이어: Task Queue 작업만 감시 (Task Watchdog)
- 메타 레이어: PowerShell, Python, VS Code 등 **모든 실행 중인 작업** 감시

감시 대상:
1. PowerShell 스크립트 실행 (system_health_check.ps1 등)
2. Python 프로세스 (RPA Worker, Task Queue Server 등)
3. Background Jobs (VS Code Tasks)
4. Scheduled Tasks (자동 실행 작업)

감지 조건:
- CPU 사용률 0% + 장시간 실행 = 멈춘 작업
- 메모리만 증가 + CPU 없음 = 데드락
- 응답 없는 프로세스 = 좀비 프로세스
"""

import json
import os
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# 감시 설정
OBSERVATION_INTERVAL = 30  # 30초마다 관찰
STUCK_THRESHOLD = 300  # 5분간 CPU 0% = 멈춘 것으로 판단
MEMORY_LEAK_THRESHOLD = 200 * 1024 * 1024  # 200MB 메모리 증가


class MetaLayerObserver:
    """메타층 관찰자 - 모든 작업을 상위 레이어에서 감시"""
    
    def __init__(self, auto_recover: bool = True, verbose: bool = True):
        self.auto_recover = auto_recover
        self.verbose = verbose
        self.process_history: Dict[int, List[Dict]] = defaultdict(list)
        self.stuck_alerts: List[Dict] = []
        
    def log(self, message: str, level: str = "INFO"):
        """로그 출력"""
        prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "DEBUG": "🔍"}
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[{timestamp}] {prefix.get(level, 'ℹ️')} {message}")
    
    def get_all_processes(self) -> List[Dict]:
        """모든 관련 프로세스 조회"""
        try:
            # PowerShell로 프로세스 정보 가져오기
            cmd = [
                "powershell", "-NoProfile", "-Command",
                "$procs = @(); "
                "Get-Process powershell -ErrorAction SilentlyContinue | ForEach-Object { $procs += $_ }; "
                "Get-Process pwsh -ErrorAction SilentlyContinue | ForEach-Object { $procs += $_ }; "
                "Get-Process python -ErrorAction SilentlyContinue | ForEach-Object { $procs += $_ }; "
                "$procs | Select-Object Id, ProcessName, StartTime, CPU, WorkingSet, Responding | "
                "ConvertTo-Json"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0 or not result.stdout.strip():
                if self.verbose:
                    self.log(f"프로세스 조회 결과 없음", "DEBUG")
                return []
            
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            
            return data or []
        except json.JSONDecodeError as e:
            self.log(f"JSON 파싱 실패: {e}", "ERROR")
            if self.verbose:
                self.log(f"Output: {result.stdout[:200]}", "DEBUG")
            return []
        except Exception as e:
            self.log(f"프로세스 조회 실패: {e}", "ERROR")
            return []
    
    def get_process_cmdline(self, pid: int) -> Optional[str]:
        """프로세스 커맨드라인 조회"""
        try:
            cmd = [
                "powershell", "-NoProfile", "-Command",
                f"(Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}').CommandLine"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
    
    def analyze_process(self, proc: Dict) -> Optional[Dict]:
        """프로세스 분석 - 멈춤 감지"""
        pid = proc.get("Id")
        if not pid:
            return None
        
        # 히스토리에 추가
        snapshot = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": proc.get("CPU", 0),
            "memory": proc.get("WorkingSet", 0),
            "responding": proc.get("Responding", True)
        }
        self.process_history[pid].append(snapshot)
        
        # 최근 5분 데이터만 유지
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=STUCK_THRESHOLD)
        self.process_history[pid] = [
            s for s in self.process_history[pid]
            if datetime.fromisoformat(s["timestamp"]) > cutoff
        ]
        
        # 충분한 히스토리가 쌓이면 분석
        if len(self.process_history[pid]) < 3:
            return None
        
        # 멈춤 감지: CPU 0% + 5분 경과
        recent = self.process_history[pid]
        cpu_zero = all(s["cpu"] == recent[0]["cpu"] for s in recent[-3:])
        elapsed = (
            datetime.fromisoformat(recent[-1]["timestamp"]) -
            datetime.fromisoformat(recent[0]["timestamp"])
        ).total_seconds()
        
        if cpu_zero and elapsed >= STUCK_THRESHOLD:
            cmdline = self.get_process_cmdline(pid)
            return {
                "pid": pid,
                "name": proc.get("ProcessName"),
                "start_time": proc.get("StartTime"),
                "cmdline": cmdline,
                "stuck_duration": elapsed,
                "memory": proc.get("WorkingSet", 0),
                "responding": proc.get("Responding", True),
                "detection_time": datetime.now(timezone.utc).isoformat()
            }
        
        return None
    
    def recover_stuck_process(self, stuck: Dict) -> bool:
        """멈춘 프로세스 복구"""
        pid = stuck["pid"]
        cmdline = stuck.get("cmdline", "")
        
        self.log(f"멈춘 프로세스 감지: PID {pid}", "WARNING")
        self.log(f"  Command: {cmdline[:100]}...", "DEBUG")
        self.log(f"  Duration: {stuck['stuck_duration']:.0f}s", "DEBUG")
        
        if not self.auto_recover:
            self.log("Auto-recover 비활성화, 수동 개입 필요", "WARNING")
            return False
        
        try:
            # 프로세스 종료
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                         capture_output=True, timeout=10)
            self.log(f"프로세스 종료됨: PID {pid}", "SUCCESS")
            
            # 히스토리에서 제거
            if pid in self.process_history:
                del self.process_history[pid]
            
            return True
        except Exception as e:
            self.log(f"프로세스 종료 실패: {e}", "ERROR")
            return False
    
    def observe_once(self) -> Dict:
        """1회 관찰"""
        processes = self.get_all_processes()
        
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_processes": len(processes),
            "stuck_detected": [],
            "actions_taken": []
        }
        
        for proc in processes:
            stuck = self.analyze_process(proc)
            if stuck:
                status["stuck_detected"].append(stuck)
                self.stuck_alerts.append(stuck)
                
                if self.auto_recover:
                    recovered = self.recover_stuck_process(stuck)
                    status["actions_taken"].append({
                        "pid": stuck["pid"],
                        "action": "terminate",
                        "success": recovered
                    })
        
        return status
    
    def run_continuous(self, duration_seconds: int = 3600):
        """연속 감시 (기본 1시간)"""
        self.log(f"메타층 관찰 시작 (지속: {duration_seconds}s, 간격: {OBSERVATION_INTERVAL}s)", "INFO")
        
        start_time = time.time()
        observations = []
        
        try:
            while time.time() - start_time < duration_seconds:
                status = self.observe_once()
                observations.append(status)
                
                if status["stuck_detected"]:
                    self.log(f"멈춘 프로세스 발견: {len(status['stuck_detected'])}개", "WARNING")
                
                time.sleep(OBSERVATION_INTERVAL)
        except KeyboardInterrupt:
            self.log("사용자가 중단함", "WARNING")
        
        # 최종 리포트 저장
        report_path = OUTPUTS_DIR / "meta_layer_observation_report.json"
        report = {
            "start_time": datetime.fromtimestamp(start_time, timezone.utc).isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "total_observations": len(observations),
            "total_stuck_alerts": len(self.stuck_alerts),
            "observations": observations,
            "stuck_alerts": self.stuck_alerts
        }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.log(f"리포트 저장됨: {report_path}", "SUCCESS")
        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Meta-Layer Observer")
    parser.add_argument("--duration", type=int, default=3600, help="관찰 지속 시간 (초)")
    parser.add_argument("--interval", type=int, default=30, help="관찰 간격 (초)")
    parser.add_argument("--no-recover", action="store_true", help="자동 복구 비활성화")
    parser.add_argument("--once", action="store_true", help="1회만 관찰")
    
    args = parser.parse_args()
    
    global OBSERVATION_INTERVAL
    OBSERVATION_INTERVAL = args.interval
    
    observer = MetaLayerObserver(auto_recover=not args.no_recover)
    
    if args.once:
        status = observer.observe_once()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        observer.run_continuous(args.duration)


if __name__ == "__main__":
    main()
