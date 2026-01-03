"""
AGI Heartbeat Loop - 완전한 자율 행동 루프
💓 외부 명령 없이 스스로 시작하는 생명 루프

AGI_LIFE_LOOP (매 10초)
    ↓
내부 상태 읽기 (의식/무의식/배경자아)
    ↓
Resonance Guard (리듬 안전장치)
    ↓
트리거 스캔 (Trigger Detection)
    ↓
트리거 발생? → YES → ProtoGoal 생성
                       ↓
                행동 레벨 분류 (Level 1/2/3)
                       ↓
                Envelope 체크 (행동량 규제)
                       ↓
                행동 실행 (Execute Goal)
                       ↓
                결과 기록 (Memory)
    ↓
내부 상태 업데이트 (consciousness/unconscious/background_self)
"""
from __future__ import annotations

import logging
import subprocess
import sys
import threading
import time
import os
import socket
from pathlib import Path
from typing import Callable, Dict, Optional, Any
import json

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.internal_state import (
    update_internal_state,
    get_internal_state,
    AGIInternalState,
)
from agi_core.self_trigger import detect_trigger
from agi_core.resonance_guard import (
    resonance_guard,
    compute_alignment_score,
    compute_conflict_pressure,
    compute_input_alignment,
)
from agi_core.action_router import route_action
from agi_core.envelope import get_envelope
# from agi_core.vision_stream.live_frame_analyzer import start_vision_stream, stop_vision_stream

logger = logging.getLogger("HeartbeatLoop")

# ------------------------------------------------------------------------------
# Single-instance (best-effort)
# ------------------------------------------------------------------------------
_HEARTBEAT_MUTEX_HANDLE = None


def _acquire_single_heartbeat_mutex_best_effort() -> bool:
    """
    Ensure only one heartbeat daemon process is running.

    Note:
    - This does not affect in-process thread usage.
    - Prevents scheduled/accidental multi-spawn from creating console flashes + CPU waste.
    """
    global _HEARTBEAT_MUTEX_HANDLE
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

        _HEARTBEAT_MUTEX_HANDLE = h
        return True
    except Exception:
        return True  # best-effort: do not block heartbeat on mutex failures


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
HEARTBEAT_INTERVAL_SECONDS = 10 
DEEP_REST_INTERVAL_SECONDS = 60  # Deep Rest 시 심장 박동 간격 연장
DIAGNOSIS_INTERVAL_CYCLES = 6    # 자가 진단 주기 (6사이클 = 1분)
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
MEMORY_DIR = WORKSPACE_ROOT / "memory"
HEARTBEAT_FILE = OUTPUTS_DIR / "unconscious_heartbeat.json"
THOUGHT_STREAM_FILE = OUTPUTS_DIR / "thought_stream_latest.json"

AURA_COLORS = {
    "thinking": "#00FFFF",  # Cyan
    "acting": "#FF00FF",    # Magenta 
    "learning": "#00FF88",  # Green
    "idle": "#1A1A2E",      # Dark Blue
    "rest": "#4B0082"       # Indigo (Deep Rest)
}

_heartbeat_thread: Optional[threading.Thread] = None
_heartbeat_running: bool = False

def _start_aura(color_hex: str, narrative: str = "💓 Local Heartbeat Resonating...", decision: str = "pulse"):
    """오라 색상 변경 요청 (thought_stream 업데이트)"""
    try:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        stream_file = THOUGHT_STREAM_FILE
        data = {}
        
        if stream_file.exists():
            try:
                with open(stream_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except: pass
            
        # Update with local heartbeat pulse
        data.update({
            "timestamp": time.time(),
            "trigger": {"type": "local_heartbeat", "score": 0.8},
            "state": get_internal_state().to_dict(), 
            "decision": decision,
            "narrative": narrative,
        })
        
        # Write back (atomic best-effort)
        temp = stream_file.with_suffix(".tmp")
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        try:
            temp.replace(stream_file)
        except Exception:
            try:
                if stream_file.exists():
                    stream_file.unlink()
                temp.replace(stream_file)
            except Exception:
                pass
        
    except Exception as e:
        logger.error(f"Aura update failed: {e}")

def _stop_aura():
    """오라 발산 중단 (thought_stream 초기화)"""
    try:
        if THOUGHT_STREAM_FILE.exists():
            with open(THOUGHT_STREAM_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data["decision"] = "idle"
            data["narrative"] = "💤 System breathing softly..."
            with open(THOUGHT_STREAM_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
    except Exception: pass

_vision_process: Optional[subprocess.Popen] = None

def _start_vision_stream():
    """Vision Stream (Server + Analyzer) 시작"""
    global _vision_process
    try:
        # 이미 실행 중이면 무시
        if _vision_process and _vision_process.poll() is None:
            return
            
        logger.info("👁️ Starting Vision Stream processes...")
        # ws_stream_server.py와 live_frame_analyzer.py를 별도 프로세스로 실행
        # 여기서는 하위 모듈로 직접 호출하거나 배경 프로세스로 띄움
        server_path = WORKSPACE_ROOT / "agi_core" / "vision_stream" / "ws_stream_server.py"
        analyzer_path = WORKSPACE_ROOT / "agi_core" / "vision_stream" / "live_frame_analyzer.py"
        
        # 실제 환경에서는 복수의 프로세스를 관리해야 하지만, 
        # 간단하게 analyzer를 background에서 실행 (analyzer가 queue를 통해 server와 통신하는 구조라 가정)
        # 우선 server를 띄움
        server_cmd = [sys.executable, str(server_path)]
        _vision_process = subprocess.Popen(server_cmd, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        
        logger.info(f"✅ Vision Server started (PID: {_vision_process.pid})")
    except Exception as e:
        logger.error(f"Vision stream start failed: {e}")

def _stop_vision_stream():
    """Vision Stream 프로세스 종료"""
    global _vision_process
    if _vision_process and _vision_process.poll() is None:
        logger.info("👁️ Stopping Vision Stream processes...")
        _vision_process.terminate()
        try:
            _vision_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _vision_process.kill()
        _vision_process = None

def _write_unconscious_heartbeat(state: AGIInternalState) -> None:
    """표준 경로에 심장 박동 기록을 남긴다."""
    try:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "host": socket.gethostname(),
            "system": sys.platform,
            "heartbeat_count": state.heartbeat_count,
            "state": state.to_dict(),
        }
        tmp = HEARTBEAT_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        tmp.replace(HEARTBEAT_FILE)
    except Exception as e:
        logger.error(f"Heartbeat write failed: {e}")

def heartbeat_loop(interval_sec: int):
    """
    💓 메인 심장 박동 루프
    
    Args:
        interval_sec: 루프 주기 (초)
    """
    global _heartbeat_running
    _heartbeat_running = True
    
    logger.info(f"💓 Heartbeat Loop 시작됨 (주기: {interval_sec}초)")
    
    # Vision Stream 시작
    _start_vision_stream()
    
    envelope = get_envelope()
    current_interval = interval_sec
    cycle_count = 0
    deep_rest_mode = False
    
    while _heartbeat_running:
        cycle_count += 1
        try:
            # 0. 자가 진단 (주기적 실행)
            if cycle_count % DIAGNOSIS_INTERVAL_CYCLES == 0:
                diagnosis_path = WORKSPACE_ROOT / "scripts" / "self_diagnosis.py"
                try:
                    # 결과 읽기
                    from scripts.self_diagnosis import self_diagnosis
                    health_state = self_diagnosis()
                    
                    if health_state == "CRITICAL" and not deep_rest_mode:
                        logger.warning("🚨 CRITICAL STATE DETECTED! Entering Deep Rest...")
                        deep_rest_mode = True
                        _stop_vision_stream()
                        current_interval = DEEP_REST_INTERVAL_SECONDS
                    elif health_state == "HEALTHY" and deep_rest_mode:
                        logger.info("✨ Recovery detected. Leaving Deep Rest...")
                        deep_rest_mode = False
                        _start_vision_stream()
                        current_interval = interval_sec
                except Exception as diag_err:
                    logger.error(f"Self-diagnosis execution failed: {diag_err}")

            # 1. 내부 상태 업데이트 (1회만)
            state = update_internal_state()
            state_dict = state.to_dict()

            # 1-1. 심장 파일 기록 (단일 소스)
            _write_unconscious_heartbeat(state)

            # 2. Resonance Guard (리듬 체크)
            alignment = compute_alignment_score(state_dict)
            conflict = compute_conflict_pressure(state_dict)

            logger.debug(f"💓 Pulse - Align: {alignment:.2f}, Conflict: {conflict:.2f}")

            # 3. Envelope 갱신 (시간 경과에 따른 토큰 회복)
            # envelope.replenish() # 제거 (ActionEnvelope에 없음)

            # 4. 트리거 감지 (상태 기반)
            trigger = detect_trigger(state_dict)

            # Narrative Generation (Core Thinking)
            narrative = "💓 Checking Resonance..."
            decision = "pulse"
            
            if deep_rest_mode:
                narrative = "💤 Entering Deep Rest (Metacognitive Recovery)..."
                decision = "rest"
            elif trigger:
                narrative = f"⚡ Triggered: {trigger.type.value} ({trigger.reason})"
                decision = "alert"
            elif alignment > 0.8:
                narrative = "🎶 High Harmony - Analyzing Flows..."
                decision = "flow"
            elif conflict > 0.6:
                narrative = "🌪️ Internal Conflict Detected - Seeking Resolution..."
                decision = "resolve"

            if deep_rest_mode:
                _start_aura(AURA_COLORS["rest"], narrative, decision)
            elif trigger:
                # [신규] 입력 정렬 (Input Alignment) 계산
                # 트리거가 현재 내면의 맥락과 맞는가?
                input_align = compute_input_alignment(trigger.type.value, state_dict)

                # 종합 정렬 점수 (Total Alignment) 리밸런싱
                # 기존 내부정렬(60%) + 입력정렬(40%)
                total_alignment = (alignment * 0.6) + (input_align * 0.4)

                logger.info(f"🎯 트리거 감지: {trigger.type.value} (점수: {trigger.score:.2f})")
                logger.debug(f"   ⚖️ 정렬 재계산: Int({alignment:.2f}) + Inp({input_align:.2f}) -> Tot({total_alignment:.2f})")

                # Dynamic Aura Pulse for Trigger
                _start_aura(AURA_COLORS["acting"], narrative, decision)
            elif not deep_rest_mode and interval_sec < 5:
                # Core Mode: Always pulse aura on beat if no trigger
                _start_aura(AURA_COLORS["thinking"], narrative, decision)

            if not trigger or deep_rest_mode:
                logger.info("😴 트리거 없음 - 조용히 쉬는 중")
                envelope.on_idle()
            
            # ------------------------------------------------------------------
        except Exception as e:
            logger.error(f"💓 Heartbeat Loop Error: {e}", exc_info=True)
            time.sleep(1)  # Prevent tight loop on error

        # Sleep before next cycle
        time.sleep(current_interval)
    
    _heartbeat_running = False
    _stop_vision_stream()  # Vision Stream 종료
    logger.info("💔 Heartbeat Loop 종료됨")


def start_heartbeat(interval_sec: int = HEARTBEAT_INTERVAL_SECONDS) -> threading.Thread:
    """
    💓 Heartbeat 루프를 별도 스레드에서 시작
    
    Returns:
        실행 중인 스레드 객체
    """
    global _heartbeat_thread, _heartbeat_running
    
    if _heartbeat_running and _heartbeat_thread and _heartbeat_thread.is_alive():
        logger.warning("Heartbeat already running")
        return _heartbeat_thread
    
    _heartbeat_thread = threading.Thread(
        target=heartbeat_loop,
        args=(interval_sec,),
        daemon=True,
        name="AGI-Heartbeat"
    )
    _heartbeat_thread.start()
    
    logger.info(f"💓 Heartbeat 스레드 시작됨 (interval={interval_sec}s)")
    return _heartbeat_thread


def stop_heartbeat() -> None:
    """💔 Heartbeat 루프 중단"""
    global _heartbeat_running
    _heartbeat_running = False
    logger.info("💔 Heartbeat 중단 요청됨")


def is_heartbeat_running() -> bool:
    """Heartbeat 실행 상태 확인"""
    return _heartbeat_running


def get_heartbeat_status() -> Dict[str, Any]:
    """Heartbeat 상태 정보 반환"""
    state = get_internal_state()
    envelope = get_envelope()
    
    return {
        "running": _heartbeat_running,
        "internal_state": state.to_dict(),
        "envelope": envelope.get_status(),
        "heartbeat_count": state.heartbeat_count,
    }


if __name__ == "__main__":
    # Daemon Execution
    import os

    # Single-instance guard (best-effort)
    if not _acquire_single_heartbeat_mutex_best_effort():
        # Another heartbeat process already exists. Exit quickly and quietly.
        try:
            sys.exit(0)
        except Exception:
            raise SystemExit(0)

    # Windows에서 console(python.exe)로 실행되더라도 창이 뜨지 않게 숨김
    if os.name == "nt":
        try:
            import ctypes

            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
                try:
                    ctypes.windll.kernel32.FreeConsole()
                except Exception:
                    pass
        except Exception:
            pass
    
    # Setup Logging to file
    log_dir = WORKSPACE_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "heartbeat_loop.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger.info("💓 AGI Heartbeat Loop Starting (Daemon Mode)...")
    
    try:
        # Determine Interval (Core Acceleration)
        interval = 10
        CORE_KEY_FILE = WORKSPACE_ROOT / "inputs" / "core_passkey.txt"
        if CORE_KEY_FILE.exists():
            interval = 3 # Fast Heartbeat
            logger.info("✨ Core Mode Detected: Accelerated Heartbeat (3s)")
        
        # Start Loop
        heartbeat_loop(interval)
            
    except KeyboardInterrupt:
        logger.info("🛑 Daemon Stopped by User")
    except Exception as e:
        logger.critical(f"💥 Critical Daemon Error: {e}")
        time.sleep(5)
