#!/usr/bin/env python3
"""
Flow Observer → Frequency Parameter Encoder
리듬 상태를 음악 주파수로 변환

Usage:
    python scripts/flow_to_frequency.py
    → outputs/flow_frequency_params.json 생성
"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any
from workspace_root import get_workspace_root

@dataclass
class FrequencyParams:
    """음악 생성을 위한 주파수 파라미터"""
    base_freq: int          # 기본 주파수 (Hz)
    beat_freq: float        # Binaural beat 주파수 (Hz)
    carrier_wave: str       # 파형 타입
    amplitude: float        # 볼륨 (0.0-1.0)
    duration_sec: int       # 권장 재생 시간 (초)
    description: str        # 설명

class FlowFrequencyEncoder:
    """Flow 상태 → 주파수 변환기"""
    
    # Solfeggio frequencies (치유 주파수)
    FREQUENCIES = {
        "grounding": 396,      # 불안 해소
        "change": 417,         # 변화 촉진
        "harmony": 432,        # 자연 조화
        "transformation": 528, # DNA 복구
        "connection": 639,     # 관계 회복
        "awakening": 852       # 직관 활성화
    }
    
    # Brain wave frequencies
    BRAIN_WAVES = {
        "delta": (0.5, 4),    # 깊은 수면
        "theta": (4, 8),      # 명상, 창의성
        "alpha": (8, 13),     # 편안한 집중
        "beta": (13, 30),     # 활성 사고
        "gamma": (30, 100)    # 고차원 인지
    }
    
    def encode(self, flow_quality: float, energy_level: float = 0.7) -> FrequencyParams:
        """
        Flow 품질 → 음악 파라미터
        
        Args:
            flow_quality: 0.0 (산만) ~ 1.0 (깊은 몰입)
            energy_level: 0.0 (피곤) ~ 1.0 (활력)
        """
        if flow_quality >= 0.8:
            # 깊은 Flow: Alpha wave (10 Hz)
            return FrequencyParams(
                base_freq=self.FREQUENCIES["harmony"],  # 432 Hz
                beat_freq=10.0,
                carrier_wave="sine",
                amplitude=0.6,
                duration_sec=3600,  # 1시간 유지
                description="Deep Focus (Alpha 10Hz @ 432Hz)"
            )
        
        elif flow_quality >= 0.5:
            # 중간 집중: Low Beta (15 Hz)
            return FrequencyParams(
                base_freq=self.FREQUENCIES["transformation"],  # 528 Hz
                beat_freq=15.0,
                carrier_wave="sine",
                amplitude=0.7,
                duration_sec=1800,  # 30분 유지
                description="Active Focus (Beta 15Hz @ 528Hz)"
            )
        
        elif flow_quality >= 0.3:
            # 약한 집중: High Alpha (12 Hz)
            return FrequencyParams(
                base_freq=self.FREQUENCIES["change"],  # 417 Hz
                beat_freq=12.0,
                carrier_wave="sine",
                amplitude=0.5,
                duration_sec=900,  # 15분 유지
                description="Relaxed Attention (Alpha 12Hz @ 417Hz)"
            )
        
        else:
            # 산만: Theta (6 Hz) - 재충전
            return FrequencyParams(
                base_freq=self.FREQUENCIES["grounding"],  # 396 Hz
                beat_freq=6.0,
                carrier_wave="square",
                amplitude=0.4,
                duration_sec=600,  # 10분 휴식
                description="Reset & Recharge (Theta 6Hz @ 396Hz)"
            )

def main():
    workspace = get_workspace_root()
    flow_report = workspace / "outputs" / "flow_observer_report_latest.json"
    
    if not flow_report.exists():
        print("⚠️  Flow report not found. Run 'Flow: Generate Report (1h)' first.")
        return 1
    
    # Flow 상태 로드
    with open(flow_report) as f:
        data = json.load(f)
    
    current_flow = data.get("current_state", {})
    flow_quality = current_flow.get("quality", 0.5)
    
    # 주파수 파라미터 생성
    encoder = FlowFrequencyEncoder()
    params = encoder.encode(flow_quality)
    
    # 저장
    output = workspace / "outputs" / "flow_frequency_params.json"
    output.parent.mkdir(exist_ok=True)
    
    result = {
        "timestamp": data.get("timestamp"),
        "flow_quality": flow_quality,
        "frequency_params": asdict(params),
        "usage": {
            "spotify": f"Search for '{params.description}' playlists",
            "local_gen": f"Use tone generator with {params.base_freq}Hz + {params.beat_freq}Hz beat",
            "binaural": f"Left: {params.base_freq}Hz, Right: {params.base_freq + params.beat_freq}Hz"
        }
    }
    
    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Frequency params generated")
    print(f"   Flow Quality: {flow_quality:.2f}")
    print(f"   Recommendation: {params.description}")
    print(f"   Base Frequency: {params.base_freq} Hz")
    print(f"   Brain Wave: {params.beat_freq} Hz")
    print(f"\n📄 Output: {output}")
    
    return 0

if __name__ == "__main__":
    exit(main())
