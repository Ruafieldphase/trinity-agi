"""
Flow Observer → Music Frequency Encoder
흐름 상태를 음악 주파수 파라미터로 변환
"""
import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Optional
from datetime import datetime
from workspace_root import get_workspace_root

@dataclass
class BiauralBeatParams:
    """Binaural Beat 생성 파라미터"""
    base_freq: int      # 기본 주파수 (Hz)
    beat_freq: float    # 비트 주파수 (Hz) - 뇌파 유도
    carrier_wave: str   # 파형 타입
    duration: float     # 지속 시간 (초)
    brain_state: str    # 목표 뇌 상태
    reason: str         # 선택 이유

@dataclass
class FlowFrequency:
    """Flow 상태 → 음악 주파수 매핑"""
    flow_quality: float     # 0.0-1.0
    energy_level: float     # 0.0-1.0
    focus_duration: int     # 분
    
    def to_binaural_params(self) -> BiauralBeatParams:
        """Flow quality → Binaural beat 주파수 매핑"""
        
        # Deep Flow (0.8-1.0): Gamma/High Alpha
        if self.flow_quality >= 0.8:
            return BiauralBeatParams(
                base_freq=432,          # A=432Hz (자연 공명 주파수)
                beat_freq=10.0,         # Alpha (10 Hz) - 깊은 집중
                carrier_wave="sine",
                duration=min(self.focus_duration * 60, 3600),
                brain_state="Deep Focus (Alpha 10Hz)",
                reason=f"Flow quality {self.flow_quality:.2f} - 깊은 몰입 상태 유지"
            )
        
        # Medium Flow (0.5-0.8): Beta
        elif self.flow_quality >= 0.5:
            return BiauralBeatParams(
                base_freq=528,          # C=528Hz (치유/변환 주파수)
                beat_freq=15.0,         # Low Beta (15 Hz) - 활성 집중
                carrier_wave="sine",
                duration=min(self.focus_duration * 60, 2400),
                brain_state="Active Focus (Beta 15Hz)",
                reason=f"Flow quality {self.flow_quality:.2f} - 중간 집중 상태"
            )
        
        # Low Flow (0.3-0.5): Theta/Alpha transition
        elif self.flow_quality >= 0.3:
            return BiauralBeatParams(
                base_freq=396,          # G=396Hz (Grounding, 불안 해소)
                beat_freq=7.5,          # Theta-Alpha (7.5 Hz) - 창의성
                carrier_wave="sine",
                duration=min(self.focus_duration * 60, 1800),
                brain_state="Creative Relaxation (Theta 7.5Hz)",
                reason=f"Flow quality {self.flow_quality:.2f} - 이완 필요"
            )
        
        # Very Low Flow (<0.3): Theta for reset
        else:
            return BiauralBeatParams(
                base_freq=528,          # 치유 주파수
                beat_freq=6.0,          # Theta (6 Hz) - 명상/휴식
                carrier_wave="square",  # 부드러운 파형
                duration=min(self.focus_duration * 60, 1200),
                brain_state="Reset Mode (Theta 6Hz)",
                reason=f"Flow quality {self.flow_quality:.2f} - 재충전 필요"
            )

def analyze_flow_report(report_path: Path) -> Optional[FlowFrequency]:
    """Flow observer 리포트 분석"""
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 현재 상태 추출
        if "current_state" in data:
            state = data["current_state"]
            return FlowFrequency(
                flow_quality=state.get("quality", 0.5),
                energy_level=state.get("energy", 0.5),
                focus_duration=state.get("duration_minutes", 30)
            )
        
        # 평균 상태 계산
        elif "flow_states" in data and data["flow_states"]:
            states = data["flow_states"]
            avg_quality = sum(s.get("quality", 0.5) for s in states) / len(states)
            avg_duration = sum(s.get("duration", 30) for s in states) / len(states)
            return FlowFrequency(
                flow_quality=avg_quality,
                energy_level=0.5,  # 기본값
                focus_duration=int(avg_duration)
            )
        
        return None
    except Exception as e:
        print(f"❌ Error reading flow report: {e}", file=sys.stderr)
        return None

def main():
    """Flow → Music Frequency 변환 실행"""
    workspace = get_workspace_root()
    flow_report = workspace / "outputs" / "flow_observer_report_latest.json"
    
    print("🎵 Flow Frequency Encoder")
    print("=" * 60)
    
    # Flow report 분석
    if not flow_report.exists():
        print(f"⚠️  Flow report not found: {flow_report}")
        print("   Run Task: '🌊 Flow: Generate Report (1h)' first")
        return 1
    
    flow = analyze_flow_report(flow_report)
    if not flow:
        print("❌ Failed to analyze flow report")
        return 1
    
    # 주파수 파라미터 생성
    params = flow.to_binaural_params()
    
    # 결과 출력
    print(f"\n📊 Flow Analysis:")
    print(f"   Quality: {flow.flow_quality:.2%}")
    print(f"   Energy:  {flow.energy_level:.2%}")
    print(f"   Duration: {flow.focus_duration} minutes")
    
    print(f"\n🎶 Recommended Music Parameters:")
    print(f"   Base Frequency:  {params.base_freq} Hz")
    print(f"   Beat Frequency:  {params.beat_freq} Hz")
    print(f"   Carrier Wave:    {params.carrier_wave}")
    print(f"   Duration:        {params.duration/60:.1f} minutes")
    print(f"   Brain State:     {params.brain_state}")
    print(f"   Reason:          {params.reason}")
    
    # JSON 저장
    output_file = workspace / "outputs" / "flow_frequency_params_latest.json"
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "flow_state": asdict(flow),
        "music_params": asdict(params),
        "next_steps": [
            "Use Spotify API with these params",
            "Generate binaural beat audio file",
            "Schedule playback during next work session"
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved to: {output_file.relative_to(workspace)}")
    print("\n💡 Next Steps:")
    print("   1. Integrate with Spotify API")
    print("   2. Create binaural beat generator")
    print("   3. Auto-schedule playback based on flow state")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
