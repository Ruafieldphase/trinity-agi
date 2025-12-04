#!/usr/bin/env python3
"""
AGI Second Pass 원인 분석 스크립트
- quality < min_quality 케이스 분석
- confidence vs quality 상관관계
- second_pass 발생 패턴 도출
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
import statistics


def load_ledger(ledger_path: Path):
    """Load resonance ledger JSONL"""
    events = []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def analyze_second_pass_causes(events, hours=24):
    """Analyze causes of second_pass events"""
    
    # Filter by time window
    now = datetime.now().timestamp()
    cutoff = now - (hours * 3600)
    recent_events = [e for e in events if e.get('ts', 0) >= cutoff]
    
    # Exclude test tasks
    exclude_prefixes = ['integration_test_', 'low_confidence_test_', 'temp_low_conf_']
    def is_real_task(task_id):
        return not any(task_id.startswith(prefix) for prefix in exclude_prefixes)
    
    # Group by task_id
    tasks = defaultdict(list)
    for event in recent_events:
        task_id = event.get('task_id')
        if task_id and is_real_task(task_id):
            tasks[task_id].append(event)
    
    # Analyze second_pass tasks
    second_pass_analysis = []
    
    for task_id, task_events in tasks.items():
        # Find second_pass event
        has_second_pass = any(e.get('event') == 'second_pass' for e in task_events)
        if not has_second_pass:
            continue
        
        # Extract relevant metrics
        run_config = next((e for e in task_events if e.get('event') == 'run_config'), {})
        meta_cognition = next((e for e in task_events if e.get('event') == 'meta_cognition'), {})
        
        # Find eval results (pass 1)
        eval_events = [e for e in task_events if e.get('event') == 'eval' and e.get('quality') is not None]
        
        if eval_events:
            first_eval = eval_events[0]
            quality = first_eval.get('quality', 0)
            evidence_ok = first_eval.get('evidence_ok', False)
            
            # Find rune (recommendations)
            rune_event = next((e for e in task_events if e.get('event') == 'rune'), {})
            rune_data = rune_event.get('rune', {})
            
            second_pass_analysis.append({
                'task_id': task_id,
                'min_quality': run_config.get('evaluation', {}).get('min_quality', 0.6),
                'first_quality': quality,
                'quality_gap': run_config.get('evaluation', {}).get('min_quality', 0.6) - quality,
                'evidence_ok': evidence_ok,
                'confidence': meta_cognition.get('confidence', 0),
                'past_performance': meta_cognition.get('past_performance', 0),
                'impact': rune_data.get('impact', 0),
                'transparency': rune_data.get('transparency', 0),
                'rune_confidence': rune_data.get('confidence', 0),
                'recommendations': rune_data.get('recommendations', []),
                'replan': rune_data.get('replan', False)
            })
    
    return second_pass_analysis


def print_analysis(analysis):
    """Print analysis results"""
    
    if not analysis:
        print("⚠️  No second_pass events found in the time window")
        return
    
    print(f"\n🔍 Second Pass 원인 분석 ({len(analysis)} cases)")
    print("=" * 80)
    
    # 1. Quality Gap 분석
    quality_gaps = [case['quality_gap'] for case in analysis]
    print(f"\n📊 Quality Gap (min_quality - actual_quality)")
    print(f"   평균: {statistics.mean(quality_gaps):.3f}")
    print(f"   중앙값: {statistics.median(quality_gaps):.3f}")
    print(f"   범위: {min(quality_gaps):.3f} ~ {max(quality_gaps):.3f}")
    
    # 2. Confidence vs Quality 상관관계
    confidences = [case['confidence'] for case in analysis]
    qualities = [case['first_quality'] for case in analysis]
    print(f"\n🎯 Confidence vs Quality")
    print(f"   평균 Confidence: {statistics.mean(confidences):.3f}")
    print(f"   평균 Quality: {statistics.mean(qualities):.3f}")
    print(f"   Confidence 높은데 Quality 낮음: 예측 불일치")
    
    # 3. Evidence 문제
    evidence_failures = sum(1 for case in analysis if not case['evidence_ok'])
    print(f"\n📝 Evidence 문제")
    print(f"   evidence_ok=False: {evidence_failures}/{len(analysis)} ({evidence_failures/len(analysis)*100:.1f}%)")
    
    # 4. Recommendations 패턴
    all_recommendations = []
    for case in analysis:
        all_recommendations.extend(case['recommendations'])
    
    recommendation_counts = defaultdict(int)
    for rec in all_recommendations:
        recommendation_counts[rec] += 1
    
    print(f"\n💡 자주 등장하는 Recommendations (개선 포인트)")
    for rec, count in sorted(recommendation_counts.items(), key=lambda x: -x[1]):
        print(f"   '{rec}': {count}회 ({count/len(analysis)*100:.1f}%)")
    
    # 5. 개별 케이스 상세
    print(f"\n📋 개별 케이스 상세 (최근 3건)")
    for i, case in enumerate(analysis[-3:], 1):
        print(f"\n   Case {i}: {case['task_id'][:8]}...")
        print(f"      Quality: {case['first_quality']:.2f} (목표: {case['min_quality']:.2f}, 부족: {case['quality_gap']:.2f})")
        print(f"      Confidence: {case['confidence']:.2f}")
        print(f"      Evidence OK: {case['evidence_ok']}")
        print(f"      Recommendations: {', '.join(case['recommendations'][:2])}")
    
    # 6. 개선 방안 제시
    print(f"\n\n🎯 개선 방안 (우선순위)")
    print("=" * 80)
    
    avg_quality_gap = statistics.mean(quality_gaps)
    if avg_quality_gap > 0.15:
        print(f"1️⃣ CRITICAL: Quality Gap 너무 큼 ({avg_quality_gap:.3f})")
        print(f"   → min_quality 0.6 → 0.5로 완화 (또는 quality 평가 기준 개선)")
    
    if evidence_failures / len(analysis) > 0.5:
        print(f"2️⃣ HIGH: Evidence 검증 실패율 높음 ({evidence_failures/len(analysis)*100:.1f}%)")
        print(f"   → Prompt에 '구체적 근거 포함' 명시 강화")
    
    most_common_rec = max(recommendation_counts.items(), key=lambda x: x[1])[0] if recommendation_counts else None
    if most_common_rec:
        print(f"3️⃣ MEDIUM: 반복되는 추천 '{most_common_rec}'")
        print(f"   → Few-shot learning에 해당 패턴 추가")
    
    avg_confidence = statistics.mean(confidences)
    avg_quality = statistics.mean(qualities)
    if avg_confidence - avg_quality > 0.15:
        print(f"4️⃣ LOW: Confidence vs Quality 불일치 (conf={avg_confidence:.2f}, qual={avg_quality:.2f})")
        print(f"   → Meta-cognition calibration 필요")


def main():
    ledger_path = Path(__file__).parent.parent / "memory" / "resonance_ledger.jsonl"
    
    if not ledger_path.exists():
        print(f"❌ Ledger not found: {ledger_path}")
        return
    
    print(f"📂 Loading: {ledger_path}")
    events = load_ledger(ledger_path)
    print(f"   Total events: {len(events)}")
    
    # Analyze last 24 hours
    analysis = analyze_second_pass_causes(events, hours=24)
    print_analysis(analysis)
    
    # Export to JSON for dashboard
    output_path = Path(__file__).parent.parent / "outputs" / "second_pass_analysis.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'window_hours': 24,
            'total_cases': len(analysis),
            'cases': analysis,
            'summary': {
                'avg_quality_gap': statistics.mean([c['quality_gap'] for c in analysis]) if analysis else 0,
                'avg_confidence': statistics.mean([c['confidence'] for c in analysis]) if analysis else 0,
                'avg_quality': statistics.mean([c['first_quality'] for c in analysis]) if analysis else 0,
                'evidence_failure_rate': sum(1 for c in analysis if not c['evidence_ok']) / len(analysis) if analysis else 0,
                'recommendations': dict(defaultdict(int, {
                    rec: sum(1 for c in analysis for r in c['recommendations'] if r == rec)
                    for rec in set(r for c in analysis for r in c['recommendations'])
                }))
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analysis exported: {output_path}")


if __name__ == "__main__":
    main()
