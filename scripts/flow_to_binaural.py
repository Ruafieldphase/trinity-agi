#!/usr/bin/env python3
"""
Flow Observer 데이터 → Binaural Beat 파라미터 변환
실시간 Flow 상태를 음악적 주파수로 인코딩

Usage:
    python scripts/flow_to_binaural.py --input outputs/flow_observer_report_latest.json
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Literal

@dataclass
class BinauralParams:
    """Binaural beat 생성 파라미터"""
    base_freq: int      # 기본 주파수 (Hz)
    beat_freq: float    # 비트 주파수 (Hz) - 뇌파 유도 목표
    carrier: Literal["sine", "square", "triangle"]
    state: str          # Flow 상태 설명
    
    def to_dict(self):
        return asdict(self)

class FlowFrequencyEncoder:
    """Flow quality → 음악 주파수 매핑"""
    
    # Solfeggio Frequencies (치유 주파수)
    FREQ_MAP = {
        "deep_flow": 528,      # DNA repair, transformation
        "focused": 432,        # Natural tuning, relaxation
        "moderate": 396,       # Grounding, liberation from fear
        "scattered": 285,      # Healing tissue, quantum cognition
    }
    
    # 뇌파 매핑
    BRAINWAVE_MAP = {
        "deep_flow": 10.0,     # Alpha (깊은 집중)
        "focused": 15.0,       # Low Beta (활성 사고)
        "moderate": 6.0,       # Theta (창의성)
        "scattered": 4.0,      # Theta-Delta (이완)
    }
    
    def encode(self, flow_quality: float) -> BinauralParams:
        """
        Flow quality (0.0-1.0) → Binaural beat 파라미터
        
        매핑 로직:
        - 0.8+ : Deep flow (528 Hz + 10 Hz Alpha)
        - 0.5-0.8 : Focused (432 Hz + 15 Hz Low Beta)
        - 0.3-0.5 : Moderate (396 Hz + 6 Hz Theta)
        - <0.3 : Scattered (285 Hz + 4 Hz Theta)
        """
        if flow_quality >= 0.8:
            state = "deep_flow"
            carrier = "sine"
        elif flow_quality >= 0.5:
            state = "focused"
            carrier = "sine"
        elif flow_quality >= 0.3:
            state = "moderate"
            carrier = "triangle"
        else:
            state = "scattered"
            carrier = "square"
        
        return BinauralParams(
            base_freq=self.FREQ_MAP[state],
            beat_freq=self.BRAINWAVE_MAP[state],
            carrier=carrier,
            state=f"{state} (quality={flow_quality:.2f})"
        )

def load_flow_report(path: Path) -> dict:
    """Flow Observer 리포트 로드"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Flow → Binaural Beat 변환")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("outputs/flow_observer_report_latest.json"),
        help="Flow Observer 리포트 경로"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/binaural_params_latest.json"),
        help="Binaural 파라미터 출력 경로"
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"❌ Flow report not found: {args.input}", file=sys.stderr)
        print("💡 Run task: '🌊 Flow: Generate Report (1h)' first", file=sys.stderr)
        sys.exit(1)
    
    # Flow 데이터 로드
    flow_data = load_flow_report(args.input)
    
    # 현재 상태 추출
    if "current_state" in flow_data:
        current_quality = flow_data["current_state"].get("quality", 0.5)
    elif "summary" in flow_data and "average_quality" in flow_data["summary"]:
        current_quality = flow_data["summary"]["average_quality"]
    else:
        print("⚠️  No quality data found, using default 0.5", file=sys.stderr)
        current_quality = 0.5
    
    # 주파수 인코딩
    encoder = FlowFrequencyEncoder()
    params = encoder.encode(current_quality)
    
    # 결과 저장
    output_data = {
        "timestamp": flow_data.get("timestamp", "unknown"),
        "input_quality": current_quality,
        "binaural_params": params.to_dict(),
        "usage": {
            "spotify_api": f"Search for '{params.state.split()[0]}' focus music",
            "local_generator": "Use base_freq and beat_freq to generate WAV",
            "recommendation": f"Play music at {params.base_freq} Hz with {params.beat_freq} Hz modulation"
        }
    }
    
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # 콘솔 출력
    print(f"\n🎵 Flow → Music Encoding Complete")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Input Quality: {current_quality:.2%}")
    print(f"State: {params.state}")
    print(f"Base Frequency: {params.base_freq} Hz")
    print(f"Beat Frequency: {params.beat_freq} Hz ({_get_brainwave_name(params.beat_freq)})")
    print(f"Carrier Wave: {params.carrier}")
    print(f"\n💡 Next Steps:")
    print(f"  1. Use these params with a binaural beat generator")
    print(f"  2. Or search Spotify/YouTube for '{params.state.split()[0]} focus music'")
    print(f"  3. Output saved: {args.output}")
    print()

def _get_brainwave_name(freq: float) -> str:
    """주파수 → 뇌파 이름"""
    if freq < 4:
        return "Delta (deep sleep)"
    elif freq < 8:
        return "Theta (creativity)"
    elif freq < 13:
        return "Alpha (relaxed focus)"
    elif freq < 30:
        return "Beta (active thinking)"
    else:
        return "Gamma (peak performance)"

if __name__ == "__main__":
    main()
