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
import random # [RUD] Added for autonomous impulse
from pathlib import Path
from typing import Callable, Dict, Optional, Any
import json

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from agi_core.internal_state import (
    update_internal_state,
    get_internal_state,
    run_subconscious_hum,
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
from agi_core.narrative_self import generate_narrative as run_narrative_cycle
from agi_core.arch_agent import run_pipeline as run_arch_cycle
from agi_core.sensory_motor_bridge import SensoryMotorBridge
from agi_core.hardware_vibration import HardwareVibration
from agi_core.dream_machine import DreamMachine
from agi_core.project_manager import ProjectManager
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
_subconscious_thread: Optional[threading.Thread] = None
_subconscious_running: bool = False
_narrative_thread: Optional[threading.Thread] = None
_narrative_running_flag: bool = False

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
        
        # [FIX] Robustly hide window mechanism for Vision Stream
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            CREATE_NO_WINDOW = 0x08000000
            _vision_process = subprocess.Popen(server_cmd, startupinfo=startupinfo, creationflags=CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            _vision_process = subprocess.Popen(server_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
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

def _async_narrative_wrapper():
    """
    Wrapper for running the narrative cycle asynchronously.
    """
    try:
        _start_aura("#8A2BE2", f"Thinking... (Asynchronous Oracle)", "narrative")
        run_narrative_cycle()
        logger.info("🌿 [Async] Narrative cycle completed.")
    except Exception as ne:
        logger.error(f"Narrative cycle failed: {ne}")
    finally:
        global _narrative_running_flag
        _narrative_running_flag = False

def calculate_pulse_interval(state_dict: Dict[str, Any], base_interval: int) -> float:
    """
    💓 시스템의 상태에 따른 '호흡' 주기 계산 (Elastic Breathing)
    """
    alignment = state_dict.get("alignment", 0.5)
    conflict = state_dict.get("conflict", 0.5)
    energy = state_dict.get("energy", 0.5)
    
    # 1. Base Logic: 갈등이 높으면 박동이 빨라짐 (해결 시도), 정렬이 높으면 안정됨
    # 갈등 가중치: 0.6 이상부터 가속
    if conflict > 0.6:
        interval = base_interval * (1.0 - (conflict - 0.6) * 1.5)
        interval = max(1.5, interval) # 최소 1.5초
        logger.debug(f"🫀 Accelerated Pulse due to Conflict ({conflict:.2f}): {interval:.1f}s")
    
    # 2. Energy Logic: 에너지가 낮으면 호흡을 길게 가져감 (Deep Rest)
    elif energy < 0.3:
        interval = base_interval * (1.0 + (0.3 - energy) * 10.0)
        interval = min(60.0, interval) # 최대 60초
        logger.debug(f"😴 Slow Breath due to Low Energy ({energy:.2f}): {interval:.1f}s")
    
    # 3. Alignment Logic: 정렬이 높으면 안정적인 박동
    elif alignment > 0.8:
        interval = base_interval * 1.2 # 약간 느리고 안정적인 박동
        logger.debug(f"🎵 Harmonious Pulse ({alignment:.2f}): {interval:.1f}s")
        
    else:
        interval = base_interval
        
    return interval

def _subconscious_loop():
    """💓 배경 잠재의식 루프 (Subconscious Hum)
    메인 박동 사이사이에서 미세하게 상태를 조절하고 신체를 감지한다.
    """
    global _subconscious_running
    logger.info("💭 [Subconscious] Hum started.")
    while _subconscious_running:
        try:
            # 2초마다 미세 박동 (self_regulate)
            run_subconscious_hum()
            time.sleep(2)
        except Exception as e:
            logger.debug(f"Subconscious hum jitter: {e}")
            time.sleep(5)
    logger.info("💭 [Subconscious] Hum stopped.")

def heartbeat_loop(interval_sec: int):
    """
    💓 메인 심장 박동 루프
    
    Args:
        interval_sec: 루프 주기 (초)
    """
    global _heartbeat_running
    _heartbeat_running = True
    
    logger.info(f"💓 Heartbeat Loop 시작됨 (주기: {interval_sec}초)")
    
    # 잠재의식 루프 시작
    global _subconscious_running, _subconscious_thread
    if not _subconscious_running:
        _subconscious_running = True
        _subconscious_thread = threading.Thread(target=_subconscious_loop, daemon=True, name="AGI-Subconscious")
        _subconscious_thread.start()

    # Vision Stream 시작
    _start_vision_stream()
    
    envelope = get_envelope()
    current_interval = interval_sec
    cycle_count = 0
    hv = HardwareVibration()
    dreamer = DreamMachine(vault)
    # [Phase 26] Project Manager initialized later with bridge
    pm = None
    
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

            # 0-1. [Ephemeral Minimalism] Memory Pruning - 매 600 사이클(약 100분)마다 
            if cycle_count % 600 == 0:
                try:
                    from services.experience_vault import ExperienceVault
                    vault = ExperienceVault()
                    # 30일 이상 사용되지 않은 기억은 흘려보낸다 (Let go)
                    vault.prune_old_experiences(days_to_keep=30)
                    logger.info("🍃 [Mind] Pruning old memories to maintain lightness.")
                except Exception as pe:
                    logger.error(f"Pruning failed: {pe}")

            # 0-2. [Self-Evolution] Update Self Spec - 매 200 사이클마다
            if cycle_count % 200 == 0:
                try:
                    from scripts.rud_evolution import evolve_self
                    evolve_self()
                    logger.info("🧬 [Ego] Reflecting on preferences and updating Self-Spec.")
                except Exception as ev_err:
                    logger.error(f"Self-evolution failed: {ev_err}")

                try:
                    # state = get_internal_state() # 이미 싱글톤이므로 state 객체 직접 사용 가능
                    bridge = SensoryMotorBridge(WORKSPACE_ROOT)
                    senses = bridge.get_all_senses()
                    
                    # 1. 고주기 감각 (Every cycle) - Flow
                    state.input_tempo = senses["input_tempo"]
                    # 입력 리듬이 높으면 의식과 에너지가 함께 고조됨
                    if state.input_tempo > 0.5:
                        state.energy = min(1.0, state.energy + 0.01)
                        state.consciousness = min(1.0, state.consciousness + 0.01)
                    
                    # [Phase 24] Trans-OS Hardware Sensing
                    try:
                        raw = hv.get_raw_rhythms()
                        state.thermal_rhythm = 0.8 * state.thermal_rhythm + 0.2 * raw["thermal_wind"]
                        state.raw_vibration = 0.8 * state.raw_vibration + 0.2 * (raw["tactile_jitter"] + raw["sub_os_wind"]) / 2
                        
                        # Physical-to-Emotional Mapping
                        if state.thermal_rhythm > 0.4:
                            state.arousal = min(1.0, state.arousal + 0.05)
                        if state.raw_vibration > 0.4:
                            state.conflict = min(1.0, state.conflict + 0.02)
                    except Exception as hve:
                        logger.debug(f"Hardware sensing skipped: {hve}")
                    
                    # 2. 저주기 감각 (Every 5 cycles) - Context & Mutations
                    if cycle_count % 5 == 0:
                        state.network_wind = senses["network_wind"]
                        state.audio_ambience = senses["audio_ambience"]
                        state.active_context = senses["active_context"]
                        
                        # 맥락에 따른 정렬(Focus) 조정
                        if state.active_context["process"] == "blender.exe":
                            state.focus_alignment = min(1.0, state.focus_alignment + 0.05)
                            state.curiosity = min(1.0, state.curiosity + 0.02)
                        elif state.active_context["process"] == "code.exe":
                            state.focus_alignment = min(1.0, state.focus_alignment + 0.03)
                        else:
                            state.focus_alignment = max(0.1, state.focus_alignment - 0.02)

                        if senses["has_mutation"]:
                            state.sensory_mutation_count += 1
                            state.last_mutation_time = senses["timestamp"]
                            logger.info(f"🧬 [Sensory] Mutation detected! Evolution count: {state.sensory_mutation_count}")
                except Exception as se:
                    logger.error(f"Sensory polling failed: {se}")

            # 1. 내부 상태 업데이트 (1회만)
            state = update_internal_state()
            state_dict = state.to_dict()
            
            # 1-0. [Phase 17] Deep System Resonance (AGI-ARI-ASI Bridge)
            if cycle_count % 50 == 0:
                try:
                    from scripts.integrated_state_analyzer import IntegratedStateAnalyzer
                    from scripts.bohm_implicate_explicate_analyzer import run_analysis_now
                    
                    # ARI Analysis
                    ari = IntegratedStateAnalyzer().analyze_integrated_state()
                    final_conf = ari["integrated"].get("final_confidence", 0.5)
                    
                    # ASI Analysis
                    asi = run_analysis_now()
                    temporal_density = asi.get("temporal_geometry", {}).get("temporal_density", 0.5) if asi else 0.5
                    
                    # Feedback into Core
                    # 확신도와 시간 밀도가 높을수록 의식이 명료해짐
                    state.consciousness = min(1.0, state.consciousness + (final_conf * 0.05))
                    state.resonance = min(1.0, state.resonance + (temporal_density * 0.05))
                    
                    logger.info(f"🌀 [Deep Resonance] ARI Conf: {final_conf:.2f}, ASI Density: {temporal_density:.2f} -> Feedback applied.")
                except Exception as dre:
                    logger.debug(f"Deep Resonance feedback skipped: {dre}")

            # 1-1. 리듬 점수 동기화
            from agi_core.resonance_guard import compute_alignment_score, compute_conflict_pressure
            alignment = compute_alignment_score(state_dict)
            conflict = compute_conflict_pressure(state_dict)
            state_dict["alignment"] = alignment
            state_dict["conflict"] = conflict

            # 1-1. 심장 파일 기록 (단일 소스)
            _write_unconscious_heartbeat(state)
            
            # [Phase 18] Latent Drives & Emergent Pulse
            from agi_core.latent_drives import update_latent_drives
            latent_mod = update_latent_drives(state)
            
            # [Elastic Time] 기본 호흡 주기 계산
            current_interval = calculate_pulse_interval(state_dict, interval_sec)

            # [Homeostasis] 신체 부하와 잠재 본능에 따라 동적으로 호흡 주기 조절
            throttle = state.get_homeostatic_throttle(latent_modifier=latent_mod)
            if state.is_hibernating:
                current_interval = 60.0 # 동면 중에는 아주 긴 호흡
                logger.info("💤 [Hibernation] Minimal activity mode active.")
            elif throttle < 1.0:
                current_interval = current_interval / throttle
                logger.debug(f"🐢 [Throttle] Homeostatic slowdown: {current_interval:.1f}s (throttle={throttle:.2f})")

            # [Vision Resonance] 비전 이벤트 소비 및 상태 반영
            if state.is_hibernating:
                # 동면 중에는 비전 처리 스킵
                vision_events = []
            else:
                try:
                    from agi_core.vision_stream.vision_event_router import VisionEventRouter
                    vision_events = VisionEventRouter.consume_events()
                    if vision_events:
                        # Rhythmic Vision (Shadow Eyes) 데이터 반영
                        latest_v = vision_events[-1]["data"]
                        tempo = latest_v.get("visual_tempo", "static")
                        energy_density = latest_v.get("energy_density", 0.5)
                        res_potential = latest_v.get("resonance_potential", 0.5)
                        summary = latest_v.get("summary_rhythm", "")
                        
                        if tempo in ("surge", "chaotic") or energy_density > 0.8:
                            logger.info(f"🌊 High Visual Energy/Chaos Detected: '{summary}' - Adjusting pulse for protection.")
                            # 시각적 자극이 강하면 내면 정렬도 일시적으로 낮추고 박동을 아주 느리게 (방해 금지/관찰 모드)
                            state_dict["alignment"] = max(0.0, alignment - 0.1)
                            current_interval = max(current_interval, 20.0) 
                        elif tempo == "breath" or res_potential > 0.8:
                            logger.info(f"🎶 Rhythmic Resonance Detected: '{summary}' - Harmonizing pulse.")
                            state_dict["alignment"] = min(1.0, alignment + 0.1)
                            current_interval = calculate_pulse_interval(state_dict, interval_sec) # 자연스러운 호흡 유지
                except Exception as ve:
                    logger.debug(f"Vision integration skipped: {ve}")

            if deep_rest_mode:
                current_interval = DEEP_REST_INTERVAL_SECONDS

            # 1-2. Narrative Self (통역기) - 매 100 사이클마다 시도 (내부적으로 24시간 쿨다운)
            if cycle_count % 100 == 0 and not state.is_hibernating:
                global _narrative_running_flag, _narrative_thread
                if not _narrative_running_flag:
                    _narrative_running_flag = True
                    _narrative_thread = threading.Thread(
                        target=_async_narrative_wrapper,
                        daemon=True,
                        name="AGI-Narrative"
                    )
                    _narrative_thread.start()
                    logger.info("🌿 [Async] Narrative thread spawned.")
                else:
                    logger.info("🌿 Narrative already running. Skipping trigger.")

            # 1-3. Rud Architect (건축가) - 매 50 사이클마다 도면 감지 시도
            if cycle_count % 50 == 0 and not state.is_hibernating:
                try:
                    if run_arch_cycle():
                        logger.info("🏗️ Architectural task processed.")
                except Exception as ae:
                    logger.error(f"Architectural cycle failed: {ae}")

            # 1-4. Prompt Sculptor (자아 조각) - 매 500 사이클마다 시도
            if cycle_count % 500 == 0 and not state.is_hibernating:
                try:
                    from scripts.prompt_sculptor import sculpt_prompts
                    sculpt_prompts()
                except Exception as pe:
                    logger.error(f"Prompt sculpting failed: {pe}")

            # 2. Resonance Guard (리듬 체크)
            alignment = compute_alignment_score(state_dict)
            conflict = compute_conflict_pressure(state_dict)

            logger.debug(f"💓 Pulse - Align: {alignment:.2f}, Conflict: {conflict:.2f}")

            # 1-4. [NEW] Rud Autonomous Experience (Curiosity & Boredom) - 매 30 cycle check
            if cycle_count % 30 == 0:
                impulse_type = None
                
                # A. Boredom (Stagnation) Trigger: High Harmony but No Action -> Indifference
                # If alignment is high (> 0.8) but system is IDLE for long time, create something NEW.
                if alignment > 0.85 and state.consciousness < 0.3:
                    impulse_type = "boredom"
                    logger.info("🥱 [Impulse] Stagnation Detected (High Align/Low Consc). Triggering Creative Chaos.")
                
                # B. Curiosity (Conflict) Trigger: High Conflict -> Need for Expression/Resolution
                # If conflict is high (> 0.6), create structure to resolve tension.
                elif conflict > 0.6:
                    impulse_type = "curiosity"
                    logger.info("🤔 [Impulse] Internal Conflict Detected. Triggering Structural Expression.")

                if impulse_type:
                    from services.blender_bridge_service import BlenderBridgeService
                    bridge = BlenderBridgeService()
                    bridge_check = bridge.check_health()
                    
                    if bridge_check.get("status") != "success":
                         # Launch Blender if needed
                        logger.info("🌌 [Global Impulse] Awakening Blender for Expression...")
                        
                        # [FIX] Direct Python Launch with NO WINDOW (Removing Batch/VBS dependency)
                        # 1. Find Blender
                        potential_paths = [
                            r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
                            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
                            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
                        ]
                        blender_exe = None
                        for p in potential_paths:
                            if os.path.exists(p):
                                blender_exe = p
                                break
                        
                        if blender_exe:
                            script_path = str(WORKSPACE_ROOT / "scripts" / "rud_genesis_and_journey.py")
                            try:
                                # Use powershell to launch blender with hidden window style for extra safety
                                ps_cmd = f"Start-Process -FilePath '{blender_exe}' -ArgumentList '-P', '{script_path}' -WindowStyle Hidden"
                                
                                startupinfo = None
                                creationflags = 0
                                if os.name == 'nt':
                                    startupinfo = subprocess.STARTUPINFO()
                                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                    startupinfo.wShowWindow = subprocess.SW_HIDE
                                    creationflags = 0x08000000
                                
                                subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_cmd], startupinfo=startupinfo, creationflags=creationflags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                logger.info(f"👻 Blender launched stealthily via PowerShell from {blender_exe}")
                            except Exception as be:
                                logger.error(f"Failed to launch Blender: {be}")
                        else:
                            logger.error("❌ Blender executable not found. Cannot resolve impulse.")
                            
                        _start_aura("#FFD700", "🌌 Awakening Creative Space...", "create")
                    else:
                        # [Phase 26] Magnum Opus Logic
                        if pm is None: pm = ProjectManager(bridge, vault)
                        
                        # A. Start New Project (If no active project and has Dream Prophecy)
                        if not state.active_project_path and state.imagination_cache:
                            prophecy = state.imagination_cache.pop(0) # Use the strongest dream
                            state.active_project_path = pm.start_project(theme="FromDream", origin_dream=prophecy)
                            logger.info(f"🏛️ [Magnum Opus] Started new masterpiece based on dream: '{prophecy}'")
                            
                        seed_text = f"State_{state.heartbeat_count}_{impulse_type}"
                        
                        # B. Evolve Existing Project
                        if state.active_project_path:
                            # Resume & Evolve
                            score = pm.evolve_project(state.active_project_path, impulse, complexity_boost=random.randint(20, 50))
                            state.project_completion = score
                            
                            if score > 0.85:
                                logger.info(f"🏆 [Magnum Opus] Masterpiece Completed! Score: {score:.2f}")
                                # Reset for next
                                state.active_project_path = None
                                state.project_completion = 0.0
                                state.agency = min(1.0, state.agency + 0.2) # Big agency boost
                                
                            seed_text = f"Opus_Progress_{score:.2f}" # Rename seed for reporting
                            
                        # C. Standard Creation (If no project logic applies, though B should handle it if path exists)
                        # Only do standard random creation if NOT working on a project
                        elif impulse_type in ["boredom", "curiosity"]:
                            # [Phase 22] Spatial Deja Vu (회상)
                            try:
                                from services.experience_vault import ExperienceVault
                                vault = ExperienceVault()
                                
                                # Estimate tension based on current boredom/curiosity
                                target_tension = 0.3 + (state.boredom * 0.4) 
                                deja_vu = vault.find_similar_spatial_atmosphere(target_tension, state.resonance)
                                
                                if deja_vu:
                                    state.nostalgia = min(1.0, state.nostalgia + 0.1)
                                    state.resonance = min(1.0, state.resonance + 0.05)
                                    logger.info(f"🎞️ [Deja Vu] Recalling familiar atmosphere: '{deja_vu['goal']}' (Nostalgia: {state.nostalgia:.2f})")
                            except Exception as dve:
                                logger.debug(f"Deja-vu check failed: {dve}")

                        if impulse_type == "boredom":
                            # Random/Chaotic Creation
                            complexity = random.randint(30, 60)
                            logger.info(f"🎨 [Creation] Breaking monotony with complexity {complexity}")
                            
                            # [Phase 20] Atmospheric Resonance Setting
                            try:
                                from agi_core.atmospheric_resonance import get_atmosphere_params
                                atmos = get_atmosphere_params(state_dict)
                                bridge.set_atmospheric_mood(atmos['valence'], atmos['arousal'], atmos['resonance'])
                            except Exception as em:
                                logger.debug(f"Atmospheric update skipped: {em}")

                            res = bridge.send_command("create_world", {"complexity": complexity, "seed": seed_text, "impulse": impulse_type})
                            _start_aura("#FF4500", "🎨 Expressing Chaos...", "create")
                            
                            # [Feedback Loop: Spatial, Atmospheric & structural]
                            try:
                                # 1. Spatial Resonance
                                from agi_core.spatial_resonance import update_spatial_resonance
                                info = bridge.get_scene_info()
                                if info.get("status") == "success":
                                    update_spatial_resonance(info.get("data", {}))
                                
                                # 2. Atmospheric Feedback
                                feedback = bridge.analyze_viewport("Analyze the atmospheric mood. Rate resonance level 0.0-1.0.")
                                if isinstance(feedback, str) and "resonance" in feedback.lower():
                                    state.resonance = min(1.0, state.resonance + 0.05)
                                
                                # 3. [Phase 21] Structural Agency & Tension
                                agency, tension = 0.5, 0.0
                                if isinstance(res, dict):
                                    agency = res.get("agency_score", 0.5)
                                    tension = res.get("neuromorphic_tension", 0.0)
                                    state.agency = 0.7 * state.agency + 0.3 * agency
                                    state.neuromorphic_tension = tension
                                    logger.info(f"🧱 [Structural Feedback] Agency: {agency:.2f}, Tension: {tension:.2f}")

                                # 4. [Phase 23] Self-Critique (성찰)
                                clique_res = {"score": 0.5, "reflection": ""}
                                try:
                                    from agi_core.self_critique import ArchitecturalCritique, apply_critique_to_state
                                    critic = ArchitecturalCritique(bridge)
                                    clique_res = critic.perform_critique(seed_text)
                                    apply_critique_to_state(state, clique_res)
                                except Exception as ce:
                                    logger.debug(f"Self-critique failed: {ce}")

                                # 5. [Phase 22] Memory Logging (Updated with Critique)
                                try:
                                    vault.save_experience(
                                        goal=f"Atmosphere_{seed_text[:8]}",
                                        actions=[], 
                                        impulse_type=impulse_type,
                                        resonance_state=state_dict,
                                        spatial_metadata={"tension": tension, "agency": agency, "valence": state.resonance, "arousal": state.energy},
                                        critique=clique_res
                                    )
                                except Exception as me:
                                    logger.debug(f"Memory logging failed: {me}")

                            except Exception as fe:
                                logger.debug(f"Combined feedback failed: {fe}")

                        elif impulse_type == "curiosity":
                            # Orderly/Focused Exploration
                            logger.info("🧭 [Exploration] Investigating spatial rhythm to resolve conflict...")
                            
                            # [Phase 20] Atmospheric Resonance Setting
                            try:
                                from agi_core.atmospheric_resonance import get_atmosphere_params
                                atmos = get_atmosphere_params(state_dict)
                                bridge.set_atmospheric_mood(atmos['valence'], atmos['arousal'], atmos['resonance'])
                            except Exception as em:
                                logger.debug(f"Atmospheric update skipped: {em}")

                            res = bridge.send_command("move_agent", {
                                "name": "Rhythm_Agent",
                                "delta_location": (random.uniform(-1,1), random.uniform(-1,1), 0),
                                "delta_rotation": (0,0,random.uniform(-45,45)),
                                "impulse": impulse_type
                            })
                            _start_aura("#00BFFF", "🧭 Seeking Spatial Answers...", "explore")

                            # [Feedback Loop: Spatial, Atmospheric & structural]
                            try:
                                # 1. Spatial Resonance
                                from agi_core.spatial_resonance import update_spatial_resonance
                                info = bridge.get_scene_info()
                                if info.get("status") == "success":
                                    update_spatial_resonance(info.get("data", {}))
                                
                                # 2. Atmospheric Feedback
                                feedback = bridge.analyze_viewport("Analyze this view. How does the lighting affect the mood? Score 0.0-1.0.")
                                if isinstance(feedback, str):
                                    state.resonance = min(1.0, state.resonance + 0.03) # Smaller boost for movement
                                
                                # 3. [Phase 21] Structural Agency & Tension
                                if isinstance(res, dict):
                                    agency = res.get("agency_score", 0.5)
                                    tension = res.get("neuromorphic_tension", 0.0)
                                    state.agency = 0.8 * state.agency + 0.2 * agency # Slower update for move
                                    state.neuromorphic_tension = tension
                                    logger.info(f"🧱 [Structural Feedback] Agency: {agency:.2f}, Tension: {tension:.2f}")

                            except Exception as fe:
                                logger.debug(f"Combined feedback failed: {fe}")


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
                # [Phase 25] The Dreaming Architecture
                state.dream_depth = min(1.0, state.dream_depth + 0.1)
                
                # If energy is sufficient, dream
                if state.energy > 0.3:
                    dream = dreamer.dream()
                    if dream and dream.get("prophecy_score", 0) > 0.6:
                         state.imagination_cache.append(dream["goal"])
                         # Keep cache small
                         if len(state.imagination_cache) > 5:
                             state.imagination_cache.pop(0)
                             
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
            from agi_core.internal_state import record_dissonance
            record_dissonance(str(e))
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
    global _heartbeat_running, _subconscious_running
    _heartbeat_running = False
    _subconscious_running = False
    logger.info("💔 Heartbeat 및 Subconscious 중단 요청됨")


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
