import json

# Load recent events
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from workspace_utils import find_fdo_root

ledger_path = find_fdo_root(Path(__file__).parent) / 'memory' / 'resonance_ledger.jsonl'
lines = open(ledger_path, encoding='utf-8').readlines()
events = [json.loads(l) for l in lines]

print(f"Total events: {len(events)}")

# Filter batch_val tasks from recent run
batch_tasks = [e.get('task_id') for e in events if 'batch_val' in e.get('task_id', '')]
unique_batch = set(batch_tasks)
print(f"\nUnique batch_val tasks: {len(unique_batch)}")

# Analyze each batch_val task
task_analysis = {}

for event in events:
    task_id = event.get('task_id')
    if not task_id or 'batch_val' not in task_id:
        continue
    
    if task_id not in task_analysis:
        task_analysis[task_id] = {
            'thesis_citations': None,
            'synthesis_citations': None,
            'quality': None,
            'evidence_ok': None,
            'replan': None
        }
    
    event_type = event.get('event')
    
    if event_type == 'thesis_end':
        citations = event.get('citations')
        if citations is not None:
            task_analysis[task_id]['thesis_citations'] = citations
    
    elif event_type == 'synthesis_end':
        citations = event.get('citations')
        if citations is not None:
            task_analysis[task_id]['synthesis_citations'] = citations
    
    elif event_type == 'eval':
        task_analysis[task_id]['quality'] = event.get('quality')
        task_analysis[task_id]['evidence_ok'] = event.get('evidence_ok')
    
    elif event_type == 'rune':
        rune_data = event.get('rune', {})
        task_analysis[task_id]['replan'] = rune_data.get('replan')

# Filter tasks with citations logged (improved version)
improved_tasks = {
    tid: data for tid, data in task_analysis.items()
    if data['thesis_citations'] is not None
}

print(f"\n" + "="*80)
print(f"ANALYSIS: Batch Validation Tasks with Improved PLAN Prompt")
print("="*80)

if not improved_tasks:
    print("\n⚠️  No batch_val tasks found with citations logging")
    print("   (This means the improved code hasn't been tested yet)")
else:
    print(f"\nTasks with Citations: {len(improved_tasks)}")
    
    # Statistics
    replans = [tid for tid, data in improved_tasks.items() if data['replan'] is True]
    no_replans = [tid for tid, data in improved_tasks.items() if data['replan'] is False]
    
    print(f"\n📊 Results:")
    print(f"   Total: {len(improved_tasks)}")
    print(f"   Replans: {len(replans)} ({len(replans)/len(improved_tasks)*100:.1f}%)")
    print(f"   No Replans: {len(no_replans)} ({len(no_replans)/len(improved_tasks)*100:.1f}%)")
    
    # Citations analysis
    avg_thesis_cites = sum(d['thesis_citations'] for d in improved_tasks.values() if d['thesis_citations']) / len(improved_tasks)
    avg_synth_cites = sum(d['synthesis_citations'] for d in improved_tasks.values() if d['synthesis_citations']) / len(improved_tasks)
    
    print(f"\n📋 Citations:")
    print(f"   Avg Thesis Citations: {avg_thesis_cites:.1f}")
    print(f"   Avg Synthesis Citations: {avg_synth_cites:.1f}")
    
    # Quality analysis
    if no_replans:
        avg_quality_ok = sum(improved_tasks[tid]['quality'] for tid in no_replans if improved_tasks[tid]['quality']) / len(no_replans)
        evidence_ok_rate = sum(1 for tid in no_replans if improved_tasks[tid]['evidence_ok']) / len(no_replans) * 100
        print(f"\n✅ No-Replan Group:")
        print(f"   Avg Quality: {avg_quality_ok:.2f}")
        print(f"   Evidence OK Rate: {evidence_ok_rate:.1f}%")
    
    if replans:
        avg_quality_replan = sum(improved_tasks[tid]['quality'] for tid in replans if improved_tasks[tid]['quality']) / len(replans)
        evidence_ok_rate_replan = sum(1 for tid in replans if improved_tasks[tid]['evidence_ok']) / len(replans) * 100
        print(f"\n❌ Replan Group:")
        print(f"   Avg Quality: {avg_quality_replan:.2f}")
        print(f"   Evidence OK Rate: {evidence_ok_rate_replan:.1f}%")
    
    # Sample tasks
    print(f"\n📋 Sample Tasks:")
    for tid, data in list(improved_tasks.items())[:3]:
        print(f"\n   {tid}:")
        print(f"      Thesis Citations: {data['thesis_citations']}")
        print(f"      Synthesis Citations: {data['synthesis_citations']}")
        quality_str = f"{data['quality']:.2f}" if data['quality'] is not None else 'N/A'
        print(f"      Quality: {quality_str}")
        print(f"      Evidence OK: {data['evidence_ok']}")
        print(f"      Replan: {data['replan']}")
    
    # Comparison with baseline
    baseline_replan = 48.0
    new_replan = len(replans) / len(improved_tasks) * 100
    improvement = baseline_replan - new_replan
    
    print(f"\n" + "="*80)
    print(f"COMPARISON WITH BASELINE (Real Tasks)")
    print("="*80)
    print(f"   Baseline Replan Rate: {baseline_replan:.1f}%")
    print(f"   New Replan Rate: {new_replan:.1f}%")
    print(f"   Improvement: {improvement:+.1f}%p")
    
    if new_replan < 20:
        print(f"\n🎯 ✅ TARGET ACHIEVED: Replan rate below 20%!")
    elif new_replan < baseline_replan:
        print(f"\n📈 IMPROVED: Replan rate reduced")
    else:
        print(f"\n⚠️  Need further optimization")

print("\n" + "="*80)
