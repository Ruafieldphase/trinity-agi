#!/usr/bin/env python3
"""
🎼 Rhythm Report → Audio Signature Generator
24시간 리듬을 24초 청각 시그니처로 변환합니다.

컨셉:
- 1시간 = 1초 오디오
- Rest phase → 낮은 주파수 (200-400 Hz)
- Active phase → 높은 주파수 (600-1200 Hz)
- Energy level → 볼륨
- 하루 전체 리듬을 귀로 듣고 패턴 인식

Usage:
    python scripts/rhythm_audio_signature.py
    python scripts/rhythm_audio_signature.py --hours 12
"""

import json
import sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from datetime import datetime, timedelta
import argparse
from typing import List, Tuple


class RhythmAudioMapper:
    """Rhythm state → Audio frequency/amplitude 매핑"""
    
    # Frequency ranges (Hz)
    FREQ_DEEP_REST = 200    # 깊은 휴식
    FREQ_REST = 300         # 휴식
    FREQ_NEUTRAL = 500      # 중립
    FREQ_ACTIVE = 700       # 활동
    FREQ_PEAK = 1000        # 피크
    
    def __init__(self, rhythm_data: dict):
        self.data = rhythm_data
    
    def map_phase_to_freq(self, phase: str) -> float:
        """Phase → 주파수"""
        mapping = {
            "deep_rest": self.FREQ_DEEP_REST,
            "rest": self.FREQ_REST,
            "neutral": self.FREQ_NEUTRAL,
            "active": self.FREQ_ACTIVE,
            "peak": self.FREQ_PEAK
        }
        return mapping.get(phase, self.FREQ_NEUTRAL)
    
    def map_energy_to_amplitude(self, energy: float) -> float:
        """Energy (0-1) → 진폭 (0-1)"""
        # Energy 0.0 → 0.2 (최소 들림)
        # Energy 1.0 → 1.0 (최대)
        return 0.2 + (energy * 0.8)
    
    def extract_hourly_states(self, hours: int = 24) -> List[Tuple[str, float]]:
        """
        시간대별 (phase, energy) 추출
        
        Returns:
            [(phase, energy), ...] 최대 hours개
        """
        # RHYTHM_REST_PHASE_*.md 파싱 필요
        # 임시로 더미 데이터
        states = []
        
        # 실제 구현: outputs/RHYTHM_*.md 파싱
        # 또는 rhythm system에서 JSON export 기능 추가
        
        # Fallback: 샘플 패턴
        sample_pattern = [
            ("deep_rest", 0.2),  # 0-1시
            ("deep_rest", 0.1),
            ("rest", 0.3),
            ("rest", 0.4),
            ("rest", 0.5),
            ("neutral", 0.6),    # 6시
            ("active", 0.7),
            ("active", 0.8),
            ("peak", 0.9),       # 9시
            ("peak", 1.0),
            ("peak", 0.95),
            ("active", 0.85),
            ("active", 0.8),
            ("neutral", 0.7),    # 14시
            ("neutral", 0.6),
            ("active", 0.7),
            ("active", 0.75),
            ("peak", 0.85),      # 18시
            ("active", 0.8),
            ("neutral", 0.7),
            ("neutral", 0.6),
            ("rest", 0.5),       # 22시
            ("rest", 0.4),
            ("deep_rest", 0.3),
        ]
        
        return sample_pattern[:hours]


class AudioSignatureGenerator:
    """청각 시그니처 생성기"""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
    
    def generate_tone(
        self,
        frequency: float,
        amplitude: float,
        duration: float
    ) -> np.ndarray:
        """
        단일 톤 생성
        
        Args:
            frequency: Hz
            amplitude: 0.0 - 1.0
            duration: 초
        """
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        wave = amplitude * np.sin(2 * np.pi * frequency * t)
        return wave
    
    def generate_signature(
        self,
        states: List[Tuple[str, float]],
        duration_per_state: float = 1.0
    ) -> np.ndarray:
        """
        전체 시그니처 생성
        
        Args:
            states: [(phase, energy), ...]
            duration_per_state: 각 상태당 초
        """
        mapper = RhythmAudioMapper({})
        segments = []
        
        for phase, energy in states:
            freq = mapper.map_phase_to_freq(phase)
            amp = mapper.map_energy_to_amplitude(energy)
            
            tone = self.generate_tone(freq, amp, duration_per_state)
            segments.append(tone)
        
        # 연결
        full_audio = np.concatenate(segments)
        
        # Normalize
        full_audio = full_audio / np.max(np.abs(full_audio))
        
        # Fade in/out
        fade_samples = int(0.5 * self.sample_rate)
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        full_audio[:fade_samples] *= fade_in
        full_audio[-fade_samples:] *= fade_out
        
        # To 16-bit
        return (full_audio * 0.8 * 32767).astype(np.int16)


def main():
    parser = argparse.ArgumentParser(description="Rhythm → Audio Signature")
    parser.add_argument("--hours", type=int, default=24, help="Hours to encode")
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    args = parser.parse_args()
    
    print(f"\n🎼 Rhythm Audio Signature Generator")
    print(f"   Encoding: {args.hours} hours → {args.hours} seconds audio")
    
    # Rhythm 상태 로드 (더미)
    mapper = RhythmAudioMapper({})
    states = mapper.extract_hourly_states(args.hours)
    
    print(f"\n📊 Hourly states:")
    for i, (phase, energy) in enumerate(states):
        bar = "█" * int(energy * 20)
        print(f"   {i:2d}시: {phase:12s} [{bar:<20s}] {energy:.2f}")
    
    # 오디오 생성
    generator = AudioSignatureGenerator()
    audio = generator.generate_signature(states, duration_per_state=1.0)
    
    # 저장
    output_dir = args.output_dir or (Path(__file__).parent.parent / "outputs")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rhythm_signature_{args.hours}h_{timestamp}.wav"
    output_path = output_dir / filename
    
    wavfile.write(output_path, 44100, audio)
    
    print(f"\n✅ Generated: {output_path}")
    print(f"   Duration: {args.hours} seconds")
    print(f"\n🎧 How to listen:")
    print(f"   - 1초 = 1시간의 리듬")
    print(f"   - 낮은 음 = 휴식 phase")
    print(f"   - 높은 음 = 활동 phase")
    print(f"   - 볼륨 = 에너지 레벨")
    print(f"\n💡 Use case:")
    print(f"   - 하루 패턴을 귀로 인식")
    print(f"   - 여러 날 비교 (음색 차이)")
    print(f"   - 자율 시스템 상태 청각 모니터링")
    
    # Metadata
    metadata = {
        "timestamp": timestamp,
        "hours_encoded": args.hours,
        "audio_file": str(output_path),
        "duration_seconds": args.hours,
        "states": [{"hour": i, "phase": p, "energy": e} for i, (p, e) in enumerate(states)]
    }
    
    metadata_path = output_dir / f"rhythm_signature_metadata_{timestamp}.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 Metadata: {metadata_path}")
    
    return output_path


if __name__ == "__main__":
    main()
