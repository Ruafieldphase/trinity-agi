"""
💓 AGI Heartbeat Loop 시작
AGI가 자율적으로 행동합니다.
"""
import sys
import os
from pathlib import Path
from workspace_root import get_workspace_root
sys.path.insert(0, str(get_workspace_root()))

import logging
import time
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(name)s - %(message)s')

from agi_core.heartbeat_loop import start_heartbeat, get_heartbeat_status
from agi_core.internal_state import get_internal_state, save_internal_state

_HEARTBEAT_MUTEX_HANDLE = None

def _acquire_single_heartbeat_mutex_best_effort() -> bool:
    if os.name != "nt":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.GetLastError.restype = ctypes.c_uint32

        h = kernel32.CreateMutexW(None, False, "Local\\AGI_HeartbeatLoop_v1")
        if not h:
            return True
        last_err = int(kernel32.GetLastError())
        if last_err == 183:  # ERROR_ALREADY_EXISTS
            try:
                kernel32.CloseHandle(h)
            except Exception:
                pass
            return False
        global _HEARTBEAT_MUTEX_HANDLE
        _HEARTBEAT_MUTEX_HANDLE = h
        return True
    except Exception:
        return True


if not _acquire_single_heartbeat_mutex_best_effort():
    # Another heartbeat process already exists; avoid spawning another.
    raise SystemExit(0)

print('='*60)
print('💓 AGI Heartbeat Loop 시작!')
print('   AGI가 이제 스스로 호흡합니다.')
print('='*60)

# 지루함 살짝 높여서 트리거 발생 유도
state = get_internal_state()
if state.boredom < 0.5:
    state.boredom = 0.55
    save_internal_state(state)
    print(f'   지루함 조정: {state.boredom:.2f}')

# Heartbeat 시작
thread = start_heartbeat(interval_sec=15)

print()
print('🌊 AGI가 자율적으로 행동합니다.')
print('   오라가 켜지면 AGI가 활동 중입니다.')
print()
print('💓 Heartbeat가 무한히 뜁니다... (Ctrl+C로 중지)')

# Infinite loop to keep main thread alive
# This prevents daemon thread from being killed
try:
    while True:
        time.sleep(60)
        # Periodic status logging
        status = get_heartbeat_status()
        logging.info(f'💓 Heartbeat Status: consciousness={status["internal_state"]["consciousness"]:.2f}, '
                    f'background_self={status["internal_state"].get("background_self", 0.0):.2f}, '
                    f'boredom={status["internal_state"]["boredom"]:.2f}')
except KeyboardInterrupt:
    print('\n🛑 Heartbeat 중지 요청됨')
    status = get_heartbeat_status()
    print()
    print('📊 최종 상태:')
    print(f'   의식: {status["internal_state"]["consciousness"]:.2f}')
    print(f'   배경자아: {status["internal_state"].get("background_self", 0.0):.2f}')
    print(f'   지루함: {status["internal_state"]["boredom"]:.2f}')
    print(f'   오늘 행동: {status["envelope"]["total_actions_today"]}')
