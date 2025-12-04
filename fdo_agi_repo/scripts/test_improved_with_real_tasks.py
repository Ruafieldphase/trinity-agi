#!/usr/bin/env python3
"""
Test improved PLAN prompt with new complex Real tasks
- Execute tasks with citations-enforced PLAN prompt
- Measure: replan rate, citations count, quality, evidence_ok
- Compare with 48.1% baseline

Usage:
    python test_improved_with_real_tasks.py --count 3
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add repo root to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "fdo_agi_repo"))

from orchestrator.pipeline import run_task
from orchestrator.contracts import TaskSpec

def create_complex_real_tasks():
    """Create 5 complex Real tasks to test improved prompt"""
    tasks = [
        {
            "task_id": "real_improved_001",
            "title": "Evidence Gate Analysis",
            "goal": "Explain the complete Evidence Gate 3-stage correction process (targeted → broaden → synthetic) with specific implementation details from the codebase",
            "constraints": [],
            "inputs": {},
            "scope": "analysis",
            "permissions": ["READ"],
            "evidence_required": True,
            "complexity": "high",
            "category": "real"
        },
        {
            "task_id": "real_improved_002",
            "title": "Hybrid RAG Architecture",
            "goal": "Analyze the Hybrid RAG architecture combining BM25 and Dense retrieval with RRF fusion, including when each method is preferred",
            "constraints": [],
            "inputs": {},
            "scope": "analysis",
            "permissions": ["READ"],
            "evidence_required": True,
            "complexity": "high",
            "category": "real"
        },
        {
            "task_id": "real_improved_003",
            "title": "Self-Correction System",
            "goal": "Describe the Self-correction system's two-pass architecture with learning from resonance_ledger.jsonl, including pass selection logic",
            "constraints": [],
            "inputs": {},
            "scope": "analysis",
            "permissions": ["READ"],
            "evidence_required": True,
            "complexity": "high",
            "category": "real"
        },
        {
            "task_id": "real_improved_004",
            "title": "Persona Responsibilities",
            "goal": "Compare the roles and responsibilities of PLAN, THESIS, ANTITHESIS, and SYNTHESIS personas in the dialectic reasoning process",
            "constraints": [],
            "inputs": {},
            "scope": "analysis",
            "permissions": ["READ"],
            "evidence_required": True,
            "complexity": "medium",
            "category": "real"
        },
        {
            "task_id": "real_improved_005",
            "title": "Meta-Cognition System",
            "goal": "Explain the meta-cognition system's confidence scoring, delegation logic, and how it decides between local LLM and cloud API",
            "constraints": [],
            "inputs": {},
            "scope": "analysis",
            "permissions": ["READ"],
            "evidence_required": True,
            "complexity": "medium",
            "category": "real"
        }
    ]
    return tasks

def execute_and_analyze(tool_cfg, tasks):
    """Execute tasks and analyze results"""
    print("=" * 80)
    print("IMPROVED PLAN PROMPT: Real Task Validation")
    print("=" * 80)
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Tasks: {len(tasks)}\n")
    
    results = []
    
    for idx, task in enumerate(tasks, 1):
        task_id = task['task_id']
        goal = task['goal']
        
        print(f"\n[Task {idx}/{len(tasks)}] {task_id}")
        print(f"Goal: {goal[:80]}...")
        print(f"Complexity: {task['complexity']}")
        
        try:
            # Execute task
            start_time = datetime.now()
            result = run_task(tool_cfg, task)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Extract metrics from result
            success = result.get('success', False)
            replan = result.get('replan', False)
            quality = result.get('quality', None)
            evidence_ok = result.get('evidence_ok', None)
            
            # Count citations from ledger
            ledger_path = Path(__file__).parent.parent / "resonance_ledger.jsonl"
            citations_thesis = None
            citations_synthesis = None
            
            if ledger_path.exists():
                with open(ledger_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        event = json.loads(line)
                        if event.get('task_id') == task_id:
                            if event.get('event') == 'thesis_end' and 'citations' in event:
                                citations_thesis = event['citations']
                            elif event.get('event') == 'synthesis_end' and 'citations' in event:
                                citations_synthesis = event['citations']
            
            task_result = {
                'task_id': task_id,
                'goal': goal,
                'complexity': task['complexity'],
                'success': success,
                'replan': replan,
                'quality': quality,
                'evidence_ok': evidence_ok,
                'citations_thesis': citations_thesis,
                'citations_synthesis': citations_synthesis,
                'duration': duration
            }
            
            results.append(task_result)
            
            print(f"  ✓ Completed in {duration:.1f}s")
            print(f"    Success: {success}, Replan: {replan}, Quality: {quality}")
            print(f"    Citations: Thesis={citations_thesis}, Synthesis={citations_synthesis}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results.append({
                'task_id': task_id,
                'goal': goal,
                'error': str(e)
            })
    
    return results

def analyze_results(results):
    """Analyze and report results"""
    print("\n" + "=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)
    
    # Filter valid results
    valid_results = [r for r in results if 'error' not in r]
    total = len(valid_results)
    
    if total == 0:
        print("No valid results to analyze")
        return
    
    # Calculate metrics
    replans = [r for r in valid_results if r.get('replan', False)]
    no_replans = [r for r in valid_results if not r.get('replan', False)]
    
    replan_count = len(replans)
    replan_rate = (replan_count / total * 100) if total > 0 else 0
    
    # Citations
    citations_thesis = [r['citations_thesis'] for r in valid_results if r.get('citations_thesis') is not None]
    citations_synthesis = [r['citations_synthesis'] for r in valid_results if r.get('citations_synthesis') is not None]
    
    avg_thesis_citations = sum(citations_thesis) / len(citations_thesis) if citations_thesis else 0
    avg_synthesis_citations = sum(citations_synthesis) / len(citations_synthesis) if citations_synthesis else 0
    
    # Quality
    qualities = [r['quality'] for r in valid_results if r.get('quality') is not None]
    avg_quality = sum(qualities) / len(qualities) if qualities else 0
    
    # Evidence OK
    evidence_ok_count = sum(1 for r in valid_results if r.get('evidence_ok', False))
    evidence_ok_rate = (evidence_ok_count / total * 100) if total > 0 else 0
    
    print(f"\n📊 Summary:")
    print(f"   Total Tasks: {total}")
    print(f"   Replans: {replan_count} ({replan_rate:.1f}%)")
    print(f"   No Replans: {len(no_replans)} ({100-replan_rate:.1f}%)")
    
    print(f"\n📋 Citations:")
    print(f"   Avg Thesis Citations: {avg_thesis_citations:.1f}")
    print(f"   Avg Synthesis Citations: {avg_synthesis_citations:.1f}")
    
    print(f"\n✅ Quality:")
    print(f"   Avg Quality: {avg_quality:.2f}")
    print(f"   Evidence OK Rate: {evidence_ok_rate:.1f}%")
    
    # Comparison with baseline
    print("\n" + "=" * 80)
    print("COMPARISON WITH BASELINE")
    print("=" * 80)
    baseline_replan = 48.1
    improvement = baseline_replan - replan_rate
    
    print(f"   Baseline Replan Rate (Real Tasks): {baseline_replan:.1f}%")
    print(f"   New Replan Rate: {replan_rate:.1f}%")
    print(f"   Improvement: {improvement:+.1f}%p")
    
    if replan_rate < 20:
        print(f"\n🎯 ✅ TARGET ACHIEVED: Replan rate below 20%!")
    else:
        print(f"\n⚠️ Target not met: Replan rate {replan_rate:.1f}% (target <20%)")
    
    # Detailed results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    for r in valid_results:
        print(f"\n{r['task_id']}:")
        print(f"  Goal: {r['goal'][:60]}...")
        print(f"  Complexity: {r['complexity']}")
        print(f"  Success: {r['success']}, Replan: {r['replan']}")
        print(f"  Quality: {r.get('quality', 'N/A')}")
        print(f"  Evidence OK: {r.get('evidence_ok', 'N/A')}")
        print(f"  Citations: Thesis={r.get('citations_thesis', 'N/A')}, Synthesis={r.get('citations_synthesis', 'N/A')}")
        print(f"  Duration: {r.get('duration', 0):.1f}s")

def main():
    """Main execution"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=3, help="Number of tasks to run (1-5)")
    args = parser.parse_args()

    # Tool configuration
    tool_cfg = {
        "rag": {"index_path": "memory/vectorstore", "top_k": 8},
        "fileio": {"sandbox_root": "sandbox/"},
    }

    # Create tasks and apply count limit
    tasks = create_complex_real_tasks()
    n = max(1, min(int(args.count), len(tasks)))
    tasks = tasks[:n]

    # Execute and analyze
    results = execute_and_analyze(tool_cfg, tasks)

    # Analyze results
    analyze_results(results)

    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)

if __name__ == "__main__":
    main()
