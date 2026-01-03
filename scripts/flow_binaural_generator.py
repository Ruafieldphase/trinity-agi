#!/usr/bin/env python3
"""
🎵 Flow State → Binaural Beat Generator
Flow Observer 데이터를 읽어 뇌파 동기화 오디오를 생성합니다.

과학적 근거:
- Binaural beats: 양쪽 귀에 약간 다른 주파수 → 뇌가 차이 주파수로 동기화
- Alpha (8-13 Hz): 편안한 집중, 창의성
- Beta (13-30 Hz): 활성 사고, 문제 해결
- Theta (4-8 Hz): 명상, 깊은 휴식
- Delta (0.5-4 Hz): 깊은 수면

Usage:
    python scripts/flow_binaural_generator.py
    python scripts/flow_binaural_generator.py --duration 600 --quality 0.5
"""

import json
import sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from datetime import datetime
import argparse
from workspace_root import get_workspace_root


class FlowFrequencyMapper:
    """Flow quality → 뇌파 주파수 매핑"""
    
    # Solfeggio frequencies (고대 치유 주파수)
    FREQ_396 = 396   # Grounding, 불안 해소
    FREQ_432 = 432   # 자연 공명 주파수
    FREQ_528 = 528   # DNA repair, 치유
    FREQ_639 = 639   # 관계, 소통
    FREQ_741 = 741   # 직관, 문제 해결
    
    def __init__(self, flow_quality: float):
        """
        Args:
            flow_quality: 0.0 ~ 1.0 (Flow Observer에서)
        """
        self.quality = flow_quality
    
    def get_brainwave_params(self) -> dict:
        """Flow quality → Brainwave 파라미터"""
        
        if self.quality > 0.85:
            # 깊은 몰입: Alpha-Theta 경계
            return {
                "name": "Deep Flow (Alpha-Theta)",
                "base_freq": self.FREQ_432,
                "beat_freq": 10,  # 10 Hz (High Alpha)
                "carrier_type": "sine",
                "reason": "깊은 몰입 상태 유지"
            }
        
        elif self.quality > 0.7:
            # 좋은 집중: Mid Alpha
            return {
                "name": "Good Focus (Mid Alpha)",
                "base_freq": self.FREQ_528,
                "beat_freq": 12,  # 12 Hz (Mid Alpha)
                "carrier_type": "sine",
                "reason": "집중력 강화, 창의성 활성"
            }
        
        elif self.quality > 0.5:
            # 보통 집중: Low Beta
            return {
                "name": "Active Focus (Low Beta)",
                "base_freq": self.FREQ_639,
                "beat_freq": 15,  # 15 Hz (Low Beta)
                "carrier_type": "sine",
                "reason": "활성 사고, 문제 해결"
            }
        
        elif self.quality > 0.3:
            # 산만함: Theta로 진정
            return {
                "name": "Calming Down (Theta)",
                "base_freq": self.FREQ_396,
                "beat_freq": 6,  # 6 Hz (Theta)
                "carrier_type": "sine",
                "reason": "긴장 완화, 재집중 준비"
            }
        
        else:
            # 매우 산만: Deep Theta
            return {
                "name": "Deep Rest (Deep Theta)",
                "base_freq": self.FREQ_396,
                "beat_freq": 4.5,  # 4.5 Hz (Deep Theta)
                "carrier_type": "sine",
                "reason": "깊은 휴식, 리셋"
            }


class BinauralBeatGenerator:
    """Binaural beat 오디오 생성기"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
    
    def generate(
        self,
        base_freq: float,
        beat_freq: float,
        duration: int,
        carrier_type: str = "sine",
        fade_duration: float = 2.0
    ) -> np.ndarray:
        """
        Binaural beat 생성
        
        Args:
            base_freq: 기본 주파수 (Hz)
            beat_freq: 비트 주파수 (Hz) - 뇌가 인지할 주파수
            duration: 길이 (초)
            carrier_type: "sine" or "square"
            fade_duration: Fade in/out 길이 (초)
        
        Returns:
            Stereo audio array (int16)
        """
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Left channel: base_freq
        # Right channel: base_freq + beat_freq
        if carrier_type == "sine":
            left = np.sin(2 * np.pi * base_freq * t)
            right = np.sin(2 * np.pi * (base_freq + beat_freq) * t)
        else:
            # Square wave (더 강한 자극)
            left = np.sign(np.sin(2 * np.pi * base_freq * t))
            right = np.sign(np.sin(2 * np.pi * (base_freq + beat_freq) * t))
        
        # Fade in/out (갑작스런 소리 방지)
        fade_samples = int(fade_duration * self.sample_rate)
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        
        left[:fade_samples] *= fade_in
        left[-fade_samples:] *= fade_out
        right[:fade_samples] *= fade_in
        right[-fade_samples:] *= fade_out
        
        # Stereo array
        stereo = np.vstack([left, right]).T
        
        # Normalize to 16-bit
        stereo = (stereo * 0.8 * 32767).astype(np.int16)
        
        return stereo


def load_flow_state(report_path: Path = None) -> dict:
    """Flow Observer 리포트 로드"""
    if report_path is None:
        report_path = get_workspace_root() / "outputs" / "flow_observer_report_latest.json"
    
    if not report_path.exists():
        print(f"⚠️  Flow report not found: {report_path}")
        print(f"   Run: Flow Observer first")
        return None
    
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Flow State → Binaural Beat Generator")
    parser.add_argument("--duration", type=int, default=300, help="Audio duration (seconds)")
    parser.add_argument("--quality", type=float, help="Override flow quality (0.0-1.0)")
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument("--force-brainwave", type=str, choices=["delta", "theta", "alpha", "beta"], 
                        help="Force specific brainwave target (override Flow analysis)")
    args = parser.parse_args()
    
    # Force brainwave 모드
    if args.force_brainwave:
        brainwave_map = {
            "delta": ("Delta (0.5-4 Hz) - Deep Sleep", 2.0),
            "theta": ("Theta (4-8 Hz) - Creativity", 6.0),
            "alpha": ("Alpha (8-13 Hz) - Relaxed Focus", 10.0),
            "beta": ("Beta (14-30 Hz) - Active Focus", 18.0)
        }
        
        if args.force_brainwave in brainwave_map:
            state_name, beat_freq = brainwave_map[args.force_brainwave]
            print(f"\n🎯 Force Mode: {state_name}")
            print(f"🔊 Beat Frequency: {beat_freq} Hz")
            
            generator = BinauralBeatGenerator()
            audio = generator.generate(
                base_freq=200.0,
                beat_freq=beat_freq,
                duration=args.duration
            )
            
            # 저장
            output_dir = args.output_dir if args.output_dir else Path("outputs")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"binaural_{args.force_brainwave}_{timestamp}.wav"
            output_path = output_dir / filename
            
            wavfile.write(str(output_path), generator.sample_rate, audio)
            print(f"\n✅ Generated: {output_path}")
            print(f"📏 Duration: {args.duration}s")
            print(f"🎵 Target: {state_name}")
            
            return
    
    # Flow 상태 로드 (기존 로직)
    flow_data = load_flow_state()
    if flow_data is None:
        print("\n💡 Fallback: 기본 Alpha wave 생성 (quality=0.75)")
        quality = args.quality if args.quality else 0.75
    else:
        # 현재 Flow quality 추출
        quality = flow_data.get("summary", {}).get("average_flow_quality", 0.5)
        if args.quality:
            quality = args.quality
        
        print(f"\n📊 Current Flow Quality: {quality:.2f}")
    
    # Flow → 주파수 매핑
    mapper = FlowFrequencyMapper(quality)
    params = mapper.get_brainwave_params()
    
    print(f"\n🎵 Generating: {params['name']}")
    print(f"   Base Frequency: {params['base_freq']} Hz")
    print(f"   Beat Frequency: {params['beat_freq']} Hz (뇌가 인지)")
    print(f"   Reason: {params['reason']}")
    print(f"   Duration: {args.duration // 60}분 {args.duration % 60}초")
    
    # 오디오 생성
    generator = BinauralBeatGenerator()
    audio = generator.generate(
        base_freq=params["base_freq"],
        beat_freq=params["beat_freq"],
        duration=args.duration,
        carrier_type=params["carrier_type"]
    )
    
    # 저장
    output_dir = args.output_dir or (get_workspace_root() / "outputs")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"binaural_flow_q{int(quality*100)}_{timestamp}.wav"
    output_path = output_dir / filename
    
    wavfile.write(output_path, 44100, audio)
    
    print(f"\n✅ Generated: {output_path}")
    print(f"\n🎧 How to use:")
    print(f"   1. 헤드폰 착용 (필수! 양쪽 귀에 다른 주파수)")
    print(f"   2. 편안한 볼륨으로 재생")
    print(f"   3. 5-10분 청취 → 뇌파 자동 동기화")
    print(f"\n💡 Expected effect:")
    print(f"   - {params['reason']}")
    print(f"   - 약 3-5분 후 효과 시작")
    
    # Metadata 저장
    metadata = {
        "timestamp": timestamp,
        "flow_quality": quality,
        "audio_file": str(output_path),
        "params": params,
        "duration_seconds": args.duration
    }
    
    metadata_path = output_dir / f"binaural_metadata_{timestamp}.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 Metadata: {metadata_path}")
    
    return output_path


if __name__ == "__main__":
    main()
