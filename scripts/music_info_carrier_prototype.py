#!/usr/bin/env python3
"""
음악 정보 캐리어 프로토타입
Music Information Carrier System - Proof of Concept

Phase 1: 음악에서 정보 추출 (Read)
- 스펙트럼 분석으로 숨겨진 패턴 감지
- 서브소닉 주파수 대역 분석
- 자연적 주파수 패턴 발견

Phase 2: 음악에 정보 삽입 (Write)
- Morse Code를 서브소닉 주파수로 인코딩
- 원본 음질 유지하며 데이터 삽입
- FLAC/WAV 형식으로 저장

Phase 3: 실시간 적용 (Real-time)
- Reaper DAW 실시간 스트림 조작
- Observer Telemetry 연동
- 자동 상태 감지 및 반응
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from workspace_root import get_workspace_root

# 프로젝트 루트 추가
workspace_root = get_workspace_root()
sys.path.insert(0, str(workspace_root))

try:
    import librosa
    import soundfile as sf
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False
    print("⚠️  Warning: librosa/soundfile not installed. Install with:")
    print("   pip install librosa soundfile")


class MusicInfoCarrier:
    """음악을 통한 정보 전달/저장 시스템"""
    
    # 리듬 페이즈별 주파수 시그니처
    PHASE_FREQUENCIES = {
        "FOCUS": 432.0,      # 알파파 유도 (집중)
        "FLOW": 528.0,       # 극대 집중
        "BREAK": 256.0,      # 이완
        "DEEP_WORK": 396.0,  # 몰입
        "CREATIVE": 639.0,   # 창의성
    }
    
    # 서브소닉 주파수 범위 (20Hz 이하, 인간 청각 불가)
    SUBSONIC_RANGE = (5.0, 18.0)
    
    # 초음파 범위 (20kHz 이상, 인간 청각 불가)
    ULTRASONIC_RANGE = (20000.0, 22000.0)
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.output_dir = workspace_root / "outputs" / "music_info_carrier"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def analyze_spectrum(self, audio_file: Path) -> Dict:
        """
        오디오 파일의 스펙트럼 분석
        
        Returns:
            Dict containing:
            - subsonic_energy: 서브소닉 주파수 에너지
            - phase_signatures: 리듬 페이즈 주파수 감지
            - hidden_patterns: 숨겨진 패턴 후보
        """
        if not AUDIO_LIBS_AVAILABLE:
            return {"error": "Audio libraries not installed"}
        
        # 오디오 로드
        y, sr = librosa.load(str(audio_file), sr=self.sample_rate)
        
        # STFT (Short-time Fourier Transform)
        D = librosa.stft(y)
        magnitude = np.abs(D)
        
        # 주파수 축 생성
        frequencies = librosa.fft_frequencies(sr=sr)
        
        # 서브소닉 범위 분석
        subsonic_mask = (frequencies >= self.SUBSONIC_RANGE[0]) & \
                        (frequencies <= self.SUBSONIC_RANGE[1])
        subsonic_energy = float(np.mean(magnitude[subsonic_mask]))
        
        # 리듬 페이즈 주파수 감지
        phase_signatures = {}
        for phase, freq in self.PHASE_FREQUENCIES.items():
            # 해당 주파수 근처 에너지 측정 (±5Hz)
            freq_mask = (frequencies >= freq - 5) & (frequencies <= freq + 5)
            energy = float(np.mean(magnitude[freq_mask]))
            phase_signatures[phase] = {
                "frequency": freq,
                "energy": energy,
                "detected": energy > subsonic_energy * 1.5  # 임계값
            }
        
        # 결과 저장
        result = {
            "timestamp": datetime.now().isoformat(),
            "audio_file": str(audio_file.name),
            "sample_rate": sr,
            "duration_seconds": float(len(y) / sr),
            "subsonic_energy": subsonic_energy,
            "phase_signatures": phase_signatures,
            "detected_phases": [
                phase for phase, sig in phase_signatures.items()
                if sig["detected"]
            ]
        }
        
        # JSON 저장
        output_file = self.output_dir / f"spectrum_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result
    
    def encode_morse_code(self, message: str, frequency: float = 10.0) -> np.ndarray:
        """
        Morse Code를 서브소닉 주파수로 인코딩
        
        Args:
            message: 인코딩할 메시지 (알파벳/숫자만)
            frequency: 캐리어 주파수 (기본: 10Hz, 서브소닉)
        
        Returns:
            numpy array of encoded audio signal
        """
        # Morse Code 테이블
        MORSE_CODE = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.',
            'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
            'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---',
            'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
            'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--',
            'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
            '3': '...--', '4': '....-', '5': '.....', '6': '-....',
            '7': '--...', '8': '---..', '9': '----.',
            ' ': '/'  # 단어 구분
        }
        
        # 타이밍 (초 단위)
        dot_duration = 0.1  # dot = 100ms
        dash_duration = dot_duration * 3  # dash = 300ms
        symbol_gap = dot_duration  # 심볼 간 간격
        letter_gap = dot_duration * 3  # 문자 간 간격
        
        # 신호 생성
        signal = []
        
        for char in message.upper():
            if char not in MORSE_CODE:
                continue
            
            morse = MORSE_CODE[char]
            
            for symbol in morse:
                if symbol == '.':
                    duration = dot_duration
                elif symbol == '-':
                    duration = dash_duration
                elif symbol == '/':
                    # 단어 구분 (무음)
                    signal.extend([0] * int(letter_gap * self.sample_rate))
                    continue
                else:
                    continue
                
                # 톤 생성 (sine wave)
                t = np.linspace(0, duration, int(duration * self.sample_rate))
                tone = np.sin(2 * np.pi * frequency * t) * 0.1  # 낮은 볼륨
                signal.extend(tone)
                
                # 심볼 간 간격
                signal.extend([0] * int(symbol_gap * self.sample_rate))
            
            # 문자 간 간격
            signal.extend([0] * int(letter_gap * self.sample_rate))
        
        return np.array(signal)
    
    def embed_info_in_music(self, 
                           music_file: Path,
                           message: str,
                           phase: str = "FOCUS",
                           output_file: Optional[Path] = None) -> Path:
        """
        음악 파일에 정보 삽입
        
        Args:
            music_file: 원본 음악 파일
            message: 삽입할 메시지
            phase: 리듬 페이즈 (FOCUS, FLOW, BREAK 등)
            output_file: 출력 파일 (None이면 자동 생성)
        
        Returns:
            Path to output file
        """
        if not AUDIO_LIBS_AVAILABLE:
            raise ImportError("Audio libraries not installed")
        
        # 음악 로드
        y, sr = librosa.load(str(music_file), sr=self.sample_rate)
        
        # Morse Code 생성
        morse_signal = self.encode_morse_code(message, frequency=self.SUBSONIC_RANGE[0])
        
        # 페이즈 주파수 톤 생성
        phase_freq = self.PHASE_FREQUENCIES.get(phase, 432.0)
        phase_tone = np.sin(2 * np.pi * phase_freq * np.arange(len(y)) / sr) * 0.05
        
        # 음악에 신호 삽입
        # 1. Morse Code (서브소닉)
        if len(morse_signal) < len(y):
            # Morse를 음악 길이만큼 반복
            morse_repeated = np.tile(morse_signal, int(np.ceil(len(y) / len(morse_signal))))
            morse_repeated = morse_repeated[:len(y)]
        else:
            morse_repeated = morse_signal[:len(y)]
        
        # 2. 합성 (원본 음악 + 서브소닉 Morse + 페이즈 톤)
        y_embedded = y + morse_repeated + phase_tone
        
        # 정규화 (클리핑 방지)
        y_embedded = y_embedded / np.max(np.abs(y_embedded)) * 0.95
        
        # 출력 파일 결정
        if output_file is None:
            output_file = self.output_dir / f"embedded_{music_file.stem}_{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        
        # 저장 (FLAC 또는 WAV 권장, MP3는 서브소닉 손실 가능)
        sf.write(str(output_file), y_embedded, sr, subtype='PCM_24')
        
        # 메타데이터 저장
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "original_file": str(music_file.name),
            "embedded_file": str(output_file.name),
            "message": message,
            "phase": phase,
            "phase_frequency": phase_freq,
            "morse_frequency": float(self.SUBSONIC_RANGE[0]),
            "sample_rate": sr,
            "duration_seconds": float(len(y) / sr)
        }
        
        metadata_file = output_file.with_suffix('.json')
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 음악에 정보 삽입 완료!")
        print(f"   출력: {output_file}")
        print(f"   메타: {metadata_file}")
        
        return output_file
    
    def decode_from_music(self, music_file: Path) -> Dict:
        """
        음악에서 정보 추출 (디코딩)
        
        Returns:
            Dict containing decoded information
        """
        # 일단 스펙트럼 분석으로 간단히 구현
        return self.analyze_spectrum(music_file)


def main():
    """프로토타입 실행"""
    print("🎵 음악 정보 캐리어 시스템 - 프로토타입")
    print("=" * 60)
    
    carrier = MusicInfoCarrier()
    
    # 예제: 테스트 음악 파일 찾기
    music_dir = workspace_root / "outputs" / "music_samples"
    
    if not music_dir.exists():
        print(f"\n⚠️  음악 샘플 디렉토리가 없습니다: {music_dir}")
        print("테스트용 음악 파일을 여기에 넣어주세요.")
        
        # 간단한 테스트 톤 생성
        print("\n🔧 테스트 톤 생성 중...")
        if AUDIO_LIBS_AVAILABLE:
            sr = 44100
            duration = 5.0
            t = np.linspace(0, duration, int(duration * sr))
            
            # 432Hz 톤 (FOCUS)
            test_tone = np.sin(2 * np.pi * 432 * t) * 0.3
            
            test_file = carrier.output_dir / "test_tone_432hz.wav"
            sf.write(str(test_file), test_tone, sr)
            print(f"✅ 테스트 톤 생성: {test_file}")
            
            # 스펙트럼 분석
            print("\n📊 스펙트럼 분석 중...")
            result = carrier.analyze_spectrum(test_file)
            
            print(f"\n결과:")
            print(f"  - 서브소닉 에너지: {result['subsonic_energy']:.6f}")
            print(f"  - 감지된 페이즈: {', '.join(result['detected_phases']) or '없음'}")
            
            for phase, sig in result['phase_signatures'].items():
                status = "✅" if sig['detected'] else "❌"
                print(f"  - {status} {phase}: {sig['frequency']}Hz (에너지: {sig['energy']:.6f})")
        
    else:
        # 실제 음악 파일 분석
        music_files = list(music_dir.glob("*.wav")) + list(music_dir.glob("*.mp3"))
        
        if music_files:
            print(f"\n🎵 발견된 음악 파일: {len(music_files)}개")
            
            # 첫 번째 파일 분석
            test_file = music_files[0]
            print(f"\n분석 중: {test_file.name}")
            
            result = carrier.analyze_spectrum(test_file)
            
            print(f"\n결과:")
            print(f"  - 길이: {result['duration_seconds']:.2f}초")
            print(f"  - 서브소닉 에너지: {result['subsonic_energy']:.6f}")
            print(f"  - 감지된 페이즈: {', '.join(result['detected_phases']) or '없음'}")
    
    print(f"\n📂 출력 디렉토리: {carrier.output_dir}")
    print("\n✅ 프로토타입 실행 완료!")


if __name__ == "__main__":
    main()
