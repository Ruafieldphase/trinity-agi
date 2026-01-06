#!/usr/bin/env python3
"""
Flow Observer → 음악 주파수 매핑 시스템
현재 Flow 상태를 읽어 권장 음악 파라미터 생성

Usage:
    python scripts/flow_frequency_mapper.py
    python scripts/flow_frequency_mapper.py --output outputs/music_recommendation.json
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import argparse


@dataclass
class MusicFrequencyParams:
    """음악 주파수 파라미터"""
    base_freq: int          # Hz (기본 주파수)
    beat_freq: float        # Hz (Binaural beat 차이)
    brain_state: str        # 목표 뇌파 상태
    carrier_wave: str       # 파형 타입
    volume_percent: int     # 권장 볼륨 (%)
    duration_min: int       # 권장 재생 시간 (분)
    spotify_query: str      # Spotify 검색 쿼리
    reason: str             # 추천 이유


class FlowFrequencyMapper:
    """Flow 상태 → 음악 주파수 변환"""
    
    # Solfeggio Frequencies (치유 주파수)
    FREQ_LIBERATION = 396      # Fear → Liberation
    FREQ_TRANSFORMATION = 417  # Change
    FREQ_DNA_REPAIR = 528      # Miracles, DNA repair
    FREQ_CONNECTION = 639      # Relationships
    FREQ_AWAKENING = 741       # Intuition
    FREQ_SPIRITUAL = 852       # Spiritual order
    
    # Natural Frequencies
    FREQ_NATURE = 432          # Natural tuning (A=432Hz)
    
    @staticmethod
    def map_flow_to_music(flow_quality: float, energy_level: float = 0.5) -> MusicFrequencyParams:
        """
        Flow quality와 에너지 레벨 → 음악 파라미터
        
        Args:
            flow_quality: 0.0-1.0 (Flow Observer에서)
            energy_level: 0.0-1.0 (optional, 기본 0.5)
        
        Returns:
            MusicFrequencyParams
        """
        if flow_quality >= 0.85:  # 깊은 몰입 (Deep Flow)
            return MusicFrequencyParams(
                base_freq=FlowFrequencyMapper.FREQ_NATURE,
                beat_freq=10.0,  # Alpha (10 Hz)
                brain_state="Alpha (Deep Focus)",
                carrier_wave="sine",
                volume_percent=40,
                duration_min=90,
                spotify_query="ambient focus deep concentration",
                reason="깊은 Flow 유지를 위한 Alpha 파 유도"
            )
        
        elif flow_quality >= 0.65:  # 중간 집중 (Active Focus)
            return MusicFrequencyParams(
                base_freq=FlowFrequencyMapper.FREQ_DNA_REPAIR,
                beat_freq=15.0,  # Low Beta (15 Hz)
                brain_state="Low Beta (Active Thinking)",
                carrier_wave="sine",
                volume_percent=50,
                duration_min=60,
                spotify_query="lo-fi study beats instrumental",
                reason="활성 사고를 위한 Low Beta 파 유도"
            )
        
        elif flow_quality >= 0.40:  # 가벼운 작업 (Light Work)
            return MusicFrequencyParams(
                base_freq=FlowFrequencyMapper.FREQ_CONNECTION,
                beat_freq=18.0,  # Mid Beta (18 Hz)
                brain_state="Mid Beta (Alert)",
                carrier_wave="triangle",
                volume_percent=55,
                duration_min=45,
                spotify_query="chill coding programming background",
                reason="경계 상태 유지를 위한 Mid Beta 파"
            )
        
        elif flow_quality >= 0.20:  # 산만 (Distracted)
            return MusicFrequencyParams(
                base_freq=FlowFrequencyMapper.FREQ_TRANSFORMATION,
                beat_freq=6.5,  # Theta (6.5 Hz)
                brain_state="Theta (Creative Relaxation)",
                carrier_wave="sine",
                volume_percent=30,
                duration_min=20,
                spotify_query="meditation relaxing calm",
                reason="재집중을 위한 Theta 파 유도 (창의성)"
            )
        
        else:  # 매우 산만 (Need Reset)
            return MusicFrequencyParams(
                base_freq=FlowFrequencyMapper.FREQ_LIBERATION,
                beat_freq=3.0,  # Delta (3 Hz)
                brain_state="Delta (Deep Reset)",
                carrier_wave="sine",
                volume_percent=25,
                duration_min=15,
                spotify_query="binaural beats deep sleep reset",
                reason="완전 리셋을 위한 Delta 파 (짧은 휴식 권장)"
            )


def load_latest_flow_state(workspace: Path) -> Optional[dict]:
    """최신 Flow Observer 리포트 로드"""
    flow_report = workspace / "outputs" / "flow_observer_report_latest.json"
    
    if not flow_report.exists():
        print(f"⚠️  Flow report not found: {flow_report}", file=sys.stderr)
        print("   Run: python fdo_agi_repo/copilot/flow_observer_integration.py", file=sys.stderr)
        return None
    
    with open(flow_report, encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Flow → Music Frequency Mapper")
    parser.add_argument("--flow-quality", type=float, help="Manual flow quality (0.0-1.0)")
    parser.add_argument("--energy", type=float, default=0.5, help="Energy level (0.0-1.0)")
    parser.add_argument("--output", type=Path, help="Output JSON path")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
    args = parser.parse_args()
    
    workspace = args.workspace
    
    # Flow quality 결정
    if args.flow_quality is not None:
        flow_quality = args.flow_quality
        source = "manual input"
    else:
        flow_data = load_latest_flow_state(workspace)
        if flow_data is None:
            print("❌ No flow data available. Use --flow-quality option.", file=sys.stderr)
            return 1
        
        # 최근 flow state 가져오기
        flow_quality = flow_data.get("current_flow_quality", 0.5)
        source = "Flow Observer"
    
    # 변환
    mapper = FlowFrequencyMapper()
    music_params = mapper.map_flow_to_music(flow_quality, args.energy)
    
    # 출력
    result = {
        "timestamp": "2025-11-10T00:00:00Z",  # TODO: 실제 타임스탬프
        "source": source,
        "input": {
            "flow_quality": flow_quality,
            "energy_level": args.energy
        },
        "recommendation": asdict(music_params)
    }
    
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved: {args.output}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 사람이 읽을 수 있는 요약
    print("\n🎵 음악 추천:", file=sys.stderr)
    print(f"   Flow Quality: {flow_quality:.1%}", file=sys.stderr)
    print(f"   목표 뇌파: {music_params.brain_state}", file=sys.stderr)
    print(f"   기본 주파수: {music_params.base_freq} Hz", file=sys.stderr)
    print(f"   Binaural Beat: {music_params.beat_freq} Hz", file=sys.stderr)
    print(f"   Spotify: '{music_params.spotify_query}'", file=sys.stderr)
    print(f"   이유: {music_params.reason}", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
