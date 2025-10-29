#!/usr/bin/env python3
"""
Replan 원인 분석 스크립트
Rune에서 replan=True가 발생한 케이스를 분석하여 개선 포인트 도출
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter
from typing import Dict, List, Any

# Repo root 경로 추가
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def load_ledger(ledger_path: Path) -> List[Dict[str, Any]]:
    """resonance_ledger.jsonl 로드"""
    events = []
    with open(ledger_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def analyze_replan_causes(events: List[Dict[str, Any]], hours: float = 24) -> Dict[str, Any]:
    """Replan 원인 분석"""
    
    # 시간 필터링 (UTC 기준, aware datetime)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Task별 이벤트 그룹핑
    task_events: Dict[str, List[Dict]] = {}
    for evt in events:
        # ts(Unix epoch) 우선 사용, 실패 시 ISO 문자열(timestamp) 사용
        evt_time = None
        ts_val = evt.get('ts')
        if isinstance(ts_val, (int, float)):
            try:
                # ts는 UTC epoch seconds로 가정
                evt_time = datetime.fromtimestamp(ts_val, tz=timezone.utc)
            except Exception:
                evt_time = None
        if evt_time is None:
            ts_str = evt.get('timestamp', '')
            if ts_str:
                try:
                    dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    evt_time = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                    evt_time = evt_time.astimezone(timezone.utc)
                except Exception:
                    evt_time = None
        # 컷오프 이전이면 스킵 (타임스탬프 없는 이벤트는 유지)
        if evt_time is not None and evt_time < cutoff:
            continue
        
        task_id = evt.get('task_id', '')
        if task_id:
            if task_id not in task_events:
                task_events[task_id] = []
            # 정렬을 위해 내부 시간 보관
            if evt_time is not None:
                evt['_evt_time'] = evt_time
            task_events[task_id].append(evt)
    
    # Replan 케이스 찾기
    replan_cases = []
    
    for task_id, task_evts in task_events.items():
        # 테스트 태스크 제외
        if any(prefix in task_id for prefix in ['integration_test_', 'low_confidence_test_', 'temp_low_conf_']):
            continue

        # 최신 이벤트 우선으로 정렬하여 최근 상태 반영
        task_evts_sorted = sorted(task_evts, key=lambda e: e.get('_evt_time', cutoff), reverse=True)
        # Rune 이벤트에서 replan=True 찾기
        for evt in task_evts_sorted:
            if evt.get('event') == 'rune' and evt.get('rune', {}).get('replan', False):
                # 해당 태스크의 eval, meta_cognition 정보 수집 (가장 최근 것을 선택)
                eval_evt = next((e for e in task_evts_sorted if e.get('event') == 'eval'), None)
                meta_evt = next((e for e in task_evts_sorted if e.get('event') == 'meta_cognition'), None)

                case = {
                    'task_id': task_id,
                    'replan': True,
                }

                # Eval 정보
                if eval_evt:
                    case['quality'] = eval_evt.get('quality')
                    # min_quality는 상위 및 eval 서브필드 모두에서 탐색
                    min_q = eval_evt.get('min_quality')
                    if min_q is None:
                        min_q = (eval_evt.get('eval') or {}).get('min_quality')
                    if min_q is None:
                        min_q = 0.6
                    case['min_quality'] = min_q
                    case['evidence_ok'] = eval_evt.get('evidence_ok')
                    if case['quality'] is not None and case['min_quality'] is not None:
                        case['quality_gap'] = case['min_quality'] - case['quality']

                # Meta-cognition 정보
                if meta_evt:
                    case['confidence'] = meta_evt.get('confidence')
                    case['past_performance'] = meta_evt.get('past_performance')

                # Rune 정보
                rune = evt.get('rune', {})
                case['rune_confidence'] = rune.get('confidence')
                case['recommendations'] = rune.get('recommendations', [])
                case['reasoning'] = rune.get('reasoning', '')

                replan_cases.append(case)
                break  # 한 task당 첫 replan만 기록
    
    # 통계 계산
    total_cases = len(replan_cases)
    
    if total_cases == 0:
        return {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'window_hours': hours,
            'total_cases': 0,
            'statistics': {
                'avg_quality_gap': 0,
                'median_quality_gap': 0,
                'avg_confidence': 0,
                'avg_quality': 0,
                'evidence_failure_rate': 0,
                'quality_failure_rate': 0,
            },
            'top_recommendations': {},
            'reasoning_keywords': {},
            'cases': [],
        }
    
    # Quality gap 통계
    quality_gaps = [c['quality_gap'] for c in replan_cases if 'quality_gap' in c]
    avg_quality_gap = sum(quality_gaps) / len(quality_gaps) if quality_gaps else 0
    # 중앙값 계산 (짝수 개수일 경우 중앙 두 값의 평균)
    if quality_gaps:
        q_sorted = sorted(quality_gaps)
        n = len(q_sorted)
        mid = n // 2
        if n % 2 == 1:
            median_quality_gap = q_sorted[mid]
        else:
            median_quality_gap = (q_sorted[mid - 1] + q_sorted[mid]) / 2
    else:
        median_quality_gap = 0
    
    # Evidence 문제
    evidence_issues = sum(1 for c in replan_cases if c.get('evidence_ok') == False)
    evidence_failure_rate = evidence_issues / total_cases if total_cases > 0 else 0
    
    # Quality 미달
    quality_failures = sum(1 for c in replan_cases if c.get('quality_gap', 0) > 0)
    quality_failure_rate = quality_failures / total_cases if total_cases > 0 else 0
    
    # Confidence 통계
    confidences = [c['confidence'] for c in replan_cases if 'confidence' in c]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    qualities = [c['quality'] for c in replan_cases if 'quality' in c]
    avg_quality = sum(qualities) / len(qualities) if qualities else 0
    
    # Recommendations 집계
    all_recs = []
    for c in replan_cases:
        all_recs.extend(c.get('recommendations', []))
    rec_counter = Counter(all_recs)
    
    # Reasoning 키워드 분석
    all_reasoning = ' '.join([c.get('reasoning', '') for c in replan_cases])
    reasoning_keywords = []
    for keyword in ['근거', '증거', '품질', '모호', '불명확', '부족', '미흡']:
        if keyword in all_reasoning:
            count = all_reasoning.count(keyword)
            reasoning_keywords.append((keyword, count))
    reasoning_keywords.sort(key=lambda x: x[1], reverse=True)
    
    return {
        'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'window_hours': hours,
        'total_cases': total_cases,
        'statistics': {
            'avg_quality_gap': avg_quality_gap,
            'median_quality_gap': median_quality_gap,
            'avg_confidence': avg_confidence,
            'avg_quality': avg_quality,
            'evidence_failure_rate': evidence_failure_rate,
            'quality_failure_rate': quality_failure_rate,
        },
        'top_recommendations': dict(rec_counter.most_common(5)),
        'reasoning_keywords': dict(reasoning_keywords[:5]),
        'cases': replan_cases,
    }


def print_analysis(analysis: Dict[str, Any]):
    """분석 결과 출력"""
    total = analysis['total_cases']
    stats = analysis['statistics']
    
    print(f"\n🔍 Replan 원인 분석 ({total} cases)")
    print("=" * 80)
    
    if total == 0:
        print("\n✅ Replan 케이스 없음 (최근 24시간)")
        return
    
    print(f"\n📊 Quality & Confidence")
    print(f"   평균 Quality: {stats['avg_quality']:.3f}")
    print(f"   평균 Confidence: {stats['avg_confidence']:.3f}")
    print(f"   평균 Quality Gap: {stats['avg_quality_gap']:.3f}")
    print(f"   중앙값 Quality Gap: {stats['median_quality_gap']:.3f}")
    
    print(f"\n📝 실패 원인 분석")
    print(f"   Evidence 문제: {int(stats['evidence_failure_rate'] * 100)}% ({int(stats['evidence_failure_rate'] * total)}/{total} cases)")
    print(f"   Quality 미달: {int(stats['quality_failure_rate'] * 100)}% ({int(stats['quality_failure_rate'] * total)}/{total} cases)")
    
    print(f"\n💡 자주 등장하는 Recommendations")
    for rec, count in analysis['top_recommendations'].items():
        pct = (count / total) * 100
        print(f"   '{rec}': {count}회 ({pct:.1f}%)")
    
    print(f"\n🔑 Reasoning 키워드 분석")
    for keyword, count in analysis['reasoning_keywords'].items():
        print(f"   '{keyword}': {count}회")
    
    print(f"\n📋 개별 케이스 상세 (최근 3건)")
    for i, case in enumerate(analysis['cases'][-3:], 1):
        print(f"\n   Case {i}: {case['task_id'][:8]}...")
        if 'quality' in case:
            print(f"      Quality: {case['quality']:.2f} (목표: {case['min_quality']:.2f}, 부족: {case.get('quality_gap', 0):.2f})")
        if 'confidence' in case:
            print(f"      Confidence: {case['confidence']:.2f}")
        if 'evidence_ok' in case:
            print(f"      Evidence OK: {case['evidence_ok']}")
        if case.get('recommendations'):
            print(f"      Recommendations: {', '.join(case['recommendations'])}")
    
    print(f"\n\n🎯 개선 방안 (우선순위)")
    print("=" * 80)
    
    priorities = []
    
    if stats['quality_failure_rate'] > 0.5:
        priorities.append(f"1️⃣ CRITICAL: Quality 미달 비율 높음 ({int(stats['quality_failure_rate']*100)}%)")
        priorities.append(f"   → P2.1 프롬프트 개선 효과 확인 (근거 강화)")
    
    if stats['evidence_failure_rate'] > 0.5:
        priorities.append(f"2️⃣ HIGH: Evidence 검증 실패율 높음 ({int(stats['evidence_failure_rate']*100)}%)")
        priorities.append(f"   → P2.1과 연계, 프롬프트 개선 효과 24h 후 재측정")
    
    if stats['avg_quality_gap'] > 0.15:
        priorities.append(f"3️⃣ MEDIUM: Quality Gap 큼 ({stats['avg_quality_gap']:.3f})")
        priorities.append(f"   → min_quality 조정 또는 평가 기준 완화 고려")
    
    if analysis['top_recommendations']:
        top_rec = list(analysis['top_recommendations'].keys())[0]
        priorities.append(f"4️⃣ LOW: 반복되는 추천 '{top_rec}'")
        priorities.append(f"   → Few-shot learning에 해당 패턴 추가")
    
    if not priorities:
        priorities.append("✅ 주요 문제점 없음, 모니터링 지속")
    
    for p in priorities:
        print(p)


def main():
    """메인 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Replan 원인 분석')
    parser.add_argument('--hours', type=float, default=24, help='분석 시간 범위 (기본: 24시간)')
    args = parser.parse_args()
    
    # 레저 파일 로드
    ledger_path = repo_root / "memory" / "resonance_ledger.jsonl"
    
    if not ledger_path.exists():
        print(f"❌ Error: {ledger_path} not found")
        sys.exit(1)
    
    print(f"📂 Loading: {ledger_path}")
    events = load_ledger(ledger_path)
    print(f"   Total events: {len(events)}")
    
    # 분석 실행
    analysis = analyze_replan_causes(events, hours=args.hours)
    
    # 결과 출력
    print_analysis(analysis)
    
    # JSON 출력
    output_path = repo_root / "outputs" / "replan_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analysis exported: {output_path}")


if __name__ == '__main__':
    main()
