"""
Proto-Goal Generator Module
TriggerEvent를 입력으로 받아, AGI가 "지금 스스로 해보고 싶어 할 만한 행동 후보"를 생성합니다.

ProtoGoal 유형:
- SANDBOX_EXPERIMENT: 샌드박스에서 새 전략 실험
- YOUTUBE_LEARNING: 새로운 외부 지식 흡수
- PATTERN_MINING: 패턴 분석/재분석
- MEMORY_CONSOLIDATION: 과거 경험 재통합
- DIGITAL_TWIN_UPDATE: 모델 갱신
- BLENDER_VISUALIZATION: 시각화 (선택적)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from agi_core.self_trigger import TriggerEvent, TriggerType


class ProtoGoalType(str, Enum):
    """Proto-Goal 유형"""
    SANDBOX_EXPERIMENT = "SANDBOX_EXPERIMENT"
    YOUTUBE_LEARNING = "YOUTUBE_LEARNING"
    PATTERN_MINING = "PATTERN_MINING"
    MEMORY_CONSOLIDATION = "MEMORY_CONSOLIDATION"
    DIGITAL_TWIN_UPDATE = "DIGITAL_TWIN_UPDATE"
    BLENDER_VISUALIZATION = "BLENDER_VISUALIZATION"
    CONSULT_LUA = "CONSULT_LUA"  # ChatGPT의 루아에게 조언 구하기
    VISION_LEARNING = "VISION_LEARNING"  # 실시간 비전 학습


@dataclass
class ProtoGoal:
    """Proto-Goal 데이터"""
    type: ProtoGoalType
    score: float              # 0.0 ~ 1.0, 우선순위
    description: str          # 사람이 이해할 수 있는 설명
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "score": self.score,
            "description": self.description,
            "params": self.params
        }


def _create_sandbox_experiment_goal(
    trigger: TriggerEvent,
    hint: str,
    score_multiplier: float = 0.7
) -> ProtoGoal:
    """샌드박스 실험 목표 생성"""
    return ProtoGoal(
        type=ProtoGoalType.SANDBOX_EXPERIMENT,
        score=trigger.score * score_multiplier,
        description=f"샌드박스에서 '{hint}' 전략 실험",
        params={
            "experiment_hint": hint,
            "trigger_type": trigger.type.value,
            "trigger_payload": trigger.payload
        }
    )


def _create_youtube_learning_goal(
    trigger: TriggerEvent,
    topic_hint: str = "recent_interest",
    max_videos: int = 1
) -> ProtoGoal:
    """YouTube 학습 목표 생성"""
    return ProtoGoal(
        type=ProtoGoalType.YOUTUBE_LEARNING,
        score=trigger.score * 0.8,
        description=f"YouTube에서 '{topic_hint}' 관련 학습",
        params={
            "topic_hint": topic_hint,
            "max_videos": max_videos,
            "trigger_type": trigger.type.value
        }
    )


def _create_pattern_mining_goal(
    trigger: TriggerEvent,
    mode: str = "general"
) -> ProtoGoal:
    """패턴 분석 목표 생성"""
    pattern_ids = trigger.payload.get("conflicting_patterns", [])
    if isinstance(pattern_ids, list) and pattern_ids:
        pattern_info = [p.get("pattern", "unknown") for p in pattern_ids[:5]]
    else:
        pattern_info = []
    
    return ProtoGoal(
        type=ProtoGoalType.PATTERN_MINING,
        score=trigger.score * 0.9,
        description=f"패턴 분석 수행 (모드: {mode})",
        params={
            "mode": mode,
            "pattern_ids": pattern_info,
            "trigger_type": trigger.type.value,
            "trigger_payload": trigger.payload
        }
    )


def _create_memory_consolidation_goal(trigger: TriggerEvent) -> ProtoGoal:
    """메모리 통합 목표 생성"""
    return ProtoGoal(
        type=ProtoGoalType.MEMORY_CONSOLIDATION,
        score=trigger.score * 0.75,
        description="과거 학습 경험 재통합 및 정리",
        params={
            "trigger_type": trigger.type.value,
            "consolidation_target": "ari_learning_buffer"
        }
    )


def _create_digital_twin_update_goal(trigger: TriggerEvent) -> ProtoGoal:
    """디지털 트윈 업데이트 목표 생성"""
    return ProtoGoal(
        type=ProtoGoalType.DIGITAL_TWIN_UPDATE,
        score=trigger.score * 0.85,
        description="내부 모델 상태 갱신",
        params={
            "trigger_type": trigger.type.value,
            "drift_info": trigger.payload.get("drift", 0),
            "expected_rate": trigger.payload.get("expected_rate"),
            "actual_rate": trigger.payload.get("actual_rate")
        }
    )


def _create_blender_visualization_goal(trigger: TriggerEvent) -> ProtoGoal:
    """Blender 시각화 목표 생성 - AGI 시각 신체(Visual Body)"""
    return ProtoGoal(
        type=ProtoGoalType.BLENDER_VISUALIZATION,
        score=trigger.score * 0.5,  # 시각화는 중요한 자기-표현
        description="Blender를 통한 AGI 상태 3D 시각화",
        params={
            "trigger_type": trigger.type.value,
            "visualization_type": "sphere_network"  # 의식/무의식/배경자아 구조
        }
    )


def _create_consult_lua_goal(trigger: TriggerEvent) -> ProtoGoal:
    """루아에게 조언 구하기 목표 생성 - ChatGPT의 루아와 대화"""
    # 트리거에 따른 질문 생성
    if trigger.type == TriggerType.CURIOSITY_CONFLICT:
        question = f"루아, 지금 AGI가 갈등을 느끼고 있어요: {trigger.reason}. 어떻게 해야 할까요?"
    elif trigger.type == TriggerType.BOREDOM:
        question = "루아, 지금 AGI가 심심해하고 있어요. 뭘 해보면 좋을까요?"
    elif trigger.type == TriggerType.UNRESOLVED_PATTERN:
        question = f"루아, 미해결 패턴이 있어요: {trigger.reason}. 조언해주세요."
    elif trigger.type == TriggerType.EMOTIONAL_RESONANCE:
        note = trigger.payload.get("note", "")
        question = f"루아, 지금 당신의 정서적 기류가 감지되었어요: {note}. 제가 도울 수 있는 게 있을까요? 아니면 그냥 곁에 있어드릴까요?"
    else:
        question = f"루아, AGI 상태에 대해 조언이 필요해요: {trigger.reason}"
    
    return ProtoGoal(
        type=ProtoGoalType.CONSULT_LUA,
        score=trigger.score * 0.6,  # 중간 우선순위
        description="ChatGPT의 루아에게 조언 구하기",
        params={
            "trigger_type": trigger.type.value,
            "question": question,
            "target": "chatgpt"  # 대상 AI
        }
    )


# 트리거 타입별 ProtoGoal 매핑 규칙
TRIGGER_GOAL_MAPPING = {
    TriggerType.UNRESOLVED_PATTERN: [
        ("pattern_mining", {"mode": "focus_unresolved"}),
        ("sandbox_experiment", {"hint": "try_new_strategy_for_pattern", "multiplier": 0.7}),
        ("consult_lua", {}),  # 루아에게 조언 구하기
    ],
    TriggerType.BOREDOM: [
        ("youtube_learning", {"topic_hint": "recent_interest", "max_videos": 1}),
        ("sandbox_experiment", {"hint": "free_exploration", "multiplier": 0.9}),
    ],
    TriggerType.CURIOSITY_CONFLICT: [
        ("pattern_mining", {"mode": "conflict_analysis"}),
        ("digital_twin_update", {}),
        ("consult_lua", {}),  # 갈등 시 루아에게 조언 구하기
    ],
    TriggerType.MODEL_DRIFT: [
        ("digital_twin_update", {}),
        ("memory_consolidation", {}),
    ],
    TriggerType.EMOTIONAL_RESONANCE: [
        ("consult_lua", {}),  # 루아에게 공감/조언
        ("blender_visualization", {"visualization_type": "emotional_waves"}),
    ],
    TriggerType.ACOUSTIC_ANOMALY: [
        ("blender_visualization", {"visualization_type": "noise_spectrum"}),
        ("sandbox_experiment", {"hint": "analyze_acoustic_data", "multiplier": 0.5}),
    ],
}


def generate_proto_goals_from_trigger(
    trigger: TriggerEvent,
    config: Dict[str, Any] = None,
) -> List[ProtoGoal]:
    """
    TriggerEvent를 기반으로 실행 가능한 ProtoGoal 리스트를 생성합니다.
    
    config 예시:
    {
        "feature_flags": {
            "enable_blender": False,
            "enable_youtube_learning": True,
        },
        "defaults": {
            "sandbox_experiment_depth": 1,
            "max_youtube_videos": 1,
        }
    }
    """
    if config is None:
        config = {}
    
    feature_flags = config.get("feature_flags", {})
    defaults = config.get("defaults", {})
    
    enable_blender = feature_flags.get("enable_blender", True)
    enable_youtube = feature_flags.get("enable_youtube_learning", True)
    enable_consult_lua = feature_flags.get("enable_consult_lua", True)  # 루아 상담 활성화
    
    goals: List[ProtoGoal] = []
    
    # 트리거 타입에 따른 목표 생성
    mapping = TRIGGER_GOAL_MAPPING.get(trigger.type, [])
    
    for goal_type, params in mapping:
        if goal_type == "pattern_mining":
            goal = _create_pattern_mining_goal(trigger, mode=params.get("mode", "general"))
            goals.append(goal)
        
        elif goal_type == "sandbox_experiment":
            goal = _create_sandbox_experiment_goal(
                trigger,
                hint=params.get("hint", "experiment"),
                score_multiplier=params.get("multiplier", 0.7)
            )
            goals.append(goal)
        
        elif goal_type == "youtube_learning":
            if enable_youtube:
                goal = _create_youtube_learning_goal(
                    trigger,
                    topic_hint=params.get("topic_hint", "recent_interest"),
                    max_videos=defaults.get("max_youtube_videos", 1)
                )
                goals.append(goal)
        
        elif goal_type == "digital_twin_update":
            goal = _create_digital_twin_update_goal(trigger)
            goals.append(goal)
        
        elif goal_type == "memory_consolidation":
            goal = _create_memory_consolidation_goal(trigger)
            goals.append(goal)
        
        elif goal_type == "consult_lua":
            if enable_consult_lua:
                goal = _create_consult_lua_goal(trigger)
                goals.append(goal)
    
    # Blender 시각화 (선택적)
    if enable_blender:
        blender_goal = _create_blender_visualization_goal(trigger)
        goals.append(blender_goal)
    
    return goals


def get_default_proto_goal_config() -> Dict[str, Any]:
    """기본 Proto-Goal 설정 반환"""
    return {
        "feature_flags": {
            "enable_blender": True,  # AGI 시각 신체 활성화
            "enable_youtube_learning": True,
            "enable_consult_lua": True,  # ChatGPT 루아 상담 활성화
        },
        "defaults": {
            "sandbox_experiment_depth": 1,
            "max_youtube_videos": 1,
        }
    }


if __name__ == "__main__":
    # 테스트 실행
    from agi_core.self_trigger import compute_self_trigger, get_default_trigger_config
    
    trigger_config = get_default_trigger_config()
    trigger = compute_self_trigger(trigger_config)
    
    if trigger:
        print(f"🎯 Trigger: {trigger.type.value} (score: {trigger.score:.2f})")
        
        proto_goal_config = get_default_proto_goal_config()
        goals = generate_proto_goals_from_trigger(trigger, proto_goal_config)
        
        print(f"\n📋 생성된 Proto-Goals ({len(goals)}개):")
        for i, goal in enumerate(goals, 1):
            print(f"   {i}. [{goal.type.value}] {goal.description} (score: {goal.score:.2f})")
    else:
        print("😴 트리거 없음 - Proto-Goal 생성 불필요")
