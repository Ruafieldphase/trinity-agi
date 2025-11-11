#!/usr/bin/env python3
"""
Flow Observer → 음악 주파수 매핑 시스템
실시간 flow 상태를 Binaural beats 파라미터로 변환
"""
import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict

@dataclass
class BiauralParams:
    """Binaural beat 생성 파라미터"""
    base_freq: int      # 기본 주파수 (Hz)
    beat_freq: float    # 비트 주파수 (Hz)
    carrier_wave: str   # 파형 타입
    duration_sec: int   # 지속 시간
    purpose: str        # 용도 설명

class FlowFrequencyMapper:
    """Flow quality → 음악 주파수 매핑"""
    
    # Solfeggio frequencies (치유/명상 주파수)
    SOLFEGGIO = {
        "liberation": 396,      # 두려움 해소
        "transformation": 417,  # 변화 촉진
        "miracles": 528,        # DNA 복구, 치유
        "connection": 639,      # 관계, 연결
        "awakening": 741,       # 직관, 각성
        "harmony": 852          # 영적 조화
    }
    
    def __init__(self):
        self.workspace = Path(__file__).parent.parent
        self.flow_report_path = self.workspace / "outputs" / "flow_observer_report_latest.json"
    
    def load_current_flow(self) -> float:
        """최근 flow quality 로드"""
        if not self.flow_report_path.exists():
            print(f"⚠️  Flow report not found: {self.flow_report_path}", file=sys.stderr)
            return 0.5  # 기본값
        
        with open(self.flow_report_path, encoding='utf-8') as f:
            data = json.load(f)
            current = data.get("current_state", {})
            return current.get("quality", 0.5)
    
    def map_to_binaural(self, flow_quality: float) -> BiauralParams:
        """
        Flow quality → Binaural beat 파라미터 매핑
        
        Flow quality 범위:
        - 0.9-1.0: 극도의 몰입 (Gamma)
        - 0.7-0.9: 깊은 집중 (Alpha-Beta)
        - 0.5-0.7: 중간 집중 (Beta)
        - 0.3-0.5: 산만 (Theta로 유도)
        - 0.0-0.3: 매우 산만 (Delta로 진정)
        """
        if flow_quality >= 0.9:  # 극도의 몰입
            return BiauralParams(
                base_freq=self.SOLFEGGIO["miracles"],  # 528 Hz
                beat_freq=40.0,  # Gamma wave
                carrier_wave="sine",
                duration_sec=1800,  # 30분
                purpose="Extreme focus - Gamma brain state"
            )
        elif flow_quality >= 0.7:  # 깊은 집중
            return BiauralParams(
                base_freq=432,  # Natural frequency
                beat_freq=10.0,  # Alpha wave
                carrier_wave="sine",
                duration_sec=2700,  # 45분
                purpose="Deep focus - Alpha brain state"
            )
        elif flow_quality >= 0.5:  # 중간 집중
            return BiauralParams(
                base_freq=self.SOLFEGGIO["transformation"],  # 417 Hz
                beat_freq=15.0,  # Low Beta wave
                carrier_wave="sine",
                duration_sec=1800,
                purpose="Moderate focus - Beta brain state"
            )
        elif flow_quality >= 0.3:  # 산만
            return BiauralParams(
                base_freq=self.SOLFEGGIO["liberation"],  # 396 Hz
                beat_freq=6.0,  # Theta wave
                carrier_wave="sine",
                duration_sec=1200,  # 20분
                purpose="Relaxation needed - Theta induction"
            )
        else:  # 매우 산만
            return BiauralParams(
                base_freq=self.SOLFEGGIO["liberation"],
                beat_freq=3.0,  # Delta wave
                carrier_wave="sine",
                duration_sec=900,  # 15분
                purpose="Deep relaxation - Delta induction"
            )
    
    def generate_report(self, output_path: Path = None) -> Dict:
        """현재 flow → 음악 파라미터 리포트 생성"""
        flow_quality = self.load_current_flow()
        params = self.map_to_binaural(flow_quality)
        
        report = {
            "timestamp": "2025-11-10T00:00:00Z",
            "flow_quality": round(flow_quality, 3),
            "binaural_params": asdict(params),
            "spotify_search_query": self._generate_spotify_query(params),
            "local_generation_cmd": self._generate_sox_command(params)
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✅ Report saved: {output_path}")
        
        return report
    
    def _generate_spotify_query(self, params: BiauralParams) -> str:
        """Spotify 검색 쿼리 생성"""
        if params.beat_freq >= 30:
            return "gamma waves focus music"
        elif params.beat_freq >= 13:
            return "alpha waves concentration music"
        elif params.beat_freq >= 8:
            return "beta waves productivity music"
        elif params.beat_freq >= 4:
            return "theta waves meditation music"
        else:
            return "delta waves deep sleep music"
    
    def _generate_sox_command(self, params: BiauralParams) -> str:
        """SoX를 사용한 로컬 binaural beat 생성 명령"""
        left_freq = params.base_freq
        right_freq = params.base_freq + params.beat_freq
        
        return (
            f"sox -n -r 44100 -c 2 binaural_{params.beat_freq}hz.wav "
            f"synth {params.duration_sec} {params.carrier_wave} {left_freq} "
            f"{params.carrier_wave} {right_freq} channels 2"
        )

def main():
    """CLI 실행"""
    mapper = FlowFrequencyMapper()
    
    output_dir = mapper.workspace / "outputs"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "flow_music_params_latest.json"
    
    report = mapper.generate_report(output_path)
    
    # 콘솔 출력
    print("\n🎵 Flow → Music Frequency Mapping")
    print("=" * 50)
    print(f"📊 Current Flow Quality: {report['flow_quality']:.1%}")
    print(f"🎶 Recommended Frequency: {report['binaural_params']['base_freq']} Hz")
    print(f"🧠 Target Brain Wave: {report['binaural_params']['beat_freq']} Hz ({report['binaural_params']['purpose']})")
    print(f"⏱️  Duration: {report['binaural_params']['duration_sec'] // 60} minutes")
    print(f"\n🎧 Spotify Search: \"{report['spotify_search_query']}\"")
    print(f"\n💻 Local Generation:\n{report['local_generation_cmd']}")
    print("=" * 50)

if __name__ == "__main__":
    main()
