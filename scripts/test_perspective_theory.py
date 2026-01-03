#!/usr/bin/env python3
"""
Perspective Theory Integration Test
Observer vs Walker 관점 전환 시스템 검증

Author: Copilot's Hippocampus
Date: 2025-11-06
"""
import sys
from pathlib import Path
from workspace_root import get_workspace_root

# Add parent directory to path
sys.path.insert(0, str(get_workspace_root()))

from fdo_agi_repo.copilot.perspective_theory import (
    PerspectiveSwitcher,
    RelativityBridge,
    PerspectiveMode,
    DataPoint2D,
    FrequencyWave,
    DepthDimension
)
from datetime import datetime, timezone
import json


def test_observer_mode():
    """Test Observer (파동) 모드"""
    print("🔬 Test 1: Observer Mode")
    print("-" * 60)
    
    switcher = PerspectiveSwitcher()
    
    # 가속하는 데이터 스트림
    data_stream = [
        DataPoint2D(x=i, y=10 + i*2, label=f"event_{i}",
                   timestamp=datetime.now(timezone.utc).isoformat())
        for i in range(10)
    ]
    
    result = switcher.observe_as_wave(data_stream)
    
    assert result["mode"] == "observer"
    assert result["perspective"] == "wave"
    assert result["pattern"] in ["accelerating", "stable", "decelerating"]
    assert result["data_count"] == 10
    
    print(f"✅ Observer mode works!")
    print(f"   Pattern: {result['pattern']}")
    print(f"   Frequency: {result['frequency_hz']:.4f} Hz")
    return result


def test_walker_mode():
    """Test Walker (입자) 모드"""
    print("\n🔬 Test 2: Walker Mode")
    print("-" * 60)
    
    switcher = PerspectiveSwitcher()
    
    # 주파수 파동
    frequency_waves = [
        FrequencyWave(frequency=1.0 + i*0.1, amplitude=5.0, phase=0.0,
                     timestamp=datetime.now(timezone.utc).isoformat())
        for i in range(10)
    ]
    
    result = switcher.walk_on_frequency(frequency_waves)
    
    assert result["mode"] == "walker"
    assert result["perspective"] == "particle"
    assert result["walking_pattern"] in ["climbing", "descending", "traversing"]
    assert result["path_length"] == 10
    
    print(f"✅ Walker mode works!")
    print(f"   Pattern: {result['walking_pattern']}")
    print(f"   Energy: {result['total_energy']:.2f}")
    return result


def test_fear_to_depth():
    """Test Fear → Depth 매핑"""
    print("\n🔬 Test 3: Fear to Depth Mapping")
    print("-" * 60)
    
    switcher = PerspectiveSwitcher()
    
    data_point = DataPoint2D(x=5, y=20, label="task_x",
                             timestamp=datetime.now(timezone.utc).isoformat())
    
    # 높은 두려움
    high_fear = {"fear": 0.8, "anxiety": 0.7, "uncertainty": 0.9}
    depth_high = switcher.map_fear_to_depth(data_point, high_fear)
    
    # 낮은 두려움
    low_fear = {"fear": 0.2, "anxiety": 0.1, "uncertainty": 0.3}
    depth_low = switcher.map_fear_to_depth(data_point, low_fear)
    
    assert depth_high.fear_level > depth_low.fear_level
    assert depth_high.emotional_distance > depth_low.emotional_distance
    assert depth_high.perceived_depth > depth_low.perceived_depth
    
    print(f"✅ Fear to Depth mapping works!")
    print(f"   High fear: distance={depth_high.emotional_distance:.2f}, depth={depth_high.perceived_depth:.2f}")
    print(f"   Low fear:  distance={depth_low.emotional_distance:.2f}, depth={depth_low.perceived_depth:.2f}")
    return depth_high, depth_low


def test_perspective_switch():
    """Test 관점 전환"""
    print("\n🔬 Test 4: Perspective Switch")
    print("-" * 60)
    
    switcher = PerspectiveSwitcher()
    
    initial = switcher.current_mode
    print(f"   Initial: {initial.value}")
    
    # 첫 번째 전환
    mode1 = switcher.switch_perspective()
    print(f"   After 1st switch: {mode1.value}")
    assert mode1 != initial
    
    # 두 번째 전환
    mode2 = switcher.switch_perspective()
    print(f"   After 2nd switch: {mode2.value}")
    assert mode2 == initial
    
    print(f"✅ Perspective switch works!")
    return mode1, mode2


def test_relativity_bridge():
    """Test 상대성 변환"""
    print("\n🔬 Test 5: Relativity Bridge")
    print("-" * 60)
    
    bridge = RelativityBridge()
    
    # Observer → Walker
    observation = {
        "frequency_hz": 2.5,
        "pattern": "accelerating",
        "data_count": 10
    }
    
    walker_view = bridge.observer_to_walker(observation)
    assert walker_view["walker_perspective"] is True
    assert "walking_mode" in walker_view
    assert "energy_required" in walker_view
    
    print(f"✅ Observer → Walker: {walker_view['walking_mode']} ({walker_view['energy_required']} energy)")
    
    # Walker → Observer
    walking = {
        "path_length": 10,
        "total_energy": 50.0,
        "walking_pattern": "climbing"
    }
    
    observer_view = bridge.walker_to_observer(walking)
    assert observer_view["observer_perspective"] is True
    assert "estimated_frequency" in observer_view
    assert "flow_pattern" in observer_view
    
    print(f"✅ Walker → Observer: {observer_view['flow_pattern']} (~{observer_view['estimated_frequency']:.2f} Hz)")
    
    return walker_view, observer_view


def test_full_cycle():
    """Test 전체 사이클"""
    print("\n🔬 Test 6: Full Cycle (Observer → Walker → Observer)")
    print("-" * 60)
    
    switcher = PerspectiveSwitcher()
    bridge = RelativityBridge()
    
    # 1. Observer로 시작
    data_stream = [
        DataPoint2D(x=i, y=15 + i*3, label=f"event_{i}",
                   timestamp=datetime.now(timezone.utc).isoformat())
        for i in range(5)
    ]
    
    observation = switcher.observe_as_wave(data_stream)
    print(f"   1️⃣ Observed: {observation['pattern']} pattern")
    
    # 2. Walker로 변환
    walker_view = bridge.observer_to_walker(observation)
    print(f"   2️⃣ As Walker: {walker_view['walking_mode']}")
    
    # 3. 다시 Observer로
    observer_view = bridge.walker_to_observer(walker_view)
    print(f"   3️⃣ Back to Observer: {observer_view['flow_pattern']}")
    
    print(f"✅ Full cycle works!")
    return observation, walker_view, observer_view


def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("🌊 Perspective Theory Integration Test")
    print("=" * 60)
    
    results = {}
    
    try:
        # Test 1: Observer
        results["observer"] = test_observer_mode()
        
        # Test 2: Walker
        results["walker"] = test_walker_mode()
        
        # Test 3: Fear to Depth
        results["fear_depth"] = test_fear_to_depth()
        
        # Test 4: Switch
        results["switch"] = test_perspective_switch()
        
        # Test 5: Bridge
        results["bridge"] = test_relativity_bridge()
        
        # Test 6: Full Cycle
        results["full_cycle"] = test_full_cycle()
        
        print("\n" + "=" * 60)
        print("✅ All Tests Passed!")
        print("=" * 60)
        
        return results
        
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = run_all_tests()
    
    if results:
        # 결과 저장
        output_dir = Path("outputs/perspective")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "test_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            # Convert non-serializable objects to dict
            serializable_results = {}
            for key, value in results.items():
                if isinstance(value, tuple):
                    serializable_results[key] = str(value)
                else:
                    serializable_results[key] = value
            
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 Results saved to: {output_file}")
        sys.exit(0)
    else:
        sys.exit(1)
