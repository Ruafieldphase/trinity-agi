#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Trigger Once (Windows-friendly)

목표:
- `scripts/trigger_listener.py`의 무한 루프를 쓰지 않고,
  스케줄러(Windows Task Scheduler)로 1분마다 호출해도 동작하도록 1회 처리만 수행한다.

동작:
- 트리거 파일이 있으면 1회 처리 후 종료
- 트리거가 없으면 아무 일도 하지 않고 종료
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path
import os
import subprocess
import atexit
from workspace_root import get_workspace_root


_LOCK_HANDLE = None
_MUTEX_HANDLE = None


def _acquire_single_instance_best_effort() -> bool:
    """
    Best-effort single-instance guard for scheduled invocations.

    Why:
    - Windows Task Scheduler can overlap runs when the previous tick is slow.
    - Overlaps can amplify background work (idle_tick/report generation) and look like "thrash".

    Policy:
    - If another instance is running, exit quietly (return False).
    - If the guard itself fails, proceed (best-effort).
    """
    global _LOCK_HANDLE, _MUTEX_HANDLE
    root = get_workspace_root()
    lock_path = root / "outputs" / "sync_cache" / "run_trigger_once.instance.lock"

    try:
        if os.name == "nt":
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
                kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
                kernel32.CreateMutexW.restype = ctypes.c_void_p
                h = kernel32.CreateMutexW(None, False, "Local\\AGI_RunTriggerOnce_v1")
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

        lock_path.parent.mkdir(parents=True, exist_ok=True)
        f = open(lock_path, "a+b")
        f.seek(0, 2)
        if int(f.tell()) <= 0:
            f.write(b"0")
            f.flush()
        f.seek(0)

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

        _LOCK_HANDLE = f
        return True
    except Exception:
        return True


def _release_single_instance_best_effort() -> None:
    global _LOCK_HANDLE, _MUTEX_HANDLE
    try:
        if _LOCK_HANDLE is not None:
            try:
                _LOCK_HANDLE.close()
            except Exception:
                pass
    finally:
        _LOCK_HANDLE = None
    if os.name != "nt":
        _MUTEX_HANDLE = None
        return
    try:
        if _MUTEX_HANDLE is None:
            return
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        try:
            kernel32.CloseHandle(_MUTEX_HANDLE)
        except Exception:
            pass
    except Exception:
        pass
    _MUTEX_HANDLE = None


def _trigger_listener_daemon_running() -> bool:
    """
    `scripts/trigger_listener.py`가 이미 백그라운드(daemon)로 돌고 있으면,
    --once 스케줄러는 아무것도 하지 않는다.

    Why:
    - daemon + scheduler(--once)가 동시에 돌면 동일 트리거를 중복 처리하거나,
      idle_tick이 과도하게 호출되어 rest_gate/오라/리포트가 "폭주"처럼 보일 수 있다.
    """
    try:
        root = get_workspace_root()
        needle = str(root / "scripts" / "trigger_listener.py").lower()
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            out = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_Process | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress",
                ],
                capture_output=True,
                text=True,
                timeout=4,
                creationflags=creationflags,
            )
            if out.returncode != 0 or not out.stdout:
                return False
            try:
                import json

                items = json.loads(out.stdout)
            except Exception:
                return False
            if isinstance(items, dict):
                items = [items]
            for it in items or []:
                cmd = str((it or {}).get("CommandLine") or "").lower()
                # 어떤 형태로든(trigger_listener.py가) 이미 돌아가면, scheduler는 중복 처리를 피한다.
                # - --silent: 상시 daemon
                # - (옵션 없음): 상시 daemon
                # - --action/--once: 1회성일 수 있으나, 겹치면 중복 처리 위험이 있어 보수적으로 skip한다.
                if needle in cmd:
                    return True
            return False

        out = subprocess.run(["bash", "-lc", "ps aux | grep -F trigger_listener.py | grep -v grep"], capture_output=True, text=True, timeout=4)
        return out.returncode == 0 and ("trigger_listener.py" in (out.stdout or ""))
    except Exception:
        return False


def _load_trigger_listener() -> object:
    root = get_workspace_root()
    path = root / "scripts" / "trigger_listener.py"
    spec = importlib.util.spec_from_file_location("trigger_listener", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load trigger_listener spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules["trigger_listener"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    try:
        if not _acquire_single_instance_best_effort():
            return 0
        atexit.register(_release_single_instance_best_effort)

        # If the daemon is already alive, skip the once-tick entirely.
        if _trigger_listener_daemon_running():
            return 0
        tl = _load_trigger_listener()
        # Always allow human→AGI dropbox ingestion even in --once mode.
        try:
            tick = getattr(tl, "tick_binoche_dropbox_once", None)
            if callable(tick):
                tick()
        except Exception:
            pass
        path = tl.resolve_signal_path()
        if path.exists():
            tl.handle_trigger(path)
        else:
            # "아무것도 안 해도 정상"인 생존 상태를 유지하기 위한 최소 틱
            # (리포트/결정/행동 없음, 관측 가능한 heartbeat/life_state만 갱신)
            try:
                tl.idle_tick()
            except Exception:
                pass
        return 0
    except Exception:
        # 스케줄러/백그라운드 실행에서 "실패로 인해 루프가 멈추는 것"을 막기 위해 항상 0 종료.
        # 필요 시 traceback은 Windows 이벤트 로그/작업 스케줄러 기록으로 남는다.
        try:
            root = get_workspace_root()
            out = root / "outputs" / "run_trigger_once_last_error.txt"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(traceback.format_exc(), encoding="utf-8")
        except Exception:
            pass
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
