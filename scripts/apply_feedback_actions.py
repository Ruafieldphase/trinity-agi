#!/usr/bin/env python3
"""
Feedback Action Applicator

Feedback 분석 결과를 기반으로 자동 개선 조치 실행.
완전한 자율 순환 시스템의 피드백 루프 완성.

Usage:
    python apply_feedback_actions.py
    python apply_feedback_actions.py --dry-run
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from workspace_root import get_workspace_root

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

WORKSPACE_ROOT = get_workspace_root()
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"


def load_feedback_analysis() -> Dict[str, Any]:
    """최신 Feedback 분석 로드"""
    feedback_path = OUTPUTS_DIR / "feedback_analysis_latest.json"
    
    if not feedback_path.exists():
        raise FileNotFoundError(f"Feedback 분석 없음: {feedback_path}")
    
    with open(feedback_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Feedback 분석 로드: 점수={data.get('feedback_score', 0):.1f}")
    return data


def generate_self_care_actions(
    feedback: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Self-Care 개선 액션 생성"""
    actions = []
    score = feedback.get('feedback_score', 0.0)
    
    self_care = feedback.get('self_care_summary')
    if not self_care:
        return actions
    
    quantum = self_care.get('quantum_flow', {})
    coherence = quantum.get('coherence', 0.0)
    
    # Coherence 기반 액션
    if coherence < 0.5:
        actions.append({
            'type': 'self_care',
            'priority': 'high',
            'action': 'force_break',
            'description': '강제 휴식 필요 (Coherence < 0.5)',
            'duration_minutes': 15,
            'reason': f'현재 Coherence: {coherence:.2f}'
        })
    elif coherence < 0.7:
        actions.append({
            'type': 'self_care',
            'priority': 'medium',
            'action': 'suggest_break',
            'description': '휴식 권장 (Coherence < 0.7)',
            'duration_minutes': 10,
            'reason': f'현재 Coherence: {coherence:.2f}'
        })
    
    # Stagnation 기반
    telemetry = self_care.get('telemetry', {})
    avg_stagnation = telemetry.get('avg_stagnation', 0.0)
    
    if avg_stagnation > 0.5:
        actions.append({
            'type': 'goal_generation',
            'priority': 'high',
            'action': 'regenerate_goals',
            'description': '새로운 Goal 생성 필요 (높은 Stagnation)',
            'reason': f'평균 Stagnation: {avg_stagnation:.2f}'
        })
    
    # Goal 성공률 기반
    goal_analysis = feedback.get('goal_analysis', {})
    success_rate = goal_analysis.get('success_rate', 0.0)
    
    if success_rate < 50.0:
        actions.append({
            'type': 'goal_strategy',
            'priority': 'high',
            'action': 'adjust_difficulty',
            'description': 'Goal 난이도 조정 필요',
            'reason': f'성공률: {success_rate:.1f}%',
            'suggestion': '더 작고 달성 가능한 Goal로 조정'
        })
    
    # Resonance 개입 기반
    resonance = feedback.get('resonance_analysis', {})
    total_events = resonance.get('total_events', 0)
    interventions = resonance.get('intervention_count', 0)
    
    if total_events > 0:
        intervention_ratio = interventions / total_events
        if intervention_ratio > 0.3:
            actions.append({
                'type': 'resonance_policy',
                'priority': 'high',
                'action': 'adjust_policy',
                'description': 'Resonance Policy 조정 필요',
                'reason': f'개입 비율: {intervention_ratio:.1%}',
                'suggestion': '더 관대한 Policy로 전환'
            })
    
    return actions


def apply_actions(
    actions: List[Dict[str, Any]],
    dry_run: bool = False
) -> Dict[str, Any]:
    """액션 실행"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'dry_run': dry_run,
        'actions_executed': [],
        'actions_failed': []
    }
    
    for action in actions:
        action_type = action['type']
        action_name = action['action']
        
        logger.info(f"{'[DRY-RUN] ' if dry_run else ''}실행: {action_type}.{action_name}")
        
        if dry_run:
            results['actions_executed'].append({
                'action': action,
                'status': 'simulated',
                'message': 'Dry-run 모드'
            })
            continue
        
        try:
            # 실제 액션 실행 (향후 구현)
            if action_name == 'force_break':
                # TODO: 실제 Break 알림 구현
                logger.info(f"⏸️  Break 알림: {action['duration_minutes']}분")
            elif action_name == 'regenerate_goals':
                # TODO: Goal 재생성 트리거
                logger.info("🎯 Goal 재생성 예약")
            elif action_name == 'adjust_difficulty':
                # TODO: Goal 난이도 조정
                logger.info("📊 Goal 난이도 조정 권장")
            elif action_name == 'adjust_policy':
                # TODO: Resonance Policy 조정
                logger.info("🌊 Resonance Policy 조정 권장")
            
            results['actions_executed'].append({
                'action': action,
                'status': 'success',
                'message': '실행 완료'
            })
        except Exception as e:
            logger.error(f"액션 실패: {e}")
            results['actions_failed'].append({
                'action': action,
                'error': str(e)
            })
    
    return results


def save_action_results(
    results: Dict[str, Any],
    output_path: Path
):
    """액션 결과 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ 액션 결과 저장: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Apply Feedback Actions")
    parser.add_argument('--dry-run', action='store_true', help="시뮬레이션만 수행")
    
    args = parser.parse_args()
    
    logger.info("🔄 Feedback 액션 적용 시작")
    
    try:
        # Feedback 분석 로드
        feedback = load_feedback_analysis()
        
        # 액션 생성
        actions = generate_self_care_actions(feedback)
        
        if not actions:
            logger.info("✅ 필요한 액션 없음 - 시스템 정상")
            print("\n✅ 시스템이 정상적으로 작동 중입니다.")
            return 0
        
        logger.info(f"📋 생성된 액션: {len(actions)}개")
        
        # 액션 실행
        results = apply_actions(actions, dry_run=args.dry_run)
        
        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = OUTPUTS_DIR / f"feedback_actions_{timestamp}.json"
        save_action_results(results, output_path)
        
        # 콘솔 출력
        print(f"\n🔄 Feedback 액션 {'시뮬레이션' if args.dry_run else '적용'} 완료")
        print(f"실행: {len(results['actions_executed'])}개")
        print(f"실패: {len(results['actions_failed'])}개")
        
        if actions:
            print("\n📋 주요 액션:")
            for action in actions[:3]:
                priority_emoji = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(action.get('priority', 'low'), '⚪')
                
                print(f"  {priority_emoji} {action['description']}")
        
        return 0
    
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        print(f"\n❌ 오류: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
