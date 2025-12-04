"""
Flow Observer → Binaural Beat Generator
흐름 상태를 뇌파 동기화 주파수로 변환

사용법:
  python flow_to_binaural_encoder.py --duration 600  # 10분
  python flow_to_binaural_encoder.py --quality 0.85  # 특정 품질 시뮬
"""

import json
import numpy as np
import wave
import struct
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import argparse


class BinauralBeatGenerator:
    """Binaural Beat 오디오 생성기"""
    
    SAMPLE_RATE = 44100  # CD quality
    
    # Solfeggio frequencies (치유/집중 주파수)
    FREQUENCIES = {
        "grounding": 174,   # 안정화
        "liberation": 396,  # 두려움 해소
        "transformation": 417,  # 변화 촉진
        "miracle": 528,     # DNA 복구
        "connection": 639,  # 관계 조화
        "awakening": 852,   # 직관 활성화
        "natural": 432      # 자연 공명
    }
    
    def __init__(self):
        self.output_dir = Path("outputs/sonic_memory")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_binaural(
        self,
        base_freq: float,
        beat_freq: float,
        duration_sec: int,
        amplitude: float = 0.3
    ) -> np.ndarray:
        """
        Binaural beat 생성
        
        Args:
            base_freq: 기준 주파수 (Hz)
            beat_freq: 뇌파 목표 주파수 (Hz)
            duration_sec: 길이 (초)
            amplitude: 볼륨 (0.0-1.0)
        
        Returns:
            스테레오 오디오 샘플 (L/R)
        """
        samples = duration_sec * self.SAMPLE_RATE
        t = np.linspace(0, duration_sec, samples, False)
        
        # 좌측: base_freq
        left = amplitude * np.sin(2 * np.pi * base_freq * t)
        
        # 우측: base_freq + beat_freq
        right = amplitude * np.sin(2 * np.pi * (base_freq + beat_freq) * t)
        
        # 스테레오 결합
        stereo = np.column_stack((left, right))
        return (stereo * 32767).astype(np.int16)
    
    def flow_to_params(self, flow_quality: float) -> Dict[str, float]:
        """
        Flow quality → 음악 파라미터 매핑
        
        Args:
            flow_quality: 0.0 (산만) ~ 1.0 (완전 몰입)
        
        Returns:
            {base_freq, beat_freq, amplitude}
        """
        if flow_quality >= 0.85:
            # 깊은 몰입: Alpha-Theta 경계
            return {
                "base_freq": self.FREQUENCIES["natural"],
                "beat_freq": 10,  # Alpha (10 Hz)
                "amplitude": 0.25,
                "state": "deep_flow"
            }
        elif flow_quality >= 0.6:
            # 중간 집중: Low Beta
            return {
                "base_freq": self.FREQUENCIES["miracle"],
                "beat_freq": 15,  # Low Beta (15 Hz)
                "amplitude": 0.3,
                "state": "focused"
            }
        elif flow_quality >= 0.3:
            # 약한 집중: High Alpha
            return {
                "base_freq": self.FREQUENCIES["connection"],
                "beat_freq": 12,  # High Alpha (12 Hz)
                "amplitude": 0.35,
                "state": "light_focus"
            }
        else:
            # 산만: Theta (재집중 유도)
            return {
                "base_freq": self.FREQUENCIES["grounding"],
                "beat_freq": 6,  # Theta (6 Hz)
                "amplitude": 0.4,
                "state": "distracted"
            }
    
    def save_wav(self, audio: np.ndarray, filename: str):
        """WAV 파일 저장"""
        path = self.output_dir / filename
        
        with wave.open(str(path), 'w') as wav:
            wav.setnchannels(2)  # 스테레오
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(self.SAMPLE_RATE)
            wav.writeframes(audio.tobytes())
        
        print(f"✅ Saved: {path}")
        return path
    
    def generate_from_flow_report(
        self,
        duration_sec: int = 600
    ) -> Optional[Path]:
        """
        Flow Observer 리포트 → Binaural beat 생성
        
        Args:
            duration_sec: 생성 길이 (기본 10분)
        
        Returns:
            생성된 WAV 파일 경로
        """
        report_path = Path("outputs/flow_observer_report_latest.json")
        
        if not report_path.exists():
            print("❌ Flow report not found. Run: Flow: Generate Report (1h)")
            return None
        
        with open(report_path) as f:
            data = json.load(f)
        
        # 현재 Flow quality 추출
        flow_quality = data.get("current_flow_quality", 0.5)
        
        # 파라미터 생성
        params = self.flow_to_params(flow_quality)
        
        print(f"🎵 Generating binaural beat:")
        print(f"   Flow Quality: {flow_quality:.2f}")
        print(f"   State: {params['state']}")
        print(f"   Base Freq: {params['base_freq']} Hz")
        print(f"   Beat Freq: {params['beat_freq']} Hz")
        print(f"   Duration: {duration_sec // 60}m {duration_sec % 60}s")
        
        # 오디오 생성
        audio = self.generate_binaural(
            base_freq=params["base_freq"],
            beat_freq=params["beat_freq"],
            duration_sec=duration_sec,
            amplitude=params["amplitude"]
        )
        
        # 파일명
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"binaural_{params['state']}_{timestamp}.wav"
        
        # 저장
        return self.save_wav(audio, filename)


def main():
    parser = argparse.ArgumentParser(
        description="Flow state to binaural beat converter"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=600,
        help="Duration in seconds (default: 600 = 10 min)"
    )
    parser.add_argument(
        "--quality",
        type=float,
        help="Override flow quality (0.0-1.0)"
    )
    
    args = parser.parse_args()
    
    generator = BinauralBeatGenerator()
    
    # Manual quality override
    if args.quality is not None:
        params = generator.flow_to_params(args.quality)
        audio = generator.generate_binaural(
            base_freq=params["base_freq"],
            beat_freq=params["beat_freq"],
            duration_sec=args.duration,
            amplitude=params["amplitude"]
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"binaural_manual_{params['state']}_{timestamp}.wav"
        generator.save_wav(audio, filename)
    else:
        # From flow report
        generator.generate_from_flow_report(args.duration)


if __name__ == "__main__":
    main()
