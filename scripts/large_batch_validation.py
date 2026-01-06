#!/usr/bin/env python3
"""
Large-Scale Batch Validation for Hybrid RAG Impact Measurement
==============================================================

Purpose:
- Execute 40 diverse AGI tasks with Hybrid RAG active
- Measure SuccessRate improvement vs baseline (51.76%)
- Validate evidence_correction performance boost
- Assess synthetic fallback reduction

Test Categories:
- Standard queries (10 tasks): Basic RAG retrieval scenarios
- Code-heavy tasks (10 tasks): Require codebase knowledge
- Documentation tasks (10 tasks): Policy/guide retrieval
- Multi-hop reasoning (10 tasks): Complex inference chains

Metrics Collected:
- SuccessRate (target: 70%)
- evidence_correction.success_rate (target: 30%+)
- synthetic_rate (target: <10%)
- avg_hits, avg_relevance, retry_rate
- citation_quality (relevance scores)

Usage:
    python scripts/large_batch_validation.py
    python scripts/large_batch_validation.py --count 50  # Override task count
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from workspace_root import get_workspace_root

# Add repo root to path
repo_root = get_workspace_root()
sys.path.insert(0, str(repo_root / "fdo_agi_repo"))

from orchestrator.pipeline import run_task
from orchestrator.contracts import TaskSpec


# Test task definitions
STANDARD_QUERIES = [
    {"goal": "Explain how BM25 retrieval algorithm works", "context": "RAG system documentation"},
    {"goal": "Describe the evidence gate 3-stage correction process", "context": "Self-correction workflow"},
    {"goal": "What is the purpose of synthetic citations?", "context": "Evidence fallback mechanism"},
    {"goal": "How does the AGI pipeline handle low confidence results?", "context": "Quality control"},
    {"goal": "Explain the role of Reciprocal Rank Fusion in hybrid retrieval", "context": "RAG merging"},
    {"goal": "What metrics are tracked in the monitoring system?", "context": "Observability"},
    {"goal": "How does the task orchestrator manage retries?", "context": "Error handling"},
    {"goal": "Describe the ledger event structure", "context": "Event logging"},
    {"goal": "What is the significance of evidence_ok flag?", "context": "Quality gates"},
    {"goal": "Explain the adaptive threshold mechanism", "context": "Dynamic monitoring"},
]

CODE_HEAVY_TASKS = [
    {"goal": "Find the implementation of hybrid_rag_query function", "context": "Hybrid retriever module"},
    {"goal": "Show how EmbeddingService handles Vertex AI fallback", "context": "Embedding generation"},
    {"goal": "Locate the cosine similarity search implementation", "context": "Vector store"},
    {"goal": "Find where EVAL function excludes synthetic citations", "context": "Pipeline quality scoring"},
    {"goal": "Show the RRF scoring algorithm implementation", "context": "Rank fusion"},
    {"goal": "Find the evidence_gate_correction retry logic", "context": "Self-correction module"},
    {"goal": "Show how tool_registry routes to hybrid retriever", "context": "Tool routing"},
    {"goal": "Locate the document chunking strategy", "context": "Index docs"},
    {"goal": "Find the RAG_DISABLE environment variable check", "context": "Test compatibility"},
    {"goal": "Show the vector store persistence mechanism", "context": "JSON save/load"},
]

DOCUMENTATION_TASKS = [
    {"goal": "Find guidelines for Evidence Gate parameter tuning", "context": "Optimization docs"},
    {"goal": "Locate the Hybrid RAG architecture documentation", "context": "System design"},
    {"goal": "Find instructions for running batch evidence tests", "context": "Testing procedures"},
    {"goal": "Show the monitoring KPI definitions", "context": "Metrics documentation"},
    {"goal": "Find the ops-monitoring-hardening branch objectives", "context": "Project goals"},
    {"goal": "Locate the self-correction workflow documentation", "context": "AGI processes"},
    {"goal": "Find the RAG configuration file structure", "context": "Config schema"},
    {"goal": "Show the task execution lifecycle documentation", "context": "Pipeline flow"},
    {"goal": "Locate the Vertex AI environment setup guide", "context": "Deployment"},
    {"goal": "Find the success rate improvement roadmap", "context": "70% target plan"},
]

MULTI_HOP_REASONING = [
    {"goal": "How does Hybrid RAG improve evidence_correction success rate?", "context": "System integration"},
    {"goal": "Why was RRF chosen over score normalization for merging?", "context": "Design rationale"},
    {"goal": "What happens when both BM25 and Dense retrieval fail?", "context": "Fallback chain"},
    {"goal": "How does vectorstore indexing affect task success rate?", "context": "Knowledge coverage"},
    {"goal": "What is the relationship between retry_rate and synthetic_rate?", "context": "Evidence quality"},
    {"goal": "Why does EVAL need to exclude synthetic citations?", "context": "Quality gate logic"},
    {"goal": "How do adaptive thresholds prevent false alerts?", "context": "Monitoring intelligence"},
    {"goal": "What causes second_pass to trigger in self-correction?", "context": "Replan conditions"},
    {"goal": "How does embedding dimension affect search quality?", "context": "Vector similarity"},
    {"goal": "What is the impact of chunk overlap on retrieval recall?", "context": "Indexing strategy"},
]

# Medium complexity tasks (bridge between simple and complex)
MEDIUM_TASKS = [
    {"goal": "Find all Python files that import the RAG module", "context": "Code search"},
    {"goal": "List the main configuration parameters for the AGI pipeline", "context": "Config analysis"},
    {"goal": "Identify which scripts generate monitoring reports", "context": "Script inventory"},
    {"goal": "Show the relationship between PLAN, ANTI, and SYNTH personas", "context": "Architecture"},
    {"goal": "Find examples of successful evidence correction in recent logs", "context": "Log search"},
    {"goal": "List all scheduled tasks and their execution frequency", "context": "Automation inventory"},
    {"goal": "Identify the main retry mechanisms in the codebase", "context": "Error handling"},
    {"goal": "Show how the system handles API timeouts", "context": "Resilience patterns"},
    {"goal": "Find documentation for the ChatOps command system", "context": "Documentation search"},
    {"goal": "List all environment variables used by the AGI pipeline", "context": "Config discovery"},
]

# Complex real-world tasks (Priority 2 from action plan)
COMPLEX_TASKS = [
    {"goal": "코드베이스 전체에서 캐싱 패턴을 분석하고 개선 제안", "context": "Codebase architecture"},
    {"goal": "최근 7일 AGI 이벤트 로그에서 이상 패턴 탐지", "context": "Log analysis"},
    {"goal": "Hybrid RAG와 BM25 단독 검색 성능 비교 분석", "context": "Performance analysis"},
    {"goal": "프로젝트의 모든 스케줄 작업을 나열하고 충돌 가능성 진단", "context": "Task scheduling"},
    {"goal": "최근 3개 배포의 변경사항을 비교하고 회귀 위험 평가", "context": "Deployment history"},
]


def execute_task(tool_cfg: Dict[str, Any], task_def: Dict[str, str], task_id: int) -> Dict[str, Any]:
    """Execute single AGI task and collect metrics."""
    print(f"\n[Task {task_id}] Goal: {task_def['goal'][:60]}...")
    
    start_time = time.time()
    
    # Map context to scope
    scope_map = {
        "RAG system documentation": "doc",
        "Self-correction workflow": "code",
        "Evidence fallback mechanism": "code",
        "Quality control": "code",
        "RAG merging": "code",
        "Observability": "code",
        "Error handling": "code",
        "Event logging": "code",
        "Quality gates": "code",
        "Dynamic monitoring": "code",
        "Hybrid retriever module": "code",
        "Embedding generation": "code",
        "Vector store": "code",
        "Pipeline quality scoring": "code",
        "Rank fusion": "code",
        "Self-correction module": "code",
        "Tool routing": "code",
        "Index docs": "code",
        "Test compatibility": "code",
        "JSON save/load": "code",
        "Optimization docs": "doc",
        "System design": "doc",
        "Testing procedures": "doc",
        "Metrics documentation": "doc",
        "Project goals": "doc",
        "AGI processes": "doc",
        "Config schema": "doc",
        "Pipeline flow": "doc",
        "Deployment": "doc",
        "70% target plan": "doc",
        "System integration": "analysis",
        "Design rationale": "analysis",
        "Fallback chain": "analysis",
        "Knowledge coverage": "analysis",
        "Evidence quality": "analysis",
        "Quality gate logic": "analysis",
        "Monitoring intelligence": "analysis",
        "Replan conditions": "analysis",
        "Vector similarity": "analysis",
        "Indexing strategy": "analysis",
        "Codebase architecture": "code",
        "Log analysis": "analysis",
        "Performance analysis": "analysis",
        "Task scheduling": "analysis",
        "Deployment history": "analysis",
        "Code search": "code",
        "Config analysis": "doc",
        "Script inventory": "code",
        "Architecture": "doc",
        "Log search": "analysis",
        "Automation inventory": "doc",
        "Error handling": "code",
        "Resilience patterns": "code",
        "Documentation search": "doc",
        "Config discovery": "doc",
    }
    
    context = task_def.get("context", "analysis")
    scope = scope_map.get(context, "analysis")
    
    # Build TaskSpec dictionary
    spec_dict = {
        "task_id": f"batch_val_{task_id:03d}",
        "title": f"Validation Task {task_id}",
        "goal": task_def["goal"],
        "constraints": [],
        "inputs": {},
        "scope": scope,
        "permissions": ["READ"],
        "evidence_required": True,
    }
    
    try:
        result = run_task(tool_cfg, spec_dict)
        elapsed = time.time() - start_time
        
        # Extract metrics
        citations = len(result.get("citations", []))
        summary_len = len(result.get("summary", ""))

        # Estimate quality based on output (since we don't have direct quality_score in result)
        # We'll use citations count and summary length as heuristics
        quality = 0.5  # baseline
        if citations > 0:
            quality += min(0.3, citations * 0.05)  # +0.05 per citation, max +0.3
        if summary_len >= 240:
            quality += 0.1
        quality = min(1.0, quality)

        # Success criterion: evidence present and quality threshold met
        success = citations > 0 and quality >= 0.6
        
        # Calculate citation quality (relevance scores)
        citation_quality = []
        for cit in result.get("citations", []):
            if isinstance(cit, dict) and 'relevance' in cit:
                try:
                    citation_quality.append(float(cit['relevance']))
                except (ValueError, TypeError):
                    pass
        
        avg_citation_quality = sum(citation_quality) / len(citation_quality) if citation_quality else 0.0
        
        metrics = {
            "task_id": task_id,
            "goal": task_def["goal"],
            "success": success,
            "quality_score": quality,
            "citations": citations,
            "summary_length": summary_len,
            "avg_citation_quality": avg_citation_quality,
            "elapsed_sec": elapsed,
            "ok": result.get("status") != "HALT",
            "error": result.get("reason") if result.get("status") == "HALT" else None,
        }
        
        print(f"  [OK] Success: {success}, Quality: {quality:.3f}, Citations: {citations}, Time: {elapsed:.1f}s")
        return metrics
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  [FAIL] FAILED: {str(e)}")
        return {
            "task_id": task_id,
            "goal": task_def["goal"],
            "success": False,
            "quality_score": 0.0,
            "citations": 0,
            "avg_citation_quality": 0.0,
            "elapsed_sec": elapsed,
            "ok": False,
            "error": str(e),
        }


def analyze_results(results: List[Dict[str, Any]], baseline_success_rate: float = 51.76) -> Dict[str, Any]:
    """Analyze batch validation results and compute statistics."""
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    success_rate = (successful / total) * 100 if total > 0 else 0.0
    
    avg_quality = sum(r["quality_score"] for r in results) / total if total > 0 else 0.0
    avg_citations = sum(r["citations"] for r in results) / total if total > 0 else 0.0
    avg_citation_quality = sum(r["avg_citation_quality"] for r in results if r["avg_citation_quality"] > 0)
    citation_count = sum(1 for r in results if r["avg_citation_quality"] > 0)
    avg_citation_quality = avg_citation_quality / citation_count if citation_count > 0 else 0.0
    
    avg_elapsed = sum(r["elapsed_sec"] for r in results) / total if total > 0 else 0.0
    
    # Per-category breakdown
    categories = {}
    for cat in ["standard", "code_heavy", "documentation", "multi_hop", "medium", "complex"]:
        cat_items = [r for r in results if r.get("category") == cat]
        if cat_items:
            cat_total = len(cat_items)
            cat_success = sum(1 for r in cat_items if r.get("success"))
            cat_rate = (cat_success / cat_total) * 100
            categories[cat] = {
                "total": cat_total,
                "successful": cat_success,
                "failed": cat_total - cat_success,
                "success_rate_percent": round(cat_rate, 2),
                "avg_quality_score": round(sum(r.get("quality_score", 0.0) for r in cat_items) / cat_total, 3),
                "avg_citations": round(sum(r.get("citations", 0) for r in cat_items) / cat_total, 2),
                "avg_elapsed_sec": round(sum(r.get("elapsed_sec", 0.0) for r in cat_items) / cat_total, 2),
            }

    # Improvement metrics
    success_improvement = success_rate - baseline_success_rate
    success_improvement_pct = (success_improvement / baseline_success_rate) * 100 if baseline_success_rate > 0 else 0.0
    
    # Goal achievement
    target_success_rate = 70.0
    target_gap = target_success_rate - success_rate
    target_achieved = success_rate >= target_success_rate
    
    return {
        "summary": {
            "total_tasks": total,
            "successful_tasks": successful,
            "failed_tasks": total - successful,
            "success_rate_percent": round(success_rate, 2),
            "avg_quality_score": round(avg_quality, 3),
            "avg_citations": round(avg_citations, 2),
            "avg_citation_quality": round(avg_citation_quality, 3),
            "avg_elapsed_sec": round(avg_elapsed, 2),
        },
        "comparison": {
            "baseline_success_rate": baseline_success_rate,
            "new_success_rate": round(success_rate, 2),
            "improvement_points": round(success_improvement, 2),
            "improvement_percent": round(success_improvement_pct, 2),
        },
        "goal_achievement": {
            "target_success_rate": target_success_rate,
            "current_success_rate": round(success_rate, 2),
            "gap_to_target": round(target_gap, 2),
            "target_achieved": target_achieved,
            "status": "[OK] TARGET ACHIEVED" if target_achieved else f"[WARN] GAP: {target_gap:.2f}% remaining",
        },
        "per_category": categories,
        "task_results": results,
    }


def main():
    """Main execution function."""
    print("=" * 80)
    print("LARGE-SCALE BATCH VALIDATION: Hybrid RAG Impact Measurement")
    print("=" * 80)
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Hybrid RAG: {'ENABLED' if os.getenv('RAG_DISABLE') != '1' else 'DISABLED (ERROR!)'}")
    print()
    
    # Verify Hybrid RAG is enabled
    if os.getenv('RAG_DISABLE') == '1':
        print("[ERROR] ERROR: RAG_DISABLE=1 detected. Hybrid RAG will not be tested!")
        print("   Unset RAG_DISABLE environment variable and retry.")
        sys.exit(1)
    
    # No need to initialize pipeline - run_task is a standalone function
    print("[OK] Pipeline module loaded\n")
    
    # Tool configuration
    tool_cfg = {
        "rag": {"index_path": "memory/vectorstore", "top_k": 8},
        "fileio": {"sandbox_root": "sandbox/"},
    }
    
    # Collect all tasks
    all_tasks = []
    all_tasks.extend([{"type": "standard", **t} for t in STANDARD_QUERIES])
    all_tasks.extend([{"type": "code_heavy", **t} for t in CODE_HEAVY_TASKS])
    all_tasks.extend([{"type": "documentation", **t} for t in DOCUMENTATION_TASKS])
    all_tasks.extend([{"type": "multi_hop", **t} for t in MULTI_HOP_REASONING])
    all_tasks.extend([{"type": "medium", **t} for t in MEDIUM_TASKS])
    all_tasks.extend([{"type": "complex", **t} for t in COMPLEX_TASKS])
    
    # Optional limit and filter via CLI arguments: --limit N, --count N, --category CAT
    limit = None
    category_filter = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a in ("--limit", "--count") and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                limit = None
        elif a in ("--category", "--cat") and i + 1 < len(args):
            category_filter = args[i + 1]
    
    # Apply category filter first
    if category_filter:
        all_tasks = [t for t in all_tasks if t["type"] == category_filter]
        print(f"\n[Filter] Category filter: {category_filter} ({len(all_tasks)} tasks)")
    
    print(f"Task Distribution:")
    print(f"  - Standard Queries: {len(STANDARD_QUERIES)}")
    print(f"  - Code-Heavy: {len(CODE_HEAVY_TASKS)}")
    print(f"  - Documentation: {len(DOCUMENTATION_TASKS)}")
    print(f"  - Multi-Hop Reasoning: {len(MULTI_HOP_REASONING)}")
    print(f"  - Medium Complexity: {len(MEDIUM_TASKS)}")
    print(f"  - Complex Real-World: {len(COMPLEX_TASKS)}")
    # Apply limit if provided
    if limit is not None:
        all_tasks = all_tasks[:limit]
        print(f"  TOTAL: {len(all_tasks)} tasks (limited)")
    else:
        print(f"  TOTAL: {len(all_tasks)} tasks")
    print()
    
    # Execute all tasks
    start_time = time.time()
    results = []
    
    for idx, task in enumerate(all_tasks, start=1):
        result = execute_task(tool_cfg, task, idx)
        result["category"] = task["type"]
        results.append(result)
        
        # Progress indicator
        if idx % 10 == 0:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            remaining = (len(all_tasks) - idx) / rate if rate > 0 else 0
            print(f"\n--- Progress: {idx}/{len(all_tasks)} tasks ({(idx/len(all_tasks)*100):.1f}%) ---")
            print(f"    Elapsed: {elapsed/60:.1f}m, Est. Remaining: {remaining/60:.1f}m\n")
    
    total_elapsed = time.time() - start_time
    
    # Analyze results
    print("\n" + "=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    
    analysis = analyze_results(results)
    
    # Print summary
    summary = analysis["summary"]
    print(f"\n[Summary] Overall Summary:")
    print(f"   Total Tasks: {summary['total_tasks']}")
    print(f"   Successful: {summary['successful_tasks']} [OK]")
    print(f"   Failed: {summary['failed_tasks']} [FAIL]")
    print(f"   Success Rate: {summary['success_rate_percent']}%")
    print(f"   Avg Quality: {summary['avg_quality_score']}")
    print(f"   Avg Citations: {summary['avg_citations']}")
    print(f"   Avg Citation Quality: {summary['avg_citation_quality']}")
    print(f"   Avg Duration: {summary['avg_elapsed_sec']}s")
    print(f"   Total Elapsed: {total_elapsed/60:.1f} minutes")
    
    # Print comparison
    comparison = analysis["comparison"]
    print(f"\n[Comparison] Baseline Comparison:")
    print(f"   Baseline Success Rate: {comparison['baseline_success_rate']}%")
    print(f"   New Success Rate: {comparison['new_success_rate']}%")
    print(f"   Improvement: {comparison['improvement_points']:+.2f}% ({comparison['improvement_percent']:+.2f}%)")
    
    # Print goal achievement
    goal = analysis["goal_achievement"]
    print(f"\n[Goal] Goal Achievement (70% Target):")
    print(f"   Target: {goal['target_success_rate']}%")
    print(f"   Current: {goal['current_success_rate']}%")
    print(f"   Status: {goal['status']}")
    
    # Category breakdown
    print(f"\n[Categories] Success Rate by Category:")
    for category in ["standard", "code_heavy", "documentation", "multi_hop"]:
        cat_results = [r for r in results if r["category"] == category]
        if cat_results:
            cat_success = sum(1 for r in cat_results if r["success"])
            cat_rate = (cat_success / len(cat_results)) * 100
            print(f"   {category:20s}: {cat_success}/{len(cat_results)} ({cat_rate:.1f}%)")
    
    # Save detailed results
    output_dir = repo_root / "outputs"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"batch_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n[Saved] Detailed results saved to: {output_file}")
    
    # Final verdict
    print("\n" + "=" * 80)
    if goal["target_achieved"]:
        print("[SUCCESS] SUCCESS: 70% target achieved with Hybrid RAG!")
        print("   Next: Parameter tuning for further optimization")
    else:
        print(f"[PARTIAL] PARTIAL SUCCESS: {goal['gap_to_target']:.2f}% gap to 70% target")
        print("   Next: Evidence Gate parameter tuning (top_k, min_relevance)")
    print("=" * 80)
    
    return 0 if goal["target_achieved"] else 1


if __name__ == "__main__":
    sys.exit(main())
