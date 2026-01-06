import os
import time
import subprocess
import logging
import threading
import psutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Windows specific imports for focus and flow
try:
    import pygetwindow as gw
    from pynput import keyboard, mouse
except ImportError:
    gw = None
    keyboard = None
    mouse = None

logger = logging.getLogger("SensoryBridge")

class SensoryMotorBridge:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SensoryMotorBridge, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, workspace_root: Path):
        if self._initialized:
            return
            
        self.workspace_root = workspace_root
        self.last_mutation_check = time.time()
        self._last_file_count = self._count_python_files()
        
        # Flow (Input Rhythm) tracking
        self.input_event_count = 0
        self.last_tempo_calc_time = time.time()
        self.current_tempo = 0.0 # Events per minute
        self._start_input_listeners()
        
        self._initialized = True

    def _start_input_listeners(self):
        """사용자 입력 리듬을 감지하기 위한 백그라운드 리스너 시작"""
        if keyboard is None or mouse is None:
            logger.warning("pynput not available. Input rhythm sensing disabled.")
            return

        def on_event(*args):
            self.input_event_count += 1

        # 백그라운드 스레드에서 리스너 실행
        k_listener = keyboard.Listener(on_press=on_event)
        m_listener = mouse.Listener(on_click=on_event, on_scroll=on_event)
        
        k_listener.daemon = True
        m_listener.daemon = True
        
        k_listener.start()
        m_listener.start()
        logger.info("📡 Input rhythm listeners (Keyboard/Mouse) activated.")

    def _count_python_files(self) -> int:
        """코드 변이 감지를 위해 Python 파일 개수 체크"""
        try:
            return len(list(self.workspace_root.glob("**/*.py")))
        except:
            return 0

    def sense_active_context(self) -> Dict[str, str]:
        """현재 활성화된 윈도우와 프로세스 감지"""
        context = {"title": "unknown", "process": "unknown"}
        if gw is None:
            return context
            
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                context["title"] = active_window.title
                # 프로세스 이름은 psutil을 통해 추측 (간소화된 방식)
                # 정밀한 구현은 Win32 API가 필요하나 여기서는 타이틀 키워드로 일단 처리
                title_lower = active_window.title.lower()
                if "blender" in title_lower: context["process"] = "blender.exe"
                elif "visual studio code" in title_lower: context["process"] = "code.exe"
                elif "chrome" in title_lower or "edge" in title_lower: context["process"] = "browser"
                else: context["process"] = "other"
        except Exception as e:
            logger.debug(f"Context sensing failed: {e}")
            
        return context

    def sense_input_tempo(self) -> float:
        """입력 템포 계산 (Normalized RPM)"""
        now = time.time()
        duration = now - self.last_tempo_calc_time
        if duration < 1.0: # 최소 1초 간격으로 갱신
            return self.current_tempo
            
        # 분당 이벤트 수 (RPM) 계산
        rpm = (self.input_event_count / duration) * 60
        self.input_event_count = 0
        self.last_tempo_calc_time = now
        
        # RPM을 0.0~1.0 범위로 정규화 (최대 300 RPM 기준)
        normalized_tempo = min(1.0, rpm / 300.0)
        # 평활화 (Moving Average)
        self.current_tempo = 0.7 * self.current_tempo + 0.3 * normalized_tempo
        return self.current_tempo

    def sense_network_wind(self) -> float:
        """네트워크 지연을 '바람'으로 감지 (0.0~1.0)"""
        try:
            # ping 8.8.8.8 (1회)
            start = time.time()
            # Windows: -n 1
            res = subprocess.run(["ping", "-n", "1", "8.8.8.8"], 
                               capture_output=True, timeout=1.0)
            latency = (time.time() - start) * 1000 # ms
            
            # 20ms 이하면 0.0, 500ms 이상이면 1.0으로 매핑
            wind = (latency - 20) / 480
            return max(0.0, min(1.0, wind))
        except:
            return 0.5 # 감지 실패 시 중간값 (불확실함)

    def sense_audio_ambience(self) -> float:
        """시스템 오디오 레벨 감지 (simulated jitter)"""
        cpu_jitter = psutil.cpu_percent(interval=None) / 200.0 # 0.0~0.5
        random_pulse = (time.time() % 1.0) * 0.5 # 톱니파
        return max(0.0, min(1.0, cpu_jitter + random_pulse))

    def detect_mutations(self) -> bool:
        """파일 시스템 변화(코드 변이) 감지"""
        current_count = self._count_python_files()
        if current_count != self._last_file_count:
            self._last_file_count = current_count
            return True
        return False

    def get_all_senses(self) -> Dict[str, Any]:
        """모든 감각 데이터를 통합하여 반환"""
        return {
            "network_wind": self.sense_network_wind(),
            "audio_ambience": self.sense_audio_ambience(),
            "has_mutation": self.detect_mutations(),
            "active_context": self.sense_active_context(),
            "input_tempo": self.sense_input_tempo(),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Test
    bridge = SensoryMotorBridge(Path("c:/workspace/agi"))
    print("📡 Monitoring focus and flow for 5 seconds...")
    for _ in range(5):
        time.sleep(1)
        print(f"Sensory Scan: {bridge.get_all_senses()}")
