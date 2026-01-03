#!/usr/bin/env python3
"""
Binoche_Observer Online Learner (Phase 6l)

Real-time ensemble weight adaptation based on production feedback.
Continuously monitors performance and adjusts weights to minimize prediction error.

Usage:
    python binoche_online_learner.py --window-hours 24 --learning-rate 0.01
    
Output:
    - outputs/ensemble_weights_updated.json
    - outputs/online_learning_log.jsonl
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import math

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from file_lock_util import FileLock


def load_ledger(ledger_path: Path, hours: int) -> List[Dict[str, Any]]:
    """Load recent events from resonance ledger."""
    from datetime import datetime, timezone
    
    cutoff = datetime.now().timestamp() - (hours * 3600)
    events = []
    
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                event = json.loads(line)
                ts = event.get('ts', 0)
                
                # Handle both timestamp formats
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                    except:
                        ts = 0
                else:
                    ts = float(ts)
                
                if ts >= cutoff:
                    events.append(event)
    
    return events


def extract_predictions_and_outcomes(
    events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Extract ensemble predictions and actual outcomes.
    
    Returns:
        List of {
            'task_id': str,
            'timestamp': float,
            'ensemble_decision': str,
            'ensemble_confidence': float,
            'actual_decision': str,
            'is_correct': bool,
            'judges': {
                'logic': {'decision': str, 'confidence': float},
                'emotion': {'decision': str, 'confidence': float},
                'rhythm': {'decision': str, 'confidence': float}
            }
        }
    """
    # Build task_id -> actual decision mapping
    actual_outcomes = {}
    for event in events:
        evt_type = event.get('event')
        if evt_type in ['binoche_auto_approve', 'binoche_auto_revise', 'binoche_manual_decision']:
            task_id = event.get('task_id')
            # Infer actual decision from event type
            if evt_type == 'binoche_auto_approve':
                actual = 'approve'
            elif evt_type == 'binoche_auto_revise':
                actual = 'revise'
            else:
                actual = event.get('decision', 'approve')  # fallback
            
            if task_id and actual:
                actual_outcomes[task_id] = actual
    
    # Extract ensemble predictions with judge details
    predictions = []
    for event in events:
        if event.get('event') == 'binoche_decision':
            task_id = event.get('task_id')
            ensemble_decision = event.get('ensemble_decision')
            ensemble_conf = event.get('ensemble_confidence')
            
            # Get individual judge predictions (Phase 7 format)
            judges_data = event.get('judges', {})
            logic = judges_data.get('logic', {})
            emotion = judges_data.get('emotion', {})
            rhythm = judges_data.get('rhythm', {})
            
            if not (task_id and ensemble_decision and ensemble_conf):
                continue
            
            # Skip if no judge data (old events before Phase 7)
            if not (logic and emotion and rhythm):
                continue
            
            actual = actual_outcomes.get(task_id)
            if not actual:
                continue
            
            predictions.append({
                'task_id': task_id,
                'timestamp': event.get('ts', 0),
                'ensemble_decision': ensemble_decision,
                'ensemble_confidence': ensemble_conf,
                'actual_decision': actual,
                'is_correct': (ensemble_decision == actual),
                'judges': {
                    'logic': {
                        'decision': logic.get('decision'),
                        'confidence': logic.get('confidence', 0.0)
                    },
                    'emotion': {
                        'decision': emotion.get('decision'),
                        'confidence': emotion.get('confidence', 0.0)
                    },
                    'rhythm': {
                        'decision': rhythm.get('decision'),
                        'confidence': rhythm.get('confidence', 0.0)
                    }
                }
            })
    
    return predictions
    
    return predictions


def load_current_weights(weights_path: Path) -> Dict[str, float]:
    """Load current ensemble weights from file."""
    if not weights_path.exists():
        # Default weights from Phase 7
        return {
            'logic': 0.40,
            'emotion': 0.35,
            'rhythm': 0.25
        }
    
    with open(weights_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('weights', {
            'logic': 0.40,
            'emotion': 0.35,
            'rhythm': 0.25
        })


def calculate_judge_accuracy(
    predictions: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate accuracy and confidence calibration for each judge.
    
    Returns:
        {
            'logic': {
                'accuracy': float,
                'avg_confidence': float,
                'correct_count': int,
                'total_count': int,
                'calibration_error': float  # |accuracy - avg_confidence|
            },
            ...
        }
    """
    judge_stats = {
        'logic': {'correct': 0, 'total': 0, 'conf_sum': 0.0},
        'emotion': {'correct': 0, 'total': 0, 'conf_sum': 0.0},
        'rhythm': {'correct': 0, 'total': 0, 'conf_sum': 0.0}
    }
    
    for pred in predictions:
        actual = pred['actual_decision']
        for judge_name in ['logic', 'emotion', 'rhythm']:
            judge = pred['judges'][judge_name]
            decision = judge['decision']
            confidence = judge['confidence']
            
            if decision:
                judge_stats[judge_name]['total'] += 1
                judge_stats[judge_name]['conf_sum'] += confidence
                if decision == actual:
                    judge_stats[judge_name]['correct'] += 1
    
    # Calculate metrics
    results = {}
    for judge_name, stats in judge_stats.items():
        total = stats['total']
        if total > 0:
            accuracy = stats['correct'] / total
            avg_conf = stats['conf_sum'] / total
            calibration_error = abs(accuracy - avg_conf)
        else:
            accuracy = 0.0
            avg_conf = 0.0
            calibration_error = 0.0
        
        results[judge_name] = {
            'accuracy': accuracy,
            'avg_confidence': avg_conf,
            'correct_count': stats['correct'],
            'total_count': total,
            'calibration_error': calibration_error
        }
    
    return results


def update_weights_gradient_descent(
    current_weights: Dict[str, float],
    judge_stats: Dict[str, Dict[str, Any]],
    learning_rate: float = 0.01
) -> Dict[str, float]:
    """
    Update weights using gradient descent based on judge accuracy.
    
    Strategy:
    - Increase weight for high-accuracy judges
    - Decrease weight for low-accuracy judges
    - Maintain sum(weights) = 1.0
    - Use calibration error as additional signal
    """
    # Calculate gradient: accuracy - current_weight
    # High accuracy → positive gradient → increase weight
    gradients = {}
    for judge_name in ['logic', 'emotion', 'rhythm']:
        accuracy = judge_stats[judge_name]['accuracy']
        current_w = current_weights[judge_name]
        
        # Gradient = accuracy - current_weight (normalized)
        # If judge is more accurate than its weight suggests, increase it
        gradients[judge_name] = (accuracy - current_w) * learning_rate
    
    # Update weights
    new_weights = {}
    for judge_name in ['logic', 'emotion', 'rhythm']:
        new_weights[judge_name] = current_weights[judge_name] + gradients[judge_name]
    
    # Normalize to sum = 1.0 (softmax-style)
    total = sum(new_weights.values())
    if total > 0:
        for judge_name in new_weights:
            new_weights[judge_name] /= total
    
    # Clip to [0.1, 0.8] to prevent extreme weights
    for judge_name in new_weights:
        new_weights[judge_name] = max(0.1, min(0.8, new_weights[judge_name]))
    
    # Re-normalize after clipping
    total = sum(new_weights.values())
    for judge_name in new_weights:
        new_weights[judge_name] /= total
    
    return new_weights


def calculate_weight_change(
    old_weights: Dict[str, float],
    new_weights: Dict[str, float]
) -> float:
    """Calculate L2 norm of weight change vector."""
    change_sq = sum((new_weights[j] - old_weights[j])**2 for j in old_weights)
    return math.sqrt(change_sq)


def save_weights(
    weights: Dict[str, float],
    output_path: Path,
    metadata: Dict[str, Any]
):
    """Save updated weights with metadata."""
    data = {
        'timestamp': datetime.now().isoformat(),
        'weights': weights,
        'metadata': metadata
    }
    
    # Use file lock to prevent concurrent writes
    with FileLock(str(output_path), timeout=10):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[OnlineLearner] Weights saved to: {output_path}")


def log_learning_step(
    log_path: Path,
    step_data: Dict[str, Any]
):
    """Append learning step to JSONL log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use file lock to prevent concurrent writes
    with FileLock(str(log_path), timeout=10):
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(step_data, ensure_ascii=False) + '\n')


def generate_report(
    old_weights: Dict[str, float],
    new_weights: Dict[str, float],
    judge_stats: Dict[str, Dict[str, Any]],
    predictions_count: int,
    weight_change: float
) -> str:
    """Generate human-readable learning report."""
    lines = []
    lines.append("=" * 60)
    lines.append("🧠 Binoche_Observer Online Learner (Phase 6l)")
    lines.append("=" * 60)
    lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Predictions analyzed: {predictions_count}")
    lines.append("")
    
    # Judge statistics
    lines.append("📊 Judge Performance:")
    for judge_name in ['logic', 'emotion', 'rhythm']:
        stats = judge_stats[judge_name]
        lines.append(f"  {judge_name.capitalize()}:")
        lines.append(f"    Accuracy: {stats['accuracy']*100:.1f}% ({stats['correct_count']}/{stats['total_count']})")
        lines.append(f"    Avg Confidence: {stats['avg_confidence']*100:.1f}%")
        lines.append(f"    Calibration Error: {stats['calibration_error']:.3f}")
    lines.append("")
    
    # Weight changes
    lines.append("⚖️ Weight Updates:")
    for judge_name in ['logic', 'emotion', 'rhythm']:
        old_w = old_weights[judge_name]
        new_w = new_weights[judge_name]
        change = new_w - old_w
        change_pct = (change / old_w) * 100 if old_w > 0 else 0
        
        arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
        lines.append(f"  {judge_name.capitalize()}: {old_w:.3f} {arrow} {new_w:.3f} ({change_pct:+.1f}%)")
    lines.append("")
    
    lines.append(f"🔄 Total Weight Change (L2): {weight_change:.4f}")
    
    if weight_change < 0.01:
        lines.append("✅ Weights converged (change < 0.01)")
    elif weight_change < 0.05:
        lines.append("⚠️ Weights nearly converged (0.01 ≤ change < 0.05)")
    else:
        lines.append("🔁 Weights still adapting (change ≥ 0.05)")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Binoche_Observer Online Learner (Phase 6l)')
    parser.add_argument('--window-hours', type=int, default=24,
                       help='Time window for learning (hours)')
    parser.add_argument('--learning-rate', type=float, default=0.01,
                       help='Learning rate for gradient descent')
    parser.add_argument('--ledger', type=str,
                       default='memory/resonance_ledger.jsonl',
                       help='Path to resonance ledger')
    parser.add_argument('--weights-file', type=str,
                       default='outputs/ensemble_weights.json',
                       help='Path to weights file (input/output)')
    parser.add_argument('--log-file', type=str,
                       default='outputs/online_learning_log.jsonl',
                       help='Path to learning log')
    
    args = parser.parse_args()
    
    print("[OnlineLearner] Starting Binoche_Observer Online Learner (Phase 6l)")
    print(f"[OnlineLearner] Time window: last {args.window_hours} hours")
    print(f"[OnlineLearner] Learning rate: {args.learning_rate}")
    print()
    
    # Resolve paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    ledger_path = repo_root / args.ledger
    weights_path = repo_root / args.weights_file
    log_path = repo_root / args.log_file
    
    # Step 1: Load events
    events = load_ledger(ledger_path, args.window_hours)
    print(f"[OnlineLearner] Loaded {len(events)} events from ledger")
    
    # Step 2: Extract predictions and outcomes
    predictions = extract_predictions_and_outcomes(events)
    print(f"[OnlineLearner] Extracted {len(predictions)} predictions with outcomes")
    
    if len(predictions) < 5:
        print("[OnlineLearner] ⚠️ Not enough data for learning (need ≥5 predictions)")
        print("[OnlineLearner] Skipping weight update")
        return
    
    # Step 3: Load current weights
    old_weights = load_current_weights(weights_path)
    print(f"[OnlineLearner] Current weights: {old_weights}")
    
    # Step 4: Calculate judge statistics
    judge_stats = calculate_judge_accuracy(predictions)
    
    # Step 5: Update weights
    new_weights = update_weights_gradient_descent(
        old_weights,
        judge_stats,
        args.learning_rate
    )
    
    # Step 6: Calculate change magnitude
    weight_change = calculate_weight_change(old_weights, new_weights)
    
    # Step 7: Generate report
    report = generate_report(
        old_weights,
        new_weights,
        judge_stats,
        len(predictions),
        weight_change
    )
    print(report)
    
    # Step 8: Save updated weights
    metadata = {
        'learning_rate': args.learning_rate,
        'predictions_count': len(predictions),
        'judge_stats': judge_stats,
        'weight_change': weight_change,
        'window_hours': args.window_hours
    }
    save_weights(new_weights, weights_path, metadata)
    
    # Step 9: Log learning step
    step_data = {
        'timestamp': datetime.now().isoformat(),
        'old_weights': old_weights,
        'new_weights': new_weights,
        'weight_change': weight_change,
        'judge_stats': judge_stats,
        'predictions_count': len(predictions),
        'learning_rate': args.learning_rate
    }
    log_learning_step(log_path, step_data)
    
    print()
    print("[OnlineLearner] Phase 6l learning complete!")


if __name__ == '__main__':
    main()
