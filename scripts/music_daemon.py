#!/usr/bin/env python3
"""
🎵 Music Daemon - 자동 Binaural Beat 재생 시스템
Flow 상태 모니터링 → 자동 음악 생성 → 재생 (Windows Media Player)
+ Event Bus 통합: 리듬 펄스 발행, 플로우 이벤트 구독
+ Groove Engine: 마이크로타이밍 & 스펙트럴 밸런스
"""

import json
import time
import subprocess
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add fdo_agi_repo to path
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root / "fdo_agi_repo"))

from fdo_agi_repo.utils.event_bus import EventBus
from fdo_agi_repo.utils.groove_engine import GrooveEngine, GrooveProfile

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
        
        # Event Bus 초기화
        event_log_path = workspace_root / "outputs" / "event_bus.jsonl"
        self.event_bus = EventBus(str(event_log_path))
        
        # Groove Engine 초기화
        groove_profile_path = workspace_root / "outputs" / "groove_profile_latest.json"
        if groove_profile_path.exists():
            self.groove_engine = GrooveEngine.load_profile(str(groove_profile_path))
            logger.info(f"✅ Loaded groove profile: {groove_profile_path}")
        else:
            self.groove_engine = GrooveEngine()
            logger.info("ℹ️ Using default groove profile")
        
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
        self.event_bus.publish("rhythm_pulse", {
            "brainwave_target": brainwave,
            "tempo_bpm": tempo_bpm,
            "timestamp": datetime.now().isoformat(),
            "source": "music_daemon"
        })
        logger.debug(f"📡 Published rhythm_pulse: {brainwave} @ {tempo_bpm} BPM")
        
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
    
    def generate_binaural_beat(self, brainwave: str, duration: int = 300) -> Path:
        """Binaural Beat 생성 (Groove Engine 적용)"""
        logger.info(f"🎼 Generating {brainwave} binaural beat ({duration}s)...")
        
        # Groove Engine에서 microtiming offset 가져오기
        groove_hint = self.groove_engine.compute_microtiming_offset(brainwave, 1.0)  # phase=1.0 (기본)
        offset_ms = groove_hint.get("offset_ms", 0.0)
        swing_factor = groove_hint.get("swing_factor", 0.0)
        
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
        """음악 재생 여부 판단"""
        if not analysis.get("need_music"):
            return False
        
        # 최소 재생 간격 체크
        if self.last_play_time:
            elapsed = datetime.now() - self.last_play_time
            if elapsed < self.min_play_interval:
                logger.debug(f"⏳ Too soon to play (waited {elapsed.total_seconds():.0f}s / {self.min_play_interval.total_seconds():.0f}s)")
                return False
        
        return True
    
    def run_once(self):
        """1회 체크 + 필요 시 재생"""
        logger.info("🔍 Checking Flow state...")
        
        # Flow 리포트 읽기
        report = self.get_latest_flow_report()
        if not report:
            logger.warning("No flow report available, skipping...")
            return
        
        # 상태 분석
        analysis = self.analyze_flow_state(report)
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
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    workspace_root = Path(__file__).parent.parent
    daemon = MusicDaemon(workspace_root, interval=args.interval, flow_threshold=args.threshold)
    
    if args.once:
        daemon.run_once()
    else:
        daemon.run()


if __name__ == "__main__":
    main()
