"""
Glymphatic 시스템과 자율 목표 시스템 통합 테스트

시나리오:
1. Goal 실행 → 작업량 증가 감지
2. Glymphatic 피로도 측정
3. 청소 필요 시점 판단
4. 청소 실행 → Goal 일시 중지/재개
"""
import sys
import time
from pathlib import Path

# 경로 추가
repo_path = Path(__file__).parent.parent / "fdo_agi_repo"
sys.path.insert(0, str(repo_path))

from orchestrator.adaptive_glymphatic_system import AdaptiveGlymphaticSystem


def simulate_goal_execution():
    """Goal 실행 시뮬레이션"""
    print("🎯 자율 목표 실행 시뮬레이션\n")
    
    system = AdaptiveGlymphaticSystem()
    
    # 초기 상태
    print("━━━ 시작 상태 ━━━")
    status = system.monitor_and_decide()
    print_status(status)
    
    # Goal 실행 (작업량 증가)
    print("\n━━━ Goal 실행 중 (30초) ━━━")
    print("💼 목표: 리듬 상태 리포트 생성")
    time.sleep(2)
    
    status = system.monitor_and_decide()
    print_status(status)
    
    # 중간 체크
    print("\n━━━ 중간 체크 ━━━")
    status = system.monitor_and_decide()
    print_status(status)
    
    if status['should_cleanup']:
        print("\n🧹 청소 필요! 실행 중...")
        result = system.run_cleanup()
        
        if result['success']:
            print(f"✅ 청소 완료 (소요: {result['duration']:.1f}초)")
            print(f"📊 정리된 항목: {result.get('items_cleaned', 'N/A')}")
        else:
            print(f"❌ 청소 실패: {result.get('error', 'Unknown')}")
    
    # 최종 상태
    print("\n━━━ 최종 상태 ━━━")
    status = system.monitor_and_decide()
    print_status(status)
    
    # 권장사항
    print("\n💡 권장사항:")
    if status['decision']['action'] == 'cleanup_now':
        print("   즉시 청소 실행")
    elif status['decision']['action'] == 'schedule_default':
        print(f"   {status['decision']['delay_minutes']}분 후 청소 예약")
    else:
        print("   현재 청소 불필요")


def print_status(status):
    """상태 출력"""
    print(f"   작업량: {status['workload']['workload_percent']:.1f}%")
    print(f"   피로도: {status['fatigue']['fatigue_level']:.1f}%")
    print(f"   결정: {status['decision']['action']}")
    print(f"   지연: {status['decision']['delay_minutes']}분")
    print(f"   청소 필요: {'예' if status['should_cleanup'] else '아니오'}")


if __name__ == "__main__":
    simulate_goal_execution()
