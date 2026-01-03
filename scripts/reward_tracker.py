#!/usr/bin/env python3
"""
Reward Tracker - 기저핵의 보상 신호 추적 기능

기존 시스템에 보상 학습을 추가하는 경량 모듈:
1. 목표 달성 시 보상 신호 기록
2. Self-care 개선 시 보상 신호 기록
3. 사용자 피드백 → 보상 신호 변환
4. 과거 행동의 성공률 추적
5. Goal Generator가 이 데이터를 읽어 우선순위 조정

생물학적 기저핵의 "도파민 보상 예측 오류" 개념을 단순화한 버전
"""
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict
from workspace_root import get_workspace_root

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RewardTracker:
    """행동-결과 보상 신호 추적"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.memory_dir = workspace_root / "fdo_agi_repo" / "memory"
        self.reward_log = self.memory_dir / "reward_signals.jsonl"
        self.policy_cache = self.memory_dir / "action_policy.json"
        
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def record_reward_signal(
        self,
        action_type: str,  # "goal_execution", "self_care", "user_feedback"
        action_id: str,
        reward: float,  # -1.0 ~ 1.0
        context: Dict[str, Any]
    ):
        """보상 신호 기록 (도파민 방출 모사)"""
        signal = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "action_id": action_id,
            "reward": reward,
            "context": context
        }
        
        with open(self.reward_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(signal, ensure_ascii=False) + "\n")
        
        logger.info(f"💰 Reward signal: {action_type}/{action_id} → {reward:+.2f}")
    
    def calculate_action_success_rate(
        self,
        action_type: str,
        lookback_hours: int = 168
    ) -> Dict[str, float]:
        """특정 행동 유형의 성공률 계산"""
        if not self.reward_log.exists():
            return {}
        
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        action_rewards = defaultdict(list)
        
        with open(self.reward_log, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                signal = json.loads(line)
                
                ts = datetime.fromisoformat(signal["timestamp"])
                if ts < cutoff:
                    continue
                
                if signal["action_type"] == action_type:
                    action_id = signal["action_id"]
                    reward = signal["reward"]
                    action_rewards[action_id].append(reward)
        
        # 평균 보상 계산
        success_rates = {}
        for action_id, rewards in action_rewards.items():
            avg_reward = sum(rewards) / len(rewards)
            success_rates[action_id] = avg_reward
        
        return success_rates
    
    def get_top_performing_actions(
        self,
        action_type: str,
        top_n: int = 5,
        lookback_hours: int = 168
    ) -> List[tuple]:
        """가장 성공적인 행동 패턴"""
        success_rates = self.calculate_action_success_rate(action_type, lookback_hours)
        
        sorted_actions = sorted(
            success_rates.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_actions[:top_n]
    
    def update_policy(self):
        """행동 정책 업데이트 (습관 강화)"""
        policy = {
            "goal_execution": self.get_top_performing_actions("goal_execution"),
            "self_care": self.get_top_performing_actions("self_care"),
            "updated_at": datetime.now().isoformat()
        }
        
        with open(self.policy_cache, "w", encoding="utf-8") as f:
            json.dump(policy, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Policy updated: {len(policy['goal_execution'])} goal patterns, "
                   f"{len(policy['self_care'])} self-care patterns")
    
    def get_policy(self) -> Dict:
        """현재 행동 정책 읽기"""
        if not self.policy_cache.exists():
            return {"goal_execution": [], "self_care": []}
        
        with open(self.policy_cache, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def calculate_goal_boost(self, goal_title: str) -> float:
        """목표에 대한 우선순위 부스트 계산 (습관 강화)"""
        policy = self.get_policy()
        
        for action_id, score in policy.get("goal_execution", []):
            if goal_title.lower() in action_id.lower():
                # 성공률이 높았던 목표는 우선순위 부스트
                return score * 0.3  # 최대 +0.3 부스트
        
        return 0.0


def demo_usage():
    """사용 예시"""
    workspace_root = get_workspace_root()
    tracker = RewardTracker(workspace_root)
    
    # 1. 목표 실행 후 보상 기록
    tracker.record_reward_signal(
        action_type="goal_execution",
        action_id="clean_outputs_dir",
        reward=0.8,  # 성공!
        context={"duration_seconds": 120, "files_cleaned": 45}
    )
    
    # 2. Self-care 행동 후 보상
    tracker.record_reward_signal(
        action_type="self_care",
        action_id="break_taken",
        reward=0.9,
        context={"break_duration_minutes": 15, "mood_improvement": "significant"}
    )
    
    # 3. 정책 업데이트
    tracker.update_policy()
    
    # 4. 목표 우선순위 부스트 계산
    boost = tracker.calculate_goal_boost("clean outputs")
    print(f"Priority boost for 'clean outputs': {boost:+.2f}")
    
    # 5. 가장 성공적인 패턴 확인
    top_goals = tracker.get_top_performing_actions("goal_execution", top_n=3)
    print("\n🏆 Top performing actions:")
    for action_id, score in top_goals:
        print(f"  {action_id}: {score:+.2f}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "update-policy":
        # CLI 모드: 정책 업데이트
        workspace_root = get_workspace_root()
        tracker = RewardTracker(workspace_root)
        
        tracker.update_policy()
        policy = tracker.get_policy()
        
        print(json.dumps({
            "goal_execution": dict(policy.get("goal_execution", [])),
            "self_care": dict(policy.get("self_care", [])),
            "updated_at": policy.get("updated_at")
        }, indent=2))
        
        sys.exit(0)
    else:
        # 데모 모드
        demo_usage()
