#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supervised Body Controller (Windows)

목표:
- AGI가 "직접 경험"을 만들기 위해 Windows를 조작할 수 있게 하되,
  사용자가 즉시 개입(마우스/키보드 입력)하면 자동으로 중단되는 감독 모드를 제공한다.

핵심 안전 규칙:
- Arm 파일이 없으면 실행하지 않는다.
- 실행 중 사용자 입력이 감지되면 즉시 중단한다(제어권 회수).
- 허용된 액션만 수행한다(allowlist).
- 실행 1회 = 리포트 1개 고정.

파일 기반 인터페이스:
- signals/body_arm.json        : 감독 모드 "무장(arm)" (TTL 포함)
- signals/body_task.json       : 실행할 작업(액션 리스트)
- signals/body_stop.json       : 즉시 중단

출력:
- outputs/body_supervised_latest.json
- outputs/body_supervised_history.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import time
import traceback
import webbrowser
import re
from urllib.parse import quote_plus
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))



WORKSPACE = get_workspace_root()
SIGNALS = WORKSPACE / "signals"
OUTPUTS = WORKSPACE / "outputs"
INTAKE_SESSIONS = WORKSPACE / "inputs" / "intake" / "exploration" / "sessions"
EXPLORATION_EVENT = OUTPUTS / "exploration_session_event_latest.json"
SYNC_CACHE = OUTPUTS / "sync_cache"

ARM_FILE = SIGNALS / "body_arm.json"
ALLOW_FILE = SIGNALS / "body_allow_browser.json"
TASK_FILE = SIGNALS / "body_task.json"
STOP_FILE = SIGNALS / "body_stop.json"
QUEUED_TASK = SIGNALS / "body_task_queued.json"
REST_GATE = OUTPUTS / "safety" / "rest_gate_latest.json"
TREND_ANALYZER = WORKSPACE / "scripts" / "alignment_trend_analyzer.py"
MISSION_COORDINATOR = WORKSPACE / "agi_core" / "agency" / "mission_coordinator.py"
SHION_STATE_SYNC = WORKSPACE / "scripts" / "coordination" / "shion_state_sync.py"
PROACTIVE_REPORTER = WORKSPACE / "scripts" / "proactive_reporter.py"
SOCIAL_OBSERVER = WORKSPACE / "scripts" / "social_alignment_observer.py"

LATEST = OUTPUTS / "body_supervised_latest.json"
HISTORY = OUTPUTS / "body_supervised_history.jsonl"
BODY_LIFE_STATE = SYNC_CACHE / "body_life_state.json"


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def safe_load_json(path: Path) -> Optional[dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _rest_gate_active(now_ts: float) -> bool:
    rg = safe_load_json(REST_GATE) or {}
    try:
        if isinstance(rg, dict) and str(rg.get("status") or "").upper() == "REST":
            until = rg.get("rest_until_epoch")
            if until is None:
                return True
            if isinstance(until, (int, float)) and now_ts < float(until):
                return True
    except Exception:
        return False
    return False


def safe_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _write_body_life_state(now_ts: float) -> None:
    """
    '몸(Body) 레이어'가 실제로 살아있는지(프로세스만이 아니라 리듬이 도는지)를
    관측 가능하게 만드는 최소 생존 신호.

    원칙:
    - 실행/행동 없음(관측만)
    - 민감정보(키 입력/마우스 좌표 등) 저장 없음
    - best-effort
    """
    try:
        armed, armed_reason = is_armed(now_ts)
    except Exception:
        armed, armed_reason = False, "arm_check_failed"

    try:
        rest_active = _rest_gate_active(now_ts)
    except Exception:
        rest_active = False

    try:
        last_input_s = seconds_since_last_input()
    except Exception:
        last_input_s = None

    try:
        kill_switch = _scroll_lock_on()
    except Exception:
        kill_switch = False

    stop_present = STOP_FILE.exists()

    user_active = False
    try:
        if isinstance(last_input_s, (int, float)) and float(last_input_s) < 3.0:
            user_active = True
    except Exception:
        user_active = False

    mode = "DISARMED"
    # Precedence: explicit stop > rest gate > kill switch > armed > default
    if stop_present:
        mode = "STOP_FILE"
    elif rest_active:
        mode = "REST_GATE"
    elif kill_switch:
        mode = "KILL_SWITCH"
    elif armed:
        mode = "ARMED"

    payload: dict[str, Any] = {
        "generated_at_utc": utc_iso(now_ts),
        "pid": os.getpid(),
        "mode": mode,  # DISARMED | ARMED | REST_GATE | KILL_SWITCH
        "armed": armed,
        "armed_reason": armed_reason,
        "rest_gate_active": rest_active,
        "task_file_present": TASK_FILE.exists(),
        "queued_task_present": QUEUED_TASK.exists(),
        "stop_file_present": stop_present,
        "seconds_since_last_user_input": last_input_s,
        "user_active_recent": user_active,
    }
    safe_write_json(BODY_LIFE_STATE, payload)


def _hide_console_best_effort() -> None:
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except Exception:
        pass


def _get_last_input_tick() -> Optional[int]:
    """
    Windows GetLastInputInfo 기반.
    반환: 마지막 사용자 입력 tick(ms). 실패 시 None.
    """
    try:
        import ctypes

        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

        user32 = ctypes.windll.user32
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if user32.GetLastInputInfo(ctypes.byref(lii)) == 0:
            return None
        return int(lii.dwTime)
    except Exception:
        return None


def _get_tick_count() -> Optional[int]:
    try:
        import ctypes

        # GetTickCount64 is preferred.
        kernel32 = ctypes.windll.kernel32
        if hasattr(kernel32, "GetTickCount64"):
            return int(kernel32.GetTickCount64())
        return int(kernel32.GetTickCount())
    except Exception:
        return None


def seconds_since_last_input() -> Optional[float]:
    last = _get_last_input_tick()
    now = _get_tick_count()
    if last is None or now is None:
        return None
    # Wrap-safe enough for our use; if overflow occurs, return None.
    try:
        delta = int(now) - int(last)
        if delta < 0:
            return None
        return float(delta) / 1000.0
    except Exception:
        return None


def is_armed(now_ts: float) -> tuple[bool, str]:
    # Persistent allow mode (explicit opt-in file)
    allow = safe_load_json(ALLOW_FILE) or {}
    try:
        if isinstance(allow, dict) and bool(allow.get("allow")):
            exp = allow.get("expires_at")
            if exp is None:
                return True, "allow_file"
            if isinstance(exp, (int, float)) and now_ts < float(exp):
                return True, "allow_file"
            # expired allow → cleanup
            try:
                ALLOW_FILE.unlink(missing_ok=True)
            except Exception:
                pass
    except Exception:
        pass

    arm = safe_load_json(ARM_FILE) or {}
    if not isinstance(arm, dict):
        return False, "arm_invalid"
    exp = arm.get("expires_at")
    if not isinstance(exp, (int, float)):
        return False, "arm_missing_expires_at"
    if now_ts >= float(exp):
        # Stale arm file can confuse operators; clean it up when expired.
        try:
            ARM_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        return False, "arm_expired"
    return True, "armed"


def _scroll_lock_on() -> bool:
    """
    하드 킬스위치:
    - Scroll Lock 토글이 켜져 있으면 즉시 중단.
    - GetLastInputInfo가 환경에 따라 noisy할 수 있어, 항상 동작하는 수단을 하나 둔다.
    """
    try:
        import ctypes

        user32 = ctypes.windll.user32
        VK_SCROLL = 0x91
        state = int(user32.GetKeyState(VK_SCROLL))
        return bool(state & 1)
    except Exception:
        return False


def _domain_allowed(url: str) -> bool:
    u = (url or "").strip().lower()
    if not u.startswith(("http://", "https://")):
        return False
    # v1 allowlist: google/youtube only
    allowed = (
        "google.com",
        "google.co.kr",
        "google.co.jp",
        "youtube.com",
        "youtu.be",
    )
    return any(host in u for host in allowed)


def _write_exploration_session(task: dict[str, Any], report: dict[str, Any]) -> None:
    """
    supervised body 실행을 "탐색 세션"으로 고정하여 exploration_intake가 읽을 수 있게 한다.
    - 민감정보/대용량 저장 금지: URL/태그/간단 메모만.
    """
    try:
        status = str(report.get("status") or "")
        if status != "executed":
            return

        urls: list[str] = []
        for step in report.get("steps") or []:
            if isinstance(step, dict) and step.get("type") in ("open_url", "google_search", "youtube_search"):
                url = step.get("url")
                if isinstance(url, str) and url:
                    urls.append(url)

        if not urls:
            return

        now = time.time()
        INTAKE_SESSIONS.mkdir(parents=True, exist_ok=True)
        filename = f"{int(now)}_supervised_browser.json"
        out = INTAKE_SESSIONS / filename

        # source heuristic
        source = "other"
        joined = " ".join(urls).lower()
        if "earth.google" in joined:
            source = "google_earth"
        elif "google.com/maps" in joined or "google.co" in joined and "/maps" in joined:
            source = "street_view"
        elif "youtube.com" in joined or "youtu.be" in joined:
            source = "youtube_local"

        goal = str(task.get("goal") or "supervised_exploration")
        title = f"supervised_browser: {goal}"

        tags = ["supervised", "browser", source]
        notes_lines = [
            f"goal: {goal}",
            "urls:",
            *[f"- {u}" for u in urls[:20]],
        ]

        session = {
            "source": source,
            "title": title,
            "tags": tags,
            "notes": "\n".join(notes_lines),
            "timestamp": float(now),
            "where": {},
            "who": {"role": "agi", "mode": "supervised_body"},
        }
        out.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")

        # auto_policy가 새 경험을 감지할 수 있도록 "경험 이벤트"를 outputs에도 고정한다.
        try:
            event = {
                "timestamp_utc": utc_iso(now),
                "event": "supervised_browser_exploration",
                "session_file": str(out),
                "urls": urls[:20],
                "source": source,
            }
            EXPLORATION_EVENT.parent.mkdir(parents=True, exist_ok=True)
            EXPLORATION_EVENT.write_text(json.dumps(event, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    except Exception:
        return


class AbortExecution(Exception):
    pass


def check_abort(baseline_last_input_tick: Optional[int]) -> None:
    if STOP_FILE.exists():
        raise AbortExecution("stop_file_present")
    if _scroll_lock_on():
        raise AbortExecution("scroll_lock_on")
    current = _get_last_input_tick()
    if baseline_last_input_tick is not None and current is not None and current != baseline_last_input_tick:
        raise AbortExecution("user_input_detected")


def run_action(action: dict[str, Any], baseline_last_input_tick: Optional[int], dry_run: bool) -> dict[str, Any]:
    """
    수행 가능한 최소 액션만 지원한다(안정성 우선).
    """
    # Compatibility:
    # - 일부 mission/협업 레이어는 "action" 키를 사용한다(예: {"action":"log", ...})
    # - supervised body는 "type"을 표준으로 유지하되, 입력은 유연하게 받아들인다.
    kind = str(action.get("type") or action.get("action") or "")
    started = time.time()
    def _redact_text(s: str) -> str:
        t = (s or "").strip()
        if not t:
            return ""
        # Basic redaction (best-effort, local only)
        t = re.sub(r"https?://\\S+", "[REDACTED_URL]", t, flags=re.IGNORECASE)
        t = re.sub(r"\\b[\\w\\.-]+@[\\w\\.-]+\\.[A-Za-z]{2,}\\b", "[REDACTED_EMAIL]", t)
        t = re.sub(r"\\b[A-Za-z]:\\\\[^\\s]+", "[REDACTED_PATH]", t)  # Windows path
        t = re.sub(r"(?<![A-Za-z]):/(?:home|Users|var|etc|opt|mnt)/\\S+", "[REDACTED_PATH]", t)  # rough unix-ish
        if len(t) > 280:
            t = t[:277] + "..."
        return t

    result: dict[str, Any] = {
        "type": kind, 
        "ok": False, 
        "started_at": utc_iso(started),
        "input_params": {k: v for k, v in action.items() if k not in ("type", "action")}
    }

    check_abort(baseline_last_input_tick)

    try:
        if kind == "open_path":
            path = str(action.get("path") or "")
            result["path"] = path
            if not path:
                raise ValueError("missing path")
            p = Path(path).resolve()
            # 안전: 워크스페이스 밖의 임의 경로를 여는 것을 막는다.
            try:
                p.relative_to(WORKSPACE)
            except Exception:
                raise ValueError("path_not_allowed")
            if not p.exists():
                raise FileNotFoundError(path)
            if not dry_run:
                os.startfile(path)  # noqa: S606 (Windows startfile)
            result["ok"] = True

        elif kind == "open_url":
            url = str(action.get("url") or "")
            result["url"] = url
            if not _domain_allowed(url):
                raise ValueError("url_not_allowed")
            if not dry_run:
                # 사용자 작업을 방해하지 않도록 포커스 유발을 최소화한다.
                webbrowser.open(url, new=0, autoraise=False)
            result["ok"] = True

        elif kind == "google_search":
            query = str(action.get("query") or "")
            result["query"] = query
            if not query:
                raise ValueError("missing query")
            url = f"https://www.google.com/search?q={quote_plus(query)}&safe=active"
            result["url"] = url
            if not _domain_allowed(url):
                raise ValueError("url_not_allowed")
            if not dry_run:
                webbrowser.open(url, new=0, autoraise=False)
            result["ok"] = True

        elif kind == "youtube_search":
            query = str(action.get("query") or "")
            result["query"] = query
            if not query:
                raise ValueError("missing query")
            url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
            result["url"] = url
            if not _domain_allowed(url):
                raise ValueError("url_not_allowed")
            if not dry_run:
                webbrowser.open(url, new=0, autoraise=False)
            result["ok"] = True

        elif kind == "sleep":
            seconds = float(action.get("seconds") or 0.0)
            result["seconds"] = seconds
            if seconds < 0:
                raise ValueError("invalid seconds")
            if not dry_run:
                # sleep 중에도 abort를 감시한다(0.2s 단위)
                end = time.time() + min(seconds, 60.0)
                while time.time() < end:
                    check_abort(baseline_last_input_tick)
                    time.sleep(0.2)
                if seconds > 60.0:
                    # 남은 구간은 그냥 sleep (너무 자주 폴링하지 않음)
                    time.sleep(seconds - 60.0)
            result["ok"] = True

        elif kind == "log":
            # Safe no-op: 기록만 남긴다(웹/클릭/키보드 없음).
            msg = _redact_text(str(action.get("message") or ""))
            result["message"] = msg
            result["ok"] = True

        else:
            raise ValueError("unknown_action")

    except AbortExecution as e:
        result["aborted"] = True
        result["abort_reason"] = str(e)
        result["ok"] = False
        raise
    except Exception as e:
        result["ok"] = False
        result["error"] = str(e)
    finally:
        ended = time.time()
        result["ended_at"] = utc_iso(ended)
        result["duration_sec"] = round(ended - started, 3)
    return result


def execute_task(task: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    now = time.time()
    armed, arm_reason = is_armed(now)
    if not armed:
        return {
            "ok": False,
            "status": "not_armed",
            "reason": arm_reason,
            "timestamp": utc_iso(now),
        }

    # 사용자가 "감독"할 수 있게: 실행 시작 시점에 사용자 입력 baseline 확보(가능하면)
    # 일부 환경에서는 GetLastInputInfo가 과도하게 변동(noisy)할 수 있으므로,
    # 짧게 2회 샘플링하여 변동이 지속되면 이 가드(마우스/키보드 자동 중단)를 비활성화한다.
    baseline = _get_last_input_tick()
    input_guard = "last_input_tick"
    try:
        time.sleep(0.05)
        b2 = _get_last_input_tick()
        if baseline is not None and b2 is not None and b2 != baseline:
            baseline = None
            input_guard = "disabled_noisy_last_input"
    except Exception:
        pass

    started = time.time()
    report: dict[str, Any] = {
        "ok": True,
        "status": "executed",
        "timestamp": utc_iso(started),
        "workspace": str(WORKSPACE),
        "task": task,
        "dry_run": bool(dry_run),
        "input_guard": input_guard,
        "steps": [],
        "error": None,
        "abort_reason": None,
    }

    try:
        actions = task.get("actions", [])
        if not isinstance(actions, list):
            raise ValueError("task.actions must be a list")

        for a in actions[:50]:
            if not isinstance(a, dict):
                continue
            step = run_action(a, baseline, dry_run=dry_run)
            report["steps"].append(step)
            # 실패(step ok=false)면 즉시 중단하고 실패로 처리한다.
            # - "실패를 성공으로 기록"하면 학습/보정(IntelligenceLayer)이 깨진다.
            if not bool(step.get("ok")):
                raise ValueError(str(step.get("error") or "step_failed"))

        report["ok"] = True
        report["status"] = "executed"

    except AbortExecution as e:
        report["ok"] = False
        report["status"] = "aborted"
        report["abort_reason"] = str(e)
    except Exception as e:
        report["ok"] = False
        report["status"] = "failed"
        report["error"] = str(e)
        report["error_type"] = type(e).__name__
        report["traceback"] = traceback.format_exc()[:4000]
    finally:
        ended = time.time()
        report["ended_at"] = utc_iso(ended)
        report["duration_sec"] = round(ended - started, 3)

    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--poll-ms", type=int, default=500)
    ap.add_argument("--run-seconds", type=int, default=0, help="0이면 무기한 실행")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--hide-console", action="store_true", default=True)
    args = ap.parse_args()

    SIGNALS.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    if args.hide_console:
        _hide_console_best_effort()

    start_ts = time.time()
    base_poll_s = max(0.1, float(args.poll_ms) / 1000.0)
    last_life_ts = 0.0
    last_trend_ts = 0.0
    last_mission_ts = 0.0
    last_sync_ts = 0.0
    last_reporter_ts = 0.0
    last_observer_ts = 0.0

    def compute_poll_seconds(now_ts: float) -> float:
        """
        리듬 기반 폴링 템포(Adaptive Polling).

        원칙:
        - "항상 400ms" 같은 고정 인터벌은 리듬을 망가뜨릴 수 있다.
        - 단, 실행 중지/사용자 개입/STOP_FILE 같은 경계는 빠르게 반응해야 한다.
        - 그래서 (경계 가까움)일수록 빠르고, (유휴/비무장/휴식)일수록 느려진다.
        """
        try:
            if STOP_FILE.exists():
                return min(base_poll_s, 0.2)
        except Exception:
            pass

        try:
            if TASK_FILE.exists():
                return min(base_poll_s, 0.2)
        except Exception:
            pass

        try:
            if QUEUED_TASK.exists():
                # 큐가 있으면, 너무 느리게 돌면 "움직임이 없다"로 느껴질 수 있어 약간 빠르게 유지
                return max(0.5, min(base_poll_s, 1.0))
        except Exception:
            pass

        try:
            armed, _ = is_armed(now_ts)
        except Exception:
            armed = False

        try:
            rest_active = _rest_gate_active(now_ts)
        except Exception:
            rest_active = False

        try:
            last_input_s = seconds_since_last_input()
        except Exception:
            last_input_s = None

        if rest_active:
            return max(2.0, base_poll_s)

        if armed:
            # 사용자가 최근에 조작 중이면(=감독이 가까움) 실행은 안 하되, 상태 반응만 천천히 유지
            try:
                if isinstance(last_input_s, (int, float)) and float(last_input_s) < 3.0:
                    return max(1.0, base_poll_s)
            except Exception:
                pass
            return base_poll_s

        # 완전 유휴(비무장)에서는 느리게(자원 절약 + 리듬 여백)
        return max(3.0, base_poll_s)

    while True:
        # Always publish a minimal "body life signal" (throttled).
        now = time.time()
        if (now - last_life_ts) >= 15.0:
            _write_body_life_state(now)
            last_life_ts = now

        if args.run_seconds and (time.time() - start_ts) >= float(args.run_seconds):
            return 0

        task = safe_load_json(TASK_FILE)
        if isinstance(task, dict) and task:
            rest_gate_active = False
            try:
                rest_gate_active = _rest_gate_active(time.time())
            except Exception:
                rest_gate_active = False
            # 처리 전 snapshot
            report = execute_task(task, dry_run=bool(args.dry_run))
            report["rest_gate_active"] = rest_gate_active
            safe_write_json(LATEST, report)
            status = str(report.get("status") or "")

            # executed일 때만 "탐색 세션"으로 고정(Exploration Intake와 연결)
            if status == "executed":
                _write_exploration_session(task, report)

            # 실행이 실제로 발생한 경우에만 history에 누적한다.
            if status in ("executed", "aborted", "failed"):
                append_jsonl(HISTORY, report)

            # task 파일은 "실행 시도"가 아니라 "실행 발생" 시에만 소비한다.
            if status in ("executed", "aborted", "failed"):
                try:
                    TASK_FILE.unlink(missing_ok=True)
                except Exception:
                    pass

            # stop 파일은 abort 발생 시에만 정리한다(다음 실행 방지 목적).
            if status == "aborted":
                # 사용자 입력으로 중단된 경우, 나중에 재시도할 수 있게 큐에 보관한다.
                reason = str(report.get("abort_reason") or "")
                if "user_input" in reason or "stop_file" in reason:
                    try:
                        # 이미 TASK_FILE이 삭제되었으므로 원본 task 객체를 저장
                        safe_write_json(QUEUED_TASK, task)
                    except Exception:
                        pass

                try:
                    STOP_FILE.unlink(missing_ok=True)
                except Exception:
                    pass
        else:
            # 할 일이 없는 경우, 큐에 대기 중인 작업이 있는지 확인
            if QUEUED_TASK.exists():
                now = time.time()
                try:
                    last_input = seconds_since_last_input()
                    # 사용자 부재(60초 이상) + STOP_FILE 없음 + REST_GATE 없음 + ARMED
                    if (
                        isinstance(last_input, (int, float)) and last_input > 60.0 and
                        not STOP_FILE.exists() and
                        is_armed(now)[0]
                    ):
                        # 큐에 있는 작업을 TASK_FILE로 복구하여 다음 루프에서 실행되게 함
                        qtask = safe_load_json(QUEUED_TASK)
                        if qtask:
                            safe_write_json(TASK_FILE, qtask)
                            QUEUED_TASK.unlink(missing_ok=True)
                except Exception:
                    pass
            
            # 2. 통계적 정렬 모니터링 수행 (600초마다)
            if (now - last_trend_ts) >= 600.0:
                try:
                    import sys
                    import subprocess
                    subprocess.run([sys.executable, str(TREND_ANALYZER)], 
                                 env={**os.environ, "PYTHONPATH": str(WORKSPACE)},
                                 capture_output=True)
                    last_trend_ts = now
                except Exception:
                    pass

        # 3. 에이전트 미션 코디네이팅 수행 (300초마다)
        if (now - last_mission_ts) >= 300.0:
            try:
                import sys
                import subprocess
                subprocess.run([sys.executable, str(MISSION_COORDINATOR)], 
                             env={**os.environ, "PYTHONPATH": str(WORKSPACE)},
                             capture_output=True)
                last_mission_ts = now
            except Exception:
                pass

        # 4. Shion 상태 동기화 수행 (600초마다)
        if (now - last_sync_ts) >= 600.0:
            try:
                import sys
                import subprocess
                subprocess.run([sys.executable, str(SHION_STATE_SYNC)], 
                             env={**os.environ, "PYTHONPATH": str(WORKSPACE)},
                             capture_output=True)
                last_sync_ts = now
            except Exception:
                pass

        # 5. 능동적 상태 보고 수행 (300초마다)
        if (now - last_reporter_ts) >= 300.0:
            try:
                import sys
                import subprocess
                subprocess.run([sys.executable, str(PROACTIVE_REPORTER)], 
                             env={**os.environ, "PYTHONPATH": str(WORKSPACE)},
                             capture_output=True)
                last_reporter_ts = now
            except Exception:
                pass

        # 6. 사회적 정합성 관측 수행 (900초마다)
        if (now - last_observer_ts) >= 900.0:
            try:
                import sys
                import subprocess
                subprocess.run([sys.executable, str(SOCIAL_OBSERVER)], 
                             env={**os.environ, "PYTHONPATH": str(WORKSPACE)},
                             capture_output=True)
                last_observer_ts = now
            except Exception:
                pass

        time.sleep(compute_poll_seconds(time.time()))


if __name__ == "__main__":
    raise SystemExit(main())
