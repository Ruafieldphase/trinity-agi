#!/usr/bin/env python3
"""
🎵 Music Daemon - 자동 Binaural Beat 재생 시스템
Flow 상태 모니터링 → 자동 음악 생성 → 재생 (Windows Media Player)
+ Event Bus 통합: 리듬 펄스 발행, 플로우 이벤트 구독
+ Groove Engine: 마이크로타이밍 & 스펙트럴 밸런스
+ System Stress Detection: CPU/메모리/프로세스 기반 자동 안정화
+ Philosophy: 음악은 시스템의 면역체계 (코어의 통찰)
"""

import json
import time
import subprocess
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging
import psutil  # 시스템 리소스 모니터링
from workspace_root import get_workspace_root

# Add fdo_agi_repo to path
workspace_root = get_workspace_root()
sys.path.insert(0, str(workspace_root))
sys.path.insert(0, str(workspace_root / "fdo_agi_repo"))

try:
    from fdo_agi_repo.utils.event_bus import EventBus
    from fdo_agi_repo.utils.groove_engine import GrooveEngine, GrooveProfile
    HAS_EVENT_BUS = True
except ImportError:
    logging.warning("EventBus not available, running in standalone mode")
    EventBus = None
    GrooveEngine = None
    GrooveProfile = None
    HAS_EVENT_BUS = False

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('outputs/music_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MusicDaemon:
    def __init__(self, workspace_root: Path, interval: int = 60, flow_threshold: float = 0.3):
        """
        Args:
            workspace_root: 워크스페이스 루트 디렉토리
            interval: 체크 간격 (초)
            flow_threshold: Flow 임계값 (이하면 음악 재생)
        """
        self.workspace_root = workspace_root
        self.interval = interval
        self.flow_threshold = flow_threshold
        self.last_play_time = None
        self.min_play_interval = timedelta(minutes=10)  # 최소 10분 간격
        self.current_player_pid = None
        
        # System Stress Thresholds (코어의 "면역체계" 개념)
        self.stress_thresholds = {
            "cpu_percent": 80.0,      # CPU 80% 이상
            "memory_percent": 85.0,   # 메모리 85% 이상
            "process_count": 200,     # 프로세스 200개 이상
            "critical_cpu": 95.0,     # 위급 상황
        }
        
        # Event Bus 초기화 (optional)
        self.event_bus = None
        self.groove_engine = None
        if HAS_EVENT_BUS:
            event_log_path = workspace_root / "outputs" / "event_bus.jsonl"
            self.event_bus = EventBus(str(event_log_path))
            
            # Groove Engine 초기화
            groove_profile_path = workspace_root / "outputs" / "groove_profile_latest.json"
            if groove_profile_path.exists():
                self.groove_engine = GrooveEngine.load_profile(str(groove_profile_path))
                logger.info(f"✅ Loaded groove profile: {groove_profile_path}")
            else:
                self.groove_engine = GrooveEngine()
                logger.info("✅ Created default groove engine")
        
        # Flow 이벤트 구독
        self.event_bus.subscribe("flow_state_changed", self._on_flow_state_changed)
        logger.info("📡 Subscribed to flow_state_changed events")
    
    def _on_flow_state_changed(self, event: dict):
        """Flow 상태 변경 이벤트 핸들러"""
        payload = event.get("payload", {})
        flow_score = payload.get("flow_score", 0.0)
        state = payload.get("state", "unknown")
        logger.info(f"📡 Received flow event: {state} (score: {flow_score:.2f})")
        
        # 이벤트 기반 즉시 반응 (옵션)
        if flow_score < self.flow_threshold * 0.5:  # 매우 낮으면 즉시 대응
            logger.warning(f"⚠️ Very low flow detected: {flow_score:.2f}")
    
    def _publish_rhythm_pulse(self, brainwave: str, tempo_bpm: float):
        """리듬 펄스 이벤트 발행"""
        if self.event_bus:
            self.event_bus.publish("rhythm_pulse", {
                "brainwave_target": brainwave,
                "tempo_bpm": tempo_bpm,
                "timestamp": datetime.now().isoformat(),
                "source": "music_daemon"
            })
            logger.debug(f"📡 Published rhythm_pulse: {brainwave} @ {tempo_bpm} BPM")
        
        # Optionally, create an auto-goal from the rhythm event when enabled
        if getattr(self, 'auto_goal', False):
            try:
                from fdo_agi_repo.utils.music_goal_mapper import ensure_goal_from_event
                goal_id = ensure_goal_from_event({
                    'data': {'brainwave_target': brainwave, 'tempo_bpm': tempo_bpm},
                    'timestamp': datetime.now().isoformat(),
                    'tempo': tempo_bpm,
                    'brainwave_band': brainwave
                })
                
                if goal_id:
                    logger.info(f"🎯 Auto-goal created: {goal_id}")
                    
                    # Log music-goal event
                    event_log_path = self.workspace_root / "outputs" / "music_goal_events.jsonl"
                    event_log_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(event_log_path, "a", encoding="utf-8") as f:
                        event_record = {
                            "timestamp": datetime.now().isoformat(),
                            "tempo": tempo_bpm,
                            "brainwave": brainwave,
                            "goal_id": goal_id,
                            "goal_created": True
                        }
                        f.write(json.dumps(event_record, ensure_ascii=False) + "\n")
            except Exception:
                logger.exception("Failed to ensure goal from rhythm event")
    
    def get_latest_flow_report(self) -> dict:
        """최근 Flow Observer 리포트 읽기"""
        report_path = self.workspace_root / "outputs" / "flow_observer_report_latest.json"
        
        if not report_path.exists():
            logger.warning(f"Flow report not found: {report_path}")
            return None
            
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read flow report: {e}")
            return None
    
    def analyze_flow_state(self, report: dict) -> dict:
        """Flow 상태 분석"""
        if not report:
            return {"state": "unknown", "score": 0.0, "need_music": False}
        
        # Flow Score 계산 (0.0 ~ 1.0)
        flow_score = report.get("flow_metrics", {}).get("flow_score", 0.5)
        current_state = report.get("current_state", "unknown")
        
        # 음악 필요 여부 판단
        need_music = flow_score < self.flow_threshold
        
        return {
            "state": current_state,
            "score": flow_score,
            "need_music": need_music,
            "brainwave_target": self._get_brainwave_target(flow_score)
        }
    
    def _get_brainwave_target(self, flow_score: float) -> str:
        """Flow Score → 목표 뇌파 대역"""
        if flow_score < 0.2:
            return "delta"  # 깊은 휴식
        elif flow_score < 0.4:
            return "theta"  # 창의성
        elif flow_score < 0.6:
            return "alpha"  # 이완된 집중
        else:
            return "beta"   # 활성 집중
    
    def detect_system_stress(self) -> dict:
        """시스템 스트레스 감지 (코어: "음악 = 면역체계")"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            process_count = len(psutil.pids())
            
            # 스트레스 레벨 계산 (0.0 ~ 1.0)
            cpu_stress = min(cpu_percent / 100.0, 1.0)
            memory_stress = memory.percent / 100.0
            process_stress = min(process_count / self.stress_thresholds["process_count"], 1.0)
            
            overall_stress = (cpu_stress * 0.5 + memory_stress * 0.3 + process_stress * 0.2)
            
            # 스트레스 상태 분류
            if overall_stress >= 0.8:
                stress_level = "critical"
                recommended_brainwave = "delta"  # 강제 휴식
            elif overall_stress >= 0.6:
                stress_level = "high"
                recommended_brainwave = "theta"  # 창의적 이완
            elif overall_stress >= 0.4:
                stress_level = "moderate"
                recommended_brainwave = "alpha"  # 차분한 집중
            else:
                stress_level = "low"
                recommended_brainwave = "beta"   # 활성 집중
            
            result = {
                "stress_level": stress_level,
                "overall_stress": overall_stress,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "process_count": process_count,
                "recommended_brainwave": recommended_brainwave,
                "needs_intervention": overall_stress >= 0.7
            }
            
            logger.info(f"🩺 System Health: {stress_level} (stress: {overall_stress:.2f}, CPU: {cpu_percent:.1f}%, MEM: {memory.percent:.1f}%)")
            
            # Event Bus에 시스템 헬스 이벤트 발행
            if overall_stress >= 0.6:
                if self.event_bus:
                    self.event_bus.publish("system_stress_detected", {
                        "stress_level": stress_level,
                        "overall_stress": overall_stress,
                        "metrics": result,
                        "timestamp": datetime.now().isoformat()
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to detect system stress: {e}")
            return {
                "stress_level": "unknown",
                "overall_stress": 0.0,
                "needs_intervention": False,
                "recommended_brainwave": "alpha"
            }
    
    def get_health_gate_status(self) -> dict:
        """Health Gate 상태 읽기 (최근 30분)"""
        status_file = self.workspace_root / "outputs" / "quick_status_latest.json"
        
        if not status_file.exists():
            return None
        
        try:
            # 파일이 30분 이내인지 체크
            file_age = datetime.now() - datetime.fromtimestamp(status_file.stat().st_mtime)
            if file_age > timedelta(minutes=30):
                logger.debug(f"Health gate status is stale ({file_age.total_seconds():.0f}s old)")
                return None
            
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read health gate status: {e}")
            return None
    
    def analyze_combined_state(self, flow_report: dict, system_stress: dict, health_gate: dict) -> dict:
        """Flow + System Stress + Health Gate 종합 분석"""
        # Flow 분석
        flow_analysis = self.analyze_flow_state(flow_report) if flow_report else {
            "state": "unknown",
            "score": 0.5,
            "need_music": False,
            "brainwave_target": "alpha"
        }
        
        # 시스템 스트레스가 높으면 Flow보다 우선
        if system_stress["needs_intervention"]:
            logger.warning(f"⚠️ System stress detected ({system_stress['stress_level']}), overriding flow analysis")
            flow_analysis["need_music"] = True
            flow_analysis["brainwave_target"] = system_stress["recommended_brainwave"]
            flow_analysis["reason"] = "system_stress"
        else:
            flow_analysis["reason"] = "flow_state"
        
        # Health Gate 상태 추가
        if health_gate:
            flow_analysis["health_gate"] = {
                "status": health_gate.get("overall_status", "unknown"),
                "degraded_components": health_gate.get("degraded_components", [])
            }
        
        flow_analysis["system_stress"] = system_stress
        
        return flow_analysis

    def _brainwave_to_bpm(self, brainwave: str) -> float:
        """
        Binaural target(알파/세타 등)를 '느슨한 템포'로 매핑한다.
        - 정확한 과학적 변환이 아니라, GrooveEngine에 넣을 BPM 스케일링용 근사치.
        """
        bw = str(brainwave or "").strip().lower()
        # 느슨한 근사: 더 느린 대역일수록 BPM을 낮춘다.
        mapping = {
            "delta": 42.0,
            "theta": 50.0,
            "alpha": 60.0,
            "beta": 80.0,
            "gamma": 110.0,
        }
        return float(mapping.get(bw, 60.0))

    def _get_groove_hint(self, brainwave: str) -> dict:
        """
        GrooveEngine의 microtiming을 안전하게 가져온다.
        - GrooveEngine API는 beat_index(int), bpm(float)을 기대한다.
        - brainwave 문자열을 beat_index로 넘기면 TypeError가 나므로, 여기서 변환한다.
        """
        bpm = self._brainwave_to_bpm(brainwave)
        hint: dict = {"offset_ms": 0.0, "swing_factor": 0.0, "bpm": bpm, "source": "none"}
        if not self.groove_engine:
            return hint
        try:
            # off-beat(1)에서 swing 영향이 더 드러나므로 1을 사용
            offset_sec = float(self.groove_engine.compute_beat_offset(1, bpm))
            hint["offset_ms"] = offset_sec * 1000.0
            hint["swing_factor"] = float(getattr(self.groove_engine.profile, "swing_ratio", 0.0))
            hint["source"] = "groove_engine"
            return hint
        except Exception as e:
            hint["source"] = "groove_engine_error"
            hint["error"] = str(e)
            logger.warning(f"⚠️ Groove hint failed: {e}")
            return hint
    
    def generate_binaural_beat(self, brainwave: str, duration: int = 300) -> Path:
        """Binaural Beat 생성 (Groove Engine 적용)"""
        logger.info(f"🎼 Generating {brainwave} binaural beat ({duration}s)...")
        
        # Groove Engine에서 microtiming hint 가져오기 (안전 변환 포함)
        groove_hint = self._get_groove_hint(brainwave)
        offset_ms = float(groove_hint.get("offset_ms", 0.0) or 0.0)
        swing_factor = float(groove_hint.get("swing_factor", 0.0) or 0.0)
        
        logger.info(f"🎵 Groove: offset={offset_ms:.1f}ms, swing={swing_factor:.2f}")
        
        script_path = self.workspace_root / "scripts" / "flow_binaural_generator.py"
        venv_python = self.workspace_root / "fdo_agi_repo" / ".venv" / "Scripts" / "python.exe"
        
        python_cmd = str(venv_python) if venv_python.exists() else "python"
        
        try:
            result = subprocess.run(
                [python_cmd, str(script_path), "--duration", str(duration), "--force-brainwave", brainwave],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # 최근 생성된 파일 찾기
                output_dir = self.workspace_root / "outputs"
                audio_files = sorted(output_dir.glob("binaural_flow_*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
                
                if audio_files:
                    logger.info(f"✅ Generated: {audio_files[0].name}")
                    
                    # 리듬 펄스 이벤트 발행
                    tempo_bpm = 60.0  # 기본 템포 (실제로는 brainwave에서 계산)
                    self._publish_rhythm_pulse(brainwave, tempo_bpm)
                    
                    return audio_files[0]
            
            logger.error(f"Failed to generate binaural beat: {result.stderr}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating binaural beat: {e}")
            return None
    
    def play_audio(self, audio_path: Path, volume: int = 30):
        """Windows Media Player로 재생 (백그라운드)"""
        try:
            # 기존 재생 중이면 중지
            if self.current_player_pid:
                try:
                    subprocess.run(["taskkill", "/F", "/PID", str(self.current_player_pid)], 
                                   capture_output=True, timeout=5)
                except:
                    pass
            
            # PowerShell 명령으로 볼륨 조절 + 재생
            ps_cmd = f"""
            $wmp = New-Object -ComObject WMPlayer.OCX
            $wmp.settings.volume = {volume}
            $wmp.URL = '{audio_path}'
            $wmp.controls.play()
            Start-Sleep -Seconds 2
            """
            
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.current_player_pid = proc.pid
            logger.info(f"🎧 Playing: {audio_path.name} (PID: {proc.pid}, Volume: {volume}%)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return False
    
    def should_play_music(self, analysis: dict) -> bool:
        """음악 재생 여부 판단 (System Stress + Flow 통합)"""
        # 1. 시스템 스트레스가 높으면 무조건 재생
        if analysis.get("reason") == "system_stress":
            logger.info("🚨 System stress intervention required")
            return True
        
        # 2. Flow Score가 임계값 이하면 재생
        if analysis.get("need_music", False):
            return True
        
        # 3. Health Gate가 degraded면 예방적 재생
        health_gate = analysis.get("health_gate", {})
        if health_gate.get("status") == "degraded":
            logger.info("⚠️ Health gate degraded, preventive music therapy")
            return True
        
        return False
    
    def run_once(self):
        """1회 체크 + 필요 시 재생 (System Stress + Flow 통합)"""
        logger.info("🔍 Checking system health + flow state...")
        
        # 1. 시스템 스트레스 감지 (최우선)
        system_stress = self.detect_system_stress()
        
        # 2. Flow 리포트 읽기
        flow_report = self.get_latest_flow_report()
        
        # 3. Health Gate 상태 읽기
        health_gate = self.get_health_gate_status()
        
        # 4. 종합 분석
        analysis = self.analyze_combined_state(flow_report, system_stress, health_gate)
        
        logger.info(f"📊 Analysis: state={analysis['state']}, score={analysis['score']:.2f}, "
                   f"stress={system_stress['stress_level']}, "
                   f"brainwave={analysis['brainwave_target']}, "
                   f"need_music={analysis['need_music']} ({analysis['reason']})")
        
        # 5. 음악 재생 판단
        if self.should_play_music(analysis):
            brainwave = analysis["brainwave_target"]
            logger.info(f"🎵 Flow {analysis['score']:.2f} < {self.flow_threshold} or stress intervention needed → Play {brainwave}")
            
            audio_file = self.generate_binaural_beat(brainwave, duration=300)
            if audio_file:
                self.play_audio(audio_file, volume=30)
                self.last_play_time = datetime.now()
                
                # 재생 이벤트 로깅
                if self.event_bus:
                    self.event_bus.publish("music_therapy_applied", {
                        "brainwave": brainwave,
                        "reason": analysis["reason"],
                        "flow_score": analysis["score"],
                        "stress_level": system_stress["stress_level"],
                        "audio_file": str(audio_file),
                        "timestamp": datetime.now().isoformat()
                    })
        else:
            logger.info(f"✅ No music needed (flow: {analysis['score']:.2f}, stress: {system_stress['stress_level']})")
        logger.info(f"📊 Flow State: {analysis['state']} (score: {analysis['score']:.2f}, target: {analysis['brainwave_target']})")
        
        # 음악 재생 필요 여부
        if self.should_play_music(analysis):
            logger.info(f"🎵 Flow is low ({analysis['score']:.2f} < {self.flow_threshold}), generating music...")
            
            # Binaural Beat 생성
            audio_path = self.generate_binaural_beat(
                brainwave=analysis['brainwave_target'],
                duration=300  # 5분
            )
            
            if audio_path and audio_path.exists():
                # 재생
                if self.play_audio(audio_path, volume=25):
                    self.last_play_time = datetime.now()
                    logger.info(f"✅ Music therapy started (target: {analysis['brainwave_target']})")
            else:
                logger.error("Failed to generate or find audio file")
        else:
            logger.info(f"✅ Flow is healthy ({analysis['score']:.2f}), no music needed")
    
    def run(self):
        """데몬 메인 루프"""
        logger.info(f"🎵 Music Daemon started (interval: {self.interval}s, threshold: {self.flow_threshold})")
        logger.info(f"📁 Workspace: {self.workspace_root}")
        
        try:
            while True:
                self.run_once()
                logger.debug(f"⏰ Sleeping for {self.interval}s...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Music Daemon stopped by user")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}", exc_info=True)


def main():
    parser = argparse.ArgumentParser(description="🎵 Music Daemon - Auto Binaural Beat Player")
    parser.add_argument("--interval", type=int, default=60, help="Check interval (seconds)")
    parser.add_argument("--threshold", type=float, default=0.3, help="Flow threshold (0.0-1.0)")
    parser.add_argument("--auto-goal", action="store_true", help="Automatically create goals from rhythm pulses")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    workspace_root = get_workspace_root()
    daemon = MusicDaemon(workspace_root, interval=args.interval, flow_threshold=args.threshold)
    daemon.auto_goal = args.auto_goal
    
    if args.once:
        daemon.run_once()
    else:
        daemon.run()


if __name__ == "__main__":
    main()
