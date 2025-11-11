#!/usr/bin/env python3
"""
Feedback Loop Analysis Script

Goal Execution 결과를 분석하고 Self-Care로 피드백합니다.
완전한 자율 순환 시스템의 마지막 연결고리.

Usage:
    python analyze_feedback.py --hours 24
    python analyze_feedback.py --hours 168 --output outputs/feedback_weekly.json
"""

import argparse
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

WORKSPACE_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
FDO_OUTPUTS_DIR = WORKSPACE_ROOT / "fdo_agi_repo" / "outputs"
MEMORY_DIR = WORKSPACE_ROOT / "fdo_agi_repo" / "memory"


def load_goal_tracker() -> Optional[Dict[str, Any]]:
    """Goal Tracker 로드"""
    tracker_path = MEMORY_DIR / "goal_tracker.json"
    
    if not tracker_path.exists():
        logger.warning(f"Goal Tracker 없음: {tracker_path}")
        return None
    
    try:
        with open(tracker_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Goal Tracker 로드 완료: {len(data.get('goals', []))} goals")
        return data
    except Exception as e:
        logger.error(f"Goal Tracker 로드 실패: {e}")
        return None


def load_resonance_ledger(hours: int) -> List[Dict[str, Any]]:
    """Resonance Ledger에서 최근 이벤트 로드"""
    ledger_path = MEMORY_DIR / "resonance_ledger.jsonl"
    
    if not ledger_path.exists():
        logger.warning(f"Resonance Ledger 없음: {ledger_path}")
        return []
    
    cutoff = datetime.now() - timedelta(hours=hours)
    events = []
    
    try:
        with open(ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    event = json.loads(line)
                    event_time = datetime.fromisoformat(event.get('timestamp', ''))
                    
                    if event_time >= cutoff:
                        events.append(event)
                except Exception as e:
                    logger.debug(f"Ledger 파싱 실패: {e}")
                    continue
        
        logger.info(f"Resonance Ledger: {len(events)} events (last {hours}h)")
        return events
    except Exception as e:
        logger.error(f"Resonance Ledger 로드 실패: {e}")
        return []


def load_self_care_summary() -> Optional[Dict[str, Any]]:
    """Self-Care 메트릭 요약 로드"""
    summary_path = OUTPUTS_DIR / "self_care_metrics_summary.json"
    
    if not summary_path.exists():
        logger.warning(f"Self-Care 요약 없음: {summary_path}")
        return None
    
    try:
        with open(summary_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("Self-Care 요약 로드 완료")
        return data
    except Exception as e:
        logger.error(f"Self-Care 요약 로드 실패: {e}")
        return None


def analyze_goal_success(tracker: Dict[str, Any]) -> Dict[str, Any]:
    """Goal 성공률 분석"""
    goals = tracker.get('goals', [])
    
    if not goals:
        return {
            'total': 0,
            'completed': 0,
            'in_progress': 0,
            'not_started': 0,
            'success_rate': 0.0
        }
    
    completed = sum(1 for g in goals if g.get('status') == 'completed')
    in_progress = sum(1 for g in goals if g.get('status') == 'in_progress')
    not_started = sum(1 for g in goals if g.get('status') == 'not_started')
    
    success_rate = (completed / len(goals)) * 100 if goals else 0.0
    
    return {
        'total': len(goals),
        'completed': completed,
        'in_progress': in_progress,
        'not_started': not_started,
        'success_rate': success_rate
    }


def analyze_resonance_patterns(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resonance 패턴 분석"""
    if not events:
        return {
            'total_events': 0,
            'policy_distribution': {},
            'intervention_count': 0,
            'avg_score': 0.0
        }
    
    policy_counts = {}
    intervention_count = 0
    scores = []
    
    for event in events:
        policy = event.get('policy', 'unknown')
        policy_counts[policy] = policy_counts.get(policy, 0) + 1
        
        if event.get('intervention_needed'):
            intervention_count += 1
        
        score = event.get('score')
        if score is not None:
            scores.append(score)
    
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    return {
        'total_events': len(events),
        'policy_distribution': policy_counts,
        'intervention_count': intervention_count,
        'avg_score': avg_score
    }


def calculate_feedback_score(
    goal_analysis: Dict[str, Any],
    resonance_analysis: Dict[str, Any],
    self_care: Optional[Dict[str, Any]]
) -> float:
    """종합 피드백 점수 계산 (0-100)"""
    
    # Goal 성공률 (40%)
    goal_score = goal_analysis.get('success_rate', 0.0) * 0.4
    
    # Resonance 안정성 (30%)
    resonance_score = 0.0
    if resonance_analysis.get('total_events', 0) > 0:
        intervention_ratio = resonance_analysis.get('intervention_count', 0) / resonance_analysis['total_events']
        # 개입이 적을수록 좋음
        resonance_score = (1.0 - intervention_ratio) * 30.0
    
    # Self-Care 건강도 (30%)
    self_care_score = 0.0
    if self_care:
        quantum_state = self_care.get('quantum_flow', {})
        coherence = quantum_state.get('coherence', 0.0)
        self_care_score = coherence * 30.0
    
    total_score = goal_score + resonance_score + self_care_score
    return min(100.0, max(0.0, total_score))


def generate_recommendations(
    feedback_score: float,
    goal_analysis: Dict[str, Any],
    resonance_analysis: Dict[str, Any],
    self_care: Optional[Dict[str, Any]]
) -> List[str]:
    """개선 권장사항 생성"""
    recommendations = []
    
    # Goal 성공률 기반
    success_rate = goal_analysis.get('success_rate', 0.0)
    if success_rate < 50.0:
        recommendations.append("🎯 Goal 성공률이 낮습니다. Goal Generation 전략 재검토 필요")
    elif success_rate < 70.0:
        recommendations.append("📈 Goal 성공률 개선 여지가 있습니다")
    
    # Resonance 개입 기반
    intervention_ratio = 0.0
    if resonance_analysis.get('total_events', 0) > 0:
        intervention_ratio = resonance_analysis.get('intervention_count', 0) / resonance_analysis['total_events']
    
    if intervention_ratio > 0.3:
        recommendations.append("🚨 Resonance 개입이 빈번합니다. Policy 조정 권장")
    elif intervention_ratio > 0.1:
        recommendations.append("⚠️  Resonance 개입이 다소 많습니다")
    
    # Self-Care 기반
    if self_care:
        coherence = self_care.get('quantum_flow', {}).get('coherence', 0.0)
        if coherence < 0.5:
            recommendations.append("🛟 Self-Care 개선 필요: 휴식, 수면, 운동 점검")
        elif coherence < 0.7:
            recommendations.append("💪 Self-Care 상태 양호, 유지 권장")
    
    # 전체 점수 기반
    if feedback_score >= 80.0:
        recommendations.append("✅ 시스템이 매우 잘 작동하고 있습니다!")
    elif feedback_score >= 60.0:
        recommendations.append("👍 시스템이 안정적으로 작동 중입니다")
    elif feedback_score >= 40.0:
        recommendations.append("🔧 시스템 개선이 필요합니다")
    else:
        recommendations.append("🚨 시스템 긴급 점검 필요!")
    
    return recommendations


def save_feedback_analysis(
    analysis: Dict[str, Any],
    output_path: Path
):
    """피드백 분석 결과 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # JSON 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ 피드백 분석 저장: {output_path}")
    
    # Markdown 보고서 생성
    md_path = output_path.with_suffix('.md')
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# 피드백 루프 분석 보고서\n\n")
        f.write(f"생성 시각: {analysis['timestamp']}\n")
        f.write(f"분석 기간: 최근 {analysis['hours']}시간\n\n")
        
        f.write("## 📊 종합 점수\n\n")
        score = analysis['feedback_score']
        if score >= 80:
            emoji = "🟢"
        elif score >= 60:
            emoji = "🟡"
        elif score >= 40:
            emoji = "🟠"
        else:
            emoji = "🔴"
        
        f.write(f"{emoji} **{score:.1f}/100**\n\n")
        
        f.write("## 🎯 Goal 분석\n\n")
        goal = analysis['goal_analysis']
        f.write(f"- 전체 Goals: {goal['total']}\n")
        f.write(f"- 완료: {goal['completed']}\n")
        f.write(f"- 진행 중: {goal['in_progress']}\n")
        f.write(f"- 미시작: {goal['not_started']}\n")
        f.write(f"- **성공률: {goal['success_rate']:.1f}%**\n\n")
        
        f.write("## 🌊 Resonance 패턴\n\n")
        res = analysis['resonance_analysis']
        f.write(f"- 전체 이벤트: {res['total_events']}\n")
        f.write(f"- 개입 횟수: {res['intervention_count']}\n")
        f.write(f"- 평균 점수: {res['avg_score']:.1f}\n\n")
        
        if res['policy_distribution']:
            f.write("### Policy 분포\n\n")
            for policy, count in res['policy_distribution'].items():
                f.write(f"- {policy}: {count}\n")
            f.write("\n")
        
        f.write("## 💡 권장사항\n\n")
        for rec in analysis['recommendations']:
            f.write(f"- {rec}\n")
        
        f.write("\n---\n\n")
        f.write("*이 보고서는 Feedback Loop 시스템에 의해 자동 생성되었습니다.*\n")
    
    logger.info(f"📄 Markdown 보고서 생성: {md_path}")
    
    # Latest 심볼릭 링크 생성
    latest_json = output_path.parent / "feedback_analysis_latest.json"
    latest_md = output_path.parent / "feedback_analysis_latest.md"
    
    try:
        if latest_json.exists():
            latest_json.unlink()
        latest_json.write_text(output_path.read_text(encoding='utf-8'), encoding='utf-8')
        
        if latest_md.exists():
            latest_md.unlink()
        latest_md.write_text(md_path.read_text(encoding='utf-8'), encoding='utf-8')
        
        logger.info("✅ Latest 링크 업데이트 완료")
    except Exception as e:
        logger.warning(f"Latest 링크 생성 실패: {e}")


def main():
    parser = argparse.ArgumentParser(description="Feedback Loop Analysis")
    parser.add_argument('--hours', type=int, default=24, help="분석 기간 (시간)")
    parser.add_argument('--output', type=str, help="출력 파일 경로")
    
    args = parser.parse_args()
    
    logger.info(f"🔄 피드백 분석 시작 (최근 {args.hours}시간)")
    
    # 데이터 로드
    tracker = load_goal_tracker()
    events = load_resonance_ledger(args.hours)
    self_care = load_self_care_summary()
    
    # 분석 수행
    goal_analysis = analyze_goal_success(tracker) if tracker else {}
    resonance_analysis = analyze_resonance_patterns(events)
    
    # 피드백 점수 계산
    feedback_score = calculate_feedback_score(
        goal_analysis,
        resonance_analysis,
        self_care
    )
    
    # 권장사항 생성
    recommendations = generate_recommendations(
        feedback_score,
        goal_analysis,
        resonance_analysis,
        self_care
    )
    
    # 결과 정리
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'hours': args.hours,
        'feedback_score': feedback_score,
        'goal_analysis': goal_analysis,
        'resonance_analysis': resonance_analysis,
        'self_care_summary': self_care,
        'recommendations': recommendations
    }
    
    # 출력 경로 결정
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = OUTPUTS_DIR / f"feedback_analysis_{timestamp}.json"
    
    # 저장
    save_feedback_analysis(analysis, output_path)
    
    # 콘솔 출력
    print(f"\n📊 피드백 분석 완료")
    print(f"점수: {feedback_score:.1f}/100")
    print(f"\n💡 주요 권장사항:")
    for rec in recommendations[:3]:
        print(f"  {rec}")
    print(f"\n📄 보고서: {output_path.with_suffix('.md')}")
    
    # Exit code로 상태 전달
    if feedback_score >= 60:
        return 0  # 정상
    elif feedback_score >= 40:
        return 1  # 경고
    else:
        return 2  # 위험


if __name__ == '__main__':
    exit(main())
