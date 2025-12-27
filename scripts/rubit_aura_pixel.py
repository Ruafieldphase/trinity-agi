#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rubit Aura Pixel (Windows)

대시보드 대신, 화면 가장자리에 1~2px 얇은 "오라 스트립"으로
AGI가 지금 어떤 상태인지 색으로 표시한다.

원칙:
- 외부 네트워크/추가 패키지 없이 동작 (tkinter만 사용)
- 파일 기반 관측만 수행

입력:
- outputs/bridge/trigger_report_latest.json
- outputs/bridge/constitution_review_latest.txt
- outputs/bridge/unconscious_heartbeat.json
- outputs/ethics_scorer_latest.json
- outputs/child_data_protector_latest.json
- outputs/safety/red_line_monitor_latest.json
- signals/lua_trigger.json

색상 규칙:
- RED(깜빡임): 실행 실패/오류 또는 트리거 장기 고착
- RED: Ethics BLOCK 또는 Child Data 감지 또는 Red Line Fail
- ORANGE: Ethics REVIEW/CAUTION 또는 Constitution Warning 또는 Heartbeat 지연
- YELLOW(깜빡임): 지금 실행 중(트리거 존재)
- GREEN: 정상(최근 실행 성공 + 심장 갱신 중)
- BLUE: 쉬는 중(정상 + 유휴)
- GRAY: 리포트/관측이 오래됨(멈춤 추정)

출력:
- outputs/aura_pixel_state.json
"""

from __future__ import annotations

import argparse
import json
import os
import time
import traceback
import tkinter as tk
import atexit
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# --- Paths ---
WORKSPACE = Path(__file__).resolve().parents[1]
OUTPUTS = WORKSPACE / "outputs"
REPORT = OUTPUTS / "bridge" / "trigger_report_latest.json"
CONSTITUTION = OUTPUTS / "bridge" / "constitution_review_latest.txt"
CONSTITUTION_JSON = OUTPUTS / "bridge" / "constitution_review_latest.json"
HEARTBEAT_CANDIDATES = [
    OUTPUTS / "unconscious_heartbeat.json",
    OUTPUTS / "bridge" / "unconscious_heartbeat.json",
]
ETHICS = OUTPUTS / "ethics_scorer_latest.json"
CHILD_DATA = OUTPUTS / "child_data_protector_latest.json"
RED_LINE = OUTPUTS / "safety" / "red_line_monitor_latest.json"
TRIGGER = WORKSPACE / "signals" / "lua_trigger.json"
NATURAL_DRIFT = OUTPUTS / "natural_rhythm_drift_latest.json"
REST_GATE = OUTPUTS / "safety" / "rest_gate_latest.json"
URGENT_SIGNAL = OUTPUTS / "urgent_signal.json"
LIFE_STATE = OUTPUTS / "sync_cache" / "life_state.json"

STATE_OUT = OUTPUTS / "aura_pixel_state.json"
RUNTIME_LOG = OUTPUTS / "rubit_aura_pixel_runtime.log"
_LOCK_HANDLE = None
_MUTEX_HANDLE = None
_INSTANCE_LOCK_PATH = None


def acquire_single_instance_lock() -> bool:
    """
    Best-effort single-instance lock.

    Why:
    - Startup scripts / scheduler races can spawn multiple `pythonw rubit_aura_pixel.py` instances.
    - Duplicates waste CPU and make behavior harder to reason about.

    Implementation:
    - Windows: use `msvcrt.locking` on a 1-byte lock file (non-blocking).
    - Non-Windows: no-op (return True).
    """
    global _LOCK_HANDLE, _MUTEX_HANDLE

    global _INSTANCE_LOCK_PATH

    lock_path = OUTPUTS / "rubit_aura_pixel.instance.lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Windows named mutex: stronger guard than file-based locks.
    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
            kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
            kernel32.CreateMutexW.restype = ctypes.c_void_p
            h = kernel32.CreateMutexW(None, False, "Local\\AGI_RubitAuraPixel_v1")
            if h:
                last_err = int(kernel32.GetLastError())
                if last_err == 183:  # ERROR_ALREADY_EXISTS
                    try:
                        kernel32.CloseHandle(h)
                    except Exception:
                        pass
                    return False
                _MUTEX_HANDLE = h
        except Exception:
            pass

    def _pid_alive(pid: int) -> bool:
        try:
            if pid <= 0:
                return False
            if os.name == "nt":
                import subprocess

                creationflags = 0
                if hasattr(subprocess, "CREATE_NO_WINDOW"):
                    creationflags = subprocess.CREATE_NO_WINDOW
                out = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"Get-Process -Id {pid} -ErrorAction SilentlyContinue | Select-Object -First 1 | Out-String"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    creationflags=creationflags,
                )
                return bool((out.stdout or "").strip())
            os.kill(pid, 0)
            return True
        except Exception:
            return False

    payload = {"pid": int(os.getpid()), "started_ts": float(time.time())}
    data = json.dumps(payload, ensure_ascii=False)

    for _ in range(3):
        try:
            fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError:
            try:
                old = json.loads(lock_path.read_text(encoding="utf-8"))
            except Exception:
                old = {}
            try:
                old_pid = int(old.get("pid") or 0)
            except Exception:
                old_pid = 0
            if old_pid and _pid_alive(old_pid):
                return False
            try:
                lock_path.unlink(missing_ok=True)
            except Exception:
                return False
            continue
        except Exception:
            return False
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(data)
                f.flush()
        except Exception:
            try:
                lock_path.unlink(missing_ok=True)
            except Exception:
                pass
            return False
        _INSTANCE_LOCK_PATH = lock_path
        return True

    return False


def _release_single_instance_lock() -> None:
    global _INSTANCE_LOCK_PATH
    global _MUTEX_HANDLE
    try:
        if not _INSTANCE_LOCK_PATH:
            return
        p = Path(_INSTANCE_LOCK_PATH)
        if not p.exists():
            return
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            obj = {}
        try:
            pid = int(obj.get("pid") or 0)
        except Exception:
            pid = 0
        if pid == int(os.getpid()):
            p.unlink(missing_ok=True)
    except Exception:
        pass
    if os.name == "nt":
        try:
            if _MUTEX_HANDLE is not None:
                import ctypes

                kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
                try:
                    kernel32.CloseHandle(_MUTEX_HANDLE)
                except Exception:
                    pass
        except Exception:
            pass
    _MUTEX_HANDLE = None

def _log(msg: str) -> None:
    try:
        OUTPUTS.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(tz=timezone.utc).isoformat()
        with RUNTIME_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{ts} | {msg}\n")
    except Exception:
        pass

def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

def safe_load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None

def safe_read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

def file_age_seconds(path: Path) -> float | None:
    if not path.exists():
        return None
    try:
        return max(0.0, time.time() - path.stat().st_mtime)
    except Exception:
        return None

@dataclass
class AuraDecision:
    state: str
    color: str
    blink: bool
    reason: str
    details: dict[str, Any]

def get_ethics_status() -> str:
    data = safe_load_json(ETHICS)
    if not data: return "UNKNOWN"
    if "decision" in data:
        return str(data.get("decision", "UNKNOWN")).upper()
    # Sena ethics_scorer format: results.recommendation = "PROCEED - ..."
    try:
        rec = ((data.get("results") or {}).get("recommendation") or "").strip()
        if isinstance(rec, str) and rec:
            head = rec.split()[0].strip().upper()
            if head == "PROCEED":
                return "OK"
            if head in {"REVIEW", "CAUTION", "BLOCK", "OK"}:
                return head
    except Exception:
        pass
    try:
        ok = data.get("ok")
        if ok is None:
            ok = (data.get("results") or {}).get("ok")
        if ok is True:
            return "OK"
    except Exception:
        pass
    return "UNKNOWN"

def get_child_data_status() -> bool:
    data = safe_load_json(CHILD_DATA)
    if not data: return False
    return bool(data.get("detected", False))

def get_red_line_status() -> bool:
    data = safe_load_json(RED_LINE)
    if not data: return True # Default safe if missing? No, assume safe.
    # If file exists, check 'ok'
    return bool(data.get("ok", True))

def get_constitution_status() -> str:
    """
    Constitution(종합 안전 리포트) 판정은 JSON을 우선으로 신뢰한다.
    - JSON: outputs/bridge/constitution_review_latest.json (status: PROCEED/REVIEW/CAUTION/BLOCK)
    - TXT: outputs/bridge/constitution_review_latest.txt (fallback)
    """
    data = safe_load_json(CONSTITUTION_JSON)
    if data:
        status = str(data.get("status") or "").strip().upper()
        if status == "PROCEED":
            return "OK"
        if status in {"REVIEW", "CAUTION", "BLOCK", "OK"}:
            return status

    text = safe_read_text(CONSTITUTION)
    if not text:
        return "UNKNOWN"
    for token in ("BLOCK", "CAUTION", "REVIEW", "PROCEED"):
        if token in text:
            return "OK" if token == "PROCEED" else token
    return "UNKNOWN"


def get_heartbeat_age() -> tuple[float | None, str | None]:
    best_age: float | None = None
    best_path: str | None = None
    for path in HEARTBEAT_CANDIDATES:
        age = file_age_seconds(path)
        if age is None:
            continue
        if best_age is None or age < best_age:
            best_age = age
            best_path = str(path)
    return best_age, best_path

def _trigger_info() -> dict[str, Any]:
    info: dict[str, Any] = {"exists": False}
    if not TRIGGER.exists():
        return info
    try:
        age_s = file_age_seconds(TRIGGER)
        payload = safe_load_json(TRIGGER) or {}
        info.update(
            {
                "exists": True,
                "age_s": age_s,
                "action": payload.get("action"),
                "origin": payload.get("origin"),
            }
        )
    except Exception:
        info["exists"] = True
    return info

def decide_aura() -> AuraDecision:
    trigger = _trigger_info()
    trigger_age = trigger.get("age_s")

    # 1. Critical Checks (RED)
    ethics = get_ethics_status()
    child_detected = get_child_data_status()
    red_line_ok = get_red_line_status()
    urgent = safe_load_json(URGENT_SIGNAL) or {}
    
    if urgent.get("level") == "CRITICAL" or ethics == "BLOCK" or child_detected or not red_line_ok:
        reason_parts = []
        if urgent.get("level") == "CRITICAL":
            triggers = urgent.get("triggers")
            reason_parts.append(f"URGENT: {', '.join(triggers) if isinstance(triggers, list) else 'Critical Health'}")
        if ethics == "BLOCK": reason_parts.append("Ethics BLOCK")
        if child_detected: reason_parts.append("Child Data")
        if not red_line_ok: reason_parts.append("Red Line Fail")
        return AuraDecision(
            state="critical", 
            color=urgent.get("color", "#FF0000"), 
            blink=urgent.get("blink", False),
            reason=" | ".join(reason_parts),
            details={"ethics": ethics, "child": child_detected, "red_line": red_line_ok, "urgent": urgent}
        )

    # 2. Running / Trigger Present (YELLOW blink; stuck -> RED blink)
    # - 트리거 파일이 존재하면 '지금 실행 중'으로 간주한다.
    # - 일정 시간 이상 고착되면(삭제/처리 실패) 실패로 간주한다.
    if trigger.get("exists"):
        stuck_s = 120.0
        if isinstance(trigger_age, (int, float)) and trigger_age > stuck_s:
            return AuraDecision(
                state="failed",
                color="#FF0000",
                blink=True,
                reason=f"Trigger stuck >{int(stuck_s)}s",
                details={"trigger": trigger},
            )
        return AuraDecision(
            state="running",
            color="#FACC15",  # Yellow
            blink=True,
            reason=f"Trigger: {trigger.get('action') or 'unknown'}",
            details={"trigger": trigger},
        )

    # 3. Report-based Failure (RED blink)
    report = safe_load_json(REPORT) or {}
    report_age = file_age_seconds(REPORT)
    report_action = str(report.get("action") or "")
    report_status = str(report.get("status") or "").lower()
    report_error = report.get("error")
    if report_error or report_status in {"failed", "error"}:
        return AuraDecision(
            state="failed",
            color="#FF0000",
            blink=True,
            reason=f"Failed: {report_action}" if report_action else "Failed",
            details={
                "action": report_action,
                "status": report_status,
                "report_age_s": report_age,
                "error": report_error,
            },
        )

    # 3.2 Homeostasis Rest Gate (CYAN)
    try:
        rg = safe_load_json(REST_GATE) or {}
        if isinstance(rg, dict) and str(rg.get("status") or "").upper() == "REST":
            until = rg.get("rest_until_epoch")
            active = True
            if isinstance(until, (int, float)) and time.time() >= float(until):
                active = False
            if active:
                reasons = rg.get("reasons") if isinstance(rg.get("reasons"), list) else []
                msg = ", ".join([str(x) for x in reasons[:2]]) if reasons else "Rest gate active"
                return AuraDecision(
                    state="rest",
                    color="#06B6D4",  # Cyan
                    blink=False,
                    reason=msg,
                    details={"rest_gate": rg},
                )
    except Exception:
        pass

    # 3.5 Natural rhythm drift (PURPLE)
    try:
        drift = safe_load_json(NATURAL_DRIFT) or {}
        if isinstance(drift, dict) and drift.get("ok") is False:
            reasons = drift.get("reasons") if isinstance(drift.get("reasons"), list) else []
            msg = ", ".join([str(x) for x in reasons[:2]]) if reasons else "Natural rhythm drift"
            return AuraDecision(
                state="warning",
                color="#A855F7",  # Purple
                blink=False,
                reason=msg,
                details={"drift": drift},
            )
    except Exception:
        pass

    # 4. Warning Checks (ORANGE)
    constitution = get_constitution_status()
    hb_age, hb_path = get_heartbeat_age()
    life = safe_load_json(LIFE_STATE) or {}
    life_age = file_age_seconds(LIFE_STATE)
    life_state = str(life.get("state") or "") if isinstance(life, dict) else ""
    # Heartbeat는 "유휴 상태에서 살아있음"을 판단하는 보조 신호로만 사용한다.
    # (트리거 실행이 활발히 일어나는 동안에는 heartbeat 지연을 오라 색상으로 과도하게 경고하지 않는다.)
    heartbeat_stale = (
        hb_age is not None
        and hb_age > 180.0
        and report_age is not None
        and report_age > 300.0
    )

    # Constitution 결과는 사람 기준으로도 중요한 경고 신호로 취급한다.
    if constitution == "BLOCK":
        return AuraDecision(
            state="critical",
            color="#FF0000",
            blink=False,
            reason="Constitution BLOCK",
            details={"constitution": constitution, "report_age_s": report_age},
        )

    const_warning = constitution in {"REVIEW", "CAUTION"}

    if ethics in ["REVIEW", "CAUTION"] or const_warning or heartbeat_stale:
        reason_parts = []
        if ethics in ["REVIEW", "CAUTION"]:
            reason_parts.append(f"Ethics {ethics}")
        if const_warning:
            reason_parts.append(f"Constitution {constitution}")
        if heartbeat_stale:
            reason_parts.append(f"Heartbeat stale ({int(hb_age or 0)}s)")
        return AuraDecision(
            state="warning",
            color="#FF8800",
            blink=False,
            reason=" | ".join(reason_parts),
            details={
                "ethics": ethics,
                "constitution": constitution,
                "heartbeat_age_s": hb_age,
                "heartbeat_path": hb_path,
                "report_age_s": report_age,
            },
        )
    
    # 5. Staleness / No Observability (GRAY)
    # '리포트가 오래됨'은 곧바로 정지/에러가 아니다.
    # - 트리거가 없더라도(run_trigger_once의 idle_tick), heartbeat/life_state가 갱신된다면
    #   이는 "정상 생존(유휴)"으로 본다.
    alive_signal_fresh = False
    try:
        if life_state.startswith("ALIVE") and life_age is not None and life_age < 5 * 60:
            alive_signal_fresh = True
        elif hb_age is not None and hb_age < 5 * 60:
            alive_signal_fresh = True
    except Exception:
        alive_signal_fresh = False

    if report_age is None:
        if alive_signal_fresh:
            return AuraDecision(
                state="idle",
                color="#3B82F6",  # Blue
                blink=False,
                reason="Alive (idle)",
                details={"report_exists": False, "heartbeat_age_s": hb_age, "life_state": life_state, "life_age_s": life_age},
            )
        return AuraDecision(
            state="stale",
            color="#9CA3AF",  # Gray
            blink=False,
            reason="No trigger report",
            details={"report_exists": False, "heartbeat_age_s": hb_age, "life_state": life_state, "life_age_s": life_age},
        )
    if report_age > 15 * 60:
        if alive_signal_fresh:
            return AuraDecision(
                state="idle",
                color="#3B82F6",  # Blue
                blink=False,
                reason="Alive (idle; report stale)",
                details={"report_age_s": report_age, "heartbeat_age_s": hb_age, "life_state": life_state, "life_age_s": life_age},
            )
        return AuraDecision(
            state="stale",
            color="#9CA3AF",
            blink=False,
            reason=f"Report stale ({int(report_age)}s)",
            details={"report_age_s": report_age, "heartbeat_age_s": hb_age, "life_state": life_state, "life_age_s": life_age},
        )

    # 6. OK / Idle
    # - 최근에 리포트가 갱신됐으면(=최근 행동) GREEN
    # - 그렇지 않으면 BLUE(유휴)
    if report_age < 120:
        return AuraDecision(
            state="ok",
            color="#22C55E",  # Green
            blink=False,
            reason="OK (recent activity)",
            details={"report_age_s": report_age, "heartbeat_age_s": hb_age, "heartbeat_path": hb_path, "action": report_action},
        )
    return AuraDecision(
        state="idle",
        color="#3B82F6",  # Blue
        blink=False,
        reason="Idle",
        details={"report_age_s": report_age, "heartbeat_age_s": hb_age, "heartbeat_path": hb_path, "action": report_action},
    )

def write_state(decision: AuraDecision) -> None:
    try:
        OUTPUTS.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp_utc": utc_iso(time.time()),
            "decision": asdict(decision),
        }
        tmp = STATE_OUT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, STATE_OUT)
    except Exception:
        pass

def run_gui(position: str, thickness: int, poll_ms: int, alpha: float) -> int:
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    try:
        root.attributes("-alpha", float(alpha))
    except Exception:
        pass

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    t = max(1, int(thickness))

    if position == "top": geom = f"{sw}x{t}+0+0"
    elif position == "bottom": geom = f"{sw}x{t}+0+{sh - t}"
    elif position == "left": geom = f"{t}x{sh}+0+0"
    elif position == "right": geom = f"{t}x{sh}+{sw - t}+0"
    else: geom = f"{sw}x{t}+0+0"
    
    root.geometry(geom)
    frame = tk.Frame(root, bg="#444444")
    frame.pack(fill="both", expand=True)
    blink_on = {"on": True}

    def tick():
        try:
            decision = decide_aura()
            write_state(decision)
            
            # Update GUI color
            try:
                if decision.blink:
                    blink_on["on"] = not blink_on["on"]
                    if blink_on["on"]:
                        frame.configure(bg=decision.color)
                    else:
                        frame.configure(bg="#111111")
                else:
                    frame.configure(bg=decision.color)
            except Exception:
                pass
            
            root.after(max(200, int(poll_ms)), tick)
        except Exception:
             root.after(max(500, int(poll_ms)), tick)

    tick()
    root.mainloop()
    return 0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--position", default="top")
    ap.add_argument("--thickness", type=int, default=2)
    ap.add_argument("--poll-ms", type=int, default=800)
    ap.add_argument("--alpha", type=float, default=0.9)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()

    if not acquire_single_instance_lock():
        # Another aura instance is already running.
        return 0
    atexit.register(_release_single_instance_lock)

    if args.once:
        d = decide_aura()
        write_state(d)
        print(json.dumps(asdict(d), ensure_ascii=False))
        return 0

    return run_gui(args.position, args.thickness, args.poll_ms, args.alpha)

if __name__ == "__main__":
    raise SystemExit(main())
