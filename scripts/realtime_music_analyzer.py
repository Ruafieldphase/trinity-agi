#!/usr/bin/env python3
"""
Realtime Music Analyzer
실시간 오디오 분석 및 리듬 페이즈 매칭 시스템

- 현재 재생 중인 음악의 템포/에너지 실시간 분석
- 리듬 페이즈와 매칭도 계산
- 부적합한 음악 감지 시 자동 전환 제안
"""

import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

try:
    import librosa
    import numpy as np
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️ librosa or sounddevice not available. Install with: pip install librosa sounddevice")


class RealtimeMusicAnalyzer:
    """실시간 음악 분석기"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.outputs_dir = workspace_root / "outputs"
        self.rhythm_status_file = self.outputs_dir / "RHYTHM_SYSTEM_STATUS_REPORT.md"
        
        # 분석 파라미터
        self.sample_rate = 22050
        self.buffer_duration = 3  # 3초 버퍼
        self.hop_length = 512
        
        # 페이즈별 기준값
        self.phase_criteria = {
            "WAKING": {"bpm": (120, 150), "energy": (0.6, 0.9)},
            "FOCUS": {"bpm": (100, 130), "energy": (0.5, 0.75)},
            "CODING": {"bpm": (90, 120), "energy": (0.4, 0.7)},
            "REST": {"bpm": (60, 90), "energy": (0.2, 0.5)},
            "DEEP_REST": {"bpm": (40, 70), "energy": (0.1, 0.4)},
        }
        
    def get_current_rhythm_phase(self) -> Optional[str]:
        """현재 리듬 페이즈 읽기"""
        if not self.rhythm_status_file.exists():
            return None
            
        try:
            content = self.rhythm_status_file.read_text(encoding="utf-8")
            # "Current Phase: FOCUS (90.9%)" 형식 파싱
            for line in content.split("\n"):
                if "Current Phase:" in line:
                    phase = line.split(":")[1].strip().split()[0]
                    return phase
        except Exception as e:
            print(f"⚠️ Failed to read rhythm phase: {e}")
            
        return None
    
    def analyze_audio_buffer(self, audio_data: np.ndarray) -> Dict:
        """오디오 버퍼 분석"""
        if not AUDIO_AVAILABLE:
            return {"error": "librosa not available"}
        
        try:
            # 템포 추정
            tempo, _ = librosa.beat.beat_track(
                y=audio_data, 
                sr=self.sample_rate,
                hop_length=self.hop_length
            )
            
            # 에너지 계산 (RMS)
            rms = librosa.feature.rms(
                y=audio_data,
                hop_length=self.hop_length
            )
            energy = float(np.mean(rms))
            
            # 스펙트럼 중심 (밝기)
            spectral_centroid = librosa.feature.spectral_centroid(
                y=audio_data,
                sr=self.sample_rate,
                hop_length=self.hop_length
            )
            brightness = float(np.mean(spectral_centroid))
            
            # 제로 크로싱 레이트 (복잡도)
            zcr = librosa.feature.zero_crossing_rate(
                y=audio_data,
                hop_length=self.hop_length
            )
            complexity = float(np.mean(zcr))
            
            return {
                "tempo": float(tempo),
                "energy": energy,
                "brightness": brightness,
                "complexity": complexity,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def calculate_phase_match(
        self, 
        music_features: Dict, 
        target_phase: str
    ) -> Tuple[float, str]:
        """음악 특성과 페이즈 매칭도 계산 (0.0 ~ 1.0)"""
        if target_phase not in self.phase_criteria:
            return 0.0, "Unknown phase"
        
        criteria = self.phase_criteria[target_phase]
        tempo = music_features.get("tempo", 0)
        energy = music_features.get("energy", 0)
        
        # BPM 매칭도
        bpm_min, bpm_max = criteria["bpm"]
        if bpm_min <= tempo <= bpm_max:
            bpm_match = 1.0
        elif tempo < bpm_min:
            bpm_match = max(0, 1 - (bpm_min - tempo) / 30)
        else:
            bpm_match = max(0, 1 - (tempo - bpm_max) / 30)
        
        # 에너지 매칭도
        energy_min, energy_max = criteria["energy"]
        if energy_min <= energy <= energy_max:
            energy_match = 1.0
        elif energy < energy_min:
            energy_match = max(0, 1 - (energy_min - energy) / 0.3)
        else:
            energy_match = max(0, 1 - (energy - energy_max) / 0.3)
        
        # 종합 매칭도 (가중 평균)
        overall_match = (bpm_match * 0.6 + energy_match * 0.4)
        
        # 판정
        if overall_match >= 0.8:
            verdict = "✅ EXCELLENT - Perfect match"
        elif overall_match >= 0.6:
            verdict = "✓ GOOD - Acceptable match"
        elif overall_match >= 0.4:
            verdict = "⚠️ SUBOPTIMAL - Consider switching"
        else:
            verdict = "❌ POOR - Immediate change recommended"
        
        return overall_match, verdict
    
    def record_audio_sample(self, duration: float = 3.0) -> Optional[np.ndarray]:
        """마이크에서 오디오 샘플 녹음 (실시간 분석용)"""
        if not AUDIO_AVAILABLE:
            print("⚠️ sounddevice not available")
            return None
        
        try:
            print(f"🎤 Recording {duration}s audio sample...")
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()
            return recording.flatten()
            
        except Exception as e:
            print(f"⚠️ Recording failed: {e}")
            return None
    
    def analyze_file(self, audio_file: Path) -> Dict:
        """오디오 파일 분석 (테스트용)"""
        if not AUDIO_AVAILABLE:
            return {"error": "librosa not available"}
        
        try:
            print(f"📁 Loading audio file: {audio_file.name}")
            audio_data, sr = librosa.load(audio_file, sr=self.sample_rate, duration=30)
            
            features = self.analyze_audio_buffer(audio_data)
            
            # 페이즈 매칭 계산
            current_phase = self.get_current_rhythm_phase() or "FOCUS"
            match_score, verdict = self.calculate_phase_match(features, current_phase)
            
            result = {
                "file": str(audio_file),
                "features": features,
                "current_phase": current_phase,
                "match_score": match_score,
                "verdict": verdict
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e), "file": str(audio_file)}
    
    def run_continuous_monitoring(self, interval: int = 30):
        """연속 모니터링 (데몬 모드)"""
        print("🎵 Starting continuous music monitoring...")
        print(f"   Interval: {interval}s")
        print("   Press Ctrl+C to stop\n")
        
        log_file = self.outputs_dir / "music_analysis_log.jsonl"
        
        try:
            while True:
                # 현재 페이즈 확인
                current_phase = self.get_current_rhythm_phase()
                if not current_phase:
                    print("⚠️ Rhythm phase not available, waiting...")
                    time.sleep(interval)
                    continue
                
                # 오디오 샘플 녹음
                audio_data = self.record_audio_sample(self.buffer_duration)
                if audio_data is None:
                    time.sleep(interval)
                    continue
                
                # 분석
                features = self.analyze_audio_buffer(audio_data)
                if "error" in features:
                    print(f"⚠️ Analysis error: {features['error']}")
                    time.sleep(interval)
                    continue
                
                # 매칭도 계산
                match_score, verdict = self.calculate_phase_match(features, current_phase)
                
                # 결과 출력
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Analysis:")
                print(f"  Phase: {current_phase}")
                print(f"  Tempo: {features['tempo']:.1f} BPM")
                print(f"  Energy: {features['energy']:.3f}")
                print(f"  Match: {match_score:.1%} - {verdict}")
                
                # 로그 저장
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "phase": current_phase,
                    "features": features,
                    "match_score": match_score,
                    "verdict": verdict
                }
                
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
                
                # 경고 발생
                if match_score < 0.4:
                    print(f"\n⚠️ WARNING: Music not suitable for {current_phase} phase!")
                    print("   Consider switching to adaptive music player")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n✓ Monitoring stopped")


def main():
    parser = argparse.ArgumentParser(description="Realtime Music Analyzer")
    parser.add_argument("--file", type=str, help="Analyze audio file")
    parser.add_argument("--monitor", action="store_true", help="Start continuous monitoring")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval (seconds)")
    parser.add_argument("--workspace", type=str, default=".", help="Workspace root")
    
    args = parser.parse_args()
    
    workspace_root = Path(args.workspace).resolve()
    analyzer = RealtimeMusicAnalyzer(workspace_root)
    
    if args.file:
        # 파일 분석 모드
        audio_file = Path(args.file)
        if not audio_file.exists():
            print(f"❌ File not found: {audio_file}")
            return 1
        
        result = analyzer.analyze_file(audio_file)
        print(json.dumps(result, indent=2))
        
    elif args.monitor:
        # 연속 모니터링 모드
        analyzer.run_continuous_monitoring(args.interval)
        
    else:
        # 기본: 단일 샘플 분석
        current_phase = analyzer.get_current_rhythm_phase() or "FOCUS"
        print(f"📊 Current rhythm phase: {current_phase}\n")
        
        audio_data = analyzer.record_audio_sample(3.0)
        if audio_data is not None:
            features = analyzer.analyze_audio_buffer(audio_data)
            match_score, verdict = analyzer.calculate_phase_match(features, current_phase)
            
            print(f"\n🎵 Music Analysis:")
            print(f"  Tempo: {features.get('tempo', 0):.1f} BPM")
            print(f"  Energy: {features.get('energy', 0):.3f}")
            print(f"  Brightness: {features.get('brightness', 0):.1f} Hz")
            print(f"  Complexity: {features.get('complexity', 0):.3f}")
            print(f"\n📈 Phase Match: {match_score:.1%}")
            print(f"  {verdict}")
    
    return 0


if __name__ == "__main__":
    exit(main())
