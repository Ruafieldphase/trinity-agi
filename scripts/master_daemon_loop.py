import os
import sys
from pathlib import Path
from workspace_root import get_workspace_root

# 부트스트래핑 및 워크스페이스 루트 탐지
current_path = Path(__file__).resolve()
for parent in current_path.parents:
    if (parent / "agi_core").exists() or parent.name == "agi":
        root = parent if parent.name == "agi" else parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        break

from agi_core.utils.paths import get_workspace_root, add_to_sys_path
WORKSPACE = add_to_sys_path()

import logging
import subprocess
import time
from datetime import datetime, timezone
from typing import Any


# Config (base bounds; actual sleep is rhythm-adaptive)
SUPERVISOR_SCRIPT = WORKSPACE / "scripts" / "meta_supervisor.py"
LOG_FILE = WORKSPACE / "logs" / "master_daemon.log"
LOCK_FILE = WORKSPACE / "outputs" / "sync_cache" / "master_daemon.instance.lock"
IDENTITY_CHECK = WORKSPACE / "scripts" / "identity_check.py"
PATH_CHECK = WORKSPACE / "scripts" / "path_integrity_check.py"

TWIN = WORKSPACE / "outputs" / "sync_cache" / "digital_twin_state.json"
REST_GATE = WORKSPACE / "outputs" / "safety" / "rest_gate_latest.json"
CONSTITUTION = WORKSPACE / "outputs" / "bridge" / "constitution_review_latest.json"
PAIN = WORKSPACE / "outputs" / "sync_cache" / "rhythm_pain_latest.json"
SUP_REPORT = WORKSPACE / "outputs" / "bridge" / "meta_supervisor_report_latest.json"

MIN_SLEEP_S = 60
MAX_SLEEP_S = 20 * 60
_LOCK_HANDLE = None
_MUTEX_HANDLE = None


def _ensure_single_instance_best_effort() -> bool:
    """
    Best-effort single-instance guard.

    Why:
    - master_daemon_loop가 중복 실행되면 같은 supervisor를 여러 번 깨워서
      리듬/자원/로그가 불필요하게 흔들릴 수 있다.
    """
    global _LOCK_HANDLE, _MUTEX_HANDLE
    try:
        # Windows: prefer named mutex (more reliable than file locks for concurrent start).
        if sys.platform == "win32":
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
                kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
                kernel32.CreateMutexW.restype = ctypes.c_void_p
                h = kernel32.CreateMutexW(None, False, "Local\\AGI_MasterDaemon_v1")
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

        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        f = open(LOCK_FILE, "a+b")
        f.seek(0, 2)
        if int(f.tell()) <= 0:
            f.write(b"0")
            f.flush()
        f.seek(0)

        if sys.platform == "win32":
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
        return True  # best-effort: 락 실패로 전체가 멈추지 않게 한다.


def _utc_iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        obj = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _file_age_s(path: Path) -> float | None:
    try:
        if not path.exists():
            return None
        return max(0.0, time.time() - path.stat().st_mtime)
    except Exception:
        return None


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))


def _compute_sleep_seconds() -> tuple[int, str]:
    """
    리듬 기반 "깨어있음" 조절.

    원칙:
    - 시간 기반 폴링이 아니라, (통증/드리프트/불일치/안전/휴식) 신호에 따라
      '지금은 깨어있어야 하나?'를 판단해 템포를 조절한다.
    - 완전 이벤트 기반은 OS/서비스 버스가 필요하므로, 여기서는 최소 주기만 둔 적응형 루프를 사용한다.
    """
    twin = _load_json(TWIN)
    rg = _load_json(REST_GATE)
    c = _load_json(CONSTITUTION)
    pain = _load_json(PAIN)

    mismatch = 0.0
    try:
        mismatch = float(twin.get("mismatch_0_1") or 0.0)
    except Exception:
        mismatch = 0.0

    rest_status = str(rg.get("status") or "").upper().strip()
    safety_status = str(c.get("status") or "").upper().strip()

    pain_level = 0.0
    pain_rec = ""
    try:
        pain_level = float(pain.get("pain_0_1") or 0.0)
    except Exception:
        pain_level = 0.0
    try:
        pain_rec = str(pain.get("recommendation") or "").upper().strip()
    except Exception:
        pain_rec = ""

    # If supervisor report is fresh, we can relax.
    sup_age = _file_age_s(SUP_REPORT)
    sup_fresh = (sup_age is not None) and (sup_age <= 8 * 60)

    # Hard gates first
    if safety_status in {"BLOCK", "REVIEW"}:
        return 10 * 60, f"safety={safety_status}"
    if rest_status == "REST" or pain_rec == "REST":
        return 10 * 60, "rest_gate_or_pain=REST"

    # If mismatch/pain is high → keep the tempo higher (more frequent checks)
    urgency = 0.0
    urgency = max(urgency, _clamp(mismatch, 0.0, 1.0))
    urgency = max(urgency, _clamp(pain_level, 0.0, 1.0) * (0.9 if pain_rec == "SLOW" else 1.0))
    if not sup_fresh:
        urgency = max(urgency, 0.55)  # "supervisor staleness" nudges a check

    # Map urgency(0..1) to sleep(MIN..MAX) inversely.
    sleep_s = int(round(MAX_SLEEP_S - (MAX_SLEEP_S - MIN_SLEEP_S) * urgency))
    sleep_s = int(_clamp(sleep_s, MIN_SLEEP_S, MAX_SLEEP_S))
    return sleep_s, f"urgency={urgency:.2f} mismatch={mismatch:.2f} pain={pain_level:.2f}"


def _perform_integrity_check() -> bool:
    """
    Run identity and path integrity checks.
    """
    all_pass = True
    for script in [IDENTITY_CHECK, PATH_CHECK]:
        if not script.exists():
            continue
        try:
            res = subprocess.run(
                [sys.executable, str(script)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if res.returncode != 0:
                all_pass = False
                logging.error(f"Integrity failure in {script.name}:\n{res.stdout}\n{res.stderr}")
        except Exception as e:
            all_pass = False
            logging.error(f"Failed to run {script.name}: {e}")
    
    return all_pass


def _run_supervisor_once() -> tuple[int, str, str]:
    if not SUPERVISOR_SCRIPT.exists():
        return 0, "", "meta_supervisor.py not found"
    try:
        res = subprocess.run(
            [sys.executable, str(SUPERVISOR_SCRIPT)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return int(res.returncode or 0), (res.stdout or "").strip(), (res.stderr or "").strip()
    except Exception as e:
        return 0, "", f"{type(e).__name__}: {e}"


def main() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")],
    )

    if not _ensure_single_instance_best_effort():
        logging.info("Another master_daemon_loop instance is already running; exiting.")
        return

    logging.info("Starting Master Supervisor Loop (rhythm-adaptive)")

    # Integrity check on startup
    safe_mode = False
    if not _perform_integrity_check():
        safe_mode = True
        logging.error("\n" + "!" * 60 + "\n[!!! RED WARNING !!!] IDENTITY OR PATH INTEGRITY FAILED!\n" + 
                      "System is entering SAFE_MODE. Aggressive features disabled.\n" + "!" * 60 + "\n")

    while True:
        try:
            if safe_mode:
                logging.info("[SAFE_MODE] Skipping meta_supervisor to prevent risky actions.")
                time.sleep(300) # Longer sleep in safe mode
                # Re-check integrity to see if fixed
                if _perform_integrity_check():
                    safe_mode = False
                    logging.info("[SAFE_MODE] Integrity restored. Resuming normal operations.")
                continue

            sleep_s, reason = _compute_sleep_seconds()
            logging.info(f"wake: {_utc_iso_now()} reason={reason}")

            rc, out, err = _run_supervisor_once()
            if out:
                logging.info(f"[meta_supervisor stdout]\n{out}")
            if err:
                logging.warning(f"[meta_supervisor stderr]\n{err}")
            logging.info(f"sleep={sleep_s}s (adaptive)")
            time.sleep(max(5, int(sleep_s)))
        except KeyboardInterrupt:
            logging.info("Stopped by user")
            break
        except Exception as e:
            logging.error(f"Master loop error: {type(e).__name__}: {e}", exc_info=True)
            time.sleep(60)


if __name__ == "__main__":
    main()
