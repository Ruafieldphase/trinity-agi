#!/usr/bin/env python3
"""
Cost Rhythm Loop 테스트

RESONANT/DISSONANT/CHAOTIC 시나리오를 시뮬레이션합니다.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from lumen.monitoring.cost_rhythm_loop import (
    CostRhythmLoop,
    RhythmStatus,
    AdaptiveAction,
)


class TestScenario:
    """테스트 시나리오"""
    
    def __init__(self, name: str, daily_costs: List[float], expected_rhythm: str):
        """
        Args:
            name: 시나리오 이름
            daily_costs: 일일 비용 리스트
            expected_rhythm: 예상 리듬 상태
        """
        self.name = name
        self.daily_costs = daily_costs
        self.expected_rhythm = expected_rhythm


def test_scenario(scenario: TestScenario) -> bool:
    """
    시나리오 테스트
    
    Args:
        scenario: TestScenario 객체
        
    Returns:
        테스트 성공 여부
    """
    print("=" * 70)
    print(f"Test Scenario: {scenario.name}")
    print("=" * 70)
    
    # Cost Rhythm Loop 초기화
    loop = CostRhythmLoop(
        project_id=os.getenv("GCP_PROJECT", "naeda-genesis"),
        service_name=os.getenv("SERVICE_NAME", "ion-api-canary"),
    )
    
    # Mock daily costs
    loop.get_daily_costs = lambda days: scenario.daily_costs[:days]
    
    # 리듬 상태 계산
    state = loop.calculate_rhythm_state()
    
    # 결과 출력
    print(f"\n📊 Daily Costs: {scenario.daily_costs}")
    print(f"💰 Forecasted: ${state.forecasted_spend:.2f}")
    print(f"\n🎼 Resonance Metrics:")
    print(f"  - Coherence: {state.coherence:.3f}")
    print(f"  - Phase: {state.phase:.3f}")
    print(f"  - Entropy: {state.entropy:.3f}")
    print(f"\n🎯 Rhythm Status: {state.rhythm_status}")
    print(f"⚡ Adaptive Action: {state.adaptive_action}")
    print(f"✅ Confidence: {state.confidence:.0%}")
    
    # 검증
    passed = state.rhythm_status == scenario.expected_rhythm
    
    if passed:
        print(f"\n✅ PASS: {scenario.name}")
    else:
        print(f"\n❌ FAIL: Expected {scenario.expected_rhythm}, got {state.rhythm_status}")
    
    print("=" * 70)
    print()
    
    return passed


def main():
    """메인 테스트 함수"""
    print("=" * 70)
    print("Cost Rhythm Loop - Scenario Tests")
    print("=" * 70)
    print()
    
    # 시나리오 정의
    scenarios = [
        # Scenario 1: RESONANT - 안정적인 비용
        TestScenario(
            name="RESONANT: Stable Costs",
            daily_costs=[0.80, 0.82, 0.81, 0.79, 0.80, 0.81, 0.80],  # ~$24/month
            expected_rhythm=RhythmStatus.RESONANT.value,
        ),
        
        # Scenario 2: DISSONANT - 변동성 있는 비용
        TestScenario(
            name="DISSONANT: Variable Costs",
            daily_costs=[0.75, 1.20, 0.90, 1.50, 0.80, 1.10, 0.95],  # ~$30/month
            expected_rhythm=RhythmStatus.DISSONANT.value,
        ),
        
        # Scenario 3: CHAOTIC - 혼란스러운 비용
        TestScenario(
            name="CHAOTIC: Unpredictable Costs",
            daily_costs=[1.0, 8.0, 2.0, 9.5, 1.5, 7.8, 3.2],  # ~$100/month (예산 초과)
            expected_rhythm=RhythmStatus.CHAOTIC.value,
        ),
        
        # Scenario 4: DISSONANT - 상승 추세
        TestScenario(
            name="DISSONANT: Rising Trend",
            daily_costs=[5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0],  # ~$190/month
            expected_rhythm=RhythmStatus.DISSONANT.value,
        ),
    ]
    
    # 테스트 실행
    results = []
    for scenario in scenarios:
        passed = test_scenario(scenario)
        results.append(passed)
    
    # 최종 결과
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
