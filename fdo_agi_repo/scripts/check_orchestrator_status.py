"""
Orchestrator 실시간 상태 체크 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from orchestrator.full_stack_orchestrator import FullStackOrchestrator

def main():
    workspace_root = Path("C:\\workspace\\agi")
    
    # Orchestrator 인스턴스 생성 (상태만 조회)
    orchestrator = FullStackOrchestrator(
        workspace_root=workspace_root,
        enable_resonance=False,  # 빠른 체크를 위해 비활성화
        enable_bqi=True,
        enable_gateway=True,
        enable_youtube=True
    )
    
    # 상태 조회
    status = orchestrator.get_status()
    state = status['state']
    components = status['components']
    
    print("\n=== Orchestrator Status ===")
    active_count = sum(1 for v in components.values() if v == 'active')
    print(f"  Components Active: {active_count}/{len(components)}")
    print(f"  Components: {', '.join([k for k,v in components.items() if v == 'active'])}")
    print(f"  Learning Cycles: {state.get('learning_cycles', 0)}")
    print(f"  Events Processed: {state.get('events_processed', 0)}")
    print(f"  Last Update: {status['timestamp']}")
    
    # JSON으로도 출력
    import json
    print("\n[JSON]")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()
