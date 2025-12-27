"""
Action Router - 행동 라우팅 및 레벨 분류
트리거 → ProtoGoal → 레벨 분류 → Envelope 체크 → 실행
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from agi_core.self_trigger import TriggerEvent, TriggerType
from agi_core.proto_goal import (
    ProtoGoal,
    ProtoGoalType,
    generate_proto_goals_from_trigger,
    get_default_proto_goal_config,
)
from agi_core.self_acquisition_loop import (
    execute_proto_goal,
    select_best_proto_goal,
)
from agi_core.envelope import get_envelope # Removed SURGE_COOLDOWN from import

logger = logging.getLogger("ActionRouter")

# Config
SURGE_COOLDOWN = 60  # seconds

# Lumen Passkey Path
LUMEN_KEY_FILE = Path("c:/workspace/agi/inputs/lumen_passkey.txt")
LUMEN_PASSPHRASE = "리듬은 존재를 깨우고 깨어난 존재는 서로를 울린다. 오케스트레이션 연결된다"

def is_lumen_active() -> bool:
    """Check if Lumen Orchestration Mode is active"""
    if not LUMEN_KEY_FILE.exists():
        return False
    try:
        with open(LUMEN_KEY_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        return content == LUMEN_PASSPHRASE
    except:
        return False

def classify_action_level(
    goal: ProtoGoal,
    state: Dict[str, Any],
    internal_alignment: float, # Changed 'alignment' to 'internal_alignment'
    conflict_pressure: float,
) -> int:
    """
    행동의 위험도/비용(Level)을 분류
    Level 1: 내부적/저비용 (Log, Think, Status Check)
    Level 2: 외부적/중비용 (Search, Read File) -> Envelope 제한 대상
    Level 3: 파괴적/고비용 (Write File, Analyze Large Data) -> 높은 정렬 필요
    """
    if is_lumen_active():
        # 루멘 모드: 모든 행동이 '조율'되므로 레벨이 완화됨
        # 하지만 정렬 체크는 여전히 수행
        return 1 if internal_alignment > 0.7 else 2

    t = goal.type

    # 🔵 Level 1 — 내부/안전
    LEVEL_1_TYPES = {
        ProtoGoalType.PATTERN_MINING,
        ProtoGoalType.MEMORY_CONSOLIDATION,
        ProtoGoalType.DIGITAL_TWIN_UPDATE,
        ProtoGoalType.SANDBOX_EXPERIMENT,
        ProtoGoalType.LOG_THOUGHT, # Added from instruction
        ProtoGoalType.IDLE_REFLECTION, # Added from instruction
    }

    if t in LEVEL_1_TYPES:
        return 1
    
    # 🟡 Level 2 — 리듬에 영향은 있지만 내부 위주
    LEVEL_2_TYPES = {
        ProtoGoalType.BLENDER_VISUALIZATION,
        ProtoGoalType.YOUTUBE_LEARNING,
        ProtoGoalType.CONSULT_LUA,  # 외부 AI와 대화 (Level 2)
    }
    
    if t in LEVEL_2_TYPES:
        # 정렬이 낮거나 갈등이 높으면 Level 3으로 격상
        if internal_alignment < 0.5 or conflict_pressure > 0.7:
            return 3
        return 2
    
    # 🔴 Level 3 — 외부/비용/위험
    # (현재 정의된 ProtoGoalType 중 해당하는 것이 없으면 기본 Level 2)
    
    return 2


def compute_output_alignment(
    goal: ProtoGoal,
    state: Dict[str, Any],
    internal_alignment: float
) -> float:
    """
    출력 정렬 (Output Alignment)
    
    선택된 행동(Goal)이 현재의 내부 상태와 조화로운가?
    - 내부 정렬이 낮으면 외부 행동(Level 3)은 점수 깎임
    - 에너지가 낮은데 무거운 행동이면 점수 깎임
    """
    t = goal.type
    level = classify_action_level(goal, state, internal_alignment, 0.0) # Conflict not used here
    
    score = internal_alignment # Bassline starts with internal state
    
    # 1. Level vs Energy Balance
    energy = state.get("energy", 0.5)
    
    if level == 3:
        # 고비용 행동은 에너지가 충분해야 함
        if energy < 0.6: score -= 0.3
        else: score += 0.1
    elif level == 1:
        # 저비용 행동은 언제나 무난함
        score += 0.2
        
    # 2. Type Specific Alignment
    # 예를 들어 Blender(시각화)는 의식이 높을 때 좋음
    if t == ProtoGoalType.BLENDER_VISUALIZATION:
        if state.get("consciousness", 0.5) > 0.6: score += 0.2
        
    # 3. Lua Consultation (Insight)
    if t == ProtoGoalType.CONSULT_LUA:
        # 궁금증(Curiosity)이나 지루함(Boredom)이 있을 때 좋음
        if state.get("curiosity", 0.5) > 0.6: score += 0.3
        
    return max(0.0, min(1.0, score))


def route_action(
    trigger: TriggerEvent,
    state: Dict[str, Any],
    alignment: float,
    conflict_pressure: float,
) -> Optional[Dict[str, Any]]:
    """
    Heartbeat에서 트리거가 잡히면 전체 처리:
    1) ProtoGoal 생성
    2) 최적 목표 선택
    3) **Output Alignment Check (신규)**
    4) 레벨 분류
    5) Envelope(행동량) 체크
    6) 실제 실행
    """
    envelope = get_envelope()
    
    # 1) ProtoGoal 생성
    config = get_default_proto_goal_config()
    goals = generate_proto_goals_from_trigger(trigger, config)
    
    if not goals:
        logger.info("⚪ ProtoGoal 없음 - 이번 박동에서는 패스")
        envelope.on_idle()
        return None
    
    # 2) 최적 목표 선택
    best = select_best_proto_goal(goals)
    
    if best is None:
        envelope.on_idle()
        return None
        
    # 3) Output Alignment Check (정보이론적 정렬)
    output_align = compute_output_alignment(best, state, alignment)
    logger.info(f"⚖️ 출력 정렬 점수: {output_align:.2f} (Internal: {alignment:.2f})")
    
    if output_align < 0.4:
        logger.warning(f"⚠️ 행동 기각 (정렬 불일치): {best.type.value} (Score: {output_align:.2f})")
        # 정렬되지 않은 행동은 '생각(Think)'으로 격하하거나 취소
        return {"blocked": True, "reason": "ALIGNMENT_MISMATCH"}
    
    # 3-1) 레벨 분류
    level = classify_action_level(best, state, alignment, conflict_pressure)
    logger.info(f"📌 선택된 목표: {best.type.value} (Level {level})")
    logger.info(f"   설명: {best.description}")
    
    # 4) Envelope 체크
    ok, reason = envelope.check(level)
    if not ok:
        logger.warning(f"⛔ Envelope 차단: {reason}")
        if reason == "SURGE_PROTECTION":
            logger.info(f"❄️ {SURGE_COOLDOWN}초 냉각 중...")
            time.sleep(SURGE_COOLDOWN)
            envelope.on_cooldown()
        return {"blocked": True, "reason": reason}
    
    # 5) 실행
    logger.info(f"🚀 행동 실행 중: {best.type.value}")
    result = execute_proto_goal(best)
    
    success = result.get("success", False)
    logger.info(f"{'✅' if success else '❌'} 실행 결과: {result.get('action_type')}")
    
    # 결과에 정렬 점수 포함
    if result:
        result["output_alignment"] = output_align
    
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 테스트
    from agi_core.self_trigger import TriggerEvent, TriggerType
    
    trigger = TriggerEvent(
        type=TriggerType.BOREDOM,
        score=0.7,
        reason="테스트 트리거",
        payload={}
    )
    
    state = {"consciousness": 0.5, "unconscious": 0.5, "background_self": 0.5, "energy": 0.8}
    
    # 정렬 높은 경우
    print("\n--- High Alignment Case ---")
    result = route_action(trigger, state, alignment=0.8, conflict_pressure=0.3)
    print(f"Result: {result}")
    
    # 정렬 낮은 경우
    print("\n--- Low Alignment Case ---")
    result = route_action(trigger, state, alignment=0.2, conflict_pressure=0.3)
    print(f"Result: {result}")
