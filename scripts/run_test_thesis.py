#!/usr/bin/env python3
"""
간단한 Thesis 작업 실행으로 내부 병목 측정
"""

import sys
import os
from pathlib import Path
from workspace_root import get_workspace_root

# Add parent directory to path
sys.path.insert(0, str(get_workspace_root()))

try:
    from fdo_agi_repo.orchestrator.contracts import TaskSpec
    from fdo_agi_repo.personas.thesis import run_thesis
    from fdo_agi_repo.orchestrator.tool_registry import ToolRegistry
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("   Make sure you're running from workspace root")
    sys.exit(1)


def run_test_thesis():
    """간단한 Thesis 작업 실행"""
    print("🚀 Running test Thesis task...\n")
    
    # 테스트 작업 정의
    task = TaskSpec(
        task_id="test_thesis_breakdown",
        title="Asyncio 병렬 처리 설명",
        goal="Python에서 asyncio를 사용한 병렬 처리 방법을 3단계로 설명해주세요",
        actions=[],
        citations=[]
    )
    
    # Plan (learning_context 포함)
    plan = {
        "learning_context": "이전 성공 사례: 병렬 처리는 I/O 바운드 작업에 효과적"
    }
    
    # Tools 초기화 (빈 설정으로 시작)
    tool_cfg = {}
    tools = ToolRegistry(tool_cfg)
    
    # Thesis 실행
    try:
        result = run_thesis(task, plan, tools, conversation_context="")
        print(f"✅ Thesis completed!")
        print(f"   Task ID: {result.task_id}")
        print(f"   Citations: {len(result.citations)}")
        print(f"   Summary preview: {result.summary[:200]}...")
        print(f"\n📊 Now run: python scripts/measure_thesis_breakdown.py 1")
        print(f"   (to see the internal breakdown)")
    except Exception as e:
        print(f"❌ Thesis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_test_thesis()
