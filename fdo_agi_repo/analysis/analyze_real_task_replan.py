#!/usr/bin/env python3
"""
Real Task Replan Pattern Deep Dive
Real 태스크(46% 재계획률)의 상세 패턴 분석 - no_evidence가 왜 발생하는지 파악
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any

def load_ledger_events(ledger_path: Path) -> List[Dict[str, Any]]:
    """Load all events from resonance_ledger.jsonl"""
    events = []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events

def identify_real_tasks(events: List[Dict[str, Any]]) -> set:
    """Identify task_ids that are 'real' workload (not batch_val or integration_test)"""
    real_tasks = set()
    
    for event in events:
        task_id = event.get('task_id')
        if not task_id:
            continue
        
        # Filter: not batch validation or integration test
        if 'batch_val' not in task_id and 'integration_test' not in task_id and 'test_' not in task_id:
            real_tasks.add(task_id)
    
    return real_tasks

def analyze_real_task_evidence_flow(events: List[Dict[str, Any]], real_tasks: set) -> Dict:
    """
    Analyze evidence gate behavior for real tasks:
    1. How many citations were initially provided in PLAN?
    2. Did evidence gate trigger? What was added?
    3. Final RUNE state (replan=true/false)
    """
    
    task_flows = {}
    
    for event in events:
        task_id = event.get('task_id')
        if task_id not in real_tasks:
            continue
        
        event_type = event.get('event')
        
        if task_id not in task_flows:
            task_flows[task_id] = {
                'thesis_citations': 0,
                'evidence_gate_triggered': False,
                'evidence_gate_reason': None,
                'citations_added': 0,
                'final_quality': 0.0,
                'final_replan': None,
                'final_evidence_ok': False
            }
        
        flow = task_flows[task_id]
        
        # Thesis output (initial PLAN)
        if event_type == 'thesis_end':
            citations = event.get('citations', 0)
            flow['thesis_citations'] = citations
        
        # Evidence gate triggered
        elif event_type == 'evidence_gate_triggered':
            flow['evidence_gate_triggered'] = True
            flow['evidence_gate_reason'] = event.get('reason', 'unknown')
            flow['citations_added'] = event.get('added', 0)
        
        # Final EVAL
        elif event_type == 'eval':
            flow['final_quality'] = event.get('quality', 0.0)
            flow['final_evidence_ok'] = event.get('evidence_ok', False)
        
        # Final RUNE
        elif event_type == 'rune':
            rune_data = event.get('rune', {})
            flow['final_replan'] = rune_data.get('replan', None)
    
    return task_flows

def analyze_patterns(task_flows: Dict) -> Dict[str, Any]:
    """Extract patterns from real task flows"""
    
    replan_tasks = [tid for tid, flow in task_flows.items() if flow['final_replan'] is True]
    no_replan_tasks = [tid for tid, flow in task_flows.items() if flow['final_replan'] is False]
    
    # Replan group stats
    replan_stats = {
        'count': len(replan_tasks),
        'avg_thesis_citations': 0.0,
        'evidence_gate_trigger_rate': 0.0,
        'avg_citations_added': 0.0,
        'avg_final_quality': 0.0,
        'evidence_ok_rate': 0.0,
        'top_gate_reasons': Counter()
    }
    
    if replan_tasks:
        replan_stats['avg_thesis_citations'] = sum(task_flows[tid]['thesis_citations'] for tid in replan_tasks) / len(replan_tasks)
        replan_stats['evidence_gate_trigger_rate'] = sum(1 for tid in replan_tasks if task_flows[tid]['evidence_gate_triggered']) / len(replan_tasks) * 100
        
        triggered = [tid for tid in replan_tasks if task_flows[tid]['evidence_gate_triggered']]
        if triggered:
            replan_stats['avg_citations_added'] = sum(task_flows[tid]['citations_added'] for tid in triggered) / len(triggered)
        
        replan_stats['avg_final_quality'] = sum(task_flows[tid]['final_quality'] for tid in replan_tasks) / len(replan_tasks)
        replan_stats['evidence_ok_rate'] = sum(1 for tid in replan_tasks if task_flows[tid]['final_evidence_ok']) / len(replan_tasks) * 100
        
        for tid in replan_tasks:
            reason = task_flows[tid]['evidence_gate_reason']
            if reason:
                replan_stats['top_gate_reasons'][reason] += 1
    
    # No-replan group stats
    no_replan_stats = {
        'count': len(no_replan_tasks),
        'avg_thesis_citations': 0.0,
        'evidence_gate_trigger_rate': 0.0,
        'avg_citations_added': 0.0,
        'avg_final_quality': 0.0,
        'evidence_ok_rate': 0.0,
        'top_gate_reasons': Counter()
    }
    
    if no_replan_tasks:
        no_replan_stats['avg_thesis_citations'] = sum(task_flows[tid]['thesis_citations'] for tid in no_replan_tasks) / len(no_replan_tasks)
        no_replan_stats['evidence_gate_trigger_rate'] = sum(1 for tid in no_replan_tasks if task_flows[tid]['evidence_gate_triggered']) / len(no_replan_tasks) * 100
        
        triggered = [tid for tid in no_replan_tasks if task_flows[tid]['evidence_gate_triggered']]
        if triggered:
            no_replan_stats['avg_citations_added'] = sum(task_flows[tid]['citations_added'] for tid in triggered) / len(triggered)
        
        no_replan_stats['avg_final_quality'] = sum(task_flows[tid]['final_quality'] for tid in no_replan_tasks) / len(no_replan_tasks)
        no_replan_stats['evidence_ok_rate'] = sum(1 for tid in no_replan_tasks if task_flows[tid]['final_evidence_ok']) / len(no_replan_tasks) * 100
        
        for tid in no_replan_tasks:
            reason = task_flows[tid]['evidence_gate_reason']
            if reason:
                no_replan_stats['top_gate_reasons'][reason] += 1
    
    return {
        'replan': replan_stats,
        'no_replan': no_replan_stats,
        'total_real_tasks': len(task_flows),
        'replan_rate': len(replan_tasks) / len(task_flows) * 100 if task_flows else 0
    }

def generate_insights(patterns: Dict) -> List[str]:
    """Generate actionable insights from patterns"""
    insights = []
    
    replan = patterns['replan']
    no_replan = patterns['no_replan']
    
    # Insight 1: Initial citation gap
    cite_gap = no_replan['avg_thesis_citations'] - replan['avg_thesis_citations']
    if cite_gap > 1.0:
        insights.append(
            f"🎯 Citation Gap: No-replan tasks start with {cite_gap:.1f} more citations. "
            f"PLAN prompt should emphasize retrieving {int(no_replan['avg_thesis_citations'])}+ sources upfront."
        )
    
    # Insight 2: Evidence gate effectiveness
    gate_delta = no_replan['evidence_gate_trigger_rate'] - replan['evidence_gate_trigger_rate']
    if replan['evidence_gate_trigger_rate'] > 50:
        insights.append(
            f"⚠️  Evidence Gate triggers {replan['evidence_gate_trigger_rate']:.1f}% for replan tasks but still fails. "
            f"Added citations ({replan['avg_citations_added']:.1f} avg) may be low-quality or irrelevant."
        )
    
    # Insight 3: Quality threshold issue
    if replan['avg_final_quality'] < 0.6:
        insights.append(
            f"📉 Quality Below Threshold: Replan tasks avg {replan['avg_final_quality']:.2f}. "
            f"Evidence Gate should add higher-impact sources, not just more sources."
        )
    
    # Insight 4: Evidence OK rate discrepancy
    evidence_gap = no_replan['evidence_ok_rate'] - replan['evidence_ok_rate']
    if evidence_gap > 30:
        insights.append(
            f"🔍 Evidence OK Gap: {evidence_gap:.1f}%p difference. "
            f"Replan tasks have citations but they're not being validated as 'evidence_ok'. "
            f"Check EVAL persona's evidence validation logic."
        )
    
    # Insight 5: Top failure reasons
    if replan['top_gate_reasons']:
        top_reason = replan['top_gate_reasons'].most_common(1)[0]
        insights.append(
            f"🚨 Top Gate Trigger: '{top_reason[0]}' ({top_reason[1]} times). "
            f"Focus optimization on this failure mode."
        )
    
    return insights

def print_report(patterns: Dict, insights: List[str], sample_tasks: Dict):
    """Print formatted analysis report"""
    print("\n" + "="*80)
    print("REAL TASK REPLAN DEEP DIVE ANALYSIS")
    print("="*80)
    
    print(f"\n📊 OVERVIEW")
    print(f"   Total Real Tasks: {patterns['total_real_tasks']}")
    print(f"   Replan Rate: {patterns['replan_rate']:.1f}%")
    print(f"   Replan Tasks: {patterns['replan']['count']}")
    print(f"   No-Replan Tasks: {patterns['no_replan']['count']}")
    
    print(f"\n🔴 REPLAN TASKS (N={patterns['replan']['count']})")
    replan = patterns['replan']
    print(f"   Avg Thesis Citations: {replan['avg_thesis_citations']:.1f}")
    print(f"   Evidence Gate Trigger Rate: {replan['evidence_gate_trigger_rate']:.1f}%")
    print(f"   Avg Citations Added by Gate: {replan['avg_citations_added']:.1f}")
    print(f"   Avg Final Quality: {replan['avg_final_quality']:.2f}")
    print(f"   Evidence OK Rate: {replan['evidence_ok_rate']:.1f}%")
    
    if replan['top_gate_reasons']:
        print(f"\n   Top Evidence Gate Triggers:")
        for reason, count in replan['top_gate_reasons'].most_common(3):
            pct = count / replan['count'] * 100
            print(f"      {reason:30s} {count:3d} ({pct:5.1f}%)")
    
    print(f"\n🟢 NO-REPLAN TASKS (N={patterns['no_replan']['count']})")
    no_replan = patterns['no_replan']
    print(f"   Avg Thesis Citations: {no_replan['avg_thesis_citations']:.1f}")
    print(f"   Evidence Gate Trigger Rate: {no_replan['evidence_gate_trigger_rate']:.1f}%")
    print(f"   Avg Citations Added by Gate: {no_replan['avg_citations_added']:.1f}")
    print(f"   Avg Final Quality: {no_replan['avg_final_quality']:.2f}")
    print(f"   Evidence OK Rate: {no_replan['evidence_ok_rate']:.1f}%")
    
    if no_replan['top_gate_reasons']:
        print(f"\n   Top Evidence Gate Triggers:")
        for reason, count in no_replan['top_gate_reasons'].most_common(3):
            pct = count / no_replan['count'] * 100
            print(f"      {reason:30s} {count:3d} ({pct:5.1f}%)")
    
    print(f"\n💡 KEY INSIGHTS")
    for i, insight in enumerate(insights, 1):
        print(f"   [{i}] {insight}")
    
    # Sample failing tasks
    replan_samples = [(tid, flow) for tid, flow in sample_tasks.items() if flow['final_replan'] is True][:3]
    if replan_samples:
        print(f"\n📋 SAMPLE FAILING TASKS")
        for i, (tid, flow) in enumerate(replan_samples, 1):
            print(f"\n   [{i}] Task: {tid}")
            print(f"       Thesis Citations: {flow['thesis_citations']}")
            print(f"       Evidence Gate: {'Yes' if flow['evidence_gate_triggered'] else 'No'}")
            if flow['evidence_gate_triggered']:
                print(f"       Gate Reason: {flow['evidence_gate_reason']}")
                print(f"       Citations Added: {flow['citations_added']}")
            print(f"       Final Quality: {flow['final_quality']:.2f}")
            print(f"       Evidence OK: {flow['final_evidence_ok']}")
    
    print("\n" + "="*80)

def main():
    # Paths
    repo_root = Path(__file__).parent.parent
    ledger_path = repo_root / "memory" / "resonance_ledger.jsonl"
    output_path = repo_root.parent / "outputs" / "real_task_replan_analysis.json"
    
    print(f"Loading events from: {ledger_path}")
    events = load_ledger_events(ledger_path)
    print(f"Loaded {len(events)} events")
    
    print("\nIdentifying real tasks...")
    real_tasks = identify_real_tasks(events)
    print(f"Found {len(real_tasks)} real tasks")
    
    print("\nAnalyzing evidence flow for real tasks...")
    task_flows = analyze_real_task_evidence_flow(events, real_tasks)
    
    print("\nExtracting patterns...")
    patterns = analyze_patterns(task_flows)
    
    print("\nGenerating insights...")
    insights = generate_insights(patterns)
    
    # Print report
    print_report(patterns, insights, task_flows)
    
    # Save JSON
    output_data = {
        'patterns': {
            'replan': {
                k: (dict(v) if isinstance(v, Counter) else v)
                for k, v in patterns['replan'].items()
            },
            'no_replan': {
                k: (dict(v) if isinstance(v, Counter) else v)
                for k, v in patterns['no_replan'].items()
            },
            'total_real_tasks': patterns['total_real_tasks'],
            'replan_rate': patterns['replan_rate']
        },
        'insights': insights,
        'sample_tasks': {
            tid: flow
            for tid, flow in list(task_flows.items())[:10]
        }
    }
    
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ JSON report saved: {output_path}")
    print("\n✅ Analysis complete")

if __name__ == "__main__":
    main()
