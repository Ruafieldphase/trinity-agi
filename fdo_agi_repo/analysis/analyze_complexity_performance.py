#!/usr/bin/env python3
"""
Complexity-Based Performance Analysis

Analyzes AGI task performance by complexity category to identify 
the gap between batch validation (100%) and real AGI (67.7%).

Extracts from:
- batch_validation_*.json files (per_category metrics)
- resonance_ledger.jsonl (real task execution)

Output:
- Complexity distribution analysis
- Success rate by category
- Quality score by category
- Replan rate by category
- Recommendations for complex task optimization
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Tuple
from datetime import datetime
import glob

# Add parent to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))


def load_batch_validations(outputs_dir: Path) -> List[Dict[str, Any]]:
    """Load all batch validation JSON files"""
    pattern = str(outputs_dir / "batch_validation_*.json")
    files = sorted(glob.glob(pattern), key=lambda x: Path(x).stat().st_mtime, reverse=True)
    
    results = []
    for fpath in files[:10]:  # Last 10 runs
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                results.append(json.load(f))
        except Exception as e:
            print(f"⚠️ Failed to load {fpath}: {e}")
    
    return results


def analyze_batch_performance(batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze batch validation performance by category"""
    category_stats = defaultdict(lambda: {
        'total_tasks': 0,
        'successful_tasks': 0,
        'total_quality': 0.0,
        'total_citations': 0,
        'runs': 0
    })
    
    overall_success = []
    overall_quality = []
    
    for batch in batch_results:
        # Overall metrics
        summary = batch.get('summary', {})
        overall_success.append(summary.get('success_rate_percent', 0))
        overall_quality.append(summary.get('avg_quality_score', 0))
        
        # Per-category metrics
        per_category = batch.get('per_category', {})
        for cat_name, cat_data in per_category.items():
            stats = category_stats[cat_name]
            stats['total_tasks'] += cat_data.get('total', 0)
            stats['successful_tasks'] += cat_data.get('successful', 0)
            stats['total_quality'] += cat_data.get('avg_quality_score', 0) * cat_data.get('total', 0)
            stats['total_citations'] += cat_data.get('avg_citations', 0) * cat_data.get('total', 0)
            stats['runs'] += 1
    
    # Calculate averages
    category_analysis = {}
    for cat_name, stats in category_stats.items():
        if stats['total_tasks'] > 0:
            category_analysis[cat_name] = {
                'total_tasks': stats['total_tasks'],
                'successful_tasks': stats['successful_tasks'],
                'success_rate_percent': (stats['successful_tasks'] / stats['total_tasks'] * 100),
                'avg_quality': stats['total_quality'] / stats['total_tasks'],
                'avg_citations': stats['total_citations'] / stats['total_tasks'],
                'runs_count': stats['runs']
            }
    
    return {
        'category_breakdown': category_analysis,
        'overall_success_rate': sum(overall_success) / len(overall_success) if overall_success else 0,
        'overall_quality': sum(overall_quality) / len(overall_quality) if overall_quality else 0,
        'batch_count': len(batch_results)
    }


def load_ledger_events(ledger_path: Path) -> List[Dict[str, Any]]:
    """Load events from resonance_ledger.jsonl"""
    events = []
    if not ledger_path.exists():
        return events
    
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def infer_task_complexity(task_goal: str, task_context: Dict) -> str:
    """
    Infer complexity category from task goal and context.
    This is heuristic-based since real AGI tasks don't have explicit categories.
    """
    goal_lower = task_goal.lower()
    
    # Multi-hop reasoning indicators
    if any(kw in goal_lower for kw in ['why', 'how does', 'what happens when', 'relationship', 'impact', 'affect']):
        if any(kw in goal_lower for kw in ['system', 'integration', 'improve', 'design', 'fallback', 'chain']):
            return 'multi_hop_reasoning'
    
    # Code-heavy indicators
    if any(kw in goal_lower for kw in ['implementation', 'function', 'locate', 'find', 'show', 'class', 'module']):
        if any(kw in goal_lower for kw in ['code', 'algorithm', 'logic', 'mechanism', '.py', 'import']):
            return 'code_heavy'
    
    # Documentation indicators
    if any(kw in goal_lower for kw in ['guidelines', 'documentation', 'instructions', 'guide', 'find', 'locate']):
        if any(kw in goal_lower for kw in ['docs', 'documentation', 'guide', 'manual', 'readme', 'architecture']):
            return 'documentation'
    
    # Default to standard
    return 'standard'


def analyze_real_agi_performance(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze real AGI task performance from ledger events"""
    # Build task_id -> result mapping
    # Note: resonance_ledger.jsonl doesn't have task_start with goal,
    # so we use thesis_start events or infer from task_id patterns
    task_info = {}
    task_evals = {}
    task_runes = {}
    
    for event in events:
        event_type = event.get('event')
        task_id = event.get('task_id')
        
        if not task_id:
            continue
        
        # Track all task_ids
        if task_id not in task_info:
            # Infer complexity from task_id pattern (batch validation tasks have specific IDs)
            complexity = 'unknown'
            if 'batch_val' in str(task_id):
                complexity = 'standard'  # Batch validation tasks
            elif 'integration_test' in str(task_id) or 'low_confidence_test' in str(task_id):
                complexity = 'test'  # Test tasks
            else:
                complexity = 'real'  # Real AGI tasks
            
            task_info[task_id] = {
                'complexity': complexity,
                'first_seen': event.get('ts', 0)
            }
        
        if event_type == 'eval':
            task_evals[task_id] = event.get('eval', {})
        
        elif event_type == 'rune':
            task_runes[task_id] = event.get('rune', {})
    
    # Aggregate by complexity
    complexity_stats = defaultdict(lambda: {
        'task_count': 0,
        'success_count': 0,
        'replan_count': 0,
        'quality_sum': 0.0,
        'evidence_ok_count': 0
    })
    
    for task_id, info in task_info.items():
        complexity = info['complexity']
        stats = complexity_stats[complexity]
        stats['task_count'] += 1
        
        # Eval data
        eval_data = task_evals.get(task_id, {})
        quality = eval_data.get('quality', 0.0)
        evidence_ok = eval_data.get('evidence_ok', False)
        
        stats['quality_sum'] += quality
        if evidence_ok:
            stats['evidence_ok_count'] += 1
        
        # RUNE data
        rune_data = task_runes.get(task_id, {})
        replan = rune_data.get('replan', False)
        if replan:
            stats['replan_count'] += 1
        
        # Success = quality >= 0.6 and not replan
        if quality >= 0.6 and not replan:
            stats['success_count'] += 1
    
    # Calculate percentages
    complexity_analysis = {}
    for complexity, stats in complexity_stats.items():
        if stats['task_count'] > 0:
            complexity_analysis[complexity] = {
                'task_count': stats['task_count'],
                'success_count': stats['success_count'],
                'success_rate_percent': (stats['success_count'] / stats['task_count'] * 100),
                'replan_rate_percent': (stats['replan_count'] / stats['task_count'] * 100),
                'avg_quality': stats['quality_sum'] / stats['task_count'],
                'evidence_ok_rate_percent': (stats['evidence_ok_count'] / stats['task_count'] * 100)
            }
    
    # Overall stats
    total_tasks = sum(s['task_count'] for s in complexity_stats.values())
    total_success = sum(s['success_count'] for s in complexity_stats.values())
    total_quality = sum(s['quality_sum'] for s in complexity_stats.values())
    
    return {
        'complexity_breakdown': complexity_analysis,
        'overall_success_rate': (total_success / total_tasks * 100) if total_tasks > 0 else 0,
        'overall_quality': (total_quality / total_tasks) if total_tasks > 0 else 0,
        'total_tasks': total_tasks
    }


def compare_batch_vs_real(batch_analysis: Dict, real_analysis: Dict) -> Dict[str, Any]:
    """Compare batch validation vs real AGI performance"""
    comparisons = {}
    
    batch_cats = batch_analysis.get('category_breakdown', {})
    real_cats = real_analysis.get('complexity_breakdown', {})
    
    # Per-category comparison
    all_categories = set(list(batch_cats.keys()) + list(real_cats.keys()))
    
    for cat in all_categories:
        batch_data = batch_cats.get(cat, {})
        real_data = real_cats.get(cat, {})
        
        batch_success = batch_data.get('success_rate_percent', 0)
        real_success = real_data.get('success_rate_percent', 0)
        
        batch_quality = batch_data.get('avg_quality', 0)
        real_quality = real_data.get('avg_quality', 0)
        
        comparisons[cat] = {
            'batch_success_rate': batch_success,
            'real_success_rate': real_success,
            'success_gap': batch_success - real_success,
            'batch_quality': batch_quality,
            'real_quality': real_quality,
            'quality_gap': batch_quality - real_quality,
            'batch_task_count': batch_data.get('total_tasks', 0),
            'real_task_count': real_data.get('task_count', 0)
        }
    
    # Overall comparison
    batch_overall_success = batch_analysis.get('overall_success_rate', 0)
    real_overall_success = real_analysis.get('overall_success_rate', 0)
    
    return {
        'per_category': comparisons,
        'overall': {
            'batch_success_rate': batch_overall_success,
            'real_success_rate': real_overall_success,
            'success_gap': batch_overall_success - real_overall_success,
            'batch_quality': batch_analysis.get('overall_quality', 0),
            'real_quality': real_analysis.get('overall_quality', 0)
        }
    }


def generate_recommendations(comparison: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on analysis"""
    recs = []
    
    per_category = comparison.get('per_category', {})
    overall = comparison.get('overall', {})
    
    # Overall gap analysis
    success_gap = overall.get('success_gap', 0)
    if success_gap > 10:
        recs.append(f"🚨 Large Success Gap: Batch {overall['batch_success_rate']:.1f}% vs Real {overall['real_success_rate']:.1f}% "
                   f"({success_gap:.1f}%p gap). Batch tasks may not represent real workload complexity.")
    
    # Per-category analysis
    problem_categories = []
    for cat, data in per_category.items():
        if data['success_gap'] > 15:
            problem_categories.append((cat, data['success_gap'], data['real_success_rate']))
    
    if problem_categories:
        problem_categories.sort(key=lambda x: x[1], reverse=True)
        top_problem = problem_categories[0]
        recs.append(f"🎯 Worst Category: '{top_problem[0]}' with {top_problem[1]:.1f}%p gap "
                   f"(real success only {top_problem[2]:.1f}%). Focus optimization here.")
    
    # Category-specific recommendations
    for cat, data in per_category.items():
        real_success = data['real_success_rate']
        
        if 'multi_hop' in cat.lower() and real_success < 50:
            recs.append(f"🧠 Multi-hop Reasoning Weak: {real_success:.1f}% success. "
                       f"Consider multi-turn dialogue or chain-of-thought prompting.")
        
        if 'code' in cat.lower() and real_success < 60:
            recs.append(f"💻 Code Task Struggles: {real_success:.1f}% success. "
                       f"Improve code-aware chunking or AST-based retrieval.")
        
        if 'documentation' in cat.lower() and real_success < 70:
            recs.append(f"📚 Documentation Gaps: {real_success:.1f}% success. "
                       f"Verify markdown/docs properly indexed in vector store.")
    
    # Quality gap analysis
    quality_gap = overall.get('batch_quality', 0) - overall.get('real_quality', 0)
    if quality_gap > 0.15:
        recs.append(f"📉 Quality Degradation: Batch {overall['batch_quality']:.2f} vs Real {overall['real_quality']:.2f} "
                   f"({quality_gap:.2f} gap). Real tasks produce lower quality outputs.")
    
    return recs


def print_report(batch_analysis: Dict, real_analysis: Dict, comparison: Dict, recommendations: List[str]) -> None:
    """Print formatted analysis report"""
    print("\n" + "="*80)
    print("COMPLEXITY-BASED PERFORMANCE ANALYSIS")
    print("="*80)
    
    print(f"\n📊 BATCH VALIDATION PERFORMANCE")
    print(f"   Overall Success Rate: {batch_analysis['overall_success_rate']:.1f}%")
    print(f"   Overall Quality: {batch_analysis['overall_quality']:.2f}")
    print(f"   Batches Analyzed: {batch_analysis['batch_count']}")
    
    print(f"\n   Per-Category Breakdown:")
    for cat, data in batch_analysis.get('category_breakdown', {}).items():
        print(f"      {cat:25s} Success: {data['success_rate_percent']:5.1f}%, "
              f"Quality: {data['avg_quality']:.2f}, Tasks: {data['total_tasks']}")
    
    print(f"\n🤖 REAL AGI PERFORMANCE")
    print(f"   Overall Success Rate: {real_analysis['overall_success_rate']:.1f}%")
    print(f"   Overall Quality: {real_analysis['overall_quality']:.2f}")
    print(f"   Total Tasks: {real_analysis['total_tasks']}")
    
    print(f"\n   Per-Complexity Breakdown:")
    for cat, data in real_analysis.get('complexity_breakdown', {}).items():
        print(f"      {cat:25s} Success: {data['success_rate_percent']:5.1f}%, "
              f"Replan: {data['replan_rate_percent']:5.1f}%, Quality: {data['avg_quality']:.2f}, Tasks: {data['task_count']}")
    
    print(f"\n🔍 BATCH vs REAL COMPARISON")
    print(f"   Overall Success Gap: {comparison['overall']['success_gap']:+.1f}%p "
          f"({comparison['overall']['batch_success_rate']:.1f}% → {comparison['overall']['real_success_rate']:.1f}%)")
    print(f"   Overall Quality Gap: {comparison['overall']['batch_quality'] - comparison['overall']['real_quality']:+.2f} "
          f"({comparison['overall']['batch_quality']:.2f} → {comparison['overall']['real_quality']:.2f})")
    
    print(f"\n   Per-Category Gaps:")
    for cat, data in comparison.get('per_category', {}).items():
        gap_indicator = "✅" if abs(data['success_gap']) < 10 else "⚠️" if abs(data['success_gap']) < 20 else "🚨"
        print(f"      {gap_indicator} {cat:25s} Success Gap: {data['success_gap']:+6.1f}%p, "
              f"Quality Gap: {data['quality_gap']:+.2f}")
    
    print(f"\n💡 RECOMMENDATIONS")
    for i, rec in enumerate(recommendations, 1):
        print(f"   [{i}] {rec}")
    
    print("\n" + "="*80)


def save_json_report(batch_analysis: Dict, real_analysis: Dict, comparison: Dict, 
                     recommendations: List[str], output_path: Path) -> None:
    """Save analysis as JSON"""
    report = {
        'batch_analysis': batch_analysis,
        'real_agi_analysis': real_analysis,
        'comparison': comparison,
        'recommendations': recommendations,
        'generated_at': datetime.now().isoformat()
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n✅ JSON report saved: {output_path}")


def main():
    outputs_dir = repo_root.parent / "outputs"
    ledger_path = repo_root / "memory" / "resonance_ledger.jsonl"
    output_path = outputs_dir / "complexity_analysis_latest.json"
    
    print("Loading batch validation results...")
    batch_results = load_batch_validations(outputs_dir)
    if not batch_results:
        print("❌ No batch validation results found")
        sys.exit(1)
    print(f"Loaded {len(batch_results)} batch validation files")
    
    print("\nAnalyzing batch validation performance...")
    batch_analysis = analyze_batch_performance(batch_results)
    
    print("Loading resonance ledger events...")
    if not ledger_path.exists():
        print(f"❌ Ledger not found: {ledger_path}")
        sys.exit(1)
    events = load_ledger_events(ledger_path)
    print(f"Loaded {len(events)} events")
    
    print("Analyzing real AGI performance...")
    real_analysis = analyze_real_agi_performance(events)
    
    print("Comparing batch vs real performance...")
    comparison = compare_batch_vs_real(batch_analysis, real_analysis)
    
    print("Generating recommendations...")
    recommendations = generate_recommendations(comparison)
    
    # Print report
    print_report(batch_analysis, real_analysis, comparison, recommendations)
    
    # Save JSON
    save_json_report(batch_analysis, real_analysis, comparison, recommendations, output_path)
    
    print("\n✅ Analysis complete")


if __name__ == '__main__':
    main()
