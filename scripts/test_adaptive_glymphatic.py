"""
Adaptive Glymphatic System 테스트
"""
import sys
from pathlib import Path
from workspace_root import get_workspace_root

# 경로 추가
repo_path = get_workspace_root() / "fdo_agi_repo"
sys.path.insert(0, str(repo_path))

from orchestrator.adaptive_glymphatic_system import AdaptiveGlymphaticSystem


def test_basic():
    """기본 테스트"""
    print("🧪 적응형 Glymphatic 시스템 테스트\n")
    
    system = AdaptiveGlymphaticSystem()
    
    # 상태 체크
    print("1. 현재 상태 체크")
    status = system.monitor_and_decide()
    
    print(f"   작업량: {status['workload']['workload_percent']:.1f}%")
    print(f"   피로도: {status['fatigue']['fatigue_level']:.1f}%")
    print(f"   결정: {status['decision']['action']}")
    print(f"   지연: {status['decision']['delay_minutes']}분")
    
    # 청소 필요 여부
    if status['should_cleanup']:
        print("\n2. 청소 실행")
        result = system.run_cleanup()
        print(f"   결과: {'성공' if result['success'] else '실패'}")
        print(f"   소요: {result['duration']:.1f}초")
    else:
        print("\n2. 청소 불필요")
    
    print("\n✅ 테스트 완료")


if __name__ == "__main__":
    test_basic()
