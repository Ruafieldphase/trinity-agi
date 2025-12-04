#!/usr/bin/env python3
"""
Information Flow Score 테스트
정보이론 기반 AI 리듬 진단
"""

import sys
from pathlib import Path

# fdo_agi_repo 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "fdo_agi_repo"))

from monitor.metrics_collector import MetricsCollector


def main():
    print("=" * 70)
    print("🌊 Information Flow Analysis")
    print("=" * 70)
    
    collector = MetricsCollector()
    
    # 1시간 윈도우로 분석
    hours = 1.0
    if len(sys.argv) > 1:
        try:
            hours = float(sys.argv[1])
        except ValueError:
            pass
    
    print(f"\n📊 Analyzing last {hours} hour(s)...")
    print("-" * 70)
    
    # 정보이론 분석
    flow_data = collector.get_information_flow_score(hours=hours)
    
    # 결과 출력
    print(f"\n🎯 Flow Score: {flow_data['flow_score']:.3f}")
    print(f"   Status: {flow_data['status'].upper()}")
    print(f"\n📈 Components:")
    for key, value in flow_data['components'].items():
        bar_length = int(value * 20)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"   {key:20s} {bar} {value:.3f}")
    
    print(f"\n💡 Recommendation:")
    print(f"   {flow_data['recommendation']}")
    
    # 기존 헬스 상태와 비교
    print(f"\n🔍 Context (AGI Health):")
    print("-" * 70)
    health = collector.get_health_status()
    print(f"   Healthy: {health.get('healthy', 'unknown')}")
    print(f"   Success Rate: {health.get('metrics', {}).get('success_rate', 0):.1f}%")
    print(f"   Avg Quality: {health.get('metrics', {}).get('avg_quality', 0):.3f}")
    
    print("\n" + "=" * 70)
    
    return flow_data


if __name__ == '__main__':
    result = main()
    
    # Exit code based on flow score
    if result['flow_score'] > 0.6:
        sys.exit(0)  # Good flow
    elif result['flow_score'] > 0.4:
        sys.exit(1)  # Moderate
    else:
        sys.exit(2)  # Stagnant
