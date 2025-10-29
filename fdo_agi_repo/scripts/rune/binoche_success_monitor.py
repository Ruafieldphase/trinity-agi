#!/usr/bin/env python3
"""
Binoche Success Rate Monitor (Phase 6k)

Purpose:
    Monitor ensemble prediction accuracy in production:
    - Track ensemble confidence vs actual decision outcomes
    - Measure real-world success rate
    - Detect prediction drift (if MI drops from 100%)
    - Alert if ensemble becomes unreliable

Expected Performance (from Phase 7):
    - H(Decision|Ensemble) = 0.0 bits (perfect prediction)
    - Ensemble conf ≥ 0.8 → 100% approve accuracy
    - Ensemble conf 0.5-0.8 → 100% revise accuracy
    - Ensemble conf < 0.5 → 100% reject accuracy

Author: Gitco (GitHub Copilot)
Date: 2025-10-28
Phase: 6k (Success Rate Monitoring)
"""

import json
import sys
import math
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def load_ledger(ledger_path: Path, hours: int = 24) -> List[Dict[str, Any]]:
    """Load recent events from resonance ledger."""
    if not ledger_path.exists():
        print(f"[Monitor] Ledger not found: {ledger_path}")
        return []
    
    cutoff_timestamp = (datetime.now() - timedelta(hours=hours)).timestamp()
    events = []
    
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                # Use 'ts' field (Unix timestamp)
                event_ts = event.get('ts', 0)
                if event_ts >= cutoff_timestamp:
                    events.append(event)
            except (json.JSONDecodeError, ValueError):
                continue
    
    print(f"[Monitor] Loaded {len(events)} events from last {hours}h")
    return events


def extract_ensemble_predictions(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract ensemble predictions from ledger.
    
    Returns list of:
    {
        "task_id": str,
        "ensemble_decision": "approve" | "revise" | "reject",
        "ensemble_confidence": float,
        "ensemble_reason": str,
        "bqi_confidence": float,
        "quality": float,
        "timestamp": str
    }
    """
    predictions = []
    binoche_count = 0
    
    for event in events:
        if event.get('event') == 'binoche_decision':
            binoche_count += 1
            pred = {
                'task_id': event.get('task_id'),
                'ensemble_decision': event.get('ensemble_decision'),
                'ensemble_confidence': event.get('ensemble_confidence'),
                'ensemble_reason': event.get('ensemble_reason'),
                'bqi_confidence': event.get('confidence'),  # BQI confidence
                'quality': event.get('quality'),
                'timestamp': event.get('ts')  # Use 'ts' field
            }
            
            # Debug: print first few to see what's happening
            if binoche_count <= 3:
                print(f"[DEBUG] Binoche #{binoche_count}: decision={pred['ensemble_decision']}, conf={pred['ensemble_confidence']}")
            
            # Only include if we have ensemble data
            if pred['ensemble_decision'] and pred['ensemble_confidence'] is not None:
                predictions.append(pred)
    
    print(f"[Monitor] Found {binoche_count} binoche_decision events, extracted {len(predictions)} with ensemble data")
    return predictions


def extract_actual_outcomes(events: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Extract actual final decisions from ledger.
    
    Returns:
        {task_id: "approve" | "revise" | "reject"}
    """
    outcomes = {}
    
    for event in events:
        task_id = event.get('task_id')
        if not task_id:
            continue
        
        # Track final outcomes
        if event.get('event') == 'binoche_auto_approve':
            outcomes[task_id] = 'approve'
        elif event.get('event') in ['second_pass', 'revise']:
            outcomes[task_id] = 'revise'
        elif event.get('event') == 'reject':
            outcomes[task_id] = 'reject'
        # Also check eval event for final quality
        elif event.get('event') == 'eval':
            quality = event.get('quality')
            if quality is not None:
                # Infer outcome from quality
                if quality >= 0.8:
                    outcomes[task_id] = 'approve'
                elif quality >= 0.5:
                    outcomes[task_id] = 'revise'
                else:
                    outcomes[task_id] = 'reject'
    
    print(f"[Monitor] Extracted {len(outcomes)} actual outcomes")
    return outcomes


def calculate_success_rate(
    predictions: List[Dict[str, Any]], 
    outcomes: Dict[str, str]
) -> Dict[str, Any]:
    """
    Calculate ensemble prediction success rate.
    
    Returns:
    {
        "overall": {
            "total": int,
            "correct": int,
            "accuracy": float
        },
        "by_confidence": {
            "high (≥0.8)": {...},
            "medium (0.5-0.8)": {...},
            "low (<0.5)": {...}
        },
        "by_decision": {
            "approve": {...},
            "revise": {...},
            "reject": {...}
        },
        "confusion_matrix": {...}
    }
    """
    total = 0
    correct = 0
    
    # By confidence bucket
    conf_buckets: Dict[str, Dict[str, Any]] = {
        'high (≥0.8)': {'total': 0, 'correct': 0, 'accuracy': 0.0},
        'medium (0.5-0.8)': {'total': 0, 'correct': 0, 'accuracy': 0.0},
        'low (<0.5)': {'total': 0, 'correct': 0, 'accuracy': 0.0}
    }
    
    # By predicted decision
    decision_stats: Dict[str, Dict[str, Any]] = {
        'approve': {'total': 0, 'correct': 0, 'accuracy': 0.0},
        'revise': {'total': 0, 'correct': 0, 'accuracy': 0.0},
        'reject': {'total': 0, 'correct': 0, 'accuracy': 0.0}
    }
    
    # Confusion matrix: confusion[predicted][actual] = count
    confusion = defaultdict(lambda: defaultdict(int))
    
    for pred in predictions:
        task_id = pred['task_id']
        ensemble_decision = pred['ensemble_decision']
        ensemble_conf = pred['ensemble_confidence']
        
        # Get actual outcome
        actual = outcomes.get(task_id)
        if not actual:
            continue  # Skip if no outcome found
        
        # Overall stats
        total += 1
        is_correct = (ensemble_decision == actual)
        if is_correct:
            correct += 1
        
        # By confidence bucket
        if ensemble_conf >= 0.8:
            bucket = 'high (≥0.8)'
        elif ensemble_conf >= 0.5:
            bucket = 'medium (0.5-0.8)'
        else:
            bucket = 'low (<0.5)'
        
        conf_buckets[bucket]['total'] += 1
        if is_correct:
            conf_buckets[bucket]['correct'] += 1
        
        # By decision
        decision_stats[ensemble_decision]['total'] += 1
        if is_correct:
            decision_stats[ensemble_decision]['correct'] += 1
        
        # Confusion matrix
        confusion[ensemble_decision][actual] += 1
    
    # Calculate accuracies
    overall_accuracy = correct / total if total > 0 else 0.0
    
    for bucket in conf_buckets.values():
        total_count = bucket['total']
        bucket['accuracy'] = float(bucket['correct'] / total_count) if total_count > 0 else 0.0
    
    for decision in decision_stats.values():
        total_count = decision['total']
        decision['accuracy'] = float(decision['correct'] / total_count) if total_count > 0 else 0.0
    
    return {
        'overall': {
            'total': total,
            'correct': correct,
            'accuracy': overall_accuracy
        },
        'by_confidence': conf_buckets,
        'by_decision': decision_stats,
        'confusion_matrix': dict(confusion)
    }


def calculate_mutual_information(
    predictions: List[Dict[str, Any]], 
    outcomes: Dict[str, str]
) -> float:
    """
    Calculate actual mutual information I(Ensemble; Decision) from production data.
    
    Expected from Phase 7: I(Ensemble; Decision) = 1.1106 bits (100%)
    """
    # Count joint occurrences: (ensemble_conf_bucket, actual_decision)
    joint_counts = defaultdict(int)
    ensemble_counts = defaultdict(int)
    decision_counts = defaultdict(int)
    total = 0
    
    for pred in predictions:
        task_id = pred['task_id']
        ensemble_conf = pred['ensemble_confidence']
        
        actual = outcomes.get(task_id)
        if not actual:
            continue
        
        # Bin ensemble confidence
        if ensemble_conf >= 0.8:
            conf_bucket = 'high'
        elif ensemble_conf >= 0.5:
            conf_bucket = 'medium'
        else:
            conf_bucket = 'low'
        
        joint_counts[(conf_bucket, actual)] += 1
        ensemble_counts[conf_bucket] += 1
        decision_counts[actual] += 1
        total += 1
    
    if total == 0:
        return 0.0
    
    # Calculate MI: I(X;Y) = ΣΣ P(x,y) log2(P(x,y) / (P(x)P(y)))
    mi = 0.0
    for (conf_bucket, decision), joint_count in joint_counts.items():
        p_xy = joint_count / total
        p_x = ensemble_counts[conf_bucket] / total
        p_y = decision_counts[decision] / total
        
        if p_xy > 0 and p_x > 0 and p_y > 0:
            mi += p_xy * math.log2(p_xy / (p_x * p_y))
    
    return mi


def detect_drift(
    current_mi: float, 
    predictions: List[Dict[str, Any]],
    outcomes: Dict[str, str],
    expected_mi: float = 1.1106,
    threshold: float = 0.95
) -> Tuple[bool, str]:
    """
    Detect if ensemble predictive power has drifted from Phase 7 baseline.
    
    Args:
        current_mi: Current mutual information from production
        predictions: List of ensemble predictions to check which outcomes to consider
        outcomes: All actual outcomes dict
        expected_mi: Expected MI from Phase 7 (1.1106 bits = 100%)
        threshold: Alert if current < threshold * expected (default 95%)
    
    Returns:
        (has_drifted, message)
    """
    # Get only the outcomes that were actually predicted by ensemble
    predicted_task_ids = {p['task_id'] for p in predictions}
    matched_outcomes = {tid: outcome for tid, outcome in outcomes.items() 
                       if tid in predicted_task_ids}
    
    # Check if MI=0 is due to single category (not a real drift)
    unique_decisions = len(set(matched_outcomes.values()))
    if current_mi == 0.0 and unique_decisions == 1:
        single_category = list(matched_outcomes.values())[0]
        return (
            False,
            f"✅ No drift: MI=0.0 due to single outcome category ('{single_category}')\n"
            f"  ℹ️ This is expected when system maintains consistent high quality"
        )
    
    if current_mi < threshold * expected_mi:
        drop_percent = (1 - current_mi / expected_mi) * 100
        return (
            True, 
            f"⚠️ DRIFT DETECTED: MI dropped {drop_percent:.1f}% "
            f"(current={current_mi:.4f}, expected={expected_mi:.4f})"
        )
    return (False, f"✅ No drift: MI={current_mi:.4f} (expected={expected_mi:.4f})")


def generate_report(
    predictions: List[Dict[str, Any]],
    outcomes: Dict[str, str],
    success_rate: Dict[str, Any],
    current_mi: float,
    hours: int
) -> str:
    """Generate human-readable monitoring report."""
    lines = []
    lines.append("=" * 60)
    lines.append("🔍 Binoche Ensemble Success Rate Monitor (Phase 6k)")
    lines.append("=" * 60)
    lines.append(f"Time Window: Last {hours} hours")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Overall accuracy
    overall = success_rate['overall']
    lines.append("📊 Overall Performance:")
    lines.append(f"  Total predictions: {overall['total']}")
    lines.append(f"  Correct: {overall['correct']}")
    lines.append(f"  Accuracy: {overall['accuracy']*100:.1f}%")
    lines.append("")
    
    # By confidence bucket
    lines.append("🎯 Accuracy by Ensemble Confidence:")
    for bucket_name, stats in success_rate['by_confidence'].items():
        if stats['total'] > 0:
            lines.append(f"  {bucket_name}:")
            lines.append(f"    Total: {stats['total']}")
            lines.append(f"    Correct: {stats['correct']}")
            lines.append(f"    Accuracy: {stats['accuracy']*100:.1f}%")
            
            # Phase 7 expectation check
            if 'high' in bucket_name and stats['accuracy'] < 1.0:
                lines.append(f"    ⚠️ Expected 100% (Phase 7), got {stats['accuracy']*100:.1f}%")
    lines.append("")
    
    # By decision type
    lines.append("📈 Accuracy by Decision Type:")
    for decision, stats in success_rate['by_decision'].items():
        if stats['total'] > 0:
            lines.append(f"  {decision.capitalize()}:")
            lines.append(f"    Total: {stats['total']}")
            lines.append(f"    Correct: {stats['correct']}")
            lines.append(f"    Accuracy: {stats['accuracy']*100:.1f}%")
    lines.append("")
    
    # Confusion matrix
    lines.append("🔀 Confusion Matrix (Predicted vs Actual):")
    confusion = success_rate['confusion_matrix']
    decisions = ['approve', 'revise', 'reject']
    
    # Header
    lines.append("  Predicted │ " + " │ ".join(f"{d:^8}" for d in decisions))
    lines.append("  " + "─" * 50)
    
    for pred_decision in decisions:
        if pred_decision in confusion:
            row = f"  {pred_decision:>9} │"
            for actual_decision in decisions:
                count = confusion[pred_decision].get(actual_decision, 0)
                row += f" {count:^8} │"
            lines.append(row)
    lines.append("")
    
    # Information Theory
    lines.append("🧠 Information Theory (Production):")
    lines.append(f"  Mutual Information: {current_mi:.4f} bits")
    
    # Compare with Phase 7
    expected_mi = 1.1106
    reduction_percent = (current_mi / expected_mi) * 100 if expected_mi > 0 else 0
    lines.append(f"  Expected (Phase 7): {expected_mi:.4f} bits (100%)")
    lines.append(f"  Current: {reduction_percent:.1f}% of expected")
    
    # Check if MI=0 is due to single category (not a real drift)
    predicted_task_ids = {p['task_id'] for p in predictions}
    matched_outcomes = {tid: outcome for tid, outcome in outcomes.items() 
                       if tid in predicted_task_ids}
    unique_decisions = len(set(matched_outcomes.values()))
    
    if current_mi == 0.0 and unique_decisions == 1:
        lines.append(f"  ℹ️ MI=0 due to single outcome category ({list(matched_outcomes.values())[0]})")
        lines.append(f"  ℹ️ This is expected when system maintains high quality")
    else:
        # Drift detection
        has_drift, drift_msg = detect_drift(current_mi, predictions, outcomes, expected_mi)
        lines.append(f"  {drift_msg}")
    lines.append("")
    
    # Recommendations
    lines.append("💡 Recommendations:")
    if overall['accuracy'] >= 0.95:
        lines.append("  ✅ Ensemble performing excellently (≥95% accuracy)")
        if unique_decisions == 1:
            lines.append("  ✅ System maintaining consistent high quality")
            lines.append("  ℹ️ Consider running diverse test cases to validate full spectrum")
    elif overall['accuracy'] >= 0.85:
        lines.append("  ⚠️ Ensemble performing well but below expectations (85-95%)")
        lines.append("     Consider Phase 6l (Online Learning) to improve weights")
    else:
        lines.append("  🚨 Ensemble underperforming (<85% accuracy)")
        lines.append("     Immediate action needed:")
        lines.append("     1. Review recent failed predictions")
        lines.append("     2. Check for data distribution shift")
        lines.append("     3. Consider retraining (re-run Phase 7)")
    
    # Only show drift alert if real drift detected (not single category scenario)
    has_drift = detect_drift(current_mi, predictions, outcomes)[0]
    if has_drift and unique_decisions > 1:
        lines.append("  🚨 Drift detected - consider retraining ensemble weights")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def save_metrics(
    metrics: Dict[str, Any],
    output_path: Path
):
    """Save monitoring metrics to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[Monitor] Metrics saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor Binoche ensemble success rate in production (Phase 6k)"
    )
    parser.add_argument(
        '--hours', 
        type=int, 
        default=24,
        help='Time window in hours (default: 24)'
    )
    parser.add_argument(
        '--ledger',
        type=Path,
        default=Path(__file__).parent.parent.parent / 'memory' / 'resonance_ledger.jsonl',
        help='Path to resonance ledger'
    )
    parser.add_argument(
        '--out-json',
        type=Path,
        default=Path(__file__).parent.parent.parent / 'outputs' / 'ensemble_success_metrics.json',
        help='Output path for JSON metrics'
    )
    parser.add_argument(
        '--out-report',
        type=Path,
        default=Path(__file__).parent.parent.parent / 'outputs' / 'ensemble_success_report.txt',
        help='Output path for text report'
    )
    
    args = parser.parse_args()
    
    print(f"[Monitor] Starting Binoche Success Rate Monitor (Phase 6k)")
    print(f"[Monitor] Time window: last {args.hours} hours")
    print()
    
    # Step 1: Load ledger
    events = load_ledger(args.ledger, args.hours)
    if not events:
        print("[Monitor] No events found - exiting")
        return
    
    # Step 2: Extract ensemble predictions
    predictions = extract_ensemble_predictions(events)
    if not predictions:
        print("[Monitor] No ensemble predictions found - exiting")
        print("[Monitor] Hint: Ensemble was implemented in Phase 6j")
        return
    
    # Step 3: Extract actual outcomes
    outcomes = extract_actual_outcomes(events)
    
    # Step 4: Calculate success rate
    success_rate = calculate_success_rate(predictions, outcomes)
    
    # Step 5: Calculate MI
    current_mi = calculate_mutual_information(predictions, outcomes)
    
    # Step 6: Generate report
    report = generate_report(predictions, outcomes, success_rate, current_mi, args.hours)
    print(report)
    
    # Step 7: Save metrics
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'time_window_hours': args.hours,
        'predictions_count': len(predictions),
        'success_rate': success_rate,
        'mutual_information': {
            'current': current_mi,
            'expected': 1.1106,
            'percent_of_expected': (current_mi / 1.1106) * 100 if 1.1106 > 0 else 0
        },
        'drift_detected': detect_drift(current_mi, predictions, outcomes)[0]
    }
    
    # Ensure output directory exists
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.parent.mkdir(parents=True, exist_ok=True)
    
    save_metrics(metrics, args.out_json)
    
    # Save report
    with open(args.out_report, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"[Monitor] Report saved to: {args.out_report}")
    
    print()
    print("[Monitor] Phase 6k monitoring complete!")
    
    # Exit code: 0 if no drift, 1 if drift detected
    sys.exit(1 if metrics['drift_detected'] else 0)


if __name__ == '__main__':
    main()
