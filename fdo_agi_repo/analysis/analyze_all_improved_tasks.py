#!/usr/bin/env python3
"""
Analyze recent real tasks to measure improved PLAN prompt effectiveness
- Count tasks completed after prompt improvement
- Measure replan rate, citations, quality
- Compare with baseline 48.1%
"""

import json
from datetime import datetime
from pathlib import Path

def load_recent_events():
    """Load events from resonance_ledger.jsonl"""
    ledger_path = Path(__file__).parent.parent / "memory" / "resonance_ledger.jsonl"
    
    events = []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    
    return events

def analyze_all_recent_tasks(events):
    """Analyze ALL tasks with citations field (improved prompt version)"""
    print("=" * 80)
    print("ANALYSIS: ALL Tasks with Improved PLAN Prompt (Citations Logged)")
    print("=" * 80)
    
    # Group events by task_id
    tasks = {}
    
    for event in events:
        task_id = event.get('task_id')
        if not task_id:
            continue
        
        if task_id not in tasks:
            tasks[task_id] = {
                'task_id': task_id,
                'thesis_citations': None,
                'synthesis_citations': None,
                'quality': None,
                'evidence_ok': None,
                'replan': None
            }
        
        # Extract metrics from different event types
        event_type = event.get('event')
        
        if event_type == 'thesis_end' and 'citations' in event:
            tasks[task_id]['thesis_citations'] = event['citations']
        
        elif event_type == 'synthesis_end' and 'citations' in event:
            tasks[task_id]['synthesis_citations'] = event['citations']
        
        elif event_type == 'eval':
            tasks[task_id]['quality'] = event.get('quality')
            tasks[task_id]['evidence_ok'] = event.get('evidence_ok')
        
        elif event_type == 'rune':
            rune_data = event.get('rune', {})
            tasks[task_id]['replan'] = rune_data.get('replan')
    
    # Filter to tasks with citations (improved version)
    improved_tasks = {
        tid: data for tid, data in tasks.items()
        if data['thesis_citations'] is not None
    }
    
    print(f"\nTotal tasks in ledger: {len(tasks)}")
    print(f"Tasks with citations (improved): {len(improved_tasks)}")
    
    if len(improved_tasks) == 0:
        print("\n⚠️ No improved tasks found yet")
        return
    
    # Calculate metrics
    replans = [t for t in improved_tasks.values() if t['replan'] is True]
    no_replans = [t for t in improved_tasks.values() if t['replan'] is False]
    pending = [t for t in improved_tasks.values() if t['replan'] is None]
    
    total = len(improved_tasks)
    replan_count = len(replans)
    no_replan_count = len(no_replans)
    pending_count = len(pending)
    
    print(f"\n📊 Results:")
    print(f"   Total: {total}")
    print(f"   Replans: {replan_count} ({replan_count/total*100:.1f}%)")
    print(f"   No Replans: {no_replan_count} ({no_replan_count/total*100:.1f}%)")
    print(f"   Pending: {pending_count} ({pending_count/total*100:.1f}%)")
    
    # Citations stats
    thesis_citations = [t['thesis_citations'] for t in improved_tasks.values() if t['thesis_citations'] is not None]
    synthesis_citations = [t['synthesis_citations'] for t in improved_tasks.values() if t['synthesis_citations'] is not None]
    
    avg_thesis = sum(thesis_citations) / len(thesis_citations) if thesis_citations else 0
    avg_synthesis = sum(synthesis_citations) / len(synthesis_citations) if synthesis_citations else 0
    
    print(f"\n📋 Citations:")
    print(f"   Avg Thesis Citations: {avg_thesis:.1f}")
    print(f"   Avg Synthesis Citations: {avg_synthesis:.1f}")
    
    # Quality stats
    if no_replan_count > 0:
        qualities = [t['quality'] for t in no_replans if t['quality'] is not None]
        evidence_ok_count = sum(1 for t in no_replans if t['evidence_ok'] is True)
        
        avg_quality = sum(qualities) / len(qualities) if qualities else 0
        evidence_ok_rate = (evidence_ok_count / no_replan_count * 100) if no_replan_count > 0 else 0
        
        print(f"\n✅ No-Replan Group:")
        print(f"   Avg Quality: {avg_quality:.2f}")
        print(f"   Evidence OK Rate: {evidence_ok_rate:.1f}%")
    
    # Comparison with baseline
    print("\n" + "=" * 80)
    print("COMPARISON WITH BASELINE")
    print("=" * 80)
    
    baseline_replan = 48.1
    completed_tasks = replan_count + no_replan_count
    
    if completed_tasks > 0:
        new_replan_rate = (replan_count / completed_tasks * 100)
        improvement = baseline_replan - new_replan_rate
        
        print(f"   Baseline Replan Rate (Real Tasks): {baseline_replan:.1f}%")
        print(f"   New Replan Rate: {new_replan_rate:.1f}%")
        print(f"   Improvement: {improvement:+.1f}%p")
        
        if new_replan_rate < 20:
            print(f"\n🎯 ✅ TARGET ACHIEVED: Replan rate below 20%!")
        else:
            print(f"\n⚠️ Target not yet met: {new_replan_rate:.1f}% (target <20%)")
    else:
        print("\n⚠️ No completed tasks yet to calculate replan rate")
    
    # Show sample tasks
    print("\n" + "=" * 80)
    print("SAMPLE TASKS (first 5)")
    print("=" * 80)
    
    for tid, data in list(improved_tasks.items())[:5]:
        print(f"\n{tid}:")
        print(f"  Thesis Citations: {data['thesis_citations']}")
        print(f"  Synthesis Citations: {data['synthesis_citations']}")
        print(f"  Quality: {data['quality']}")
        print(f"  Evidence OK: {data['evidence_ok']}")
        print(f"  Replan: {data['replan']}")
    
    # Breakdown by task category
    print("\n" + "=" * 80)
    print("BREAKDOWN BY TASK CATEGORY")
    print("=" * 80)
    
    # Group by task prefix
    categories = {}
    for tid, data in improved_tasks.items():
        # Extract category from task_id
        if tid.startswith('batch_val'):
            category = 'batch_val'
        elif tid.startswith('real_improved'):
            category = 'real_improved'
        elif tid.startswith('real_'):
            category = 'real'
        elif tid.startswith('test_'):
            category = 'test'
        else:
            category = 'other'
        
        if category not in categories:
            categories[category] = []
        categories[category].append(data)
    
    for category, cat_tasks in sorted(categories.items()):
        cat_replans = sum(1 for t in cat_tasks if t['replan'] is True)
        cat_no_replans = sum(1 for t in cat_tasks if t['replan'] is False)
        cat_total_completed = cat_replans + cat_no_replans
        
        if cat_total_completed > 0:
            cat_replan_rate = (cat_replans / cat_total_completed * 100)
            print(f"\n{category}: {len(cat_tasks)} tasks")
            print(f"  Completed: {cat_total_completed}")
            print(f"  Replan Rate: {cat_replan_rate:.1f}%")

def main():
    events = load_recent_events()
    print(f"Loaded {len(events)} events from ledger\n")
    
    analyze_all_recent_tasks(events)
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
