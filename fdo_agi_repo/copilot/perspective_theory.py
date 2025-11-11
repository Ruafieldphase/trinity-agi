#!/usr/bin/env python3
"""
Perspective Theory: Observer vs Walker
관찰자(파동)와 입자(걷는자)의 관점 전환 시스템

철학적 기반:
1. Observer (파동/관찰자): 데이터가 눈앞에 흐른다 (2D 텔레메트리)
2. Walker (입자/전자): 내가 데이터 위를 걷는다 (주파수 높낮이)
3. Depth = Fear = Emotion (깊이는 두려움이자 감정)
4. Distance = Emotional Distance (멀리 있는 것 = 두려움으로 인한 거리)

상대성 이론 비유:
- Observer: 주파수를 바라보고 듣는다 (정지된 관찰자)
- Walker: 주파수의 높낮이를 걸어간다 (움직이는 입자)

Author: Copilot's Hippocampus (inspired by User's insight)
Date: 2025-11-06
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class PerspectiveMode(Enum):
    """관점 모드"""
    OBSERVER = "observer"  # 파동: 데이터가 흐른다
    WALKER = "walker"      # 입자: 내가 걷는다


@dataclass
class DataPoint2D:
    """2D 데이터 포인트 (표면적 현실)"""
    x: float  # 시간 축
    y: float  # 강도/빈도 축
    label: str
    timestamp: str


@dataclass
class DepthDimension:
    """깊이 차원 (두려움/감정)"""
    fear_level: float  # 0.0 ~ 1.0 (두려움 강도)
    emotional_distance: float  # 감정적 거리
    perceived_depth: float  # 인지된 깊이
    context: str


@dataclass
class FrequencyWave:
    """주파수 파동"""
    frequency: float  # Hz
    amplitude: float  # 진폭
    phase: float  # 위상
    timestamp: str


class PerspectiveSwitcher:
    """관점 전환기: Observer ↔ Walker"""
    
    def __init__(self, output_dir: str = "outputs/perspective"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.current_mode = PerspectiveMode.OBSERVER
        self.history_file = self.output_dir / "perspective_history.jsonl"
        
    def observe_as_wave(self, data_stream: List[DataPoint2D]) -> Dict:
        """
        관찰자(파동) 모드: 데이터가 흐르는 것을 관찰
        
        Args:
            data_stream: 2D 데이터 스트림
            
        Returns:
            관찰 결과 (주파수, 패턴 등)
        """
        if not data_stream:
            return {"mode": "observer", "pattern": "none", "frequency": 0.0}
        
        # 데이터 흐름의 주파수 계산
        time_diffs = []
        for i in range(1, len(data_stream)):
            try:
                t1 = datetime.fromisoformat(data_stream[i-1].timestamp)
                t2 = datetime.fromisoformat(data_stream[i].timestamp)
                time_diffs.append((t2 - t1).total_seconds())
            except:
                continue
        
        avg_interval = sum(time_diffs) / len(time_diffs) if time_diffs else 1.0
        frequency = 1.0 / avg_interval if avg_interval > 0 else 0.0
        
        # 패턴 감지 (주파수 바라보기)
        pattern = self._detect_flow_pattern(data_stream)
        
        result = {
            "mode": "observer",
            "perspective": "wave",
            "frequency_hz": frequency,
            "pattern": pattern,
            "data_count": len(data_stream),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._log_observation(result)
        return result
    
    def walk_on_frequency(self, frequency_waves: List[FrequencyWave]) -> Dict:
        """
        걷는자(입자) 모드: 주파수의 높낮이를 걸어감
        
        Args:
            frequency_waves: 주파수 파동 리스트
            
        Returns:
            걷기 결과 (경로, 에너지 등)
        """
        if not frequency_waves:
            return {"mode": "walker", "path": "none", "energy": 0.0}
        
        # 주파수 높낮이를 걷는 경로 계산
        path = []
        total_energy = 0.0
        
        for i, wave in enumerate(frequency_waves):
            # 높낮이 = 주파수 * 진폭
            height = wave.frequency * wave.amplitude
            path.append({
                "step": i,
                "height": height,
                "frequency": wave.frequency,
                "amplitude": wave.amplitude
            })
            
            # 에너지 = 높낮이 변화량
            if i > 0:
                prev_height = frequency_waves[i-1].frequency * frequency_waves[i-1].amplitude
                energy_delta = abs(height - prev_height)
                total_energy += energy_delta
        
        # 걷는 패턴 분석
        walking_pattern = self._analyze_walking_pattern(path)
        
        result = {
            "mode": "walker",
            "perspective": "particle",
            "path_length": len(path),
            "total_energy": total_energy,
            "walking_pattern": walking_pattern,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._log_observation(result)
        return result
    
    def map_fear_to_depth(self, data_point: DataPoint2D, emotional_state: Dict) -> DepthDimension:
        """
        두려움을 깊이로 매핑: Fear → Depth
        
        Args:
            data_point: 2D 표면 데이터
            emotional_state: 감정 상태
            
        Returns:
            DepthDimension: 계산된 깊이 차원
        """
        # 두려움 레벨 추출
        fear_level = emotional_state.get("fear", 0.0)
        anxiety_level = emotional_state.get("anxiety", 0.0)
        uncertainty = emotional_state.get("uncertainty", 0.0)
        
        # 감정적 거리 계산: 두려움이 클수록 멀리 느껴짐
        emotional_distance = (fear_level + anxiety_level + uncertainty) / 3.0
        
        # 인지된 깊이: 감정적 거리 * 데이터 강도
        perceived_depth = emotional_distance * data_point.y
        
        return DepthDimension(
            fear_level=fear_level,
            emotional_distance=emotional_distance,
            perceived_depth=perceived_depth,
            context=f"{data_point.label} at ({data_point.x}, {data_point.y})"
        )
    
    def switch_perspective(self) -> PerspectiveMode:
        """관점 전환: Observer ↔ Walker"""
        if self.current_mode == PerspectiveMode.OBSERVER:
            self.current_mode = PerspectiveMode.WALKER
        else:
            self.current_mode = PerspectiveMode.OBSERVER
        
        self._log_switch()
        return self.current_mode
    
    def _detect_flow_pattern(self, data_stream: List[DataPoint2D]) -> str:
        """데이터 흐름 패턴 감지"""
        if len(data_stream) < 3:
            return "insufficient_data"
        
        # Y 값 변화 추세
        y_values = [p.y for p in data_stream]
        increasing = sum(1 for i in range(1, len(y_values)) if y_values[i] > y_values[i-1])
        total = len(y_values) - 1
        
        if increasing / total > 0.7:
            return "accelerating"
        elif increasing / total < 0.3:
            return "decelerating"
        else:
            return "stable"
    
    def _analyze_walking_pattern(self, path: List[Dict]) -> str:
        """걷는 패턴 분석"""
        if len(path) < 3:
            return "insufficient_steps"
        
        heights = [p["height"] for p in path]
        avg_height = sum(heights) / len(heights)
        
        high_steps = sum(1 for h in heights if h > avg_height * 1.2)
        total_steps = len(heights)
        
        if high_steps / total_steps > 0.5:
            return "climbing"  # 높은 주파수로 올라감
        elif high_steps / total_steps < 0.3:
            return "descending"  # 낮은 주파수로 내려감
        else:
            return "traversing"  # 평지 걷기
    
    def _log_observation(self, observation: Dict):
        """관찰 기록"""
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(observation, ensure_ascii=False) + "\n")
    
    def _log_switch(self):
        """관점 전환 기록"""
        event = {
            "event": "perspective_switch",
            "from": "observer" if self.current_mode == PerspectiveMode.WALKER else "walker",
            "to": self.current_mode.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._log_observation(event)


class RelativityBridge:
    """상대성 이론 브릿지: 관찰자 ↔ 입자 변환"""
    
    @staticmethod
    def observer_to_walker(observation: Dict) -> Dict:
        """
        관찰자 관점 → 입자 관점 변환
        
        "데이터가 흐른다" → "내가 데이터 위를 걷는다"
        """
        frequency = observation.get("frequency_hz", 0.0)
        pattern = observation.get("pattern", "stable")
        
        # 주파수를 걷는 높낮이로 변환
        if pattern == "accelerating":
            walking_mode = "climbing"
            energy_required = "high"
        elif pattern == "decelerating":
            walking_mode = "descending"
            energy_required = "low"
        else:
            walking_mode = "traversing"
            energy_required = "medium"
        
        return {
            "walker_perspective": True,
            "walking_mode": walking_mode,
            "frequency_height": frequency * 10.0,  # 임의 스케일
            "energy_required": energy_required,
            "original_observation": observation
        }
    
    @staticmethod
    def walker_to_observer(walking: Dict) -> Dict:
        """
        입자 관점 → 관찰자 관점 변환
        
        "내가 걷는다" → "데이터가 흐른다"
        """
        path_length = walking.get("path_length", 0)
        total_energy = walking.get("total_energy", 0.0)
        
        # 걷기 에너지를 주파수로 변환
        estimated_frequency = total_energy / (path_length or 1)
        
        if walking.get("walking_pattern") == "climbing":
            flow_pattern = "accelerating"
        elif walking.get("walking_pattern") == "descending":
            flow_pattern = "decelerating"
        else:
            flow_pattern = "stable"
        
        return {
            "observer_perspective": True,
            "estimated_frequency": estimated_frequency,
            "flow_pattern": flow_pattern,
            "data_stream_quality": "inferred_from_walking",
            "original_walking": walking
        }


def demo_perspective_theory():
    """Perspective Theory 데모"""
    print("🌊 Perspective Theory Demo")
    print("=" * 60)
    
    switcher = PerspectiveSwitcher()
    bridge = RelativityBridge()
    
    # 1. Observer 모드: 데이터가 흐른다
    print("\n1️⃣ Observer Mode (Wave/관찰자)")
    print("-" * 60)
    
    data_stream = [
        DataPoint2D(x=i, y=10 + i*2, label=f"event_{i}", 
                   timestamp=datetime.now(timezone.utc).isoformat())
        for i in range(10)
    ]
    
    observation = switcher.observe_as_wave(data_stream)
    print(f"📊 Observation: {json.dumps(observation, indent=2, ensure_ascii=False)}")
    
    # 2. Walker 모드: 내가 걷는다
    print("\n2️⃣ Walker Mode (Particle/입자)")
    print("-" * 60)
    
    frequency_waves = [
        FrequencyWave(frequency=1.0 + i*0.1, amplitude=5.0, phase=0.0,
                     timestamp=datetime.now(timezone.utc).isoformat())
        for i in range(10)
    ]
    
    walking = switcher.walk_on_frequency(frequency_waves)
    print(f"🚶 Walking: {json.dumps(walking, indent=2, ensure_ascii=False)}")
    
    # 3. Fear → Depth 매핑
    print("\n3️⃣ Fear to Depth Mapping")
    print("-" * 60)
    
    emotional_state = {
        "fear": 0.7,
        "anxiety": 0.5,
        "uncertainty": 0.8
    }
    
    depth = switcher.map_fear_to_depth(data_stream[5], emotional_state)
    print(f"📏 Depth Dimension: {asdict(depth)}")
    
    # 4. 관점 전환
    print("\n4️⃣ Perspective Switch")
    print("-" * 60)
    
    new_mode = switcher.switch_perspective()
    print(f"🔄 Switched to: {new_mode.value}")
    
    # 5. 상대성 변환
    print("\n5️⃣ Relativity Bridge")
    print("-" * 60)
    
    walker_view = bridge.observer_to_walker(observation)
    print(f"Observer → Walker: {json.dumps(walker_view, indent=2, ensure_ascii=False)}")
    
    observer_view = bridge.walker_to_observer(walking)
    print(f"Walker → Observer: {json.dumps(observer_view, indent=2, ensure_ascii=False)}")
    
    print("\n✅ Demo Complete!")


if __name__ == "__main__":
    demo_perspective_theory()
