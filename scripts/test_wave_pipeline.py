#!/usr/bin/env python3
"""
파동적 Pipeline 테스트: 기존 vs Wave 비교
"""

import sys
import os
import time
from workspace_root import get_workspace_root

# Path setup
sys.path.insert(0, str(get_workspace_root() / "fdo_agi_repo"))

from orchestrator.contracts import TaskSpec
from orchestrator.streaming_pipeline import run_wave_pipeline
from orchestrator.tool_registry import ToolRegistry


def main():
    print("🌊 Testing Wave Pipeline...\n")
    
    # Sandbox 경로 설정 (절대 경로)
    sandbox_root = get_workspace_root() / "fdo_agi_repo" / "sandbox"
    os.makedirs(sandbox_root, exist_ok=True)
    os.makedirs(os.path.join(sandbox_root, "docs"), exist_ok=True)
    
    # 도구 레지스트리 초기화 (minimal config)
    cfg = {"rag_enabled": False, "rag_top_k": 3}  # RAG 비활성화로 빠른 테스트
    registry = ToolRegistry(cfg)
    
    # 테스트 작업
    task = TaskSpec(
        task_id="test_wave_pipeline",
        title="Asyncio 병렬 처리 설명",
        goal="Python에서 asyncio를 사용한 병렬 처리 방법을 3문장으로 간단히 설명해주세요",
        actions=[],
        citations=[]
    )
    
    plan = {
        "step": "explain",
        "topic": "asyncio parallel processing"
    }
    
    # Wave Pipeline 실행
    print("🚀 Running Wave Pipeline...")
    t_start = time.perf_counter()
    result = run_wave_pipeline(task, plan, registry)
    t_end = time.perf_counter()
    
    print(f"\n✅ Wave Pipeline completed!")
    print(f"   Total time: {t_end - t_start:.2f}s")
    print(f"   Task ID: {result['task_id']}")
    print(f"   Citations: {len(result['citations'])}")
    
    if 'timing' in result:
        timing = result['timing']
        print(f"\n📊 Detailed timing:")
        print(f"   Thesis:     {timing['thesis']:.2f}s")
        print(f"   Antithesis: {timing['antithesis']:.2f}s")
        print(f"   Synthesis:  {timing['synthesis']:.2f}s")
        print(f"   Total:      {timing['total']:.2f}s")
    
    print(f"\n📝 Summary preview:")
    preview = result['summary'][:300] + "..." if len(result['summary']) > 300 else result['summary']
    print(f"   {preview}")
    
    print(f"\n📈 Next step: Compare with baseline (4.66s Thesis + 0.65s others = 5.31s total)")
    print(f"   Current: {t_end - t_start:.2f}s")
    print(f"   Improvement: {((5.31 - (t_end - t_start)) / 5.31 * 100):.1f}%")


if __name__ == "__main__":
    main()
