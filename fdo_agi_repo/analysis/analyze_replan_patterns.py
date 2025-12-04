#!/usr/bin/env python3
"""
Replan Pattern Analysis

Analyzes resonance_ledger.jsonl to identify replan triggers and patterns.
Helps reduce Replan Rate from 31.8%+ to target <10%.
"""
import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Any

# Add parent to path for imports
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))


def load_events(ledger_path: Path) -> List[Dict[str, Any]]:
    """Load all events from resonance_ledger.jsonl"""
    events = []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def analyze_replan_patterns(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze replan patterns and triggers"""
    # Extract RUNE events
    runes = [e for e in events if e.get('event') == 'rune']
    eval_events = [e for e in events if e.get('event') == 'eval']
    
    # Build task_id → eval mapping
    task_evals = {}
    for ev in eval_events:
        task_id = ev.get('task_id')
        if task_id:
            task_evals[task_id] = ev.get('eval', {})
    
    # Analyze replans
    total_runes = len(runes)
    replan_count = 0
    replan_reasons = Counter()
    replan_quality_dist = []
    replan_confidence_dist = []
    no_replan_quality_dist = []
    no_replan_confidence_dist = []
    
    replan_examples = []
    
    for rune_event in runes:
        rune = rune_event.get('rune', {})
        task_id = rune_event.get('task_id')
        is_replan = rune.get('replan', False)
        
        # Get associated EVAL
        eval_data = task_evals.get(task_id, {})
        quality = eval_data.get('quality', 0.0)
        evidence_ok = eval_data.get('evidence_ok', True)
        
        # Extract confidence from RUNE
        confidence = rune.get('confidence', 0.0)
        impact = rune.get('impact', 0.0)
        transparency = rune.get('transparency', 0.0)
        
        if is_replan:
            replan_count += 1
            replan_quality_dist.append(quality)
            replan_confidence_dist.append(confidence)
            
            # Determine reason
            reasons = []
            if quality < 0.6:
                reasons.append(f"low_quality ({quality:.2f})")
            if not evidence_ok:
                reasons.append("no_evidence")
            if confidence < 0.5:
                reasons.append(f"low_confidence ({confidence:.2f})")
            if impact < 0.5:
                reasons.append(f"low_impact ({impact:.2f})")
            if len(rune.get('risks', [])) > 0:
                reasons.append(f"risks ({len(rune['risks'])})")
            
            if not reasons:
                reasons.append("unknown")
            
            for r in reasons:
                replan_reasons[r] += 1
            
            # Save example
            if len(replan_examples) < 5:
                replan_examples.append({
                    'task_id': task_id,
                    'quality': quality,
                    'confidence': confidence,
                    'evidence_ok': evidence_ok,
                    'reasons': reasons,
                    'recommendations': rune.get('recommendations', [])
                })
        else:
            no_replan_quality_dist.append(quality)
            no_replan_confidence_dist.append(confidence)
    
    replan_rate = replan_count / total_runes * 100 if total_runes > 0 else 0
    
    # Calculate averages
    avg_replan_quality = sum(replan_quality_dist) / len(replan_quality_dist) if replan_quality_dist else 0
    avg_replan_confidence = sum(replan_confidence_dist) / len(replan_confidence_dist) if replan_confidence_dist else 0
    avg_no_replan_quality = sum(no_replan_quality_dist) / len(no_replan_quality_dist) if no_replan_quality_dist else 0
    avg_no_replan_confidence = sum(no_replan_confidence_dist) / len(no_replan_confidence_dist) if no_replan_confidence_dist else 0
    
    return {
        'summary': {
            'total_runes': total_runes,
            'replan_count': replan_count,
            'replan_rate_percent': replan_rate,
            'no_replan_count': total_runes - replan_count
        },
        'replan_triggers': dict(replan_reasons.most_common()),
        'quality_comparison': {
            'replan_avg': avg_replan_quality,
            'no_replan_avg': avg_no_replan_quality,
            'delta': avg_no_replan_quality - avg_replan_quality
        },
        'confidence_comparison': {
            'replan_avg': avg_replan_confidence,
            'no_replan_avg': avg_no_replan_confidence,
            'delta': avg_no_replan_confidence - avg_replan_confidence
        },
        'replan_examples': replan_examples
    }


def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on analysis"""
    recs = []
    
    triggers = analysis['replan_triggers']
    top_trigger = max(triggers.items(), key=lambda x: x[1])[0] if triggers else None
    
    # Quality-based recommendations
    quality_delta = analysis['quality_comparison']['delta']
    if quality_delta > 0.15:
        recs.append(f"🎯 Quality Gap: Replan avg={analysis['quality_comparison']['replan_avg']:.2f}, "
                   f"No-replan avg={analysis['quality_comparison']['no_replan_avg']:.2f}. "
                   f"Strengthen PLAN persona evidence scope specification.")
    
    # Confidence-based recommendations
    conf_delta = analysis['confidence_comparison']['delta']
    if conf_delta > 0.1:
        recs.append(f"⚠️ Confidence Gap: Replan avg={analysis['confidence_comparison']['replan_avg']:.2f}, "
                   f"No-replan avg={analysis['confidence_comparison']['no_replan_avg']:.2f}. "
                   f"Add task complexity pre-assessment in PLAN.")
    
    # Trigger-specific recommendations
    if top_trigger and 'low_quality' in top_trigger:
        recs.append("📊 Top Trigger: Low Quality. Update thesis.py with explicit quality thresholds. "
                   "Consider multi-pass planning for complex tasks.")
    
    if any('no_evidence' in t for t in triggers):
        recs.append("🔍 Evidence Issue: Force evidence gate not triggering properly. "
                   "Review EvidenceStage logic in pipeline.py.")
    
    if any('low_confidence' in t for t in triggers):
        recs.append("🤔 Confidence Issue: RUNE confidence < 0.5 triggering replans. "
                   "Adjust rune_from_eval() threshold or improve EVAL confidence scoring.")
    
    # Replan rate recommendations
    replan_rate = analysis['summary']['replan_rate_percent']
    if replan_rate > 30:
        recs.append(f"🚨 High Replan Rate: {replan_rate:.1f}% (target <10%). "
                   f"Immediate action: Review top 3 triggers and patch PLAN prompt.")
    elif replan_rate > 20:
        recs.append(f"⚠️ Elevated Replan Rate: {replan_rate:.1f}% (target <10%). "
                   f"Incremental improvements needed.")
    elif replan_rate > 10:
        recs.append(f"✅ Moderate Replan Rate: {replan_rate:.1f}% (near target). "
                   f"Fine-tune edge cases.")
    else:
        recs.append(f"🎉 Low Replan Rate: {replan_rate:.1f}% (target achieved!).")
    
    return recs


def print_report(analysis: Dict[str, Any], recommendations: List[str]) -> None:
    """Print formatted analysis report"""
    print("\n" + "="*80)
    print("REPLAN PATTERN ANALYSIS")
    print("="*80)
    
    summary = analysis['summary']
    print(f"\n📊 SUMMARY")
    print(f"   Total RUNE Events: {summary['total_runes']}")
    print(f"   Replans: {summary['replan_count']} ({summary['replan_rate_percent']:.1f}%)")
    print(f"   No Replans: {summary['no_replan_count']} ({100 - summary['replan_rate_percent']:.1f}%)")
    
    print(f"\n🔍 TOP REPLAN TRIGGERS")
    for trigger, count in list(analysis['replan_triggers'].items())[:10]:
        pct = count / summary['replan_count'] * 100 if summary['replan_count'] > 0 else 0
        print(f"   {trigger:35s} {count:3d} ({pct:5.1f}%)")
    
    print(f"\n📈 QUALITY COMPARISON")
    qc = analysis['quality_comparison']
    print(f"   Replan Avg Quality:    {qc['replan_avg']:.3f}")
    print(f"   No-Replan Avg Quality: {qc['no_replan_avg']:.3f}")
    print(f"   Delta:                 {qc['delta']:+.3f}")
    
    print(f"\n🎯 CONFIDENCE COMPARISON")
    cc = analysis['confidence_comparison']
    print(f"   Replan Avg Confidence:    {cc['replan_avg']:.3f}")
    print(f"   No-Replan Avg Confidence: {cc['no_replan_avg']:.3f}")
    print(f"   Delta:                    {cc['delta']:+.3f}")
    
    if analysis['replan_examples']:
        print(f"\n📋 REPLAN EXAMPLES (first 5)")
        for i, ex in enumerate(analysis['replan_examples'], 1):
            print(f"\n   [{i}] Task: {ex['task_id']}")
            print(f"       Quality: {ex['quality']:.2f}, Confidence: {ex['confidence']:.2f}, Evidence: {ex['evidence_ok']}")
            print(f"       Reasons: {', '.join(ex['reasons'])}")
            print(f"       Recommendations: {ex['recommendations']}")
    
    print(f"\n💡 RECOMMENDATIONS")
    for i, rec in enumerate(recommendations, 1):
        print(f"   [{i}] {rec}")
    
    print("\n" + "="*80)


def save_json_report(analysis: Dict[str, Any], recommendations: List[str], output_path: Path) -> None:
    """Save analysis as JSON"""
    report = {
        'analysis': analysis,
        'recommendations': recommendations,
        'generated_at': datetime.now().isoformat()
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n✅ JSON report saved: {output_path}")


def main():
    # Paths
    ledger_path = repo_root / "memory" / "resonance_ledger.jsonl"
    output_path = repo_root.parent / "outputs" / "replan_analysis_latest.json"
    
    if not ledger_path.exists():
        print(f"❌ Error: {ledger_path} not found")
        sys.exit(1)
    
    print(f"Loading events from: {ledger_path}")
    all_events = load_events(ledger_path)
    
    # Focus on recent 200 events for current state analysis
    events = all_events[-200:] if len(all_events) > 200 else all_events
    print(f"Loaded {len(all_events)} events (analyzing last {len(events)} for recent trends)")
    
    print("\nAnalyzing replan patterns...")
    analysis = analyze_replan_patterns(events)
    
    print("Generating recommendations...")
    recommendations = generate_recommendations(analysis)
    
    # Print report
    print_report(analysis, recommendations)
    
    # Save JSON
    save_json_report(analysis, recommendations, output_path)
    
    print("\n✅ Analysis complete")


if __name__ == '__main__':
    main()
