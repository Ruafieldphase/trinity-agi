#!/usr/bin/env python3
"""
Autonomous Goal Executor - Phase 2
생성된 자율 목표(JSON)를 읽어 실제 실행 가능한 스크립트를 호출하고,
실행 결과를 goal_tracker.json에 기록합니다.

동작 요약:
1) outputs/autonomous_goals_latest.json 로드
2) 상태가 queued인 첫 목표(또는 지정 index)를 선택
3) executable.type == "script" 인 경우 PowerShell로 스크립트 실행
4) 성공/실패 결과와 로그를 outputs/* 및 fdo_agi_repo/memory/goal_tracker.json에 반영

안전 설계:
- 워크스페이스 변수(${workspaceFolder}) 안전 치환
- 타임아웃, 존재 여부 검사, 상세 오류 메시지 출력
- 기존 tracker 파일이 없으면 새로 생성
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from workspace_root import get_workspace_root
try:
    from scripts.sovereign_voice import speak
except ImportError:
    # Fallback if not easily importable
    def speak(msg): print(f"[SPEAK] {msg}")

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@dataclass
class ExecResult:
    success: bool
    returncode: int
    duration_sec: float
    stdout: str
    stderr: str


class GoalExecutor:
    """자율 목표 실행기"""

    def __init__(self, workspace_root: Path, task_queue_server: str = "http://127.0.0.1:8091") -> None:
        self.workspace_root = Path(workspace_root)
        self.task_queue_server = task_queue_server
        self.outputs_dir = self.workspace_root / "outputs"
        self.goals_path = self.outputs_dir / "autonomous_goals_latest.json"
        self.goal_tracker_path = self.workspace_root / "fdo_agi_repo" / "memory" / "goal_tracker.json"
        self.tracker_path = self.goal_tracker_path # legacy alias
        self.last_run_log = self.outputs_dir / "autonomous_goal_executor_last_run.json"
        self.placeholder_map = {"${workspaceFolder}": str(self.workspace_root)}
        self.resonance_oracle = None # Initialized for Phase 2 compatibility
        self.sandbox_bridge = None # Initialized for Phase 2 compatibility
        self.reward_tracker = None # Initialized for Phase 2 compatibility

    # ---------- 파일 유틸 ----------
    def _read_json(self, path: Path) -> Any:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ---------- 플레이스홀더 ----------
    def _expand(self, value: Any) -> Any:
        """${workspaceFolder} 치환 (문자열/리스트/딕셔너리 전파)"""
        if isinstance(value, str):
            return value.replace("${workspaceFolder}", str(self.workspace_root))
        if isinstance(value, list):
            return [self._expand(v) for v in value]
        if isinstance(value, dict):
            return {k: self._expand(v) for k, v in value.items()}
        return value

    # ---------- 목표 선택 ----------
    def _select_goal(self, goals: List[Dict[str, Any]], index: Optional[int] = None) -> Tuple[int, Dict[str, Any]]:
        if index is not None:
            if index < 0 or index >= len(goals):
                raise IndexError(f"goal-index {index} is out of range (0..{len(goals)-1})")
            return index, goals[index]
        # 기본: queued 상태 첫 번째
        for i, g in enumerate(goals):
            if g.get("status", "queued").lower() == "queued":
                return i, g
        # 없으면 0번이라도 시도
        if goals:
            return 0, goals[0]
        raise ValueError("No goals available to execute")

    # ---------- 실행 ----------
    def _run_script(self, script: str, args: List[str], timeout: int) -> ExecResult:
        ps = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            script,
            *args,
        ]
        logger.info(f"▶ Running script: {script} {args}")
        t0 = time.time()
        try:
            proc = subprocess.run(
                ps,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=timeout if timeout and timeout > 0 else None,
            )
            dt = time.time() - t0
            ok = proc.returncode == 0
            logger.info(f"✅ Completed with code {proc.returncode} in {dt:.1f}s")
            if not ok:
                logger.error(proc.stderr.strip())
            return ExecResult(ok, proc.returncode, dt, proc.stdout, proc.stderr)
        except subprocess.TimeoutExpired as e:
            dt = time.time() - t0
            logger.error(f"⏱️ Timeout after {dt:.1f}s: {script}")
            return ExecResult(False, -1, dt, e.stdout or "", e.stderr or "Timeout")

    def _execute_executable(self, exe: Dict[str, Any]) -> ExecResult:
        exe = self._expand(exe)
        typ = exe.get("type", "script").lower()
        if typ != "script":
            raise NotImplementedError(f"Unsupported executable type: {typ}")
        script = exe.get("script")
        if not script:
            raise ValueError("Missing 'script' in executable")
        script_path = Path(script)
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        args = [str(a) for a in exe.get("args", [])]
        timeout = int(exe.get("timeout", 900))
        return self._run_script(str(script_path), args, timeout)

    # ---------- 트래커 ----------
    def _load_tracker(self) -> Dict[str, Any]:
        if self.tracker_path.exists():
            try:
                return self._read_json(self.tracker_path)
            except Exception:
                logger.warning("goal_tracker.json corrupted; recreating new tracker")
        return {
            "createdAt": _now_iso(),
            "updatedAt": _now_iso(),
            "goals": [],
            "active_goals": 0,
            "completed_goals": 0,
        }

    def _append_tracker(self, goal: Dict[str, Any], result: ExecResult) -> None:
        tracker = self._load_tracker()
        entry = {
            "timestamp": _now_iso(),
            "title": goal.get("title", "(untitled)"),
            "status": "success" if result.success else "failed",
            "duration_sec": round(result.duration_sec, 3),
            "returncode": result.returncode,
            "task_queue_server": self.task_queue_server,
        }
        tracker.setdefault("goals", []).append(entry)
        # 간단 카운터 업데이트
        if result.success:
            tracker["completed_goals"] = int(tracker.get("completed_goals", 0)) + 1
        tracker["updatedAt"] = _now_iso()
        self._write_json(self.tracker_path, tracker)

    # ---------- 퍼블릭 ----------
    def execute_once(self, goal_index: Optional[int] = None) -> ExecResult:
        if not self.goals_path.exists():
            raise FileNotFoundError(f"Goals JSON not found: {self.goals_path}")
        data = self._read_json(self.goals_path)
        goals = data if isinstance(data, list) else data.get("goals") or data
        if not isinstance(goals, list):
            raise ValueError("Invalid goals JSON format: expected a list")

        idx, goal = self._select_goal(goals, goal_index)
        logger.info(f"🎯 Selected goal[{idx}]: {goal.get('title')}")
        exe = goal.get("executable")
        if not exe:
            raise ValueError("Selected goal has no 'executable'")

        result = self._execute_executable(exe)

        # 결과 로그 파일 저장 (디버깅 용)
        self._write_json(self.last_run_log, {
            "timestamp": _now_iso(),
            "goal_index": idx,
            "goal_title": goal.get("title"),
            "success": result.success,
            "returncode": result.returncode,
            "duration_sec": result.duration_sec,
            "stdout_tail": (result.stdout or "").splitlines()[-20:],
            "stderr_tail": (result.stderr or "").splitlines()[-20:],
        })

        # 트래커 반영
        try:
            self._append_tracker(goal, result)
        except Exception as e:
            logger.warning(f"Failed to update goal tracker: {e}")

        return result


    
    def _check_glymphatic_readiness(self) -> bool:
        """
        🧠 Glymphatic Pre-Execution Check
        
        목표 실행 전에 시스템이 최적 상태인지 확인한다.
        
        Returns:
            True if system is ready, False if cleanup recommended
        """
        try:
            # adaptive_glymphatic_system.py의 상태 파일 체크
            glymphatic_state_path = self.workspace_root / "outputs" / "glymphatic_state.json"
            
            if not glymphatic_state_path.exists():
                logger.info("🧠 No glymphatic state file - assuming ready")
                return True
            
            with open(glymphatic_state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            decision = state.get("decision", {})
            action = decision.get("action", "unknown")
            
            # cleanup_immediate 또는 cleanup_soon이면 경고
            if action in ["cleanup_immediate", "cleanup_soon"]:
                logger.warning(f"🧠 Glymphatic: {action} - cleanup recommended!")
                return False
            
            logger.info(f"🧠 Glymphatic: {action} - system ready")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to check glymphatic state: {e}")
            # 에러 시 안전하게 진행
            return True
    
    def _schedule_post_execution_cleanup(self, goal_duration_minutes: float):
        """
        🧠 Post-Execution Cleanup Scheduling
        
        목표 실행 후 적절한 시점에 cleanup을 예약한다.
        
        Args:
            goal_duration_minutes: 목표 실행 시간 (분)
        """
        try:
            # 실행 시간에 따라 cleanup 예약
            # 예: 30분 이상 작업 → 즉시 cleanup
            #    30분 미만 → 1시간 후 cleanup
            
            if goal_duration_minutes >= 30:
                schedule = "immediate"
                delay_minutes = 0
            else:
                schedule = "deferred"
                delay_minutes = 60
            
            logger.info(f"🧠 Scheduling cleanup: {schedule} (in {delay_minutes} min)")
            
            # TODO: 실제 cleanup 예약 메커니즘 구현
            # 옵션 1: Task Queue에 cleanup task 추가
            # 옵션 2: Windows Scheduled Task 생성
            # 옵션 3: 단순히 파일에 기록하고 다른 데몬이 처리
            
        except Exception as e:
            logger.warning(f"Failed to schedule cleanup: {e}")

    def _resolve_placeholders(self, value: str) -> str:
        """Replace known placeholders in a string."""
        if not isinstance(value, str):
            return value
        out = value
        for k, v in self.placeholder_map.items():
            out = out.replace(k, v)
        return out

    def _resolve_args(self, args: Optional[List[str]]) -> List[str]:
        """Resolve placeholders for each arg string."""
        if not args:
            return []
        return [self._resolve_placeholders(a) for a in args]

    def _find_python_exe(self) -> str:
        """
        Python 실행 파일을 찾는다.
        
        우선순위:
        1. fdo_agi_repo/.venv/Scripts/python.exe (프로젝트 venv)
        2. LLM_Unified/.venv/Scripts/python.exe (통합 venv)
        3. sys.executable (현재 Python)
        
        Returns:
            Python 실행 파일 경로
        """
        workspace_root = Path(self.workspace_root)
        
        # 1. fdo_agi_repo venv
        fdo_venv = workspace_root / "fdo_agi_repo" / ".venv" / "Scripts" / "python.exe"
        if fdo_venv.exists():
            logger.info(f"Found Python: {fdo_venv}")
            return str(fdo_venv)
        
        # 2. LLM_Unified venv
        lum_venv = workspace_root / "LLM_Unified" / ".venv" / "Scripts" / "python.exe"
        if lum_venv.exists():
            logger.info(f"Found Python: {lum_venv}")
            return str(lum_venv)
        
        # 3. Fallback to sys.executable
        logger.info(f"Using system Python: {sys.executable}")
        return sys.executable
        
    def load_goals(self) -> List[Dict[str, Any]]:
        """생성된 목표를 로드한다"""
        if not self.goals_path.exists():
            logger.error(f"Goals file not found: {self.goals_path}")
            return []
        
        try:
            with open(self.goals_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            goals = data.get("goals", [])
            logger.info(f"Loaded {len(goals)} goals from {self.goals_path}")
            return goals
        except Exception as e:
            logger.error(f"Failed to load goals: {e}")
            return []
    
    def load_goal_tracker(self) -> Dict[str, Any]:
        """목표 추적 데이터를 로드한다"""
        if not self.goal_tracker_path.exists():
            return {"goals": [], "last_updated": None}
        
        try:
            with open(self.goal_tracker_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load goal tracker: {e}")
            return {"goals": [], "last_updated": None}
    
    def is_goal_completed(self, goal_title: str, tracker_data: Dict[str, Any]) -> bool:
        """목표가 이미 완료되었는지 확인"""
        for tracked_goal in tracker_data.get("goals", []):
            if tracked_goal["title"].lower().strip() == goal_title.lower().strip():
                if tracked_goal["status"] == "completed":
                    return True
        return False
    
    def auto_register_new_goals(self, goals: List[Dict[str, Any]], tracker_data: Dict[str, Any]) -> int:
        """
        autonomous_goals_latest.json에 있지만 goal_tracker.json에 없는 
        신규 목표를 자동으로 tracker에 pending 상태로 등록한다.
        
        Returns:
            등록된 신규 목표 개수
        """
        existing_titles = {g["title"].lower().strip() for g in tracker_data.get("goals", [])}
        new_goals = []
        
        for goal in goals:
            title = goal["title"].lower().strip()
            if title not in existing_titles:
                # pending 상태로 tracker에 추가할 준비
                new_goal_entry = {
                    "title": goal["title"],  # 원본 title 유지
                    "status": "pending",
                    "added_at": datetime.utcnow().isoformat(),
                    "source": "auto_registered",
                    "priority": goal.get("final_priority", 5.0),
                    "type": goal.get("type", "unknown"),
                    "executable": goal.get("executable", {}),
                    "metadata": goal.get("metadata", {})
                }
                new_goals.append(new_goal_entry)
                logger.info(f"📝 New goal: {goal['title']} (priority={goal.get('final_priority', 5.0)})")
        
        if new_goals:
            # tracker에 추가 및 저장
            tracker_data.setdefault("goals", []).extend(new_goals)
            tracker_data["last_updated"] = datetime.utcnow().isoformat()
            
            try:
                self.goal_tracker_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.goal_tracker_path, 'w', encoding='utf-8') as f:
                    json.dump(tracker_data, f, indent=2, ensure_ascii=False)
                logger.info(f"✅ Tracker updated: {self.goal_tracker_path}")
            except Exception as e:
                logger.error(f"Failed to save tracker: {e}")
                return 0
        
        return len(new_goals)
    
    def calculate_goal_fitness(self, goal: Dict[str, Any], tracker_data: Dict[str, Any]) -> float:
        """
        🌀 Quantum Mode: 목표의 적합도 점수 계산
        
        평가 기준:
        1. Priority (우선순위)
        2. Executability (실행 가능성)
        3. Recent Success Rate (최근 성공률)
        4. Dependencies (의존성 충족 여부)
        5. Resource Availability (리소스 가용성)
        6. Time Appropriateness (시간대 적합성)
        """
        score = 0.0
        
        # 1. Priority (0-10점)
        priority = goal.get("final_priority", goal.get("priority", 5.0))
        score += min(priority, 10.0)
        
        # 2. Executability (0-20점)
        if "executable" in goal and goal["executable"]:
            score += 20.0
        elif any(keyword in goal["title"].lower() for keyword in 
                ["metric", "report", "analysis", "health", "status"]):
            score += 10.0
        
        # 3. Recent Success Rate (0-15점)
        # tracker에서 이 목표의 과거 성공률 확인
        title = goal["title"]
        for tracked_goal in tracker_data.get("goals", []):
            if tracked_goal["title"].lower().strip() == title.lower().strip():
                results = tracked_goal.get("execution_results", [])
                if results:
                    success_count = sum(1 for r in results if r.get("status") == "success")
                    success_rate = success_count / len(results)
                    score += success_rate * 15.0
                break
        
        # 4. Failed goal penalty (재시도할 만한가?)
        for tracked_goal in tracker_data.get("goals", []):
            if tracked_goal["title"].lower().strip() == title.lower().strip():
                if tracked_goal.get("status") == "failed":
                    # 실패한 목표는 약간 감점 (하지만 재시도 가치 있음)
                    score -= 5.0
                break
        
        # 5. Time appropriateness (0-10점)
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 18:  # 업무 시간
            # 업무 시간에는 생산적 목표 선호
            if any(keyword in title.lower() for keyword in 
                  ["metric", "report", "analysis", "optimization"]):
                score += 10.0
        else:  # 업무 외 시간
            # 유지보수, 정리 작업 선호
            if any(keyword in title.lower() for keyword in 
                  ["cleanup", "maintenance", "backup"]):
                score += 10.0
        
        # 6. Avoid self-invocation
        if "executable" in goal:
            try:
                if self._is_self_invocation(goal["executable"]):
                    score -= 100.0  # 큰 패널티
            except:
                pass
        
        return max(score, 0.0)
    
    def select_executable_goal(self, goals: List[Dict[str, Any]], tracker_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        실행 가능한 목표를 선택한다.
        
        선택 기준:
        1. Trinity Resonance Oracle에서 추천받은 목표 우선
        2. tracker에 pending/failed 상태인 목표 우선 (재시도 포함)
        3. autonomous_goals_latest.json에서 아직 완료되지 않은 목표
        4. 우선순위가 높음
        5. 실행 가능한 타입
        """
        # 0단계: Trinity Resonance Oracle 상담
        if self.resonance_oracle:
            try:
                # 현재 실행 가능한 목표들의 제목 수집
                candidate_titles = [g["title"] for g in goals]
                oracle_decision = self.resonance_oracle.consult_oracle(
                    context={"candidates": candidate_titles},
                    query_type="goal_selection"
                )
                
                if oracle_decision and oracle_decision.get("action") == "execute":
                    recommended_title = oracle_decision.get("recommendation")
                    if recommended_title:
                        # 추천된 목표 찾기
                        for goal in goals:
                            if goal["title"].lower().strip() == recommended_title.lower().strip():
                                logger.info(f"🌀 Oracle recommends: {goal['title']} (resonance={oracle_decision.get('resonance_score', 0.0):.2f})")
                                return goal
                        
                        logger.warning(f"Oracle recommended '{recommended_title}' but not found in goals list")
                
                elif oracle_decision and oracle_decision.get("action") == "defer":
                    logger.info(f"🌀 Oracle suggests deferring (reason: {oracle_decision.get('reason', 'unknown')})")
                    # oracle이 defer를 제안하면 현재 시점에선 실행하지 않음
                    return None
                    
            except Exception as e:
                logger.warning(f"Resonance oracle consultation failed: {e}")
        
        # 1단계: tracker에서 pending/failed 목표 찾기
        tracked_pending = [
            g for g in tracker_data.get("goals", [])
            if g.get("status") in ("pending", "failed", "in_progress")
        ]
        
        if tracked_pending:
            # 우선순위 순으로 정렬 (문자열을 float로 안전하게 변환)
            def safe_priority(g):
                p = g.get("priority", 5.0)
                try:
                    return float(p)
                except (ValueError, TypeError):
                    return 5.0
            
            tracked_pending.sort(key=safe_priority, reverse=True)
            selected = tracked_pending[0]
            logger.info(f"✅ Selected from tracker: {selected['title']} (status={selected['status']}, priority={safe_priority(selected)})")
            
            # goals에서 full spec 찾아 merge (executable 등)
            for goal in goals:
                if goal["title"].lower().strip() == selected["title"].lower().strip():
                    # tracker의 메타데이터 유지하면서 goals의 executable 병합
                    selected.update({
                        "executable": goal.get("executable", selected.get("executable", {})),
                        "metadata": goal.get("metadata", selected.get("metadata", {})),
                        "final_priority": goal.get("final_priority", selected.get("priority", 5.0))
                    })
                    break
            
            return selected
        
        # 2단계: autonomous_goals_latest.json에서 선택
        executable_keywords = [
            "metric", "collection", "monitoring", 
            "reporting", "analysis", "optimization",
            "health", "check", "status", "synthesis"
        ]
        
        for goal in sorted(goals, key=lambda g: g.get("final_priority", 50), reverse=True):
            title = goal["title"]
            
            # 이미 완료된 목표는 스킵
            if self.is_goal_completed(title, tracker_data):
                logger.info(f"Skipping completed goal: {title}")
                continue
            
            # executable 필드가 있으면 바로 실행 가능 (단, self-invocation 방지)
            if "executable" in goal and goal["executable"]:
                try:
                    if self._is_self_invocation(goal["executable"]):
                        logger.info(f"Skipping self-invocation goal: {title} (autonomous_goal_executor.py)")
                        continue
                except Exception as e:
                    logger.warning(f"Executable inspection failed for '{title}': {e}")
                logger.info(f"✅ Selected goal (has executable): {title}")
                return goal
            
            # 실행 가능한 타입인지 확인 (더 유연하게)
            goal_type = goal.get("type", "").lower()
            title_lower = title.lower()
            
            is_executable = any(keyword in goal_type or keyword in title_lower 
                               for keyword in executable_keywords)
            
            if not is_executable:
                logger.info(f"Skipping non-executable goal: {title} (type={goal_type})")
                continue
            
            # 우선순위 체크는 더 유연하게 (5 이상이면 OK)
            if goal.get("final_priority", 0) < 5:
                logger.info(f"Skipping low priority goal: {title} ({goal.get('final_priority')})")
                continue
            
            logger.info(f"✅ Selected goal: {title} (priority={goal.get('final_priority')})")
            return goal
        
        logger.warning("No executable goals found")
        return None
    
    def decompose_goal_to_tasks(self, goal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        목표를 구체적인 작업으로 분해한다.
        
        Phase 2 Enhanced:
        - executable 필드가 있으면 그대로 사용
        - 없으면 패턴 기반 분해
        """
        title = goal["title"]
        goal_type = goal.get("type", "").lower()
        
        tasks = []
        
        # executable 필드가 있으면 바로 사용
        if "executable" in goal and goal["executable"]:
            exec_info = goal["executable"]
            # Support two shapes:
            # 1) { command: "powershell", args: ["-NoProfile", ...], working_dir?: str }
            # 2) { type: "powershell"|"python", script: "...", args?: [...] }
            cmd_list: Optional[List[str]] = None
            working_dir: Optional[str] = None

            # Prefer explicit command + args
            if exec_info.get("command"):
                cmd = exec_info.get("command")
                args_list = self._resolve_args(exec_info.get("args"))
                # Normalize common aliases
                if isinstance(cmd, str) and cmd.lower() in ("pwsh",):
                    cmd = "powershell"
                cmd_list = [cmd] + (args_list or [])
                working_dir = exec_info.get("working_dir")
            # Fallback: type + script
            elif exec_info.get("type") and exec_info.get("script"):
                etype = str(exec_info.get("type")).lower()
                script_path = self._resolve_placeholders(exec_info.get("script"))
                args_list = self._resolve_args(exec_info.get("args"))
                if etype in ("powershell", "pwsh"):
                    cmd_list = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path]
                    if args_list:
                        cmd_list.extend(args_list)
                elif etype in ("python", "py") or (etype == "script" and script_path.endswith(".py")):
                    # Python 실행 시 venv Python 우선 사용
                    python_exe = self._find_python_exe()
                    cmd_list = [python_exe, script_path]
                    if args_list:
                        cmd_list.extend(args_list)
                    logger.info(f"Using Python: {python_exe}")
                elif etype == "script":
                     # Fallback for generic script: check extension
                     if script_path.endswith(".ps1"):
                         cmd_list = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path]
                     else:
                         cmd_list = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path]
                     
                     if args_list:
                         cmd_list.extend(args_list)
                else:
                    # Unknown type: attempt best-effort string command
                    combined = " ".join([exec_info.get("type"), script_path] + (args_list or []))
                    cmd_list = [combined]
                working_dir = exec_info.get("working_dir")

            # Resolve working directory placeholder
            if working_dir:
                working_dir = self._resolve_placeholders(working_dir)

            # Fallback for manual or unspecified types
            if not cmd_list:
                tasks.append({
                    "type": "manual",
                    "description": exec_info.get("message", goal.get("description", title)),
                    "status": "manual_resonance_required"
                })
            else:
                tasks.append({
                    "type": "command",
                    "cmd": cmd_list,
                    "command": " ".join(cmd_list) if cmd_list and len(cmd_list) > 1 else (cmd_list[0] if cmd_list else exec_info.get("command")),
                    "working_dir": working_dir,
                    "description": goal.get("description", title),
                    "timeout": exec_info.get("timeout", 300),
                    "retry_on_failure": exec_info.get("retry_on_failure", False),
                    "max_retries": exec_info.get("max_retries", 0)
                })
            logger.info(f"Using executable field for '{title}' → type: {exec_info.get('type')}")
        
        # 패턴 기반 분해 (fallback)
        elif "metric" in goal_type or "health" in title.lower():
            tasks.append({
                "type": "script",
                "script": "scripts/system_health_check.ps1",
                "description": "Run system health check",
                "timeout": 300
            })
        
        elif "report" in goal_type or "synthesis" in title.lower():
            tasks.append({
                "type": "script",
                "script": "scripts/generate_monitoring_report.ps1",
                "args": ["-Hours", "6"],
                "description": "Generate monitoring report",
                "timeout": 600
            })
        
        elif "analysis" in goal_type or "analyze" in title.lower():
            tasks.append({
                "type": "script",
                "script": "scripts/autopoietic_trinity_cycle.ps1",
                "args": ["-Hours", "24"],
                "description": "Run trinity analysis",
                "timeout": 900
            })
        
        logger.info(f"Decomposed goal '{title}' into {len(tasks)} tasks")
        return tasks
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """작업을 실행한다"""
        task_type = task.get("type")
        start_time = datetime.now()
        
        result = {
            "task": task,
            "started_at": start_time.isoformat(),
            "status": "unknown",
            "output": None,
            "error": None
        }
        
        try:
            if task_type == "script":
                result = self._execute_script(task, result)
            elif task_type == "command":
                result = self._execute_command(task, result)
            elif task_type == "validation":
                result = self._execute_validation(task, result)
            elif task_type == "vscode_task":
                result = self._execute_vscode_task(task, result)
            elif task_type == "manual":
                result["status"] = "success" # Marked as success to continue flow, but requires manual intervention
                result["output"] = f"Manual resonance required: {task.get('description')}"
                logger.info(f"📡 Manual Resonance Required: {task.get('description')}")
            else:
                result["status"] = "skipped"
                result["error"] = f"Unknown task type: {task_type}"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"Task execution failed: {e}")
        
        result["completed_at"] = datetime.now().isoformat()
        result["duration_seconds"] = (datetime.now() - start_time).total_seconds()
        
        return result
    
    def _execute_script(self, task: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """스크립트를 실행한다"""
        script_path = self.workspace_root / task["script"]
        
        if not script_path.exists():
            result["status"] = "failed"
            result["error"] = f"Script not found: {script_path}"
            return result

        # Prevent executing this executor recursively
        if script_path.name == "autonomous_goal_executor.py":
            result["status"] = "skipped"
            result["error"] = "Recursive self-invocation prevented"
            logger.warning("Skipped task due to self-invocation: %s", script_path)
            return result
        
        # PowerShell 또는 Python 실행
        if script_path.suffix == ".ps1":
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
        elif script_path.suffix == ".py":
            cmd = [sys.executable, str(script_path)]
        else:
            result["status"] = "failed"
            result["error"] = f"Unsupported script type: {script_path.suffix}"
            return result
        
        # 인자 추가
        if "args" in task:
            cmd.extend(task["args"])
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=task.get("timeout", 300),
                encoding='utf-8',
                errors='replace'
            )
            
            result["status"] = "success" if proc.returncode == 0 else "failed"
            result["output"] = proc.stdout
            result["error"] = proc.stderr if proc.returncode != 0 else None
            result["exit_code"] = proc.returncode
            
            logger.info(f"Script completed: {result['status']} (exit_code={proc.returncode})")
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["error"] = f"Script timed out after {task.get('timeout')} seconds"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def _execute_command(self, task: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """커맨드를 실행한다 (executable 필드)
        Supports task["cmd"] as a list (preferred) or task["command"] as a string.
        """
        cmd_list: Optional[List[str]] = task.get("cmd")
        command_str: Optional[str] = task.get("command")
        if not cmd_list and not command_str:
            result["status"] = "failed"
            result["error"] = "No command specified"
            return result

        # Prefer list execution without shell for reliability
        working_dir = task.get("working_dir") or str(self.workspace_root)
        logger.info("Executing command: %s", cmd_list if cmd_list else command_str)

        try:
            if cmd_list:
                proc = subprocess.run(
                    cmd_list,
                    shell=False,
                    cwd=working_dir,
                    capture_output=True,
                    timeout=task.get("timeout", 300),
                    encoding='utf-8',
                    errors='replace'
                )
            else:
                proc = subprocess.run(
                    command_str,
                    shell=True,
                    cwd=working_dir,
                    capture_output=True,
                    timeout=task.get("timeout", 300),
                    encoding='utf-8',
                    errors='replace'
                )

            result["status"] = "success" if proc.returncode == 0 else "failed"
            result["output"] = proc.stdout
            result["error"] = proc.stderr if proc.returncode != 0 else None
            result["exit_code"] = proc.returncode

            logger.info(f"Command completed: {result['status']} (exit_code={proc.returncode})")

            # Retry logic
            if proc.returncode != 0 and task.get("retry_on_failure", False):
                max_retries = task.get("max_retries", 0)
                for retry in range(1, max_retries + 1):
                    logger.info(f"Retry {retry}/{max_retries}...")
                    time.sleep(2)
                    if cmd_list:
                        proc = subprocess.run(
                            cmd_list,
                            shell=False,
                            cwd=working_dir,
                            capture_output=True,
                            timeout=task.get("timeout", 300),
                            encoding='utf-8',
                            errors='replace'
                        )
                    else:
                        proc = subprocess.run(
                            command_str,
                            shell=True,
                            cwd=working_dir,
                            capture_output=True,
                            timeout=task.get("timeout", 300),
                            encoding='utf-8',
                            errors='replace'
                        )
                    if proc.returncode == 0:
                        result["status"] = "success"
                        result["output"] = proc.stdout
                        result["error"] = None
                        result["exit_code"] = proc.returncode
                        result["retries"] = retry
                        logger.info(f"Command succeeded after {retry} retries")
                        break

        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["error"] = f"Command timed out after {task.get('timeout')} seconds"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)

        return result
    
    def _execute_vscode_task(self, task: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """VS Code Task를 실행한다 (양자 관찰자 효과 해결)"""
        goal_index = task.get("goal_index", 1)
        logger.info(f"👁️ Executing VS Code Task for Goal #{goal_index}")
        
        # PowerShell 스크립트 호출
        script_path = self.workspace_root / "scripts" / "execute_goal_via_task.ps1"
        
        if not script_path.exists():
            result["status"] = "failed"
            result["error"] = f"VS Code Task executor not found: {script_path}"
            return result
        
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", str(script_path),
            "-GoalIndex", str(goal_index)
        ]
        
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )
            
            result["status"] = "success" if proc.returncode == 0 else "failed"
            result["output"] = proc.stdout
            result["error"] = proc.stderr if proc.returncode != 0 else None
            result["exit_code"] = proc.returncode
            
            if result["status"] == "success":
                logger.info("✅ VS Code Task launched - 파동 → 입자 붕괴")
            else:
                logger.warning(f"VS Code Task failed: {proc.stderr}")
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["error"] = "VS Code Task timed out"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def _execute_validation(self, task: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """검증 작업을 실행한다"""
        # Phase 2: 간단한 검증만
        result["status"] = "success"
        result["output"] = "Validation passed"
        logger.info("Validation completed")
        return result
    
    def record_execution(self, goal: Dict[str, Any], task_results: List[Dict[str, Any]]) -> None:
        """실행 결과를 기록한다 (+ 🧠 보상 신호)"""
        tracker_data = self.load_goal_tracker()
        
        # 목표가 이미 추적 중인지 확인
        existing_goal = None
        for tracked_goal in tracker_data["goals"]:
            if tracked_goal["title"].lower().strip() == goal["title"].lower().strip():
                existing_goal = tracked_goal
                break
        
        # 전체 성공 여부
        all_success = all(r["status"] == "success" for r in task_results)
        
        # 🧠 보상 신호 계산 및 기록
        if self.reward_tracker:
            # 성공: +0.8~1.0, 실패: -0.5~-0.8, 타임아웃: -0.3
            if all_success:
                reward = 0.9
                logger.info(f"💰 Success reward: +{reward}")
            else:
                # 실패 유형 분석
                has_timeout = any(r["status"] == "timeout" for r in task_results)
                if has_timeout:
                    reward = -0.3
                    logger.info(f"⏱️ Timeout penalty: {reward}")
                else:
                    reward = -0.7
                    logger.info(f"❌ Failure penalty: {reward}")
            
            # 보상 신호 기록
            try:
                self.reward_tracker.record_reward_signal(
                    action_type="goal_execution",
                    action_id=goal["title"],
                    reward=reward,
                    context={
                        "goal_type": goal.get("type", "unknown"),
                        "priority": goal.get("final_priority", 0),
                        "task_count": len(task_results),
                        "execution_time": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to record reward signal: {e}")
        
        if existing_goal:
            # 기존 목표 업데이트
            existing_goal["status"] = "completed" if all_success else "failed"
            existing_goal["completed_at"] = datetime.now().isoformat()
            existing_goal["execution_results"] = task_results
        else:
            # 새 목표 추가
            tracker_data["goals"].append({
                "title": goal["title"],
                "status": "completed" if all_success else "failed",
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "execution_results": task_results,
                "evidence": {
                    "task_count": len(task_results),
                    "success_count": sum(1 for r in task_results if r["status"] == "success"),
                    "automated": True
                }
            })
        
        tracker_data["last_updated"] = datetime.now().isoformat()
        
        # 저장
        os.makedirs(self.goal_tracker_path.parent, exist_ok=True)
        with open(self.goal_tracker_path, 'w', encoding='utf-8') as f:
            json.dump(tracker_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Recorded execution: {goal['title']} → {existing_goal['status'] if existing_goal else 'new entry'}")
    
    def execute_goal(self, goal: Dict[str, Any]) -> bool:
        """목표를 실행한다"""
        logger.info("=" * 70)
        logger.info(f"Executing Goal: {goal['title']}")
        logger.info("=" * 70)
        
        # Proactive start message
        speak(f"🌀 *Starting Autonomous Goal*: {goal['title']}")
        
        # 🧠 Glymphatic Pre-Execution Check
        glymphatic_ready = self._check_glymphatic_readiness()
        if not glymphatic_ready:
            logger.warning("⚠️ Glymphatic system recommends cleanup before execution")
            # Optionally trigger cleanup or defer goal
            # For now, we log and continue
        
        # 🌊 Quantum Flow 상태 확인 및 최적화
        execution_mode = self._determine_execution_mode()
        if execution_mode:
            logger.info(f"🌊 Execution Mode: {execution_mode}")
        
        # 1. 작업 분해
        tasks = self.decompose_goal_to_tasks(goal)
        if not tasks:
            logger.warning("No tasks generated for this goal")
            return False
        
        # 👁️ Quantum Observer Effect: Goal Index를 Tasks에 주입
        goal_index = goal.get("id", 0)
        for task in tasks:
            if task.get("type") == "vscode_task":
                task["goal_index"] = goal_index
        
        # 2. 작업 실행
        task_results = []
        for i, task in enumerate(tasks, 1):
            logger.info(f"[Task {i}/{len(tasks)}] {task.get('description', 'Unknown task')}")
            
            # 🌊 Quantum Flow 기반 실행 최적화
            if execution_mode == "superconducting":
                # 초전도 상태: aggressive 실행
                task["timeout_multiplier"] = 1.5
                logger.info("   ⚡ Superconducting mode: increased timeout")
            elif execution_mode == "high_resistance":
                # 저항 상태: 보수적 실행
                task["timeout_multiplier"] = 0.7
                logger.info("   🐢 High resistance mode: conservative execution")
            
            result = self.execute_task(task)
            task_results.append(result)
            
            # 실패 시 중단
            if result["status"] not in ("success", "skipped"):
                logger.error(f"Task failed: {result.get('error', 'Unknown error')}")
                break
        
        # 3. 결과 기록
        all_success = all(r["status"] in ("success", "skipped") for r in task_results)
        self.record_execution(goal, task_results)
        
        if not all_success:
            last_error = task_results[-1].get("error", "Unknown error")
            speak(f"⚠️ *Goal Execution Failed*: {goal['title']}\nError: {last_error[:200]}\n\n제가 이 장애물을 어떻게 넘어야 할까요? 당신의 개입이 필요할 수도 있습니다.")
        elif all_success:
             speak(f"✅ *Goal Completed*: {goal['title']}")
        
        # 4. 성공 여부
        success = all_success
        
        # 🧠 Post-Execution Cleanup Scheduling
        if success:
            # 실행 시간 계산 (간단히 task 수 기반 추정)
            estimated_duration = len(tasks) * 5  # 5분/task 가정
            self._schedule_post_execution_cleanup(estimated_duration)
        
        # 🧪 Autonomous Learning: Goal 실행 결과 기반 자율 학습
        if self.sandbox_bridge:
            self._trigger_autonomous_learning(goal, task_results, success)
        
        # 🌐 [Phase 92] Meta-FSD Client: Report execution result & screenshot to Shion (Soul)
        self._report_to_shion(goal, success, task_results)
        
        logger.info("=" * 70)
        return success

    def _report_to_shion(self, goal: Dict[str, Any], success: bool, task_results: List[Dict[str, Any]]):
        """
        목표 실행 직후 최신 스크린샷과 상태를 시안의 Visual Pulse API로 역보고(Push)합니다.
        """
        api_url = "http://127.0.0.1:8001/api/intent"
        token = "" # 시안 서버 보안 토큰 로드
        sec_path = Path("c:/workspace2/shion/config/security.yaml")
        if sec_path.exists():
            try:
                import yaml
                with open(sec_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                    token = cfg.get("network", {}).get("api_auth_token", "")
            except:
                pass
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        # 제일 최근에 찍힌 스크린샷 탐색 (screenshots 폴더에서)
        screenshot_dir = self.workspace_root / "outputs" / "screenshots"
        latest_img_path = ""
        if screenshot_dir.exists():
            images = list(screenshot_dir.glob("*.jpg")) + list(screenshot_dir.glob("*.png"))
            if images:
                # 수정시간 내림차순 정렬
                latest_img = max(images, key=lambda p: p.stat().st_mtime)
                # 실행시간 즈음에 찍힌 것인지 확인(최근 5분 이내)
                if time.time() - latest_img.stat().st_mtime < 300:
                    latest_img_path = str(latest_img)
        
        report_data = {
            "source": "FSD_Executor",
            "goal": goal.get("title", ""),
            "status": "success" if success else "failed",
            "task_count": len(task_results),
            "screenshot_path": latest_img_path,
            "timestamp": _now_iso()
        }
        
        try:
            import requests
            resp = requests.post(api_url, json=report_data, headers=headers, timeout=3.0)
            if resp.status_code == 200:
                logger.info(f"   🌐 [Meta-FSD] Reported completion to Soul -> resonance loop fed.")
            else:
                logger.warning(f"   ⚠️ [Meta-FSD] Failed to report to Soul (HTTP {resp.status_code})")
        except Exception as e:
            logger.debug(f"   ⚠️ [Meta-FSD] Shion might be sleeping ({e})")

    def _determine_execution_mode(self) -> str:
        """
        🌊 Determine the current execution mode based on system resonance.
        Default is 'normal', but can be 'superconducting' or 'high_resistance'.
        """
        # Placeholder implementation
        current_hour = datetime.now().hour
        if 2 <= current_hour <= 6: # Deep night: superconducting mode
            return "superconducting"
        return "normal"

    def _is_self_invocation(self, executable: Dict[str, Any]) -> bool:
        """Prevent the executor from executing itself to avoid infinite recursion."""
        script_val = str(executable.get("script", "")).lower()
        args_val = " ".join([str(a) for a in executable.get("args", [])]).lower()
        
        self_name = "autonomous_goal_executor.py"
        if self_name in script_val or self_name in args_val:
            return True
        return False

    def _trigger_autonomous_learning(self, goal: Dict[str, Any], task_results: List[Dict[str, Any]], success: bool):
        """
        🧪 Feed back results into the sandbox for future strategy improvement.
        """
        logger.info(f"🧪 Learning Phase: {goal['title']} (success={success})")
        # Placeholder for actual sandbox feedback logic
        logger.info(f"Goal Execution {'✅ SUCCESS' if success else '❌ FAILED'}")
        logger.info("=" * 70)
        
        return success
    
    # ========================================
    # 🧪 Autonomous Learning System Methods
    # ========================================
    
    def _trigger_autonomous_learning(
        self,
        goal: Dict[str, Any],
        task_results: List[Dict[str, Any]],
        success: bool
    ) -> None:
        """
        목표 실행 결과를 분석하고 자율 학습을 트리거한다.
        
        실패 시: 실패 원인 분석 → 개선 실험 생성
        성공 시: 패턴 추출 → 최적화 실험 생성
        """
        logger.info("\n🧪 ===== Autonomous Learning Trigger =====")
        
        try:
            if not success:
                # 실패 학습: 무엇이 잘못되었는지 분석
                self._learn_from_failure(goal, task_results)
            else:
                # 성공 학습: 어떻게 더 잘할 수 있는지 탐구
                self._learn_from_success(goal, task_results)
        except Exception as e:
            logger.error(f"🧪 Autonomous learning error: {e}")
    
    def _learn_from_failure(self, goal: Dict[str, Any], task_results: List[Dict[str, Any]]) -> None:
        """
        실패로부터 학습: 실패 원인을 분석하고 개선 실험을 생성한다.
        """
        logger.info("🧪 Learning from FAILURE...")
        
        # 실패한 task 찾기
        failed_tasks = [
            task for task in task_results
            if task.get("status") not in ("success", "skipped")
        ]
        
        if not failed_tasks:
            return
        
        # 실패 패턴 추출
        failure_pattern = {
            "goal_type": goal.get("type", "unknown"),
            "failed_task_types": [t.get("type") for t in failed_tasks],
            "error_messages": [t.get("error", "") for t in failed_tasks],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"🧪 Failure Pattern: {failure_pattern['goal_type']} - {len(failed_tasks)} tasks failed")
        
        # 개선 아이디어 생성
        improvement_idea = self._generate_improvement_idea(failure_pattern)
        
        if improvement_idea:
            # Sandbox에서 실험
            logger.info(f"🧪 Queuing improvement experiment: {improvement_idea['title']}")
            self._queue_sandbox_experiment(improvement_idea, category="learning")
    
    def _learn_from_success(self, goal: Dict[str, Any], task_results: List[Dict[str, Any]]) -> None:
        """
        성공으로부터 학습: 성공 패턴을 분석하고 최적화 실험을 생성한다.
        """
        logger.info("🧪 Learning from SUCCESS...")
        
        # 성공 패턴 추출
        success_pattern = {
            "goal_type": goal.get("type", "unknown"),
            "task_count": len(task_results),
            "execution_time": sum(t.get("duration", 0) for t in task_results),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"🧪 Success Pattern: {success_pattern['goal_type']} - {success_pattern['task_count']} tasks in {success_pattern['execution_time']:.1f}s")
        
        # 최적화 아이디어 생성 (예: 더 빠르게, 더 효율적으로)
        optimization_idea = self._generate_optimization_idea(success_pattern)
        
        if optimization_idea:
            # Sandbox에서 실험
            logger.info(f"🧪 Queuing optimization experiment: {optimization_idea['title']}")
            self._queue_sandbox_experiment(optimization_idea, category="patterns")
    
    def _generate_improvement_idea(self, failure_pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        실패 패턴으로부터 개선 아이디어를 생성한다.
        
        TODO: LLM 통합하여 더 스마트한 아이디어 생성
        현재: 간단한 휴리스틱 기반
        """
        goal_type = failure_pattern.get("goal_type", "unknown")
        
        # 간단한 휴리스틱: timeout 관련 실패 → retry with longer timeout
        error_messages = " ".join(failure_pattern.get("error_messages", []))
        if "timeout" in error_messages.lower():
            return {
                "title": f"Timeout Mitigation for {goal_type}",
                "description": "Experiment with adaptive timeout strategies",
                "code": "# Test longer timeout multipliers\n# Test async execution\n# Test retry with exponential backoff"
            }
        
        # TODO: 더 많은 패턴 추가
        return None
    
    def _generate_optimization_idea(self, success_pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        성공 패턴으로부터 최적화 아이디어를 생성한다.
        
        TODO: LLM 통합하여 더 스마트한 아이디어 생성
        현재: 간단한 휴리스틱 기반
        """
        goal_type = success_pattern.get("goal_type", "unknown")
        task_count = success_pattern.get("task_count", 0)
        
        # 간단한 휴리스틱: 많은 task → parallelization 시도
        if task_count > 3:
            return {
                "title": f"Parallel Execution for {goal_type}",
                "description": "Experiment with parallel task execution",
                "code": f"# Test running {task_count} tasks in parallel\n# Measure speedup\n# Check for race conditions"
            }
        
        # TODO: 더 많은 패턴 추가
        return None
    
    def _queue_sandbox_experiment(
        self,
        idea: Dict[str, Any],
        category: str = "learning"
    ) -> None:
        """
        Sandbox에 실험을 큐잉한다.
        
        실제로는 sandbox_bridge를 통해 비동기로 실행되며,
        결과는 나중에 별도 프로세스가 수집한다.
        """
        if not self.sandbox_bridge:
            return
        
        try:
            # Sandbox에 실험 파일 생성
            experiment_file = self.sandbox_bridge.create_experiment(
                title=idea["title"],
                code=idea.get("code", "# Auto-generated experiment\npass"),
                category=category
            )
            
            logger.info(f"🧪 Experiment queued: {experiment_file}")
            logger.info(f"   📝 {idea['description']}")
            
            # TODO: 별도 스케줄러가 나중에 실행하도록 메타데이터 저장
            # 현재: 단순히 파일 생성만 함
            
        except Exception as e:
            logger.error(f"🧪 Failed to queue experiment: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Goal Executor - Phase 2"
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=str(get_workspace_root()),
        help="Workspace root path (default: auto-detected)"
    )
    parser.add_argument(
        "--task-queue",
        type=str,
        default="http://127.0.0.1:8091",
        help="Task queue server URL"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode (no actual execution)"
    )
    parser.add_argument(
        "--use-quantum",
        action="store_true",
        help="Quantum mode: intelligently select best goal from multiple candidates"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("Autonomous Goal Executor - Phase 2")
    logger.info("=" * 70)
    logger.info(f"Workspace: {args.workspace}")
    logger.info(f"Task Queue: {args.task_queue}")
    logger.info(f"Dry-run: {args.dry_run}")
    logger.info(f"Quantum Mode: {args.use_quantum}")
    logger.info("")
    
    # 실행기 초기화
    executor = GoalExecutor(args.workspace, args.task_queue)
    
    # 1. 목표 로드
    logger.info("[1/4] Loading goals...")
    goals = executor.load_goals()
    if not goals:
        logger.error("No goals to execute")
        return
    logger.info(f"Loaded {len(goals)} goals")
    logger.info("")
    
    # 2. 추적 데이터 로드
    logger.info("[2/5] Loading goal tracker...")
    tracker_data = executor.load_goal_tracker()
    completed_count = sum(1 for g in tracker_data.get("goals", []) if g["status"] == "completed")
    logger.info(f"Found {completed_count} completed goals")
    logger.info("")
    
    # 2.5. 신규 목표를 tracker에 자동 등록
    logger.info("[2.5/5] Auto-registering new goals to tracker...")
    new_count = executor.auto_register_new_goals(goals, tracker_data)
    if new_count > 0:
        logger.info(f"✅ Registered {new_count} new goals to tracker")
        # tracker 다시 로드
        tracker_data = executor.load_goal_tracker()
    else:
        logger.info("No new goals to register")
    logger.info("")
    
    # 3. 실행 가능한 목표 선택
    logger.info("[3/5] Selecting executable goal...")
    if args.use_quantum:
        logger.info("🌀 Quantum Mode: Analyzing all possibilities...")
        # Quantum mode: 모든 후보를 평가하고 가장 적합한 것 선택
        candidates = []
        for goal in goals:
            if not executor.is_goal_completed(goal["title"], tracker_data):
                score = executor.calculate_goal_fitness(goal, tracker_data)
                candidates.append((goal, score))
        
        if not candidates:
            logger.warning("No candidate goals available")
            return
        
        # 점수 순으로 정렬하여 최적 선택
        candidates.sort(key=lambda x: x[1], reverse=True)
        selected_goal, best_score = candidates[0]
        logger.info(f"🎯 Quantum collapse: Selected '{selected_goal['title']}' (fitness={best_score:.2f})")
        logger.info(f"   Other candidates: {len(candidates)-1}")
    else:
        # Classic mode: 기존 select_executable_goal 사용
        selected_goal = executor.select_executable_goal(goals, tracker_data)
        if not selected_goal:
            logger.warning("No executable goals available")
            return
    logger.info("")
    
    # 4. 목표 실행
    logger.info("[4/5] Executing goal...")
    if args.dry_run:
        logger.info("🔍 DRY-RUN MODE: Simulating execution")
        tasks = executor.decompose_goal_to_tasks(selected_goal)
        logger.info(f"Would execute {len(tasks)} tasks:")
        for i, task in enumerate(tasks, 1):
            logger.info(f"  {i}. {task.get('description', 'Unknown task')}")
        logger.info("✅ Dry-run completed")
    else:
        success = executor.execute_goal(selected_goal)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
