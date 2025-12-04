"""
Batch Evidence Gate Test: 실제 워크로드로 evidence_gate retry/synthetic 동작 검증.
10-15개 태스크를 실행해 성공률 변화를 측정합니다.
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator.pipeline import run_task

# 다양한 테스트 케이스: 근거가 쉬운 것, 어려운 것, 종합적인 것 혼합
TEST_CASES: List[Dict[str, Any]] = [
    {
        "task_id": "batch_evidence_01",
        "title": "Standard RAG Test",
        "goal": "Summarize best practices for Python exception handling",
        "constraints": [],
        "inputs": {},
        "scope": "doc",
        "permissions": ["READ"],
        "evidence_required": True,
    },
    {
        "task_id": "batch_evidence_02",
        "title": "Broadened Retry Test",
        "goal": "Explain vertex AI embeddings and how they compare to OpenAI",
        "constraints": [],
        "inputs": {},
        "scope": "analysis",
        "permissions": ["READ"],
        "evidence_required": True,
    },
    {
        "task_id": "batch_evidence_03",
        "title": "Synthetic Fallback Test",
        "goal": "Discuss the future of AGI consciousness and ethical implications",
        "constraints": [],
        "inputs": {},
        "scope": "doc",
        "permissions": ["READ"],
        "evidence_required": True,
    },
    {
        "task_id": "batch_evidence_04",
        "title": "Knowledge-rich Test",
        "goal": "Describe Redis caching strategies for LLM applications",
        "constraints": [],
        "inputs": {},
        "scope": "doc",
        "permissions": ["READ"],
        "evidence_required": True,
    },
    {
        "task_id": "batch_evidence_05",
        "title": "Domain-specific Test",
        "goal": "List key metrics for monitoring machine learning pipelines",
        "constraints": [],
        "inputs": {},
        "scope": "analysis",
        "permissions": ["READ"],
        "evidence_required": True,
    },
    {
        "task_id": "batch_evidence_06",
        "title": "Code Context Test",
        "goal": "Show examples of Pydantic model validation patterns",
        "constraints": [],
        "inputs": {},
        "scope": "code",
        "permissions": ["READ"],
        "evidence_required": True,
    },
    {
        "task_id": "batch_evidence_07",
        "title": "Multi-hop Reasoning",
        "goal": "Compare local LLM vs cloud AI for cost and latency tradeoffs",
        "constraints": [],
        "inputs": {},
        "scope": "analysis",
        "permissions": ["READ"],
        "evidence_required": True,
    },
    {
        "task_id": "batch_evidence_08",
        "title": "Narrow Domain",
        "goal": "Explain PowerShell parameter validation in automation scripts",
        "constraints": [],
        "inputs": {},
        "scope": "doc",
        "permissions": ["READ"],
        "evidence_required": True,
    },
    {
        "task_id": "batch_evidence_09",
        "title": "Broad Query",
        "goal": "Summarize strategies for improving AGI success rates",
        "constraints": [],
        "inputs": {},
        "scope": "analysis",
        "permissions": ["READ"],
        "evidence_required": True,
    },
    {
        "task_id": "batch_evidence_10",
        "title": "Technical Depth",
        "goal": "Detail the evidence gate correction logic in self-correction pipelines",
        "constraints": [],
        "inputs": {},
        "scope": "doc",
        "permissions": ["READ"],
        "evidence_required": True,
    },
]

TOOL_CFG = {
    "rag": {"index_path": "memory/vectorstore", "top_k": 6},
    "fileio": {"sandbox_root": "sandbox/"},
}


def main() -> int:
    print(f"[Batch Evidence Test] Running {len(TEST_CASES)} tasks...")
    results: List[Dict[str, Any]] = []
    
    for idx, spec in enumerate(TEST_CASES, 1):
        print(f"\n[{idx}/{len(TEST_CASES)}] {spec['task_id']}: {spec['title']}")
        try:
            result = run_task(TOOL_CFG, spec)
            citations_count = len(result.get("citations", []))
            summary_len = len(result.get("summary", ""))
            print(f"  ✓ Completed: {citations_count} citations, summary {summary_len} chars")
            results.append({
                "task_id": spec["task_id"],
                "title": spec["title"],
                "success": True,
                "citations_count": citations_count,
                "summary_length": summary_len,
            })
        except Exception as e:
            print(f"  ✗ Failed: {type(e).__name__}: {e}")
            results.append({
                "task_id": spec["task_id"],
                "title": spec["title"],
                "success": False,
                "error": f"{type(e).__name__}: {e}",
            })
    
    # Summary
    success_count = sum(1 for r in results if r.get("success"))
    success_rate = (success_count / len(results)) * 100 if results else 0
    
    print(f"\n{'='*60}")
    print(f"[Batch Test Summary]")
    print(f"  Total Tasks: {len(results)}")
    print(f"  Successes:   {success_count}")
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"{'='*60}")
    
    # Save results
    output_path = REPO / "outputs" / "batch_evidence_test_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump({
            "total": len(results),
            "success_count": success_count,
            "success_rate_percent": success_rate,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"Results saved: {output_path}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
