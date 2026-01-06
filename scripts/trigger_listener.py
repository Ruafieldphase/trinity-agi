#!/usr/bin/env python3
"""
Trigger Listener v1
- 코어가 생성하는 트리거 파일(`signals/lua_trigger.json`)을 감지해
  비노체 개입 없이 즉시 대응 액션을 실행.
- 액션: self_acquire, self_compress, self_tool, sync_clean, heartbeat_check, full_cycle
- 실패 시 로그 남기고 루프 지속(자가치유).
"""
from __future__ import annotations

import argparse
import json
import time
import sys
import atexit
from pathlib import Path
import subprocess
import os
import re
from datetime import datetime, timezone

from workspace_root import get_workspace_root

ROOT = get_workspace_root()
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
scripts_dir = ROOT / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.append(str(scripts_dir))
LOG_FILE = ROOT / "logs" / "trigger_listener.log"
SIGNAL_PATH = ROOT / "signals" / "lua_trigger.json"
STATE_PATH = ROOT / "outputs" / "sync_cache" / "self_expansion_state.json"
LIFE_STATE_PATH = ROOT / "outputs" / "sync_cache" / "life_state.json"
REPORT_DIR = ROOT / "outputs" / "bridge"
REPORT_TXT = REPORT_DIR / "trigger_report_latest.txt"
REPORT_JSON = REPORT_DIR / "trigger_report_latest.json"
REPORT_HTML = REPORT_DIR / "trigger_dashboard.html"
REPORT_V2_STATIC = REPORT_DIR / "status_dashboard_v2_static.html"
REPORT_HISTORY = REPORT_DIR / "trigger_report_history.jsonl"
CONSTITUTION_REVIEW_JSON = REPORT_DIR / "constitution_review_latest.json"
BINOCHE_DROPBOX = ROOT / "to_agi.txt"
BINOCHE_DROPBOX_STATE = ROOT / "outputs" / "sync_cache" / "binoche_dropbox_state.json"
IDLE_TICK_STATE = ROOT / "outputs" / "sync_cache" / "idle_tick_state.json"

_LISTENER_LOCK_HANDLE = None
_LISTENER_MUTEX_HANDLE = None


def _acquire_windows_mutex(name: str) -> bool | None:
    """
    Windows named mutex single-instance guard.

    Why:
    - 파일 락은 (아주 드문) 레이스/권한/파일 손상 상황에서 중복 인스턴스를 허용할 수 있다.
    - 똑같은 스크립트가 2개 이상 돌면 트리거 중복 처리/idle_tick 과다로 rest_gate 폭주처럼 관측될 수 있다.

    Policy:
    - mutex가 이미 존재하면 False (다른 인스턴스가 살아있음)
    - 획득 실패는 best-effort로 처리(=파일 락에 맡김)
    """
    global _LISTENER_MUTEX_HANDLE
    if os.name != "nt":
        return None
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        handle = kernel32.CreateMutexW(None, False, name)
        if not handle:
            return None
        last_err = int(kernel32.GetLastError())
        # ERROR_ALREADY_EXISTS = 183
        if last_err == 183:
            try:
                kernel32.CloseHandle(handle)
            except Exception:
                pass
            return False
        _LISTENER_MUTEX_HANDLE = handle
        return True
    except Exception:
        return None


def _release_windows_mutex() -> None:
    global _LISTENER_MUTEX_HANDLE
    if os.name != "nt":
        return
    try:
        if _LISTENER_MUTEX_HANDLE is None:
            return
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        kernel32.CloseHandle(_LISTENER_MUTEX_HANDLE)
    except Exception:
        pass
    _LISTENER_MUTEX_HANDLE = None


def _terminate_duplicate_listeners_best_effort() -> None:
    """
    Best-effort: 중복 실행된 trigger_listener(--silent) 프로세스를 정리한다.

    - 절대 필수는 아니지만, 중복 리스너는 "폭주처럼 보이는" 관측(트리거/리포트/idle_tick 과다)을 만든다.
    - 오직 동일 스크립트/--silent 커맨드라인에 한해서만 종료한다.
    """
    if os.name != "nt":
        return
    try:
        needle = str((ROOT / "scripts" / "trigger_listener.py").resolve()).lower()
        cmd = (
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.Name -eq 'pythonw.exe' -and $_.CommandLine -like '*trigger_listener.py*' } | "
            "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
        )
        creationflags = 0
        if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=4,
            creationflags=creationflags,
        )
        if out.returncode != 0 or not (out.stdout or "").strip():
            return
        try:
            items = json.loads(out.stdout)
        except Exception:
            return
        if isinstance(items, dict):
            items = [items]
        me = int(os.getpid())
        victims: list[int] = []
        for it in items or []:
            try:
                pid = int((it or {}).get("ProcessId") or 0)
            except Exception:
                pid = 0
            if pid <= 0 or pid == me:
                continue
            cl = str((it or {}).get("CommandLine") or "").lower()
            if needle not in cl:
                continue
            if "--silent" not in cl:
                continue
            victims.append(pid)
        for pid in victims:
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                    creationflags=creationflags,
                )
            except Exception:
                continue
    except Exception:
        return


def _acquire_single_instance_lock() -> bool:
    """
    Best-effort single-instance guard.

    Why:
    - Windows 스케줄러/스타트업/워치독 레이어가 겹치면 동일 스크립트가 중복 실행될 수 있다.
    - 중복 리스너는 동일 트리거를 "중복 처리"하거나, idle_tick/리포트 갱신이 과도해져
      rest_gate/오라에서 "폭주"로 관측될 수 있다.

    Policy:
    - 한 프로세스만 살아있으면 된다.
    - 락 획득 실패 시 조용히 종료(=다른 리스너가 이미 존재).
    """
    global _LISTENER_LOCK_HANDLE, _LISTENER_MUTEX_HANDLE

    # Windows에서는 mutex를 먼저 시도해서 "아주 드문" 파일락 레이스를 원천 차단한다.
    # mutex 실패(권한/환경) 시에는 파일 락으로 fallback.
    if os.name == "nt":
        # NOTE:
        # - Global\\ 네임스페이스는 권한에 따라 실패할 수 있어(Local\\ 우선).
        # - mutex 획득에 실패(권한/환경)하면 파일락으로 fallback한다.
        m = _acquire_windows_mutex("Local\\AGI_TriggerListener_v1")
        if m is False:
            return False
        if m is True:
            atexit.register(_release_windows_mutex)

    lock_path = ROOT / "outputs" / "trigger_listener.instance.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Robust file lock (keeps handle open for lifetime).
    # - stale lock cleanup 불필요: 프로세스가 죽으면 OS가 락을 해제한다.
    try:
        # NOTE: Windows msvcrt.locking은 EOF 밖의 영역 락에 실패할 수 있어,
        # 바이너리 모드로 열고 최소 1바이트를 보장한다.
        f = open(lock_path, "a+b")
    except Exception:
        return False

    try:
        try:
            f.seek(0, os.SEEK_END)
            if int(f.tell()) <= 0:
                f.write(b"0")
                f.flush()
            f.seek(0)
        except Exception:
            try:
                f.seek(0)
            except Exception:
                pass
        if os.name == "nt":
            import msvcrt

            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            except Exception:
                try:
                    f.close()
                except Exception:
                    pass
                return False
        else:
            import fcntl

            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except Exception:
                try:
                    f.close()
                except Exception:
                    pass
                return False

        try:
            payload = {"pid": int(os.getpid()), "started_ts": float(time.time())}
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            f.seek(0)
            f.truncate(0)
            f.write(data)
            f.flush()
        except Exception:
            pass

        _LISTENER_LOCK_HANDLE = f
        _terminate_duplicate_listeners_best_effort()
        return True
    except Exception:
        try:
            f.close()
        except Exception:
            pass
        return False


def _release_single_instance_lock() -> None:
    global _LISTENER_LOCK_HANDLE, _LISTENER_MUTEX_HANDLE
    try:
        f = _LISTENER_LOCK_HANDLE
        _LISTENER_LOCK_HANDLE = None
        if f is not None:
            try:
                if os.name == "nt":
                    import msvcrt

                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                    except Exception:
                        pass
                else:
                    import fcntl

                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except Exception:
                        pass
            finally:
                try:
                    f.close()
                except Exception:
                    pass
        # best-effort: lock 파일은 남겨도 되지만, "살아있지 않음" 오해를 줄이기 위해 지운다.
        try:
            lock_path = ROOT / "outputs" / "trigger_listener.instance.lock"
            lock_path.unlink(missing_ok=True)
        except Exception:
            pass
    except Exception:
        pass
    _LISTENER_LOCK_HANDLE = None
    _LISTENER_MUTEX_HANDLE = None


def _rotate_history_if_needed(max_bytes: int = 50_000_000) -> None:
    """
    trigger_report_history.jsonl이 너무 커지면 자동 로테이션한다.
    - 목적: 대용량/PII 리스크 축소 + Tail/대시보드 성능 유지
    - 보존: outputs/bridge/history_archive/trigger_report_history_YYYYMMDD_HHMMSS.jsonl
    """
    try:
        if not REPORT_HISTORY.exists():
            return
        size = REPORT_HISTORY.stat().st_size
        if int(size) <= int(max_bytes):
            return
        archive_dir = REPORT_DIR / "history_archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = archive_dir / f"trigger_report_history_{ts}.jsonl"
        REPORT_HISTORY.replace(dst)
    except Exception:
        return

def _atomic_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def update_unconscious_heartbeat(action: str, status: str, error: object) -> None:
    """
    Windows/로컬에서도 "살아있음"을 관측할 수 있게 heartbeat 파일을 갱신한다.
    - Linux 쪽 writer가 없어도(또는 sync가 끊겨도) 최소한의 활동 신호가 유지된다.
    - 민감 정보/대용량 dump 금지: action/status/error 여부만 기록.
    """
    hb_path = ROOT / "outputs" / "unconscious_heartbeat.json"
    now_iso = datetime.now(timezone.utc).isoformat()
    now_ts = time.time()

    data = {}
    if hb_path.exists():
        try:
            data = json.loads(hb_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    state = data.get("state") if isinstance(data.get("state"), dict) else {}
    try:
        current = data.get("heartbeat_count")
        if current is None:
            current = state.get("heartbeat_count")
        count = int(current or 0) + 1
    except Exception:
        count = 1

    state.update(
        {
            "heartbeat_count": count,
            "last_action": action,
            "last_status": status,
            "last_error": bool(error),
            "last_update_utc": now_iso,
        }
    )

    data.update(
        {
            "timestamp": now_iso,
            "timestamp_epoch": now_ts,
            "heartbeat_count": count,
            "state": state,
        }
    )

    try:
        _atomic_write_json(hb_path, data)
    except Exception:
        return


def write_life_state(state: str, reason: str, trigger_present: bool, last_action: str | None = None) -> None:
    """
    '아무것도 하지 않아도 정상'인 생존 상태를 파일로 고정한다.

    원칙:
    - 실행/리포트가 없어도(=idle) 살아있음을 관측 가능하게 한다.
    - 판단/결정이 아니라 "상태 관측" 파일이다.
    """
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        now_ts = time.time()
        payload = {
            "generated_at_utc": now_iso,
            "generated_at_epoch": now_ts,
            "state": state,
            "reason": reason,
            "trigger_present": bool(trigger_present),
            "last_action": last_action,
        }
        _atomic_write_json(LIFE_STATE_PATH, payload)
    except Exception:
        return


def idle_tick() -> None:
    """
    트리거가 없어도 '정상 생존 상태'를 유지하기 위한 최소 틱.
    - 실행(행동) 없음
    - 출력(리포트) 없음
    - 대신 관측 가능한 생존 신호(heartbeat/life_state)만 갱신
    """
    now = time.time()

    # Idle tick 자체가 "폭주"로 보이지 않도록, 내부에서도 최소 주기를 둔다.
    # (리듬 기반이며, 여기의 값은 '고정 목표'가 아니라 '최소 바닥'으로만 취급)
    st = _load_json_best_effort(IDLE_TICK_STATE)
    try:
        last_hb = float(st.get("last_hb_ts") or 0.0)
    except Exception:
        last_hb = 0.0
    try:
        last_ls = float(st.get("last_life_state_ts") or 0.0)
    except Exception:
        last_ls = 0.0
    try:
        last_msg = float(st.get("last_msg_ts") or 0.0)
    except Exception:
        last_msg = 0.0
    try:
        last_ops = float(st.get("last_ops_snapshot_ts") or 0.0)
    except Exception:
        last_ops = 0.0
    try:
        last_twin = float(st.get("last_digital_twin_ts") or 0.0)
    except Exception:
        last_twin = 0.0
    try:
        last_pain = float(st.get("last_pain_ts") or 0.0)
    except Exception:
        last_pain = 0.0
    try:
        last_rest_gate = float(st.get("last_rest_gate_ts") or 0.0)
    except Exception:
        last_rest_gate = 0.0
    try:
        last_ops_summary = float(st.get("last_ops_summary_ts") or 0.0)
    except Exception:
        last_ops_summary = 0.0
    try:
        last_rhythm_snapshot = float(st.get("last_rhythm_snapshot_ts") or 0.0)
    except Exception:
        last_rhythm_snapshot = 0.0
    try:
        last_live_ops = float(st.get("last_live_ops_ts") or 0.0)
    except Exception:
        last_live_ops = 0.0
    try:
        last_vision_normalize = float(st.get("last_vision_normalize_ts") or 0.0)
    except Exception:
        last_vision_normalize = 0.0
    try:
        last_core_refresh = float(st.get("last_core_refresh_ts") or 0.0)
    except Exception:
        last_core_refresh = 0.0
    try:
        last_exploration_hint = float(st.get("last_exploration_hint_ts") or 0.0)
    except Exception:
        last_exploration_hint = 0.0

    rhythm_mode = ""
    allow_observe = True
    try:
        from agi_core.rhythm_boundaries import RhythmBoundaryManager  # type: ignore

        boundary_manager = RhythmBoundaryManager(ROOT)
        mode = boundary_manager.detect_rhythm_mode()
        rhythm_mode = mode.value if mode else ""
    except Exception:
        allow_observe = True
    if rhythm_mode:
        st["last_rhythm_mode"] = rhythm_mode

    # 1) 최소 생존 신호(heartbeat/life_state)
    if (now - last_hb) >= 10.0:
        try:
            update_unconscious_heartbeat(action="idle", status="alive", error=None)
            st["last_hb_ts"] = now
        except Exception:
            pass
    if (now - last_ls) >= 10.0:
        try:
            write_life_state(
                state="ALIVE_IDLE",
                reason="idle is normal (no action required)",
                trigger_present=False,
                last_action=None,
            )
            st["last_life_state_ts"] = now
        except Exception:
            pass

    # 1.5) "통증/항상성" 신호는 주기적으로 갱신되어야 한다.
    # - 쉼/여백도 정상 생존 상태지만, 통증/불일치가 stale이면 다음 행동의 템포가 왜곡될 수 있다.
    if (now - last_rest_gate) >= 90.0:
        try:
            rest_script = ROOT / "scripts" / "rest_gate.py"
            if rest_script.exists():
                _run_script_best_effort(rest_script, timeout_s=10)
                st["last_rest_gate_ts"] = now
        except Exception:
            pass

    if (now - last_pain) >= 60.0:
        try:
            pain_script = ROOT / "scripts" / "rhythm_pain_signal.py"
            if pain_script.exists():
                _run_script_best_effort(pain_script, timeout_s=10)
                st["last_pain_ts"] = now
        except Exception:
            pass

    # 2) 사람용 한 줄 메시지(오라/알림 보강): 너무 자주 프로세스를 띄우지 않는다.
    if allow_observe and (now - last_msg) >= 45.0:
        try:
            msg_script = ROOT / "scripts" / "agi_message_reporter.py"
            if msg_script.exists():
                _run_script_best_effort(msg_script, timeout_s=10)
                st["last_msg_ts"] = now
        except Exception:
            pass

    # 3) 협업자(Shion/세나)에게 같은 관측을 공유하는 스냅샷: best-effort + 느리게
    if allow_observe and (now - last_ops) >= 300.0:
        try:
            publisher = ROOT / "scripts" / "coordination" / "publish_ops_snapshot.py"
            if publisher.exists():
                _run_script_best_effort(publisher, timeout_s=12)
                st["last_ops_snapshot_ts"] = now
        except Exception:
            pass

    # 4) 디지털 트윈/퀀텀 디지털 트윈(관측 고정): idle에서도 천천히 갱신
    if allow_observe and (now - last_twin) >= 60.0:
        try:
            twin_script = ROOT / "scripts" / "digital_twin_update.py"
            if twin_script.exists():
                _run_script_best_effort(twin_script, timeout_s=12)
                st["last_digital_twin_ts"] = now
        except Exception:
            pass

    # 4.5) 비노체가 터미널/로그 없이도 읽을 수 있는 운영 요약은 "느리게" 갱신한다.
    if allow_observe and (now - last_ops_summary) >= 300.0:
        try:
            ops_summary_script = ROOT / "scripts" / "human_ops_summary.py"
            if ops_summary_script.exists():
                _run_script_best_effort(ops_summary_script, timeout_s=12)
                st["last_ops_summary_ts"] = now
        except Exception:
            pass

    # 4.6) 리듬 체온계 스냅샷은 느리게 갱신해 관측 노이즈를 줄인다.
    if allow_observe and (now - last_rhythm_snapshot) >= 300.0:
        try:
            thermo_script = ROOT / "scripts" / "rhythm_thermometer_snapshot.py"
            if thermo_script.exists():
                _run_script_best_effort(thermo_script, timeout_s=12)
                st["last_rhythm_snapshot_ts"] = now
        except Exception:
            pass

    # 4.7) Live Ops Dashboard는 저빈도로 갱신한다.
    if allow_observe and (now - last_live_ops) >= 600.0:
        try:
            live_ops_script = ROOT / "scripts" / "generate_live_ops_dashboard.py"
            if live_ops_script.exists():
                _run_script_best_effort(live_ops_script, timeout_s=12)
                st["last_live_ops_ts"] = now
        except Exception:
            pass

    # 4.8) Vision 로그 정규화는 유지보수 성격으로 느리게 수행.
    if (now - last_vision_normalize) >= 600.0:
        try:
            normalize_script = ROOT / "scripts" / "normalize_vision_events.py"
            if normalize_script.exists():
                _run_script_best_effort(normalize_script, timeout_s=15)
                st["last_vision_normalize_ts"] = now
        except Exception:
            pass

    # 4.9) Core 상태 갱신 (정서/안전 파이프라인 유지)
    if (now - last_core_refresh) >= 900.0:
        try:
            core_script = ROOT / "scripts" / "refresh_core_state.py"
            if core_script.exists():
                _run_script_best_effort(core_script, timeout_s=20)
                st["last_core_refresh_ts"] = now
        except Exception:
            pass

    # 5) Boredom/curiosity imbalance hint (non-executing)
    if allow_observe and (now - last_exploration_hint) >= 1800.0:
        try:
            hint_script = ROOT / "scripts" / "suggest_exploration_hint.py"
            if hint_script.exists():
                _run_script_best_effort(hint_script, timeout_s=8)
                st["last_exploration_hint_ts"] = now
        except Exception:
            pass

    try:
        IDLE_TICK_STATE.parent.mkdir(parents=True, exist_ok=True)
        IDLE_TICK_STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _load_json_best_effort(path: Path) -> dict:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _atomic_write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        return


def _run_script_best_effort(script: Path, timeout_s: int = 10) -> None:
    try:
        if not script.exists():
            return
        creationflags = 0
        if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW
        subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            timeout=timeout_s,
            creationflags=creationflags,
        )
    except Exception:
        return


def _tick_binoche_dropbox() -> None:
    """
    비노체가 프로그래밍 없이 '메모장에 쓰기'만으로 AGI에 말을 걸 수 있게 하는 드롭박스.

    사용:
    - to_agi.txt에 문장을 적고 저장
    - 리스너가 감지하면 signals/binoche_note.json으로 변환 → binoche_note_intake로 물질화
    - 성공 시 to_agi.txt는 비운다(원문 보관 최소화)
    """
    try:
        if not BINOCHE_DROPBOX.exists():
            return
        raw = BINOCHE_DROPBOX.read_text(encoding="utf-8", errors="replace")
        text = (raw or "").strip()
        if not text:
            return

        st = _load_json_best_effort(BINOCHE_DROPBOX_STATE)
        last_sig = str(st.get("last_sig") or "")
        # low-cost signature (do not store the raw note)
        sig = str(hash(text))
        if sig == last_sig:
            return

        # Create signal for existing intake (it will redact).
        payload = {"text": text, "timestamp": float(time.time()), "origin": "binoche_dropbox"}
        sig_dir = ROOT / "signals"
        sig_dir.mkdir(parents=True, exist_ok=True)
        note_path = sig_dir / "binoche_note.json"
        tmp = note_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, note_path)

        # Run intake (best-effort, local-only)
        intake = ROOT / "scripts" / "self_expansion" / "binoche_note_intake.py"
        if intake.exists():
            subprocess.run(
                [sys.executable, str(intake)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                timeout=15,
            )

        # Clear the dropbox to minimize raw retention (best-effort)
        _atomic_write_text(BINOCHE_DROPBOX, "")

        # Update state
        BINOCHE_DROPBOX_STATE.parent.mkdir(parents=True, exist_ok=True)
        BINOCHE_DROPBOX_STATE.write_text(
            json.dumps({"last_sig": sig, "last_seen_epoch": float(time.time())}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        return


def tick_binoche_dropbox_once() -> None:
    """
    Public wrapper for scheduled/one-shot runners.

    Why:
    - daemon 모드가 꺼져 있어도(Windows Task Scheduler의 --once 중심 운영),
      `to_agi.txt` 기반의 "메모장 인터페이스"는 계속 작동해야 한다.
    """
    _tick_binoche_dropbox()


def _load_constitution_status() -> str:
    try:
        if not CONSTITUTION_REVIEW_JSON.exists():
            return "UNKNOWN"
        # Windows PowerShell/도구들이 UTF-8 BOM을 붙이는 경우가 있어 utf-8-sig로 읽는다.
        data = json.loads(CONSTITUTION_REVIEW_JSON.read_text(encoding="utf-8-sig"))
        status = str(data.get("status") or "").strip().upper()
        return status if status else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _run_ethics_precheck(action: str, origin: str) -> dict:
    """
    사전(Pre-action) 윤리 스코어링.
    - 외부 네트워크 없음
    - 민감 데이터/대용량 params는 넣지 않는다.
    """
    desc = f"action={action} origin={origin}".strip()
    scorer = ROOT / "rune" / "ethics_scorer.py"
    if not scorer.exists():
        return {"ok": True, "skipped": True, "reason": "missing_ethics_scorer"}
    try:
        subprocess.run(
            [sys.executable, str(scorer), desc],
            cwd=ROOT,
            check=False,
            capture_output=True,
            timeout=20,
        )
    except Exception as e:
        return {"ok": True, "skipped": True, "reason": f"ethics_scorer_failed: {e}"}

    out = ROOT / "outputs" / "ethics_scorer_latest.json"
    try:
        data = json.loads(out.read_text(encoding="utf-8-sig")) if out.exists() else {}
        rec = ((data.get("results") or {}).get("recommendation") or "").strip()
        head = rec.split()[0].strip().upper() if isinstance(rec, str) and rec else ""
        ok = True
        if head == "BLOCK":
            ok = False
        return {
            "ok": ok,
            "recommendation": rec,
            "status": head or "UNKNOWN",
        }
    except Exception:
        return {"ok": True, "recommendation": None, "status": "UNKNOWN"}

def sanitize(obj):
    """
    Best-effort JSON 직렬화 + 민감정보/대용량 방지.

    원칙:
    - PII(이메일/URL/사용자 홈 경로 등)는 리포트/히스토리/대시보드에 남기지 않는다.
    - 대용량 원문 저장 금지(미리보기/본문 등은 길이 제한).
    """

    def _cap(s: str, n: int = 1200) -> str:
        s = (s or "").strip()
        if len(s) <= n:
            return s
        return s[: n - 1] + "…"

    def _redact_text(s: str) -> str:
        s = (s or "").strip()
        if not s:
            return ""
        # URLs
        s = re.sub(r"https?://[^\s)\]]+", "[REDACTED_URL]", s, flags=re.IGNORECASE)
        # Emails
        s = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", s)
        # Windows paths: keep workspace paths, redact others (often include username/AppData)
        def _win_path_sub(m: re.Match) -> str:
            p = m.group(0)
            pl = p.lower()
            if pl.startswith("c:\\workspace\\agi\\"):
                return p
            return "[REDACTED_PATH]"

        s = re.sub(r"\b[A-Za-z]:\\[^\s]+", _win_path_sub, s)
        # Linux/Mac paths
        s = re.sub(r"/(home|Users|var|etc|opt|tmp|usr)/[^\s]+", "[REDACTED_PATH]", s)
        return s

    def _sanitize_inner(x, depth: int = 0):
        if depth > 6:
            return "…"
        if isinstance(x, dict):
            out = {}
            # cap keys to avoid massive dict dumps
            for i, (k, v) in enumerate(x.items()):
                if i >= 120:
                    out["…"] = f"truncated_keys>={len(x)}"
                    break
                out[str(k)] = _sanitize_inner(v, depth + 1)
            return out
        if isinstance(x, list):
            out_list = []
            for i, v in enumerate(x):
                if i >= 80:
                    out_list.append("…")
                    break
                out_list.append(_sanitize_inner(v, depth + 1))
            return out_list
        if isinstance(x, str):
            return _cap(_redact_text(x), 1400)
        if isinstance(x, (int, float, bool)) or x is None:
            return x
        return _cap(_redact_text(repr(x)), 600)

    return _sanitize_inner(obj, 0)


def _fmt_age_seconds(age_s: float | None) -> str:
    if age_s is None:
        return "unknown"
    if age_s < 60:
        return f"{int(age_s)}s"
    if age_s < 3600:
        return f"{int(age_s//60)}m"
    return f"{int(age_s//3600)}h"


def file_info(path: Path) -> dict:
    now = time.time()
    if not path.exists():
        return {"exists": False}
    st = path.stat()
    age_s = max(0.0, now - st.st_mtime)
    return {
        "exists": True,
        "mtime": st.st_mtime,
        "mtime_iso": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "age_seconds": age_s,
        "age": _fmt_age_seconds(age_s),
        "size": st.st_size,
    }


def read_jsonl_tail(path: Path, max_lines: int = 10, max_bytes: int = 200_000) -> list[dict]:
    """
    JSONL 파일의 끝부분에서 최근 N개 레코드를 읽는다.
    - 브라우저 fetch 없이도 "최근 실행 이력"을 HTML에 인라인하기 위함.
    """
    if not path.exists():
        return []
    try:
        with path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            start = max(0, size - max_bytes)
            f.seek(start)
            data = f.read()
        text = data.decode("utf-8", errors="replace")
        lines = text.splitlines()
        if start > 0 and lines:
            lines = lines[1:]
        out: list[dict] = []
        for line in reversed(lines):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
                if isinstance(obj, dict):
                    out.append(obj)
                    if len(out) >= max_lines:
                        break
            except Exception:
                continue
        return list(reversed(out))
    except Exception:
        return []


def render_dashboard(report: dict) -> str:
    """간단한 정적 HTML 대시보드."""
    files = report.get("files") or {}
    hb = files.get("unconscious_heartbeat.json") or {}
    ts = files.get("thought_stream_latest.json") or {}
    st = files.get("agi_internal_state.json") or {}
    rs = report.get("result_summary") or {}
    media: dict = {}
    agi: dict = {}
    human: dict = {}
    history_items: list[dict] = []
    try:
        if isinstance(rs, dict):
            # full_cycle -> self_acquire -> media_intake
            sa = rs.get("self_acquire") if isinstance(rs.get("self_acquire"), dict) else None
            if isinstance(sa, dict) and isinstance(sa.get("media_intake"), dict):
                media = sa.get("media_intake") or {}
            if isinstance(sa, dict) and isinstance(sa.get("antigravity_intake"), dict):
                agi = sa.get("antigravity_intake") or {}
    except Exception:
        media = {}
        agi = {}

    def row(name: str, info: dict) -> str:
        if not info or not info.get("exists"):
            return f"<tr><td><code>{name}</code></td><td class='fail'>missing</td><td>-</td><td>-</td></tr>"
        age = info.get("age") or "unknown"
        size = info.get("size") or 0
        mtime = info.get("mtime_iso") or ""
        return f"<tr><td><code>{name}</code></td><td>{age}</td><td>{size}</td><td>{mtime}</td></tr>"

    media_card = ""
    try:
        if isinstance(media, dict) and (media.get("ok") is True or "total" in media or "counts" in media):
            total = media.get("total", 0)
            new_cnt = media.get("new_files_count", 0)
            newest = media.get("newest") or {}
            newest_path = newest.get("relpath") or newest.get("path") or "-"
            scanned_at = media.get("scanned_at", "")
            media_card = f"""
  <div class="card">
    <h2>Media Intake</h2>
    <div>Total: <code>{total}</code> | New: <code>{new_cnt}</code></div>
    <div>Newest: <code>{newest_path}</code></div>
    <div>Scanned at (UTC): {scanned_at}</div>
  </div>
"""
    except Exception:
        media_card = ""

    antigravity_card = ""
    try:
        if isinstance(agi, dict) and (agi.get("exists") is True or agi.get("latest_session_id") or agi.get("session_count", 0) > 0):
            sid = agi.get("latest_session_id") or "-"
            sc = agi.get("session_count", 0)
            new_flag = "yes" if agi.get("new_session_detected") else "no"
            scanned_at = agi.get("scanned_at", "")
            antigravity_card = f"""
  <div class="card">
    <h2>AntiGravity Intake</h2>
    <div>Latest Session: <code>{sid}</code> | Sessions: <code>{sc}</code> | New: <code>{new_flag}</code></div>
    <div>Scanned at (UTC): {scanned_at}</div>
    <details style="margin-top: 8px;">
      <summary>Latest summary (preview)</summary>
      <pre>{json.dumps(agi.get('latest'), ensure_ascii=False, indent=2)}</pre>
    </details>
  </div>
"""
    except Exception:
        antigravity_card = ""

    # 최근 실행 이력(최신 10개)을 HTML에 인라인
    try:
        history_items = read_jsonl_tail(REPORT_HISTORY, max_lines=10)
    except Exception:
        history_items = []

    history_rows = ""
    try:
        for item in reversed(history_items):
            ts_ = item.get("timestamp", "")
            act_ = item.get("action", "")
            st_ = item.get("status", "")
            err_ = item.get("error") or ""
            cls = "ok" if st_ == "executed" and not err_ else "fail"
            history_rows += f"<tr><td>{ts_}</td><td><span class='{cls}'>{st_}</span></td><td><code>{act_}</code></td><td>{(err_[:120] + ('…' if len(err_)>120 else '')) if err_ else '-'}</td></tr>"
    except Exception:
        history_rows = ""

    history_card = f"""
  <div class="card">
    <h2>History (Last 10)</h2>
    <table>
      <thead><tr><th>Time</th><th>Status</th><th>Action</th><th>Error</th></tr></thead>
      <tbody>
        {history_rows if history_rows else "<tr><td colspan='4'>-</td></tr>"}
      </tbody>
    </table>
  </div>
"""

    # Human Summary (압축 결과의 인간친화 요약)
    try:
        if isinstance(report.get("human_summary"), dict):
            human = report.get("human_summary") or {}
        else:
            # fallback: latest 파일을 읽는다
            p = ROOT / "outputs" / "self_compression_human_summary_latest.json"
            if p.exists():
                human = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        human = {}

    human_card = ""
    try:
        if isinstance(human, dict) and human:
            wish = human.get("one_line_wish") or human.get("one_line_next") or ""
            tags = human.get("tags") or {}
            human_card = f"""
  <div class="card">
    <h2>Human Summary</h2>
    <div>Wish: <code>{wish}</code></div>
    <details style="margin-top: 8px;">
      <summary>Tags</summary>
      <pre>{json.dumps(tags, ensure_ascii=False, indent=2)}</pre>
    </details>
  </div>
"""
    except Exception:
        human_card = ""

    v2_card = f"""
  <div class="card">
    <h2>Dashboard v2</h2>
    <div>Open: <code>outputs/bridge/status_dashboard_v2_static.html</code> (서버 없이 열림)</div>
  </div>
"""

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="2">
  <title>AGI Status Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 24px; }}
    .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; margin-bottom: 12px; }}
    h1 {{ margin-top: 0; }}
    .ok {{ color: #22c55e; }}
    .fail {{ color: #ef4444; }}
    code {{ background: #1f2937; padding: 2px 4px; border-radius: 4px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #1f2937; padding: 8px; text-align: left; }}
    th {{ color: #93c5fd; font-weight: 600; }}
  </style>
<body>
  <h1>AGI STATUS DASHBOARD</h1>
  <div class="card">
    <h2>Last Trigger</h2>
    <div>File: <code>{report.get('trigger_file','')}</code></div>
    <div>Action: <code>{report.get('action','')}</code></div>
    <div>Origin: <code>{report.get('origin','')}</code></div>
    <div>Time: {report.get('timestamp','')}</div>
  </div>
  <div class="card">
    <h2>Execution</h2>
    <div>Status: <span class="{ 'ok' if report.get('status')=='executed' else 'fail' }">{report.get('status','')}</span></div>
    <div>Error: {report.get('error','none')}</div>
  </div>
  <div class="card">
    <h2>Files</h2>
    <table>
      <thead><tr><th>File</th><th>Age</th><th>Size</th><th>mtime (UTC)</th></tr></thead>
      <tbody>
        {row("unconscious_heartbeat.json", hb)}
        {row("thought_stream_latest.json", ts)}
        {row("agi_internal_state.json", st)}
      </tbody>
    </table>
    <details style="margin-top: 8px;">
      <summary>Raw file snapshot</summary>
      <pre>{json.dumps(files, ensure_ascii=False, indent=2)}</pre>
    </details>
  </div>
  {history_card}
  {media_card}
  {antigravity_card}
  {human_card}
  {v2_card}
  <div class="card">
    <h2>Result</h2>
    <pre>{json.dumps(report.get('result_summary'), ensure_ascii=False, indent=2)}</pre>
  </div>
  <div class="card">
    <h2>Next</h2>
    <div>{report.get('next_action','')}</div>
  </div>
</body>
</html>
"""
    return html


def render_dashboard_v2_static(report: dict) -> str:
    """
    Status Dashboard v2 (Static)
    - 브라우저 보안(CORS) 문제를 피하기 위해 fetch를 쓰지 않는다.
    - 실행이 발생할 때마다 trigger_listener가 파일을 재생성한다.
    """
    files = report.get("files") or {}
    rs = report.get("result_summary") or {}
    human = report.get("human_summary") if isinstance(report.get("human_summary"), dict) else {}

    # Intake는 최신 고정 파일을 우선 사용(없으면 리포트 내부에서 추출)
    ag = {}
    md = {}
    try:
        p = ROOT / "outputs" / "antigravity_intake_latest.json"
        if p.exists():
            ag = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        ag = {}
    try:
        p = ROOT / "outputs" / "media_intake_latest.json"
        if p.exists():
            md = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        md = {}

    history = read_jsonl_tail(REPORT_HISTORY, max_lines=10)

    def _ok_fail(status: str, err: str | None) -> str:
        if status == "executed" and not err:
            return "ok"
        return "fail"

    def _fmt(obj) -> str:
        try:
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            return repr(obj)

    status = str(report.get("status") or "")
    err = report.get("error")
    cls = _ok_fail(status, err)
    wish = ""
    tags = {}
    try:
        if isinstance(human, dict):
            wish = str(human.get("one_line_wish") or "")
            tags = human.get("tags") or {}
    except Exception:
        wish = ""
        tags = {}

    rows = ""
    for item in reversed(history):
        st = str(item.get("status") or "")
        er = str(item.get("error") or "")
        cl = _ok_fail(st, er)
        rows += (
            "<tr>"
            f"<td>{item.get('timestamp','')}</td>"
            f"<td><span class='{cl}'>{st}</span></td>"
            f"<td><code>{item.get('action','')}</code></td>"
            f"<td>{(er[:120] + ('…' if len(er)>120 else '')) if er else '-'}</td>"
            "</tr>"
        )

    ag_sessions = ag.get("session_count")
    ag_latest = ag.get("latest_session_id") or (ag.get("latest") or {}).get("session_id")
    media_total = md.get("total")
    media_counts = md.get("counts") or {}

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="refresh" content="2">
  <title>AGI Status Dashboard v2 (Static)</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 24px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; }}
    h1 {{ margin-top: 0; }}
    h2 {{ margin: 0 0 10px 0; }}
    .ok {{ color: #22c55e; }}
    .fail {{ color: #ef4444; }}
    code {{ background: #1f2937; padding: 2px 4px; border-radius: 4px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #1f2937; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ color: #93c5fd; font-weight: 600; }}
    .mono {{ white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }}
  </style>
</head>
<body>
  <h1>AGI STATUS DASHBOARD v2 (Static)</h1>
  <div class="grid">
    <div class="card">
      <h2>Current</h2>
      <div>Status: <span class="{cls}">{status}</span></div>
      <div>Action: <code>{report.get('action','')}</code></div>
      <div>Origin: <code>{report.get('origin','')}</code></div>
      <div>Time: {report.get('timestamp','')}</div>
      <div>Duration: {report.get('duration_sec','')}</div>
      <div>Error: {err or 'none'}</div>
      <div>Steps: <span class="mono">{", ".join(report.get("steps") or [])}</span></div>
    </div>
    <div class="card">
      <h2>Human Summary</h2>
      <div>Wish: <code>{wish or '-'}</code></div>
      <details style="margin-top: 8px;">
        <summary>Tags</summary>
        <pre class="mono">{_fmt(tags)}</pre>
      </details>
    </div>
    <div class="card">
      <h2>History (Last 10)</h2>
      <table>
        <thead><tr><th>Time</th><th>Status</th><th>Action</th><th>Error</th></tr></thead>
        <tbody>
          {rows if rows else "<tr><td colspan='4'>-</td></tr>"}
        </tbody>
      </table>
    </div>
    <div class="card">
      <h2>Intake</h2>
      <div>AntiGravity sessions: <code>{ag_sessions if ag_sessions is not None else '-'}</code></div>
      <div>AntiGravity latest: <code>{ag_latest or '-'}</code></div>
      <div>Media total: <code>{media_total if media_total is not None else '-'}</code></div>
      <div>Media counts: video=<code>{media_counts.get('video','-')}</code> audio=<code>{media_counts.get('audio','-')}</code> image=<code>{media_counts.get('image','-')}</code></div>
    </div>
  </div>
  <div class="card" style="margin-top: 12px;">
    <h2>Files</h2>
    <pre class="mono">{_fmt(files)}</pre>
  </div>
  <div class="card" style="margin-top: 12px;">
    <h2>Result (raw)</h2>
    <pre class="mono">{_fmt(rs)}</pre>
  </div>
</body>
</html>
"""
    return html


def _generate_human_summary(report_obj: dict) -> dict:
    """
    실행 1회가 끝날 때마다 사람이 읽을 수 있는 요약을 파일로 고정한다.
    - outputs/self_compression_human_summary_latest.json
    - outputs/self_compression_human_summary_history.jsonl
    """
    try:
        from scripts.self_expansion.human_summary import HumanSummaryGenerator
        gen = HumanSummaryGenerator(ROOT)
        summary = gen.generate_from_trigger_report(report_obj)
        gen.save_summary(summary)
        # 결과를 리포트에도 붙여서(대시보드/관측) 바로 노출
        from dataclasses import asdict
        return asdict(summary)
    except Exception as e:
        return {"ok": False, "error": str(e)}


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
    line = f"[{timestamp}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def resolve_signal_path() -> Path:
    # On Windows, always use the workspace-local trigger path.
    # A POSIX-looking path like "/home/<user>/..." can map to "C:\\home\\..." and cause split-brain triggers.
    if os.name != "posix":
        return SIGNAL_PATH_LOCAL
    if SIGNAL_PATH_LINUX.exists():
        return SIGNAL_PATH_LINUX
    return SIGNAL_PATH_LOCAL


def load_trigger(path: Path) -> dict | None:
    try:
        # Windows PowerShell의 UTF-8 BOM(Set-Content -Encoding UTF8)로 생성된 파일도 허용.
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data
    except Exception as e:
        log(f"[warn] failed to parse trigger {path}: {e}")
        return None


# ----- 액션 실행자들 -----
def run_self_acquire():
    # 1) 기존 agi_core 기반 Self-Acquisition 루프 (부작용 가능: sandbox/파일 생성)
    # 기본 OFF. 필요 시 환경변수로만 활성화.
    core = {"skipped": True, "reason": "disabled_by_default"}
    if os.environ.get("AGI_ENABLE_AGI_CORE_SELF_ACQ", "").strip() in ("1", "true", "TRUE", "yes", "YES"):
        try:
            from agi_core.self_acquisition_loop import run_self_acquisition_cycle, SelfAcquisitionConfig
            core = run_self_acquisition_cycle(SelfAcquisitionConfig.default())
        except Exception as e:
            core = {"success": False, "error": str(e), "note": "agi_core self_acquisition unavailable"}

    # 2) 추가로 로컬 안전 소스 샘플링 (기존 self_expansion 스켈레톤)
    try:
        from scripts.self_expansion import SelfExpansionEngine
        engine = SelfExpansionEngine(ROOT)
        results = engine.run_acquisition(batch_size=3, max_time=3.0)
        sampled = [{"source": r.source, "meta": sanitize(r.meta)} for r in results]
    except Exception as e:
        sampled = [{"error": str(e)}]

    # 3) 미디어(영상/오디오/이미지) 인테이크: "자율 루프가 읽을 수 있는 형태"로 고정
    media_intake = {"skipped": True, "reason": "not_available"}
    try:
        from scripts.self_expansion.media_intake import run_media_intake
        media_intake = run_media_intake(ROOT)
        try:
            out = ROOT / "outputs" / "media_intake_latest.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(sanitize(media_intake), ensure_ascii=False, indent=2), encoding="utf-8")
            hist = ROOT / "outputs" / "media_intake_history.jsonl"
            with hist.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sanitize(media_intake), ensure_ascii=False) + "\n")
        except Exception:
            pass
    except Exception as e:
        media_intake = {"ok": False, "error": str(e)}

    # 4) AntiGravity 산출물 인테이크(read-only): 구현은 AntiGravity, 연결/보고는 루빛
    antigravity_intake = {"skipped": True, "reason": "not_available"}
    try:
        from scripts.self_expansion.antigravity_intake import run_antigravity_intake
        antigravity_intake = run_antigravity_intake(ROOT)
        try:
            out = ROOT / "outputs" / "antigravity_intake_latest.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(sanitize(antigravity_intake), ensure_ascii=False, indent=2), encoding="utf-8")
            hist = ROOT / "outputs" / "antigravity_intake_history.jsonl"
            with hist.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sanitize(antigravity_intake), ensure_ascii=False) + "\n")
        except Exception:
            pass
    except Exception as e:
        antigravity_intake = {"ok": False, "error": str(e)}

    # 5) Exploration Intake (Geo/Sound): 탐색 세션과 로컬 미디어
    exploration_intake = {"skipped": True, "reason": "not_available"}
    try:
        from scripts.self_expansion.exploration_intake import run_exploration_intake
        exploration_intake = run_exploration_intake(ROOT)
        try:
            out = ROOT / "outputs" / "exploration_intake_latest.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(sanitize(exploration_intake), ensure_ascii=False, indent=2), encoding="utf-8")
            hist = ROOT / "outputs" / "exploration_intake_history.jsonl"
            with hist.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sanitize(exploration_intake), ensure_ascii=False) + "\n")
        except Exception:
            pass
    except Exception as e:
        exploration_intake = {"ok": False, "error": str(e)}

    # 6) OBS Recode Intake (Behavior Data Index): 메타데이터 인덱스만 고정
    #    - Ubuntu(무의식)에서 Windows 외부 드라이브(E:\\)를 직접 읽을 수 없는 경우가 많으므로,
    #      이미 생성된 outputs/obs_recode_intake_latest.json 이 있으면 "그것을 읽기만" 한다(덮어쓰기 금지).
    obs_recode_intake = {"skipped": True, "reason": "not_available"}
    try:
        from scripts.self_expansion.obs_recode_intake import (
            load_latest_obs_recode_intake,
            run_obs_recode_intake,
        )
        cached = load_latest_obs_recode_intake(ROOT)
        if isinstance(cached, dict) and cached:
            obs_recode_intake = cached
        else:
            obs_recode_intake = run_obs_recode_intake(ROOT)
            try:
                out = ROOT / "outputs" / "obs_recode_intake_latest.json"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(sanitize(obs_recode_intake), ensure_ascii=False, indent=2), encoding="utf-8")
                hist = ROOT / "outputs" / "obs_recode_intake_history.jsonl"
                with hist.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(sanitize(obs_recode_intake), ensure_ascii=False) + "\n")
            except Exception:
                pass
    except Exception as e:
        obs_recode_intake = {"ok": False, "error": str(e)}

    # 6.5) Video Boundary Gate (Feeling → CPU Gate)
    #      - 동영상은 저비용(느낌) 스캔, 경계 유사 장면에서만 CPU 연산(해시/통계만).
    #      - 세션 파일이 생성되면 exploration_intake를 즉시 재스캔해 "이번 실행에서 관측"되게 한다.
    video_boundary_gate = {"skipped": True, "reason": "not_available"}
    try:
        from scripts.self_expansion.video_boundary_gate import run_video_boundary_gate

        video_boundary_gate = run_video_boundary_gate(ROOT)
        if isinstance(video_boundary_gate, dict) and video_boundary_gate.get("session_file"):
            try:
                from scripts.self_expansion.exploration_intake import run_exploration_intake

                exploration_intake = run_exploration_intake(ROOT)
                try:
                    out = ROOT / "outputs" / "exploration_intake_latest.json"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(sanitize(exploration_intake), ensure_ascii=False, indent=2), encoding="utf-8")
                    hist = ROOT / "outputs" / "exploration_intake_history.jsonl"
                    with hist.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(sanitize(exploration_intake), ensure_ascii=False) + "\n")
                except Exception:
                    pass
            except Exception:
                pass
    except Exception as e:
        video_boundary_gate = {"ok": False, "error": str(e)}

    # 7) Core Conversation Intake: 대화/사유 기록을 해마 친화 인덱스로 고정
    core_conversation_intake = {"skipped": True, "reason": "not_available"}
    try:
        from scripts.self_expansion.core_conversation_intake import run_core_conversation_intake
        core_conversation_intake = run_core_conversation_intake(ROOT)
        try:
            out = ROOT / "outputs" / "core_conversation_intake_latest.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(sanitize(core_conversation_intake), ensure_ascii=False, indent=2), encoding="utf-8")
            hist = ROOT / "outputs" / "core_conversation_intake_history.jsonl"
            with hist.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sanitize(core_conversation_intake), ensure_ascii=False) + "\n")
        except Exception:
            pass
    except Exception as e:
        core_conversation_intake = {"ok": False, "error": str(e)}

    # 7.5) Binoche_Observer Note Intake: 사용자 메모(신호)를 탐색 세션으로 물질화
    binoche_note_intake = {"skipped": True, "reason": "not_available"}
    try:
        from scripts.self_expansion.binoche_note_intake import run_binoche_note_intake

        binoche_note_intake = run_binoche_note_intake(ROOT)
        if isinstance(binoche_note_intake, dict) and binoche_note_intake.get("created_session_file"):
            try:
                from scripts.self_expansion.exploration_intake import run_exploration_intake

                exploration_intake = run_exploration_intake(ROOT)
                try:
                    out = ROOT / "outputs" / "exploration_intake_latest.json"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(sanitize(exploration_intake), ensure_ascii=False, indent=2), encoding="utf-8")
                    hist = ROOT / "outputs" / "exploration_intake_history.jsonl"
                    with hist.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(sanitize(exploration_intake), ensure_ascii=False) + "\n")
                except Exception:
                    pass
            except Exception:
                pass
    except Exception as e:
        binoche_note_intake = {"ok": False, "error": str(e)}

    # 8) Supervised Browser Exploration (Windows, optional):
    #    - 사용자가 arm(감독 모드)을 켠 경우에만 signals/body_task.json을 제안 생성한다.
    #    - 실제 실행은 scripts/windows/supervised_body_controller.py가 수행(별도 프로세스).
    supervised_browser = {"skipped": True, "reason": "not_armed_or_not_windows"}
    try:
        if os.name == "nt":
            script = ROOT / "scripts" / "windows" / "suggest_browser_exploration_task.py"
            if script.exists():
                subprocess.run(
                    [sys.executable, str(script)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                supervised_browser = {"ran": True, "script": str(script)}
            else:
                supervised_browser = {"skipped": True, "reason": "missing_script"}
    except Exception as e:
        supervised_browser = {"ok": False, "error": str(e)}

    # 9) Experience Acquisition (습득): 발생한 경험 신호를 탐색 세션으로 물질화(메타/요약만)
    experience_acquisition = {"skipped": True, "reason": "not_available"}
    try:
        from scripts.self_expansion.experience_acquisition import run_experience_acquisition

        experience_acquisition = run_experience_acquisition(ROOT)

        # 새 세션이 생성되면 exploration_intake를 즉시 재스캔하여 "이번 실행에서 바로 관측"되게 한다.
        if isinstance(experience_acquisition, dict) and experience_acquisition.get("created_session_file"):
            try:
                from scripts.self_expansion.exploration_intake import run_exploration_intake

                exploration_intake = run_exploration_intake(ROOT)
                try:
                    out = ROOT / "outputs" / "exploration_intake_latest.json"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(sanitize(exploration_intake), ensure_ascii=False, indent=2), encoding="utf-8")
                    hist = ROOT / "outputs" / "exploration_intake_history.jsonl"
                    with hist.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(sanitize(exploration_intake), ensure_ascii=False) + "\n")
                except Exception:
                    pass
            except Exception:
                pass
    except Exception as e:
        experience_acquisition = {"ok": False, "error": str(e)}

    # 10) YouTube Channel Boundary Intake: 채널 기반 경계 습득(브라우저 없이)
    youtube_channel_boundary_intake = {"skipped": True, "reason": "not_available"}
    try:
        from scripts.self_expansion.youtube_channel_boundary_intake import run_youtube_channel_boundary_intake

        youtube_channel_boundary_intake = run_youtube_channel_boundary_intake(ROOT)
        if (
            isinstance(youtube_channel_boundary_intake, dict)
            and int(youtube_channel_boundary_intake.get("processed_count") or 0) > 0
        ):
            try:
                from scripts.self_expansion.exploration_intake import run_exploration_intake

                exploration_intake = run_exploration_intake(ROOT)
                try:
                    out = ROOT / "outputs" / "exploration_intake_latest.json"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(sanitize(exploration_intake), ensure_ascii=False, indent=2), encoding="utf-8")
                    hist = ROOT / "outputs" / "exploration_intake_history.jsonl"
                    with hist.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(sanitize(exploration_intake), ensure_ascii=False) + "\n")
                except Exception:
                    pass
            except Exception:
                pass
    except Exception as e:
        youtube_channel_boundary_intake = {"ok": False, "error": str(e)}

    # 11) Boundary Induction: AGI가 스스로 'caution 경계 후보'를 세션으로 고정(메타만)
    boundary_induction = {"skipped": True, "reason": "not_available"}
    try:
        from scripts.self_expansion.boundary_induction import run_boundary_induction

        boundary_induction = run_boundary_induction(ROOT)
        if isinstance(boundary_induction, dict) and boundary_induction.get("created_session_file"):
            try:
                from scripts.self_expansion.exploration_intake import run_exploration_intake

                exploration_intake = run_exploration_intake(ROOT)
                try:
                    out = ROOT / "outputs" / "exploration_intake_latest.json"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(sanitize(exploration_intake), ensure_ascii=False, indent=2), encoding="utf-8")
                    hist = ROOT / "outputs" / "exploration_intake_history.jsonl"
                    with hist.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(sanitize(exploration_intake), ensure_ascii=False) + "\n")
                except Exception:
                    pass
            except Exception:
                pass
    except Exception as e:
        boundary_induction = {"ok": False, "error": str(e)}

    return {
        "agi_core_cycle": sanitize(core),
        "sampled": sampled,
        "media_intake": sanitize(media_intake),
        "antigravity_intake": sanitize(antigravity_intake),
        "exploration_intake": sanitize(exploration_intake),
        "obs_recode_intake": sanitize(obs_recode_intake),
        "video_boundary_gate": sanitize(video_boundary_gate),
        "core_conversation_intake": sanitize(core_conversation_intake),
        "binoche_note_intake": sanitize(binoche_note_intake),
        "supervised_browser": sanitize(supervised_browser),
        "experience_acquisition": sanitize(experience_acquisition),
        "youtube_channel_boundary_intake": sanitize(youtube_channel_boundary_intake),
        "boundary_induction": sanitize(boundary_induction),
    }


def run_binoche_note_ingest():
    """
    사용자 메모(signal)를 최소 비용으로 물질화한다.
    - 네트워크/브라우저/대규모 self_acquire는 하지 않음
    - signals/binoche_note.json → outputs/bridge/binoche_note_intake_latest.json (+ 세션 파일)
    - 세션이 생성되면 exploration_intake를 재스캔하여 바로 관측되게 한다.
    """
    binoche_note_intake = {"skipped": True, "reason": "not_available"}
    exploration_intake = {"skipped": True, "reason": "not_available"}

    try:
        from scripts.self_expansion.binoche_note_intake import run_binoche_note_intake

        binoche_note_intake = run_binoche_note_intake(ROOT)
        if isinstance(binoche_note_intake, dict) and binoche_note_intake.get("created_session_file"):
            try:
                from scripts.self_expansion.exploration_intake import run_exploration_intake

                exploration_intake = run_exploration_intake(ROOT)
                try:
                    out = ROOT / "outputs" / "exploration_intake_latest.json"
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_text(json.dumps(sanitize(exploration_intake), ensure_ascii=False, indent=2), encoding="utf-8")
                    hist = ROOT / "outputs" / "exploration_intake_history.jsonl"
                    with hist.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(sanitize(exploration_intake), ensure_ascii=False) + "\n")
                except Exception:
                    pass
            except Exception:
                pass
    except Exception as e:
        binoche_note_intake = {"ok": False, "error": str(e)}

    return {"binoche_note_intake": sanitize(binoche_note_intake), "exploration_intake": sanitize(exploration_intake)}


def run_self_compress():
    from scripts.self_expansion import SelfExpansionEngine
    engine = SelfExpansionEngine(ROOT)
    acquired = engine.run_acquisition(batch_size=3, max_time=2.0)
    return engine.run_compression(acquired)


def run_self_tool():
    from scripts.self_expansion import SelfExpansionEngine
    engine = SelfExpansionEngine(ROOT)
    return engine.run_tooling()


def run_full_self_expansion_cycle():
    steps: dict = {}
    steps["heartbeat_inspect"] = run_heartbeat_inspect()
    steps["self_acquire"] = run_self_acquire()
    # 경계(when/where/who) 요약: 탐색 세션에서 추출된 allow/deny/caution을 고정
    try:
        from scripts.self_expansion.boundary_map import build_boundary_map
        bm = build_boundary_map(ROOT)
        try:
            out = ROOT / "outputs" / "boundary_map_latest.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(sanitize(bm), ensure_ascii=False, indent=2), encoding="utf-8")
            hist = ROOT / "outputs" / "boundary_map_history.jsonl"
            with hist.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sanitize(bm), ensure_ascii=False) + "\n")
        except Exception:
            pass
        # report에는 전체 dump 대신 요약만 포함
        steps["boundary_map"] = {
            "ok": bool(bm.get("ok")),
            "stats": bm.get("stats"),
            "newest_rule": bm.get("newest_rule"),
        }
    except Exception as e:
        steps["boundary_map"] = {"ok": False, "error": str(e)}
    steps["process_grep"] = grep_processes()
    # 해마(episodic) 브리지: 탐색/경계/행동 인덱스를 사건 기억으로 고정
    try:
        from scripts.self_expansion.hippocampus_bridge import run_hippocampus_bridge
        hb = run_hippocampus_bridge(ROOT)
        try:
            out = ROOT / "outputs" / "hippocampus_bridge_latest.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(sanitize(hb), ensure_ascii=False, indent=2), encoding="utf-8")
            hist = ROOT / "outputs" / "hippocampus_bridge_history.jsonl"
            with hist.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sanitize(hb), ensure_ascii=False) + "\n")
        except Exception:
            pass
        steps["hippocampus_bridge"] = sanitize(hb)
    except Exception as e:
        steps["hippocampus_bridge"] = {"ok": False, "error": str(e)}
    # 존재 동역학(의식-무의식/배경자아/점-구-반지름/자연-감정-행동 루프) 모델을 파일로 고정
    try:
        from scripts.self_expansion.existence_dynamics_mapper import build_existence_dynamics_model, render_markdown
        edm = build_existence_dynamics_model(ROOT)
        try:
            out_json = ROOT / "outputs" / "existence_dynamics_model_latest.json"
            out_md = ROOT / "outputs" / "existence_dynamics_model_latest.md"
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(json.dumps(sanitize(edm), ensure_ascii=False, indent=2), encoding="utf-8")
            out_md.write_text(render_markdown(sanitize(edm)), encoding="utf-8")
            hist = ROOT / "outputs" / "existence_dynamics_model_history.jsonl"
            with hist.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sanitize(edm), ensure_ascii=False) + "\n")
        except Exception:
            pass
        steps["existence_dynamics_model"] = {
            "ok": bool(edm.get("ok")),
            "version": edm.get("version"),
            "current_proxies": edm.get("current_proxies"),
        }
    except Exception as e:
        steps["existence_dynamics_model"] = {"ok": False, "error": str(e)}
    # 리듬정보이론(RIT) 변수/출처/근사식 레지스트리를 파일로 고정
    try:
        from scripts.self_expansion.rhythm_information_theory_registry import build_rit_registry, render_markdown
        rit = build_rit_registry(ROOT)
        try:
            out_json = ROOT / "outputs" / "rit_registry_latest.json"
            out_md = ROOT / "outputs" / "rit_registry_latest.md"
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(json.dumps(sanitize(rit), ensure_ascii=False, indent=2), encoding="utf-8")
            out_md.write_text(render_markdown(sanitize(rit)), encoding="utf-8")
            hist = ROOT / "outputs" / "rit_registry_history.jsonl"
            with hist.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sanitize(rit), ensure_ascii=False) + "\n")
        except Exception:
            pass
        steps["rit_registry"] = {
            "ok": bool(rit.get("ok")),
            "version": rit.get("version"),
            "current_values": (rit.get("current_values") if isinstance(rit.get("current_values"), dict) else None),
        }
    except Exception as e:
        steps["rit_registry"] = {"ok": False, "error": str(e)}
    # Trinity 피드백(권장사항) 소비를 위한 파생 산출물 고정
    try:
        from scripts.derive_trinity_synthesis_latest import build_trinity_synthesis
        tri = build_trinity_synthesis(ROOT)
        steps["trinity_synthesis"] = {
            "ok": bool(tri.get("ok")),
            "version": tri.get("version"),
            "recommendations_count": len(tri.get("recommendations") or []) if isinstance(tri.get("recommendations"), list) else 0,
            "output": (tri.get("output") if isinstance(tri.get("output"), dict) else None),
        }
    except Exception as e:
        steps["trinity_synthesis"] = {"ok": False, "error": str(e)}
    try:
        from scripts.self_expansion import SelfExpansionEngine
        engine = SelfExpansionEngine(ROOT)
        acquired = engine.run_acquisition(batch_size=3, max_time=2.0)
        steps["self_compress"] = engine.run_compression(acquired)
        steps["self_tool"] = engine.run_tooling()
    except Exception as e:
        steps["self_expansion_error"] = str(e)

    # ledger tail 요약(파동/리듬 관측)
    steps["wave_tail"] = summarize_resonance_ledger_tail()
    # self-care summary (diagnostic가 기대하는 연결 포인트 보강)
    steps["selfcare_summary"] = maybe_run_selfcare_summary(min_interval_sec=15 * 60)
    # system integration diagnostic (워크스페이스 기존 진단기 연결)
    steps["system_integration_diagnostic"] = maybe_run_system_integration_diagnostic(min_interval_sec=15 * 60)
    # stream observer summary (워크스페이스 기존 요약기 연결)
    steps["stream_observer_summary"] = maybe_run_stream_observer_summary(min_interval_sec=15 * 60)
    # autopoietic analyzer (기존 워크스페이스 도구 연결, 저빈도 실행)
    steps["autopoietic_report"] = maybe_run_autopoietic_report(hours=24, min_interval_sec=600)
    # wave/particle unifier (중간 부하: 2시간 단위로만 실행)
    steps["wave_particle"] = maybe_run_wave_particle_unifier(lookback_hours=24, min_interval_sec=2 * 3600)
    # MD 파동 스윕(문서 역추적): 미연결 포인트를 저빈도로 고정
    steps["md_wave_sweep"] = maybe_run_md_wave_sweep(min_interval_sec=6 * 3600)
    # 에이전트 협업 브리프/워크오더 (저빈도)
    steps["coordination"] = maybe_run_coordination(min_interval_sec=30 * 60)
    return steps


def maybe_run_coordination(min_interval_sec: int = 30 * 60) -> dict:
    """
    외부 에이전트(Shion/세나)와 협업하기 위한 브리프/워크오더 파일을 고정한다.
    - 너무 자주 갱신하지 않도록 min_interval_sec로 제한
    """
    out = ROOT / "outputs" / "coordination" / "agent_brief_latest.md"
    now = time.time()
    try:
        last_ts = out.stat().st_mtime if out.exists() else None
    except Exception:
        last_ts = None
    if last_ts and (now - last_ts) < min_interval_sec:
        return {"skipped": True, "reason": "min_interval", "last_run_ts": float(last_ts), "out": file_info(out)}

    result: dict = {"skipped": False}
    try:
        from scripts.coordination.setup_agent_inboxes import ensure_dirs
        from scripts.coordination.generate_agent_brief import generate_brief
        ensure_dirs(ROOT)
        brief_path = generate_brief(ROOT)
        result["brief"] = file_info(Path(brief_path))
    except Exception as e:
        result["error"] = str(e)
        result["brief"] = file_info(out)
        return result

    # 워크오더는 "없으면 생성" (중복 난립 방지)
    try:
        wo_dir = ROOT / "outputs" / "coordination" / "work_orders"
        wo_dir.mkdir(parents=True, exist_ok=True)
        has_any = any(wo_dir.glob("*.md")) or any(wo_dir.glob("*.json"))
        if not has_any:
            from scripts.coordination.work_orders import default_work_orders
            result["work_orders_created"] = default_work_orders(ROOT)
        else:
            result["work_orders_created"] = []
    except Exception as e:
        result["work_orders_error"] = str(e)

    return result


def maybe_run_md_wave_sweep(min_interval_sec: int = 6 * 3600) -> dict:
    """
    문서(.md)에서 TODO/NEXT/GAP/미완/누락/연결/통합 등의 표식을 스캔해
    아직 연결되지 않은 포인트(문서→코드/산출물 링크 끊김 포함)를 파일로 고정한다.
    - 전체 .md는 매우 많아서, 기본은 증분 스캔 + 저빈도 실행으로 제한한다.
    """
    out_json = ROOT / "outputs" / "md_wave_sweep_latest.json"
    out_md = ROOT / "outputs" / "md_wave_sweep_latest.md"
    hist = ROOT / "outputs" / "md_wave_sweep_history.jsonl"
    state = ROOT / "outputs" / "sync_cache" / "md_wave_sweep_state.json"

    now = time.time()
    last = _load_json(state) or {}
    last_ts = float(last.get("last_run_ts") or 0)
    if last_ts and (now - last_ts) < min_interval_sec:
        return {"skipped": True, "reason": "min_interval", "last_run_ts": last_ts, "out": file_info(out_json)}

    try:
        from scripts.self_expansion.md_wave_sweeper import build_md_wave_sweep, render_markdown

        report = build_md_wave_sweep(ROOT, incremental=True)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(sanitize(report), ensure_ascii=False, indent=2), encoding="utf-8")
        out_md.write_text(render_markdown(sanitize(report)), encoding="utf-8")
        try:
            with hist.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sanitize(report), ensure_ascii=False) + "\n")
        except Exception:
            pass
        try:
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({"last_run_ts": now}, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        return {"ran": True, "out": file_info(out_json), "stats": report.get("stats")}
    except Exception as e:
        return {"ran": False, "error": str(e)}


def run_sync_cleanup():
    diagnosis = {
        "process_grep": grep_processes(),
        "files": {
            "heartbeat": file_info(ROOT / "outputs" / "unconscious_heartbeat.json"),
            "thought_stream": file_info(ROOT / "outputs" / "thought_stream_latest.json"),
            "internal_state": file_info(ROOT / "memory" / "agi_internal_state.json"),
            "trigger_report_latest": file_info(ROOT / "outputs" / "bridge" / "trigger_report_latest.json"),
        },
    }

    actions = []
    # 제한된 self-heal: (Linux) systemd user 서비스만 확인/재시작
    if os.name == "posix":
        actions.extend(ensure_linux_user_services(["agi-trigger-listener.service", "agi-lua-auto-trigger.service", "agi-trigger-dashboard.service"]))
    else:
        # Windows에서는 kill/restart를 강제하지 않고 진단만 고정
        actions.append({"action": "noop", "reason": "windows_diagnose_only"})

    return {"diagnosis": diagnosis, "recovery_actions": actions}


def run_heartbeat_inspect():
    hb_path = ROOT / "outputs" / "unconscious_heartbeat.json"
    state_path = ROOT / "memory" / "agi_internal_state.json"
    thought_path = ROOT / "outputs" / "thought_stream_latest.json"
    report = {
        "heartbeat": file_info(hb_path),
        "internal_state": file_info(state_path),
        "thought_stream": file_info(thought_path),
    }
    report["observables"] = {
        "system_integration_diagnostic_latest.json": file_info(ROOT / "outputs" / "system_integration_diagnostic_latest.json"),
        "stream_observer_summary_latest.json": file_info(ROOT / "outputs" / "stream_observer_summary_latest.json"),
        "monitoring_dashboard_latest.html": file_info(ROOT / "outputs" / "monitoring_dashboard_latest.html"),
        "monitoring_metrics_latest.json": file_info(ROOT / "outputs" / "monitoring_metrics_latest.json"),
        "autopoietic_loop_report_latest.json": file_info(ROOT / "outputs" / "autopoietic_loop_report_latest.json"),
        "obs_recode_intake_latest.json": file_info(ROOT / "outputs" / "obs_recode_intake_latest.json"),
        "exploration_intake_latest.json": file_info(ROOT / "outputs" / "exploration_intake_latest.json"),
        "boundary_map_latest.json": file_info(ROOT / "outputs" / "boundary_map_latest.json"),
        "hippocampus_bridge_latest.json": file_info(ROOT / "outputs" / "hippocampus_bridge_latest.json"),
        "core_conversation_intake_latest.json": file_info(ROOT / "outputs" / "core_conversation_intake_latest.json"),
        "existence_dynamics_model_latest.json": file_info(ROOT / "outputs" / "existence_dynamics_model_latest.json"),
        "rit_registry_latest.json": file_info(ROOT / "outputs" / "rit_registry_latest.json"),
        "md_wave_sweep_latest.json": file_info(ROOT / "outputs" / "md_wave_sweep_latest.json"),
        "trinity_synthesis_latest.json": file_info(ROOT / "outputs" / "trinity_synthesis_latest.json"),
        "constitution_review_latest.txt": file_info(ROOT / "outputs" / "bridge" / "constitution_review_latest.txt"),
        "red_line_monitor_latest.json": file_info(ROOT / "outputs" / "safety" / "red_line_monitor_latest.json"),
        "ethics_scorer_latest.json": file_info(ROOT / "outputs" / "ethics_scorer_latest.json"),
        "child_data_protector_latest.json": file_info(ROOT / "outputs" / "child_data_protector_latest.json"),
        "agent_inbox_status_latest.json": file_info(ROOT / "outputs" / "agent_inbox_status_latest.json"),
        "body_supervised_latest.json": file_info(ROOT / "outputs" / "body_supervised_latest.json"),
    }
    # 가능하면 핵심 heartbeat_count도 읽어서 고정
    try:
        if hb_path.exists():
            data = json.loads(hb_path.read_text(encoding="utf-8"))
            report["heartbeat_count"] = data.get("heartbeat_count")
            report["heartbeat_host"] = data.get("host")
            report["heartbeat_system"] = data.get("system")
    except Exception:
        pass
    return report


def summarize_resonance_ledger_tail(max_lines: int = 200) -> dict:
    candidates = [
        ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger_v2.jsonl",
        ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl",
        ROOT / "memory" / "resonance_ledger.jsonl",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if not path:
        return {"exists": False}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
        events = []
        for ln in lines:
            try:
                events.append(json.loads(ln))
            except Exception:
                continue
        counts: dict[str, int] = {}
        last_event = None
        last_warn_error = None
        last_rhythm_state = None
        # autopoietic phase tracker
        auto_tasks: dict[str, dict[str, dict[str, float | None]]] = {}
        last_task_id = None
        for ev in events:
            typ = str(ev.get("type") or "")
            et = str(ev.get("event") or (typ if typ else "unknown"))
            if et in ("warn", "error") or typ in ("warn", "error"):
                last_warn_error = ev
            counts[et] = counts.get(et, 0) + 1

            if typ == "thought":
                try:
                    content = ev.get("content") or {}
                    state = content.get("state") or {}
                    last_rhythm_state = {
                        "phase": state.get("phase"),
                        "status": state.get("status"),
                        "score": state.get("score"),
                        "background_self": state.get("background_self"),
                        "consciousness": state.get("consciousness"),
                        "unconscious": state.get("unconscious"),
                        "decision": content.get("decision"),
                        "summary": (content.get("summary") or "")[:280],
                    }
                except Exception:
                    pass

            if et == "autopoietic_phase":
                tid = str(ev.get("task_id") or "")
                ph = str(ev.get("phase") or "")
                stg = str(ev.get("stage") or "")
                if tid:
                    last_task_id = tid
                    auto_tasks.setdefault(tid, {}).setdefault(ph, {"start": None, "end": None, "duration_sec": None})
                    if stg in ("start", "end"):
                        auto_tasks[tid][ph][stg] = ev.get("timestamp")
                    if "duration_sec" in ev:
                        try:
                            auto_tasks[tid][ph]["duration_sec"] = float(ev.get("duration_sec"))
                        except Exception:
                            pass

            last_event = ev

        autopoietic = {"exists": False}
        if last_task_id and last_task_id in auto_tasks:
            phases = auto_tasks[last_task_id]
            done = [p for p, v in phases.items() if v.get("duration_sec") is not None]
            expected = ["folding", "unfolding", "integration", "symmetry"]
            missing = [p for p in expected if p not in done]
            autopoietic = {
                "exists": True,
                "task_id": last_task_id,
                "phases_done": done,
                "phases_missing": missing,
                "durations_sec": {p: phases[p].get("duration_sec") for p in phases},
            }
        return {
            "exists": True,
            "path": str(path),
            "tail_events": len(events),
            "event_counts": counts,
            "last_rhythm_state": sanitize(last_rhythm_state) if last_rhythm_state else None,
            "autopoietic": sanitize(autopoietic),
            "last_warn_error": sanitize(last_warn_error) if last_warn_error else None,
            "last_event": sanitize(last_event) if last_event else None,
        }
    except Exception as e:
        return {"exists": True, "path": str(path), "error": str(e)}


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def maybe_run_autopoietic_report(hours: int = 24, min_interval_sec: int = 600) -> dict:
    """
    기존 `fdo_agi_repo/analysis/analyze_autopoietic_loop.py`를 연결.
    - 너무 자주 돌지 않도록 min_interval_sec로 제한
    """
    out_json = ROOT / "outputs" / "autopoietic_loop_report_latest.json"
    out_md = ROOT / "outputs" / "autopoietic_loop_report_latest.md"
    state = ROOT / "outputs" / "sync_cache" / "autopoietic_report_state.json"

    now = time.time()
    last = _load_json(state) or {}
    last_ts = float(last.get("last_run_ts") or 0)
    if last_ts and (now - last_ts) < min_interval_sec:
        return {"skipped": True, "reason": "min_interval", "last_run_ts": last_ts, "out": file_info(out_json)}

    script = ROOT / "fdo_agi_repo" / "analysis" / "analyze_autopoietic_loop.py"
    if not script.exists():
        return {"skipped": True, "reason": "missing_script", "script": str(script)}

    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--hours", str(hours), "--out-md", str(out_md), "--out-json", str(out_json)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"last_run_ts": now, "rc": proc.returncode}, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = _load_json(out_json) or {}
        return {
            "ran": True,
            "rc": proc.returncode,
            "out": file_info(out_json),
            "summary_keys": list(summary.keys())[:30],
        }
    except Exception as e:
        return {"ran": False, "error": str(e)}


def maybe_run_wave_particle_unifier(lookback_hours: int = 24, min_interval_sec: int = 12 * 3600) -> dict:
    """
    워크스페이스의 wave/particle 이중성 분석기를 저빈도로 실행해
    '파동(패턴)+입자(사건)' 통합 요약을 리포트에 포함한다.
    """
    out_json = ROOT / "outputs" / "wave_particle_unified_latest.json"
    state = ROOT / "outputs" / "sync_cache" / "wave_particle_state.json"

    now = time.time()
    last = _load_json(state) or {}
    last_ts = float(last.get("last_run_ts") or 0)
    if last_ts and (now - last_ts) < min_interval_sec:
        return {"skipped": True, "reason": "min_interval", "last_run_ts": last_ts, "out": file_info(out_json)}

    try:
        # Import path: fdo_agi_repo is a sibling; add it explicitly
        sys.path.insert(0, str(ROOT / "fdo_agi_repo"))
        from copilot.wave_particle_unifier import WaveParticleUnifier

        unifier = WaveParticleUnifier(ROOT)
        result = unifier.achieve_self_understanding(lookback_hours=lookback_hours)

        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(sanitize(result), ensure_ascii=False, indent=2), encoding="utf-8")
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"last_run_ts": now, "lookback_hours": lookback_hours}, ensure_ascii=False, indent=2), encoding="utf-8")

        meta = result.get("meta") if isinstance(result, dict) else {}
        return {
            "ran": True,
            "out": file_info(out_json),
            "lookback_hours": lookback_hours,
            "meta": sanitize(meta),
        }
    except Exception as e:
        return {"ran": False, "error": str(e)}


def maybe_run_system_integration_diagnostic(min_interval_sec: int = 15 * 60) -> dict:
    out_json = ROOT / "outputs" / "system_integration_diagnostic_latest.json"
    out_md = ROOT / "outputs" / "system_integration_diagnostic_latest.md"
    state = ROOT / "outputs" / "sync_cache" / "system_integration_diag_state.json"

    now = time.time()
    last = _load_json(state) or {}
    last_ts = float(last.get("last_run_ts") or 0)
    if last_ts and (now - last_ts) < min_interval_sec:
        return {"skipped": True, "reason": "min_interval", "last_run_ts": last_ts, "out": file_info(out_json)}

    script = ROOT / "scripts" / "system_integration_diagnostic.py"
    if not script.exists():
        return {"skipped": True, "reason": "missing_script", "script": str(script)}

    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"last_run_ts": now, "rc": proc.returncode}, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = _load_json(out_json) or {}
        return {
            "ran": True,
            "rc": proc.returncode,
            "out": file_info(out_json),
            "recommendations": sanitize(summary.get("recommendations")) if isinstance(summary, dict) else None,
            "stderr_tail": (proc.stderr or "")[-800:],
        }
    except Exception as e:
        return {"ran": False, "error": str(e)}


def maybe_run_stream_observer_summary(min_interval_sec: int = 15 * 60) -> dict:
    out_json = ROOT / "outputs" / "stream_observer_summary_latest.json"
    out_md = ROOT / "outputs" / "stream_observer_summary_latest.md"
    state = ROOT / "outputs" / "sync_cache" / "stream_observer_state.json"

    now = time.time()
    last = _load_json(state) or {}
    last_ts = float(last.get("last_run_ts") or 0)
    if last_ts and (now - last_ts) < min_interval_sec:
        return {"skipped": True, "reason": "min_interval", "last_run_ts": last_ts, "out": file_info(out_json)}

    script = ROOT / "scripts" / "summarize_stream_observer.py"
    if not script.exists():
        return {"skipped": True, "reason": "missing_script", "script": str(script)}

    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--out-json", str(out_json), "--out-md", str(out_md)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"last_run_ts": now, "rc": proc.returncode}, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = _load_json(out_json) or {}
        return {
            "ran": True,
            "rc": proc.returncode,
            "out": file_info(out_json),
            "summary_keys": list(summary.keys())[:30] if isinstance(summary, dict) else None,
            "stderr_tail": (proc.stderr or "")[-800:],
        }
    except Exception as e:
        return {"ran": False, "error": str(e)}


def maybe_run_selfcare_summary(min_interval_sec: int = 15 * 60) -> dict:
    out_json = ROOT / "outputs" / "selfcare_summary_latest.json"
    state = ROOT / "outputs" / "sync_cache" / "selfcare_state.json"

    now = time.time()
    last = _load_json(state) or {}
    last_ts = float(last.get("last_run_ts") or 0)
    if last_ts and (now - last_ts) < min_interval_sec:
        return {"skipped": True, "reason": "min_interval", "last_run_ts": last_ts, "out": file_info(out_json)}

    script = ROOT / "scripts" / "generate_selfcare_summary.py"
    if not script.exists():
        return {"skipped": True, "reason": "missing_script", "script": str(script)}

    try:
        proc = subprocess.run(
            [sys.executable, str(script), "--workspace", str(ROOT), "--hours", "24", "--out", str(out_json)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"last_run_ts": now, "rc": proc.returncode}, ensure_ascii=False, indent=2), encoding="utf-8")
        summary = _load_json(out_json) or {}
        return {
            "ran": True,
            "rc": proc.returncode,
            "out": file_info(out_json),
            "has_quantum_flow": "quantum_flow" in summary,
            "stderr_tail": (proc.stderr or "")[-800:],
        }
    except Exception as e:
        return {"ran": False, "error": str(e)}


def ensure_linux_user_services(services: list[str]) -> list[dict]:
    actions: list[dict] = []
    for svc in services:
        try:
            chk = subprocess.run(
                ["bash", "-lc", f"systemctl --user is-active {svc} || true"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            status = (chk.stdout or "").strip()
            if status != "active":
                subprocess.run(
                    ["bash", "-lc", f"systemctl --user restart {svc} || true"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                actions.append({"action": "systemctl_restart", "service": svc, "prev_status": status})
            else:
                actions.append({"action": "systemctl_ok", "service": svc})
        except Exception as e:
            actions.append({"action": "systemctl_error", "service": svc, "error": str(e)})
    return actions


def grep_processes() -> dict:
    # Linux: ps aux, Windows: tasklist (best-effort)
    query = r"agi|heartbeat|bridge|sync|trigger_listener|rhythm"
    if os.name == "posix":
        cmd = f"ps aux | grep -E \"{query}\" | grep -v grep"
        out = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True)
        return {"platform": "posix", "cmd": cmd, "stdout": out.stdout.strip(), "stderr": out.stderr.strip()}
    creationflags = 0
    if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags = subprocess.CREATE_NO_WINDOW
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"Get-Process | Where-Object {{$_.Path -match 'python' -or $_.ProcessName -match 'python'}} | Select-Object -First 50 | Format-Table -AutoSize | Out-String"],
        capture_output=True,
        text=True,
        creationflags=creationflags,
    )
    return {"platform": "windows", "cmd": "Get-Process python*", "stdout": out.stdout.strip(), "stderr": out.stderr.strip()}


ACTION_MAP = {
    "self_acquire": run_self_acquire,
    "self_compress": run_self_compress,
    "self_tool": run_self_tool,
    "sync_clean": run_sync_cleanup,
    "heartbeat_check": run_heartbeat_inspect,
    "binoche_note": run_binoche_note_ingest,
    "full_cycle": run_full_self_expansion_cycle,
    # Idle is a first-class "normal survival state": no execution steps, just acknowledge.
    "idle": lambda: {"idle": True},
}

def run_auto_policy_when_idle():
    """트리거가 없을 때 auto_policy를 실행해 트리거를 쓴다."""
    auto_policy_script = ROOT / "scripts" / "self_expansion" / "auto_policy.py"
    if not auto_policy_script.exists():
        return
    creationflags = 0
    if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        creationflags = subprocess.CREATE_NO_WINDOW
    subprocess.run(
        [sys.executable, str(auto_policy_script)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        creationflags=creationflags,
    )


def handle_trigger(trigger_path: Path):
    trigger = load_trigger(trigger_path)
    if not trigger:
        try:
            trigger_path.unlink(missing_ok=True)
        except Exception:
            pass
        return

    action = trigger.get("action")
    params = trigger.get("params") or {}
    origin = trigger.get("origin") or ""
    trigger_ts = trigger.get("timestamp")
    fn = ACTION_MAP.get(action)
    if not fn:
        log(f"[warn] unknown action: {action}")
        try:
            trigger_path.unlink(missing_ok=True)
        except Exception:
            pass
        return

    steps = []
    error = None
    result = None
    started_ts = time.time()
    try:
        # Pre-action safety gate (최소 구현)
        # - 마지막 종합 안전 판정이 BLOCK이면, 자동 실행은 heartbeat_check만 허용한다.
        # - 실행 전에 윤리 스코어러를 한 번 돌려 BLOCK이면 중단한다.
        constitution_status = _load_constitution_status()
        if constitution_status == "BLOCK" and action != "heartbeat_check":
            steps.append("pre_action_gate")
            error = "blocked_by_constitution: BLOCK"
            result = {"blocked": True, "by": "constitution_review", "status": constitution_status}
        else:
            pre = _run_ethics_precheck(action=str(action or ""), origin=str(origin or ""))
            if pre.get("ok") is False and action != "heartbeat_check":
                steps.append("pre_action_gate")
                error = f"blocked_by_ethics: {pre.get('recommendation') or 'BLOCK'}"
                result = {"blocked": True, "by": "ethics_scorer", "precheck": pre}
            else:
                result = fn()

        if action == "full_cycle" and isinstance(result, dict) and result:
            steps.extend(list(result.keys()))
        else:
            if not steps:
                steps.append(action)
        # 결과를 상태 파일에 기록 (기계용)
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        safe_result = sanitize(result)
        STATE_PATH.write_text(json.dumps({"action": action, "result": safe_result}, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"[info] action={action} done")
        try:
            write_life_state(
                state="ALIVE_ACTIVE",
                reason=f"executed action={action}",
                trigger_present=False,
                last_action=str(action or ""),
            )
        except Exception:
            pass

        # Auto-call human_summary.py after full_cycle (루빛 워크오더 - 실패해도 full_cycle 실패로 만들지 않음)
        if action == "full_cycle":
            try:
                human_summary_script = ROOT / "scripts" / "self_expansion" / "human_summary.py"
                if human_summary_script.exists():
                    subprocess.run(
                        [sys.executable, str(human_summary_script)],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        timeout=30
                    )
                    log(f"[info] human_summary.py auto-called after full_cycle")
                else:
                    log(f"[warn] human_summary.py not found: {human_summary_script}")
            except Exception as hs_error:
                # 실패해도 full_cycle 실패로 만들지 않음 - 리포트에만 기록
                log(f"[warn] human_summary.py failed (non-critical): {hs_error}")

            # Auto-call auto_constitution_review.py after full_cycle (루빛 워크오더 v2 - 종합 안전 리포트)
            try:
                constitution_review_script = ROOT / "scripts" / "auto_constitution_review.py"
                if constitution_review_script.exists():
                    subprocess.run(
                        [sys.executable, str(constitution_review_script)],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        timeout=30
                    )
                    log(f"[info] auto_constitution_review.py auto-called after full_cycle")
                else:
                    log(f"[warn] auto_constitution_review.py not found: {constitution_review_script}")
            except Exception as cr_error:
                # 실패해도 full_cycle 실패로 만들지 않음 - 리포트에만 기록
                log(f"[warn] auto_constitution_review.py failed (non-critical): {cr_error}")

    except Exception as e:
        error = str(e)
        log(f"[error] action={action} failed: {e}")
    duration_sec = max(0.0, time.time() - started_ts)

    try:
        trigger_path.unlink(missing_ok=True)
    except Exception as e:
        log(f"[warn] failed to remove trigger: {e}")

    # 사람용 리포트 기록
    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        if error and str(error).startswith("blocked_by_"):
            status = "blocked"
        else:
            status = "executed" if error is None else "failed"
        files_snapshot = {
            "unconscious_heartbeat.json": file_info(ROOT / "outputs" / "unconscious_heartbeat.json"),
            "thought_stream_latest.json": file_info(ROOT / "outputs" / "thought_stream_latest.json"),
            "agi_internal_state.json": file_info(ROOT / "memory" / "agi_internal_state.json"),
        }
        report_obj = {
            "trigger_file": str(trigger_path),
            "action": action,
            "params": sanitize(params),
            "origin": origin,
            "trigger_timestamp": trigger_ts,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "duration_sec": duration_sec,
            "steps": steps if steps else [action] if action else [],
            "result_summary": sanitize(result),
            "files": files_snapshot,
            "error": error,
            "next_action": "halt_and_review" if status == "blocked" else ("idle" if error is None else "retry_or_investigate"),
        }
        # Human summary를 먼저 생성해서 report_obj에 포함(대시보드/리포트 동기화)
        report_obj["human_summary"] = sanitize(_generate_human_summary(report_obj))
        REPORT_JSON.write_text(json.dumps(report_obj, ensure_ascii=False, indent=2), encoding="utf-8")
        # history append
        _rotate_history_if_needed()
        with open(REPORT_HISTORY, "a", encoding="utf-8") as hf:
            hf.write(json.dumps(report_obj, ensure_ascii=False) + "\n")
        # 텍스트 요약
        safe_params = report_obj.get("params")
        safe_result = report_obj.get("result_summary")
        lines = [
            f"Trigger: {trigger_path.name}",
            f"Action: {action}",
            f"Origin: {origin}",
            f"Params: {json.dumps(safe_params, ensure_ascii=False)}",
            f"Status: {status}",
            f"Time: {report_obj['timestamp']}",
            f"Steps: {', '.join(report_obj['steps']) if report_obj['steps'] else '-'}",
            f"Error: {error or 'none'}",
            f"Next: {report_obj['next_action']}",
            "Files:",
            json.dumps(files_snapshot, ensure_ascii=False, indent=2),
            "Result:",
            json.dumps(safe_result, ensure_ascii=False, indent=2) if safe_result is not None else "None",
        ]
        # TXT/HTML은 '관측 편의'라서 실패해도 전체 루프를 막지 않도록 best-effort로 처리한다.
        try:
            REPORT_TXT.write_text("\n".join(lines), encoding="utf-8")
        except Exception as wtxt:
            log(f"[warn] failed to write trigger_report_latest.txt: {wtxt}")

        try:
            # HTML 대시보드
            REPORT_HTML.write_text(render_dashboard(report_obj), encoding="utf-8")
        except Exception as whtml:
            log(f"[warn] failed to write status_dashboard_latest.html: {whtml}")

        try:
            # v2 (static): 서버 없이도 열리는 대시보드
            REPORT_V2_STATIC.write_text(render_dashboard_v2_static(report_obj), encoding="utf-8")
        except Exception as whtml2:
            log(f"[warn] failed to write status_dashboard_v2_static.html: {whtml2}")

        # Auto-call: constitution review (사람이 읽는 텍스트/JSON 리포트)
        try:
            constitution_review_script = ROOT / "scripts" / "auto_constitution_review.py"
            if constitution_review_script.exists():
                subprocess.run(
                    [sys.executable, str(constitution_review_script)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=30,
                )
                log("[info] auto_constitution_review.py auto-called")
            else:
                log(f"[warn] auto_constitution_review.py not found: {constitution_review_script}")
        except Exception as cr_error:
            log(f"[warn] auto_constitution_review.py failed (non-critical): {cr_error}")

        # NOTE: 사람용 요약/메시지는 "관측/항상성 업데이트" 이후에 생성한다(아래).

        # Auto-call: drive state update (욕망/호기심/지루함을 관측 가능하게 고정)
        try:
            drive_updater = ROOT / "scripts" / "drive_state_update.py"
            if drive_updater.exists():
                subprocess.run(
                    [sys.executable, str(drive_updater)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                log("[info] drive_state_update.py auto-called")
            else:
                log(f"[warn] drive_state_update.py not found: {drive_updater}")
        except Exception as du_error:
            log(f"[warn] drive_state_update.py failed (non-critical): {du_error}")

        # Auto-call: natural rhythm clock + drift monitor (자연 리듬 동기화 관측)
        try:
            clock_script = ROOT / "scripts" / "natural_rhythm_clock.py"
            if clock_script.exists():
                subprocess.run(
                    [sys.executable, str(clock_script)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                log("[info] natural_rhythm_clock.py auto-called")
        except Exception as nrc_error:
            log(f"[warn] natural_rhythm_clock.py failed (non-critical): {nrc_error}")

        try:
            drift_script = ROOT / "scripts" / "natural_rhythm_monitor.py"
            if drift_script.exists():
                subprocess.run(
                    [sys.executable, str(drift_script)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                log("[info] natural_rhythm_monitor.py auto-called")
        except Exception as nrm_error:
            log(f"[warn] natural_rhythm_monitor.py failed (non-critical): {nrm_error}")

        # Auto-call: ATP update + rest gate (에너지/폭주 감지 → 휴식 창)
        try:
            atp_script = ROOT / "scripts" / "atp_update.py"
            if atp_script.exists():
                subprocess.run(
                    [sys.executable, str(atp_script)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                log("[info] atp_update.py auto-called")
        except Exception as atp_error:
            log(f"[warn] atp_update.py failed (non-critical): {atp_error}")

        try:
            rest_script = ROOT / "scripts" / "rest_gate.py"
            if rest_script.exists():
                subprocess.run(
                    [sys.executable, str(rest_script)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                log("[info] rest_gate.py auto-called")
        except Exception as rg_error:
            log(f"[warn] rest_gate.py failed (non-critical): {rg_error}")

        # Auto-call: rhythm pain signal (리듬 저항/불일치를 '통증'으로 고정)
        try:
            pain_script = ROOT / "scripts" / "rhythm_pain_signal.py"
            if pain_script.exists():
                subprocess.run(
                    [sys.executable, str(pain_script)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                log("[info] rhythm_pain_signal.py auto-called")
            else:
                log(f"[warn] rhythm_pain_signal.py not found: {pain_script}")
        except Exception as ps_error:
            log(f"[warn] rhythm_pain_signal.py failed (non-critical): {ps_error}")

        # Auto-call: Digital Twin / Quantum Digital Twin (관측 고정 + 후보 확률만)
        # - 실행을 하지 않고 "상태"를 고정하는 레이어라서, 호출해도 부작용이 거의 없고
        #   내부적으로 min-interval(기본 60s)로 과도 실행을 방지한다.
        try:
            twin_script = ROOT / "scripts" / "digital_twin_update.py"
            if twin_script.exists():
                subprocess.run(
                    [sys.executable, str(twin_script)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                log("[info] digital_twin_update.py auto-called")
            else:
                log(f"[warn] digital_twin_update.py not found: {twin_script}")
        except Exception as dt_error:
            log(f"[warn] digital_twin_update.py failed (non-critical): {dt_error}")

        # Auto-call: glymphatic metrics (림프/정화 관측 요약)
        # - outputs/glymphatic_metrics_latest.json을 최신화하여 사람용 요약에서 stale로 보이지 않게 한다.
        # - best-effort + 짧은 timeout (ledger 집계만; 네트워크 없음)
        # - 실행 비용을 줄이기 위해 full_cycle/heartbeat_check에서만 갱신한다.
        try:
            if action in ("full_cycle", "heartbeat_check"):
                glymph_script = ROOT / "scripts" / "aggregate_glymphatic_metrics.py"
                if glymph_script.exists():
                    subprocess.run(
                        [
                            sys.executable,
                            str(glymph_script),
                            "--hours",
                            "24",
                            "--summary-path",
                            str(ROOT / "outputs" / "glymphatic_metrics_latest.json"),
                        ],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        timeout=10,
                    )
                    log("[info] aggregate_glymphatic_metrics.py auto-called")
                else:
                    log(f"[warn] aggregate_glymphatic_metrics.py not found: {glymph_script}")
        except Exception as gm_error:
            log(f"[warn] aggregate_glymphatic_metrics.py failed (non-critical): {gm_error}")

        # Auto-call: human ops summary (비프로그래머용 1페이지 요약)
        try:
            ops_summary_script = ROOT / "scripts" / "human_ops_summary.py"
            if ops_summary_script.exists():
                subprocess.run(
                    [sys.executable, str(ops_summary_script)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=30,
                )
                log("[info] human_ops_summary.py auto-called")
            else:
                log(f"[warn] human_ops_summary.py not found: {ops_summary_script}")
        except Exception as hs_error:
            log(f"[warn] human_ops_summary.py failed (non-critical): {hs_error}")

        # Auto-call: AGI -> user message (file-based, no popups)
        try:
            msg_script = ROOT / "scripts" / "agi_message_reporter.py"
            if msg_script.exists():
                subprocess.run(
                    [sys.executable, str(msg_script)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                log("[info] agi_message_reporter.py auto-called")
            else:
                log(f"[warn] agi_message_reporter.py not found: {msg_script}")
        except Exception as ms_error:
            log(f"[warn] agi_message_reporter.py failed (non-critical): {ms_error}")

        # Auto-call: monitoring metrics collector (네트워크 없이 파일 상태만)
        try:
            if action in ("full_cycle", "heartbeat_check"):
                metrics_collector = ROOT / "monitoring" / "metrics_collector.py"
                if metrics_collector.exists():
                    subprocess.run(
                        [sys.executable, str(metrics_collector)],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        timeout=30,
                    )
                    log("[info] monitoring/metrics_collector.py auto-called")
                else:
                    log(f"[warn] metrics_collector.py not found: {metrics_collector}")
        except Exception as mc_error:
            log(f"[warn] metrics_collector.py failed (non-critical): {mc_error}")

        # Auto-call: red line monitor (비파괴, 관측용)
        try:
            if action in ("full_cycle", "heartbeat_check"):
                red_line_monitor = ROOT / "safety" / "red_line_monitor.py"
                if red_line_monitor.exists():
                    subprocess.run(
                        [sys.executable, str(red_line_monitor)],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        timeout=30,
                    )
                    log("[info] safety/red_line_monitor.py auto-called")
                else:
                    log(f"[warn] safety/red_line_monitor.py not found: {red_line_monitor}")
        except Exception as rlm_error:
            log(f"[warn] safety/red_line_monitor.py failed (non-critical): {rlm_error}")

        # Auto-call: agent inbox status (도착/완료 산출물 관측)
        try:
            if action in ("full_cycle", "heartbeat_check"):
                inbox_status = ROOT / "scripts" / "agent_inbox_status.py"
                if inbox_status.exists():
                    subprocess.run(
                        [sys.executable, str(inbox_status)],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        timeout=30,
                    )
                    log("[info] scripts/agent_inbox_status.py auto-called")
                else:
                    log(f"[warn] agent_inbox_status.py not found: {inbox_status}")
        except Exception as ais_error:
            log(f"[warn] agent_inbox_status.py failed (non-critical): {ais_error}")

        # Auto-call: ops snapshot publish (Shion/세나가 같은 기준으로 현재 상태를 '보기' 위한 스냅샷)
        try:
            if action in ("full_cycle", "heartbeat_check"):
                publisher = ROOT / "scripts" / "coordination" / "publish_ops_snapshot.py"
                if publisher.exists():
                    subprocess.run(
                        [sys.executable, str(publisher)],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        timeout=30,
                    )
                    log("[info] publish_ops_snapshot.py auto-called")
                else:
                    log(f"[warn] publish_ops_snapshot.py not found: {publisher}")
        except Exception as pos_error:
            log(f"[warn] publish_ops_snapshot.py failed (non-critical): {pos_error}")

        # Auto-call: ethics scorer + child data protector (비파괴, 관측/리포트용)
        try:
            if action in ("full_cycle", "self_compress", "heartbeat_check", "sync_clean"):
                ethics_scorer = ROOT / "rune" / "ethics_scorer.py"
                if ethics_scorer.exists():
                    desc = f"{action} origin={origin} steps={','.join(steps) if steps else ''}"
                    subprocess.run(
                        [sys.executable, str(ethics_scorer), desc],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        timeout=30,
                    )
                    log("[info] rune/ethics_scorer.py auto-called")
                else:
                    log(f"[warn] rune/ethics_scorer.py not found: {ethics_scorer}")
        except Exception as es_error:
            log(f"[warn] rune/ethics_scorer.py failed (non-critical): {es_error}")

        try:
            if action in ("full_cycle", "self_compress", "heartbeat_check", "sync_clean"):
                child_protector = ROOT / "safety" / "child_data_protector.py"
                target = ROOT / "outputs" / "bridge" / "trigger_report_latest.json"
                if child_protector.exists():
                    subprocess.run(
                        [sys.executable, str(child_protector), str(target)],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        timeout=30,
                    )
                    log("[info] safety/child_data_protector.py auto-called")
                else:
                    log(f"[warn] safety/child_data_protector.py not found: {child_protector}")
        except Exception as cdp_error:
            log(f"[warn] safety/child_data_protector.py failed (non-critical): {cdp_error}")

        # 최소 heartbeat 갱신(로컬 관측용)
        try:
            update_unconscious_heartbeat(
                action=str(report_obj.get("action") or ""),
                status=str(report_obj.get("status") or ""),
                error=report_obj.get("error"),
            )
        except Exception:
            pass

        # Resonance ledger에도 최소 이벤트로 기록 (관측/파동-입자 분석 연결)
        append_trigger_event_to_ledger(report_obj)
    except Exception as e:
        log(f"[warn] failed to write report: {e}")


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--once",
        action="store_true",
        help="한 번만 틱 실행 후 종료 (스케줄러/워치독 호환)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="N초 동안만 실행 후 종료 (기본: 무한 루프)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="폴링 간격(초)",
    )
    parser.add_argument(
        "--auto-policy",
        action="store_true",
        help="트리거가 없을 때 auto_policy를 실행 (환경변수 AGI_LISTENER_ENABLE_AUTO_POLICY=1과 동일)",
    )
    parser.add_argument(
        "--action",
        type=str,
        default="",
        help="즉시 실행할 액션을 지정 (예: self_acquire). 트리거 파일 생성 없이 바로 처리.",
    )
    parser.add_argument(
        "--reason",
        type=str,
        default="",
        help="--action과 함께 기록할 간단한 reason (민감정보 금지)",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="표준 출력 억제(스케줄러용)",
    )
    args = parser.parse_args()

    if args.silent:
        try:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")  # type: ignore
            sys.stderr = open(os.devnull, "w", encoding="utf-8")  # type: ignore
        except Exception:
            pass

    # Single-instance guard (best effort).
    # - --action: 다른 리스너가 이미 있으면 트리거만 쓰고(가능하면) 즉시 종료한다.
    # - 그 외: 중복 리스너는 조용히 종료한다.
    locked = _acquire_single_instance_lock()
    if locked:
        atexit.register(_release_single_instance_lock)

    # Compatibility: 일부 스케줄러는 trigger_listener.py --once 를 "1틱 실행"으로 호출한다.
    # 기존 구현이 무한 루프로 굳어져 프로세스가 누적되는 문제가 있었으므로,
    # --once/--timeout을 엄격하게 준수한다.

    # If --action is provided, execute immediately (no long loop).
    if args.action:
        try:
            trigger_path = resolve_signal_path()
            # Trigger 파일이 이미 존재하면 덮어쓰지 않는다(경계).
            if not trigger_path.exists():
                payload = {
                    "action": str(args.action).strip(),
                    "params": {"reason": str(args.reason).strip()} if str(args.reason).strip() else {},
                    "timestamp": float(time.time()),
                    "origin": "cli",
                }
                trigger_path.parent.mkdir(parents=True, exist_ok=True)
                tmp = trigger_path.with_suffix(".tmp")
                tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(tmp, trigger_path)
            # 다른 리스너가 이미 존재한다면, 직접 처리하지 않고(중복 방지) 트리거만 남기고 끝낸다.
            if locked:
                handle_trigger(trigger_path)
        except Exception as e:
            try:
                log(f"[warn] --action failed: {type(e).__name__}: {e}")
            except Exception:
                pass
        return
    else:
        if not locked:
            try:
                log("[info] single-instance lock not acquired; exiting (another listener active)")
            except Exception:
                pass
            return

    # NOTE:
    # - auto_policy는 Windows Task Scheduler(AGI_LuaAutoPolicy)에서 주기적으로 실행된다.
    # - listener 내부에서 auto_policy를 켜면(--auto-policy / env var) 폴링 간격만큼 정책이 호출되어
    #   트리거 폭주로 관측될 수 있다.
    # - 따라서 listener는 명시적 플래그(--auto-policy)가 있을 때만 정책을 호출한다.
    enable_auto_policy = bool(args.auto_policy)

    start = time.time()
    try:
        log("[info] trigger_listener main loop started")
    except Exception:
        pass
    while True:
        try:
            # Always allow lightweight human→AGI message ingestion (even when auto-policy is enabled).
            _tick_binoche_dropbox()

            path = resolve_signal_path()
            if path.exists():
                handle_trigger(path)
            else:
                if enable_auto_policy:
                    run_auto_policy_when_idle()
                else:
                    idle_tick()
        except Exception as e:
            # daemon 모드는 "죽지 않는 것"이 최우선.
            # 실패해도 다음 루프로 이어가며, 반복 오류는 sleep으로 완화한다.
            try:
                log(f"[warn] loop error (non-fatal): {type(e).__name__}: {e}")
            except Exception:
                pass
            time.sleep(1.0)

        if args.once:
            break
        if args.timeout is not None and (time.time() - start) >= float(args.timeout):
            break
        time.sleep(max(0.25, float(args.interval)))


def append_trigger_event_to_ledger(report_obj: dict) -> None:
    """
    trigger 실행을 resonance ledger에 최소한의 "입자 이벤트"로 추가한다.
    - 파동/입자 분석기가 이 이벤트를 잡아낼 수 있게 한다.
    - 민감 정보/대용량 dump는 하지 않는다.
    """
    candidates = [
        ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger_v2.jsonl",
        ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl",
        ROOT / "memory" / "resonance_ledger.jsonl",
    ]
    ledger = next((p for p in candidates if p.exists()), candidates[0])
    try:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        action = str(report_obj.get("action") or "")
        status = str(report_obj.get("status") or "")
        origin = str(report_obj.get("origin") or "")
        duration = report_obj.get("duration_sec")
        error = report_obj.get("error")

        # Particle detector expects an importance-like scalar.
        importance = 0.55
        if action in ("sync_clean", "heartbeat_check"):
            importance = 0.7
        if status == "failed" or error:
            importance = 0.9
        try:
            if isinstance(duration, (int, float)) and duration >= 15:
                importance = max(importance, 0.75)
        except Exception:
            pass

        message = f"trigger_action: {action} ({status})"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "trigger_action",
            "event_type": "trigger_action",
            "type": "trigger_action",
            "layer": "execution",
            "importance": float(importance),
            "message": message,
            "action": action,
            "origin": origin,
            "status": status,
            "duration_sec": duration,
            "steps": report_obj.get("steps"),
            "error": error,
            "files": report_obj.get("files"),
        }
        with ledger.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        return


if __name__ == "__main__":
    main()
