#!/usr/bin/env python3
"""
🎼 Groove Profile Generator
최근 텔레메트리(Flow Observer, 마이크 분석)로부터 groove 설정 도출
outputs/groove_profile_latest.json에 저장
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

# Add fdo_agi_repo to path
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root / "fdo_agi_repo"))

from fdo_agi_repo.utils.groove_engine import GrooveProfile

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class GrooveProfileGenerator:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        
    def load_recent_telemetry(self, hours: int = 24) -> dict:
        """최근 텔레메트리 데이터 로드"""
        telemetry = {
            "flow_reports": [],
            "microphone_analyses": [],
            "rhythm_events": []
        }
        
        # Flow Observer 리포트
        flow_report_path = self.workspace_root / "outputs" / "flow_observer_report_latest.json"
        if flow_report_path.exists():
            try:
                with open(flow_report_path, 'r', encoding='utf-8') as f:
                    telemetry["flow_reports"].append(json.load(f))
                logger.info(f"✅ Loaded flow report: {flow_report_path}")
            except Exception as e:
                logger.warning(f"Failed to load flow report: {e}")
        
        # 마이크 분석
        mic_analysis_path = self.workspace_root / "outputs" / "microphone" / "microphone_analysis_latest.json"
        if mic_analysis_path.exists():
            try:
                with open(mic_analysis_path, 'r', encoding='utf-8') as f:
                    telemetry["microphone_analyses"].append(json.load(f))
                logger.info(f"✅ Loaded microphone analysis: {mic_analysis_path}")
            except Exception as e:
                logger.warning(f"Failed to load microphone analysis: {e}")
        
        # Event Bus 리듬 이벤트 (최근 24시간)
        event_bus_path = self.workspace_root / "outputs" / "event_bus.jsonl"
        if event_bus_path.exists():
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                with open(event_bus_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event.get("timestamp", ""))
                        if event_time >= cutoff_time and event.get("topic") == "rhythm_pulse":
                            telemetry["rhythm_events"].append(event)
                logger.info(f"✅ Loaded {len(telemetry['rhythm_events'])} rhythm events")
            except Exception as e:
                logger.warning(f"Failed to load rhythm events: {e}")
        
        return telemetry
    
    def analyze_tempo_preference(self, telemetry: dict) -> float:
        """템포 선호도 분석"""
        # 기본값
        base_tempo = 120.0
        
        # Flow 상태 기반 조정
        if telemetry["flow_reports"]:
            flow_score = telemetry["flow_reports"][0].get("flow_metrics", {}).get("flow_score", 0.5)
            # High flow → faster tempo
            base_tempo = 100 + (flow_score * 40)  # 100-140 BPM
        
        # 마이크 주파수 분석
        if telemetry["microphone_analyses"]:
            dominant_freq = telemetry["microphone_analyses"][0].get("dominant_frequency", 0)
            if dominant_freq > 0:
                # 주파수 → BPM 변환 (매우 단순화)
                estimated_bpm = (dominant_freq / 2) * 60
                if 60 <= estimated_bpm <= 180:
                    base_tempo = (base_tempo + estimated_bpm) / 2  # 평균
        
        return round(base_tempo, 1)
    
    def analyze_microtiming_style(self, telemetry: dict) -> dict:
        """마이크로타이밍 스타일 분석"""
        # 기본: laid-back (약간 뒤로 밀림)
        push_ms = -5.0  # 기본적으로 약간 laid-back
        swing = 0.1
        
        # Flow 상태에 따른 조정
        if telemetry["flow_reports"]:
            flow_score = telemetry["flow_reports"][0].get("flow_metrics", {}).get("flow_score", 0.5)
            if flow_score < 0.3:
                # Low flow → more laid-back
                push_ms = -10.0
                swing = 0.15
            elif flow_score > 0.7:
                # High flow → more on-the-beat
                push_ms = -2.0
                swing = 0.05
        
        return {
            "push_ms": push_ms,
            "swing_factor": swing
        }
    
    def analyze_spectral_balance(self, telemetry: dict) -> dict:
        """스펙트럴 밸런스 분석"""
        balance = {
            "low": 0.4,
            "mid": 0.4,
            "high": 0.2
        }
        
        # 마이크 분석 기반 조정
        if telemetry["microphone_analyses"]:
            analysis = telemetry["microphone_analyses"][0]
            dominant_freq = analysis.get("dominant_frequency", 0)
            
            if dominant_freq < 250:  # 저주파 우세
                balance = {"low": 0.5, "mid": 0.3, "high": 0.2}
            elif dominant_freq > 2000:  # 고주파 우세
                balance = {"low": 0.3, "mid": 0.3, "high": 0.4}
        
        return balance
    
    def generate_profile(self, hours: int = 24) -> GrooveProfile:
        """프로파일 생성"""
        logger.info(f"🎼 Generating groove profile from last {hours}h telemetry...")
        
        # 텔레메트리 로드
        telemetry = self.load_recent_telemetry(hours)
        
        # 분석
        tempo = self.analyze_tempo_preference(telemetry)
        microtiming = self.analyze_microtiming_style(telemetry)
        spectral = self.analyze_spectral_balance(telemetry)
        
        logger.info(f"📊 Tempo: {tempo} BPM")
        logger.info(f"📊 Microtiming: push={microtiming['push_ms']:.1f}ms, swing={microtiming['swing_factor']:.2f}")
        logger.info(f"📊 Spectral: low={spectral['low']:.1f}, mid={spectral['mid']:.1f}, high={spectral['high']:.1f}")
        
        # 프로파일 생성 (GrooveProfile의 실제 생성자 사용)
        # spectral_balance를 bass/treble boost로 변환
        bass_boost = (spectral['low'] - 0.33) * 12.0  # -12 to +12 dB
        treble_boost = (spectral['high'] - 0.33) * 12.0
        
        profile = GrooveProfile(
            swing_ratio=microtiming["swing_factor"],
            push_pull_ms=microtiming["push_ms"],
            microtiming_variance=0.3,
            bass_boost_db=bass_boost,
            treble_boost_db=treble_boost,
            warmth_factor=0.5,
            name=f"auto_generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        return profile
    
    def save_profile(self, profile: GrooveProfile, output_path: Path):
        """프로파일 저장"""
        profile.save(output_path)  # Path 객체를 직접 전달
        logger.info(f"✅ Saved groove profile: {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="🎼 Groove Profile Generator")
    parser.add_argument("--hours", type=int, default=24, help="Lookback window (hours)")
    parser.add_argument("--output", type=str, help="Output JSON path")
    
    args = parser.parse_args()
    
    workspace_root = Path(__file__).parent.parent
    generator = GrooveProfileGenerator(workspace_root)
    
    # 프로파일 생성
    profile = generator.generate_profile(args.hours)
    
    # 저장
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = workspace_root / "outputs" / "groove_profile_latest.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generator.save_profile(profile, output_path)
    
    print(f"\n✅ Groove profile generated: {output_path}")
    print(f"📊 Swing Ratio: {profile.swing_ratio:.2f}")
    print(f"📊 Push/Pull: {profile.push_pull_ms:.1f} ms")
    print(f"📊 Bass Boost: {profile.bass_boost_db:.1f} dB")
    print(f"📊 Treble Boost: {profile.treble_boost_db:.1f} dB")
    print(f"📊 Warmth: {profile.warmth_factor:.2f}")


if __name__ == "__main__":
    main()
