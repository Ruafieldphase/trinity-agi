#!/usr/bin/env python3
"""
Complexity Spectrum Analysis
============================

Compares performance across Simple, Medium, and Complex task categories
to validate system scalability.

Usage:
    python analyze_complexity_spectrum.py
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def load_batch_results(outputs_dir: Path) -> List[Dict]:
    """Load all batch validation JSON results."""
    results = []
    for json_file in outputs_dir.glob("batch_validation_*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            results.append({
                'timestamp': json_file.stem.split('_')[-1],
                'data': data
            })
    return sorted(results, key=lambda x: x['timestamp'], reverse=True)


def analyze_complexity_spectrum() -> Dict:
    """Analyze performance across complexity levels."""
    outputs_dir = Path(__file__).parent.parent / "outputs"
    results = load_batch_results(outputs_dir)
    
    if not results:
        return {"error": "No batch validation results found"}
    
    # Use most recent 3 results (should include simple, medium, complex runs)
    recent = results[:3]
    
    complexity_metrics = {}
    
    for result in recent:
        data = result['data']
        categories = data.get('per_category', {})
        
        # Map categories to complexity levels
        simple_cats = ['standard', 'code_heavy', 'documentation', 'multi_hop']
        
        for cat_name, cat_data in categories.items():
            if cat_name in simple_cats:
                complexity = 'simple'
            elif cat_name == 'medium':
                complexity = 'medium'
            elif cat_name == 'complex':
                complexity = 'complex'
            else:
                continue
            
            if complexity not in complexity_metrics:
                complexity_metrics[complexity] = {
                    'success_rates': [],
                    'avg_qualities': [],
                    'avg_times': [],
                    'total_tasks': 0
                }
            
            complexity_metrics[complexity]['success_rates'].append(cat_data['success_rate_percent'])
            complexity_metrics[complexity]['avg_qualities'].append(cat_data['avg_quality_score'])
            complexity_metrics[complexity]['avg_times'].append(cat_data['avg_elapsed_sec'])
            complexity_metrics[complexity]['total_tasks'] += cat_data['total']
    
    # Calculate aggregates
    summary = {}
    for complexity, metrics in complexity_metrics.items():
        if metrics['success_rates']:
            summary[complexity] = {
                'avg_success_rate': round(sum(metrics['success_rates']) / len(metrics['success_rates']), 2),
                'avg_quality': round(sum(metrics['avg_qualities']) / len(metrics['avg_qualities']), 3),
                'avg_time_sec': round(sum(metrics['avg_times']) / len(metrics['avg_times']), 2),
                'total_tasks': metrics['total_tasks']
            }
    
    return summary


def print_report(spectrum: Dict):
    """Print formatted complexity spectrum report."""
    print("=" * 80)
    print("COMPLEXITY SPECTRUM ANALYSIS")
    print("=" * 80)
    print()
    
    if 'error' in spectrum:
        print(f"❌ {spectrum['error']}")
        return
    
    # Print table header
    print(f"{'Complexity':<12} {'Success Rate':<15} {'Quality':<10} {'Time (s)':<10} {'Tasks':<8}")
    print("-" * 80)
    
    # Print data for each complexity level
    for complexity in ['simple', 'medium', 'complex']:
        if complexity in spectrum:
            data = spectrum[complexity]
            print(f"{complexity.capitalize():<12} "
                  f"{data['avg_success_rate']:.1f}%{'':<10} "
                  f"{data['avg_quality']:.3f}{'':<5} "
                  f"{data['avg_time_sec']:.1f}{'':<5} "
                  f"{data['total_tasks']:<8}")
    
    print()
    
    # Analysis
    if 'simple' in spectrum and 'complex' in spectrum:
        simple = spectrum['simple']
        complex_data = spectrum['complex']
        
        success_gap = abs(simple['avg_success_rate'] - complex_data['avg_success_rate'])
        quality_gap = abs(simple['avg_quality'] - complex_data['avg_quality'])
        time_increase = ((complex_data['avg_time_sec'] - simple['avg_time_sec']) / simple['avg_time_sec']) * 100
        
        print("📊 INSIGHTS:")
        print(f"   Success Rate Gap: {success_gap:.1f}%", end="")
        if success_gap < 5:
            print(" ✅ (Excellent - minimal degradation)")
        elif success_gap < 10:
            print(" ⚠️ (Acceptable)")
        else:
            print(" ❌ (Needs improvement)")
        
        print(f"   Quality Gap: {quality_gap:.3f}", end="")
        if quality_gap < 0.1:
            print(" ✅ (Excellent consistency)")
        elif quality_gap < 0.2:
            print(" ⚠️ (Acceptable)")
        else:
            print(" ❌ (Quality degradation)")
        
        print(f"   Time Increase: +{time_increase:.1f}%", end="")
        if time_increase < 20:
            print(" ✅ (Efficient scaling)")
        elif time_increase < 40:
            print(" ⚠️ (Acceptable)")
        else:
            print(" ❌ (Performance bottleneck)")
    
    print()
    print("=" * 80)


def main():
    spectrum = analyze_complexity_spectrum()
    print_report(spectrum)
    
    # Save to JSON
    output_path = Path(__file__).parent.parent / "outputs" / "complexity_spectrum_latest.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(spectrum, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Results saved to: {output_path}")


if __name__ == "__main__":
    main()
