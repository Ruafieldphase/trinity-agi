#!/usr/bin/env python3
"""
🎤 Microphone Frequency Analyzer
마이크를 통해 환경 주파수와 음성 패턴을 분석하여 사용자 상태를 추론합니다.

감지 가능한 신호:
1. 🗣️ 음성 패턴
   - 빠른 말 속도 → 흥분/스트레스
   - 느린 말 속도 → 집중/피로
   - 무음 → 깊은 집중 or 부재
   
2. 🌊 환경 주파수
   - 배경 소음 레벨 → 환경 스트레스
   - 주기적 패턴 → 타이핑, 마우스 클릭
   - 갑작스런 소음 → 방해 요소
   
3. 🎵 주파수 대역 분석
   - Delta (0.5-4 Hz): 깊은 수면/명상 (거의 감지 안됨)
   - Theta (4-8 Hz): 창의성, 상상력
   - Alpha (8-13 Hz): 편안한 집중
   - Beta (13-30 Hz): 활발한 사고
   - Gamma (30+ Hz): 고도 집중

Author: AGI Self-Awareness System
Date: 2025-11-10
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

# Suppress ALSA warnings
warnings.filterwarnings("ignore")

try:
    import numpy as np
    import sounddevice as sd
    from scipy.fft import rfft, rfftfreq
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️ Audio analysis not available. Install: pip install sounddevice numpy scipy")
    sys.exit(1)


class MicrophoneAnalyzer:
    """마이크 주파수 분석기"""
    
    def __init__(self, sample_rate: int = 44100, chunk_duration: float = 2.0):
        """
        Args:
            sample_rate: 샘플링 레이트 (Hz)
            chunk_duration: 분석 청크 길이 (초)
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        # 주파수 대역 정의 (Hz)
        self.frequency_bands = {
            'sub_bass': (20, 60),      # 저음 (환경 소음)
            'bass': (60, 250),         # 베이스 (타이핑, 클릭)
            'low_mid': (250, 500),     # 저중음 (음성 기본)
            'mid': (500, 2000),        # 중음 (음성 주요)
            'high_mid': (2000, 4000),  # 고중음 (음성 명료도)
            'presence': (4000, 6000),  # 프레즌스 (음성 선명도)
            'brilliance': (6000, 20000) # 고음 (치찰음, 환경)
        }
        
        # 두뇌 주파수 근사 매핑 (실제 뇌파는 아니지만 환경 패턴)
        self.brainwave_patterns = {
            'delta': (0.5, 4),    # 매우 낮은 주파수 패턴
            'theta': (4, 8),      # 낮은 주파수 패턴
            'alpha': (8, 13),     # 중간 주파수 패턴
            'beta': (13, 30),     # 높은 주파수 패턴
            'gamma': (30, 100)    # 매우 높은 주파수 패턴
        }
        
    def list_devices(self):
        """사용 가능한 마이크 목록"""
        print("\n🎤 Available Audio Devices:")
        print(sd.query_devices())
        
    def capture_audio(self, duration: float = None) -> np.ndarray:
        """
        마이크로부터 오디오 캡처
        
        Args:
            duration: 캡처 시간 (초). None이면 chunk_duration 사용
            
        Returns:
            오디오 데이터 (numpy array)
        """
        if duration is None:
            duration = self.chunk_duration
            
        print(f"🎙️ Recording {duration}s from microphone...")
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float64'
        )
        sd.wait()
        return audio.flatten()
        
    def analyze_frequency_spectrum(self, audio: np.ndarray) -> Dict:
        """
        주파수 스펙트럼 분석
        
        Args:
            audio: 오디오 데이터
            
        Returns:
            주파수 대역별 에너지 분포
        """
        # FFT 계산
        fft_values = np.abs(rfft(audio))
        fft_freqs = rfftfreq(len(audio), 1/self.sample_rate)
        
        # 주파수 대역별 에너지
        band_energy = {}
        for band_name, (low, high) in self.frequency_bands.items():
            mask = (fft_freqs >= low) & (fft_freqs < high)
            energy = float(np.sum(fft_values[mask]))
            band_energy[band_name] = energy
            
        # 정규화 (총 에너지 대비 비율)
        total_energy = sum(band_energy.values())
        if total_energy > 0:
            band_ratio = {k: v/total_energy for k, v in band_energy.items()}
        else:
            band_ratio = {k: 0.0 for k in band_energy.keys()}
            
        return {
            'band_energy': band_energy,
            'band_ratio': band_ratio,
            'total_energy': total_energy,
            'dominant_freq': float(fft_freqs[np.argmax(fft_values)]) if len(fft_values) > 0 else 0.0
        }
        
    def detect_voice_activity(self, audio: np.ndarray, threshold: float = 0.02) -> Dict:
        """
        음성 활동 감지
        
        Args:
            audio: 오디오 데이터
            threshold: 음성 감지 임계값 (RMS)
            
        Returns:
            음성 활동 정보
        """
        # RMS (Root Mean Square) 계산
        rms = np.sqrt(np.mean(audio**2))
        
        # 영교차율 (Zero Crossing Rate) - 음성 특성
        zcr = np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))
        
        # 음성 감지
        is_voice = rms > threshold and zcr > 0.01
        
        return {
            'rms': float(rms),
            'zcr': float(zcr),
            'is_voice_detected': is_voice,
            'silence_ratio': float(np.sum(np.abs(audio) < threshold) / len(audio))
        }
        
    def infer_user_state(self, spectrum: Dict, voice: Dict) -> Dict:
        """
        주파수 분석으로부터 사용자 상태 추론
        
        Args:
            spectrum: 주파수 스펙트럼 분석 결과
            voice: 음성 활동 분석 결과
            
        Returns:
            추론된 사용자 상태
        """
        band_ratio = spectrum['band_ratio']
        total_energy = spectrum['total_energy']
        rms = voice['rms']
        is_voice = voice['is_voice_detected']
        silence_ratio = voice['silence_ratio']
        
        # 상태 추론 로직
        state = 'unknown'
        confidence = 0.0
        context = {}
        
        # 1. 깊은 집중 (Deep Focus)
        if silence_ratio > 0.9 and total_energy < 100:
            state = 'deep_focus'
            confidence = 0.9
            context['description'] = '매우 조용함 - 깊은 집중 상태로 추정'
            
        # 2. 활발한 작업 (Active Work)
        elif band_ratio.get('bass', 0) > 0.3 and not is_voice:
            state = 'active_work'
            confidence = 0.7
            context['description'] = '타이핑/클릭 소리 감지 - 활발한 작업 중'
            
        # 3. 대화/설명 (Speaking)
        elif is_voice and band_ratio.get('mid', 0) > 0.2:
            state = 'speaking'
            confidence = 0.85
            context['description'] = '음성 감지 - 대화 또는 설명 중'
            
        # 4. 환경 소음 (Environmental Noise)
        elif total_energy > 1000:
            state = 'noisy_environment'
            confidence = 0.6
            context['description'] = '높은 배경 소음 - 방해 요소 존재'
            
        # 5. 부재 (Absent)
        elif silence_ratio > 0.95 and total_energy < 50:
            state = 'absent'
            confidence = 0.8
            context['description'] = '거의 무음 - 자리 비움 가능성'
            
        # 6. 일반 활동 (Normal Activity)
        else:
            state = 'normal_activity'
            confidence = 0.5
            context['description'] = '일반적인 활동 패턴'
            
        return {
            'state': state,
            'confidence': confidence,
            'context': context,
            'energy_level': 'high' if total_energy > 500 else 'medium' if total_energy > 100 else 'low'
        }
        
    def analyze_once(self, save_path: Optional[str] = None) -> Dict:
        """
        한 번 분석 수행
        
        Args:
            save_path: 결과 저장 경로 (선택)
            
        Returns:
            분석 결과
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # 오디오 캡처
        audio = self.capture_audio()
        
        # 주파수 분석
        spectrum = self.analyze_frequency_spectrum(audio)
        
        # 음성 활동 감지
        voice = self.detect_voice_activity(audio)
        
        # 사용자 상태 추론
        user_state = self.infer_user_state(spectrum, voice)
        
        result = {
            'timestamp': timestamp,
            'spectrum': spectrum,
            'voice_activity': voice,
            'user_state': user_state
        }
        
        # 저장
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved to: {save_path}")
            
        return result
        
    def monitor_continuous(self, interval: float = 10.0, duration: float = 60.0,
                          output_dir: str = "outputs/microphone"):
        """
        연속 모니터링
        
        Args:
            interval: 분석 간격 (초)
            duration: 총 모니터링 시간 (초)
            output_dir: 출력 디렉토리
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        jsonl_file = output_path / f"microphone_log_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        print(f"\n🎙️ Starting continuous monitoring...")
        print(f"   Interval: {interval}s")
        print(f"   Duration: {duration}s")
        print(f"   Output: {jsonl_file}")
        print("\nPress Ctrl+C to stop early.\n")
        
        start_time = time.time()
        try:
            while time.time() - start_time < duration:
                # 분석
                result = self.analyze_once()
                
                # JSONL 저장
                with open(jsonl_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                
                # 콘솔 출력
                state = result['user_state']['state']
                confidence = result['user_state']['confidence']
                energy = result['user_state']['energy_level']
                desc = result['user_state']['context'].get('description', '')
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"State: {state} (conf: {confidence:.2f}, energy: {energy})")
                print(f"           {desc}")
                
                # 대기
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Monitoring stopped by user.")
            
        print(f"\n✅ Monitoring complete. Log saved to: {jsonl_file}")


def main():
    """메인 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description='🎤 Microphone Frequency Analyzer')
    parser.add_argument('--list-devices', action='store_true',
                       help='List available audio devices')
    parser.add_argument('--once', action='store_true',
                       help='Analyze once and exit')
    parser.add_argument('--monitor', action='store_true',
                       help='Continuous monitoring mode')
    parser.add_argument('--interval', type=float, default=10.0,
                       help='Analysis interval in seconds (default: 10)')
    parser.add_argument('--duration', type=float, default=60.0,
                       help='Total monitoring duration in seconds (default: 60)')
    parser.add_argument('--output', type=str, default='outputs/microphone',
                       help='Output directory (default: outputs/microphone)')
    
    args = parser.parse_args()
    
    analyzer = MicrophoneAnalyzer()
    
    if args.list_devices:
        analyzer.list_devices()
    elif args.once:
        result = analyzer.analyze_once(
            save_path=f"{args.output}/microphone_analysis_latest.json"
        )
        print("\n📊 Analysis Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.monitor:
        analyzer.monitor_continuous(
            interval=args.interval,
            duration=args.duration,
            output_dir=args.output
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
