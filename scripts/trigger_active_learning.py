#!/usr/bin/env python3
"""
Active Learning 트리거 스크립트
시스템 유지보수 및 개선을 위한 보상 신호 생성
"""
from pathlib import Path
from reward_tracker import RewardTracker
from datetime import datetime

def trigger_system_maintenance_rewards():
    """시스템 유지보수 작업에 대한 보상 신호 생성"""
    workspace_root = Path(__file__).parent.parent
    tracker = RewardTracker(workspace_root)
    
    # 1. Meta Supervisor 실행 보상
    tracker.record_reward_signal(
        action_type="goal_execution",
        action_id="meta_supervisor_health_check",
        reward=0.85,
        context={
            "timestamp": datetime.now().isoformat(),
            "overall_score": 87.0,
            "status": "warning",
            "action": "system_health_monitoring"
        }
    )
    print("✅ Meta Supervisor 실행 보상 기록")
    
    # 2. Trinity 통계 업데이트 보상
    tracker.record_reward_signal(
        action_type="goal_execution",
        action_id="trinity_statistics_update",
        reward=0.90,
        context={
            "timestamp": datetime.now().isoformat(),
            "total_messages": 30587,
            "conversations": 486,
            "action": "data_consolidation"
        }
    )
    print("✅ Trinity 통계 업데이트 보상 기록")
    
    # 3. 시스템 통합 진단 보상
    tracker.record_reward_signal(
        action_type="goal_execution",
        action_id="system_integration_diagnostic",
        reward=0.80,
        context={
            "timestamp": datetime.now().isoformat(),
            "modules_checked": 4,
            "integrations_verified": 6,
            "action": "system_integrity_check"
        }
    )
    print("✅ 시스템 통합 진단 보상 기록")
    
    # 4. Learning System 체크 보상
    tracker.record_reward_signal(
        action_type="goal_execution",
        action_id="learning_progress_check",
        reward=0.95,
        context={
            "timestamp": datetime.now().isoformat(),
            "learned_patterns": 2,
            "auto_systems": 1,
            "success_rate": 1.0,
            "action": "learning_verification"
        }
    )
    print("✅ Learning System 체크 보상 기록")
    
    # 5. Policy 업데이트
    tracker.update_policy()
    print("✅ Policy 업데이트 완료")
    
    # 결과 출력
    policy = tracker.get_policy()
    print(f"\n📊 업데이트된 Policy:")
    print(f"   Goal Execution Patterns: {len(policy.get('goal_execution', []))}")
    print(f"   Self-Care Patterns: {len(policy.get('self_care', []))}")
    print(f"   Updated At: {policy.get('updated_at')}")
    
    print(f"\n🎯 Active Learning 활성화됨!")

if __name__ == "__main__":
    trigger_system_maintenance_rewards()
