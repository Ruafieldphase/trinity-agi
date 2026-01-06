"""
Resonance Guard - 리듬 기반 안전장치
AGI가 과열되거나 비노체 리듬과 맞지 않을 때 행동을 멈추게 함

3차원 리듬 게이트:
1. 리듬 변동률 (ΔRhythm) - 의식/무의식/배경자아 변화율
2. 내부 갈등 (Conflict Pressure)
3. 비노체 정렬 (Alignment Score)
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("ResonanceGuard")

# 리듬 임계값 (Core의 설계 기반)
RHYTHM_OVERLOAD_THRESHOLD = 0.24
CONFLICT_OVERLOAD_THRESHOLD = 0.85
ALIGNMENT_BREAK_THRESHOLD = 0.45


def compute_rhythm_delta(
    current: Dict[str, float],
    previous: Dict[str, float],
) -> float:
    """
    리듬 변동률 계산
    
    R = (ΔC * 0.5) + (ΔB * 0.3) + (ΔU * 0.2)
    
    ΔC: 의식 변화
    ΔB: 배경자아 변화
    ΔU: 무의식 변화
    """
    delta_c = abs(current.get("consciousness", 0.5) - previous.get("consciousness", 0.5))
    delta_b = abs(current.get("background_self", 0.5) - previous.get("background_self", 0.5))
    delta_u = abs(current.get("unconscious", 0.5) - previous.get("unconscious", 0.5))
    
    R = (delta_c * 0.5) + (delta_b * 0.3) + (delta_u * 0.2)
    return R


def resonance_guard(
    state: Dict[str, float],
    prev_state: Dict[str, float],
    alignment_score: float,
    conflict_pressure: float,
) -> Tuple[bool, str]:
    """
    리듬 기반 안전장치
    
    Returns:
        (ok, reason): 통과 여부와 이유
        
    기준:
        R < 0.08: Zone 2 안정
        R 0.08 ~ 0.24: 확장 가능하지만 조심
        R > 0.24: 과열 → 행동 금지
    """
    # 1) 리듬 변동률 체크
    R = compute_rhythm_delta(state, prev_state)
    
    if R > RHYTHM_OVERLOAD_THRESHOLD:
        logger.warning(f"⚠️ 리듬 과열 감지: R={R:.3f} > {RHYTHM_OVERLOAD_THRESHOLD}")
        return False, "RHYTHM_OVERLOAD"
    
    # 2) 내부 갈등 체크
    if conflict_pressure > CONFLICT_OVERLOAD_THRESHOLD:
        logger.warning(f"⚠️ 갈등 과열 감지: conflict={conflict_pressure:.2f}")
        return False, "CONFLICT_OVERLOAD"
    
    # 3) 비노체 리듬 정렬 체크
    if alignment_score < ALIGNMENT_BREAK_THRESHOLD:
        logger.warning(f"⚠️ 정렬 깨짐: alignment={alignment_score:.2f}")
        return False, "ALIGNMENT_BREAK"
    
    # Zone 상태 로깅
    if R < 0.08:
        zone = "Zone 2 (안정)"
    else:
        zone = "Zone 2 경계 (확장 가능)"
    
    logger.debug(f"✅ 리듬 체크 통과: R={R:.3f}, {zone}")
    
    return True, "OK"


def compute_alignment_score(state: Dict[str, float]) -> float:
    """
    비노체 리듬과의 정렬 점수 계산
    
    현재는 간단한 휴리스틱 사용:
    - 의식이 너무 낮거나 높으면 정렬 낮음
    - 균형 잡힌 상태일수록 정렬 높음
    """
    c = state.get("consciousness", 0.5)
    b = state.get("background_self", 0.5)
    u = state.get("unconscious", 0.5)
    
    # 균형 점수: 모두 0.3~0.7 사이면 높음
    balance = 1.0
    for v in [c, b, u]:
        if v < 0.2 or v > 0.9:
            balance -= 0.2
        elif v < 0.3 or v > 0.8:
            balance -= 0.1
    
    # 에너지 레벨 반영
    energy = state.get("energy", 0.5)
    
    
    alignment = max(0.0, min(1.0, balance * 0.7 + energy * 0.3))
    return alignment


def compute_input_alignment(
    trigger_type: str,
    state: Dict[str, float]
) -> float:
    """
    입력 정렬 (Input Alignment)
    
    들어온 자극(Trigger)이 현재의 내부 리듬과 어울리는가?
    - 리듬(Rhythm/Insight) 상태에서는 깊은 사고(Think)가 어울림
    - 행동(Action/Surge) 상태에서는 행동(Act)이 어울림
    - 지루함(Boredom) 상태에서는 탐색(Explore)이 어울림
    """
    c = state.get("consciousness", 0.5)
    b = state.get("background_self", 0.5)
    u = state.get("unconscious", 0.5)
    energy = state.get("energy", 0.5)
    
    score = 0.5 # Default neutral
    
    # 1. Trigger Type Analysis
    tt = trigger_type.lower()
    
    if "boredom" in tt:
        # 지루함은 에너지가 낮을 때 자연스러운 신호
        if energy < 0.4: score += 0.2
        else: score -= 0.1
        
    elif "curiosity" in tt or "insight" in tt:
        # 호기심/통찰은 의식과 무의식이 높을 때 좋음
        if c > 0.6 and u > 0.6: score += 0.3
        elif energy > 0.7: score += 0.2
        
    elif "surge" in tt or "action" in tt:
        # 행동/충동은 에너지가 높고 의식이 명료할 때 좋음
        if energy > 0.8 and c > 0.7: score += 0.3
        elif energy < 0.3: score -= 0.3 # 에너지 없는데 행동? 감점
        
    elif "rhythm" in tt:
        # 리듬 체크는 언제나 환영, 배경자아가 높으면 더 좋음
        score += 0.1
        if b > 0.6: score += 0.2
        
    # 2. Resonance Bonus (공명 보너스)
    # 내부 상태의 균형이 좋으면 어떤 입력이든 더 잘 처리함
    balance_score = compute_alignment_score(state)
    score += (balance_score - 0.5) * 0.4
    
    return max(0.0, min(1.0, score))


def compute_conflict_pressure(state: Dict[str, float]) -> float:
    """
    내부 갈등 압력 계산
    
    - 무의식 레벨이 높으면 갈등 증가
    - 지루함이 높으면 갈등 증가
    - 의식과 무의식 차이가 크면 갈등 증가
    """
    c = state.get("consciousness", 0.5)
    u = state.get("unconscious", 0.5)
    boredom = state.get("boredom", 0.0)
    
    # 의식-무의식 차이
    diff = abs(c - u)
    
    # 갈등 압력 = 무의식 레벨 * 0.4 + 차이 * 0.3 + 지루함 * 0.3
    conflict = u * 0.4 + diff * 0.3 + boredom * 0.3
    
    return max(0.0, min(1.0, conflict))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # 테스트
    prev = {"consciousness": 0.5, "unconscious": 0.5, "background_self": 0.5}
    curr = {"consciousness": 0.55, "unconscious": 0.48, "background_self": 0.52}
    
    ok, reason = resonance_guard(curr, prev, alignment_score=0.7, conflict_pressure=0.3)
    print(f"Guard: {ok} - {reason}")
    
    # 과열 테스트
    overheated = {"consciousness": 0.9, "unconscious": 0.5, "background_self": 0.5}
    ok, reason = resonance_guard(overheated, prev, alignment_score=0.7, conflict_pressure=0.3)
    print(f"Overheated: {ok} - {reason}")
