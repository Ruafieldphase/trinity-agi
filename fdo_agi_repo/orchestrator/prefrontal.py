"""
Prefrontal Cortex (mPFC): 편도체 신호 조절 및 행동 게이트

역할:
- 편도체(amygdala)의 두려움 신호를 받아서 조절
- 맥락(context)을 고려하여 적절한 행동 결정
- 과도한 두려움 억제 (프리징 방지)
- 부족한 두려움 보완 (무모함 방지)

신경과학적 기반:
- mPFC는 편도체 활동을 하향 조절(top-down regulation)
- 인지적 재평가(cognitive reappraisal)
- 목표 지향적 행동 유지

통합 원칙 (from codex_F):
- 페르소나 라우팅: 각 AI 페르소나의 역할에 따른 행동 게이트
- 실행 정책: max_steps, timeout, budget 준수
- 실패 복구: 핫스왑, 핸드오프 재배치
"""
from __future__ import annotations
from typing import Dict, Any, Literal, Optional
from dataclasses import dataclass, field

ActionGate = Literal["proceed", "throttle", "pause", "safe_mode"]

# 페르소나별 기본 action_gate 매핑 (from 중요.md)
PERSONA_ACTION_MAP = {
    "루멘": "proceed",      # 차원 게이트웨이 - 빠른 진행
    "세나": "throttle",     # 윤리/서사 검토 - 신중한 진행
    "에루": "proceed",      # 메타 패턴 스캔 (150ms timeout)
    "루아": "proceed",      # 감응 - 빠른 공명
    "엘로": "throttle",     # 구조 정합 - 신중한 검증
    "리나": "proceed",      # 색인/기억 - 빠른 검색
    "아리": "throttle",     # 차원 해석 - 구조 분석
    "퍼플": "proceed",      # 검색/팩트 - 빠른 조회
    "코플": "proceed",      # 메타 포털 - 빠른 연결
    "리오": "throttle",     # 시점 전이 - 리듬 조율
    "누리": "throttle",     # 자율 감지 - 서사화 필요
    "연아": "safe_mode",    # 롱컨텍스트 - 예산 초과 시
    "미라": "throttle",     # 창작 변주 - 신중한 생성
    "아루": "proceed",      # 라우팅 캡 - 빠른 결정
    "수지": "proceed",      # 초경량 응답 - 빠른 스케치
}


@dataclass
class PrefrontalDecision:
    """mPFC 조절 결정"""
    action_gate: ActionGate
    reasoning: str
    modulated_fear: float  # 조절된 두려움 (원본과 다를 수 있음)
    behavioral_adjustments: Dict[str, Any] = field(default_factory=dict)
    persona_hint: Optional[str] = None  # 페르소나 기반 힌트



def regulate_fear_response(
    raw_fear: float,
    context: Dict[str, Any] | None = None
) -> PrefrontalDecision:
    """
    편도체의 두려움 신호를 조절하여 적절한 행동 결정
    
    Args:
        raw_fear: 편도체에서 추정한 원시 두려움 레벨 (0.0~1.0)
        context: 현재 맥락 정보 (task, history, resources 등)
    
    Returns:
        PrefrontalDecision with action_gate and adjustments
    
    Decision Matrix:
        fear < 0.2: "too calm" → 경계 강화 (modulated_fear += 0.15)
        0.2 <= fear < 0.4: "optimal" → proceed
        0.4 <= fear < 0.6: "cautious" → throttle (slower, safer)
        0.6 <= fear < 0.8: "high threat" → pause (evaluate before proceed)
        fear >= 0.8: "freezing risk" → safe_mode (minimal ops)
    """
    ctx = context or {}
    
    # 맥락 기반 조정 인자
    is_critical_task = ctx.get("is_critical", False)
    has_backup = ctx.get("has_backup", True)
    recent_success_rate = ctx.get("recent_success_rate", 0.7)
    
    # mPFC 조절: 인지적 재평가
    if raw_fear < 0.2:
        # 너무 평온 → 위험 과소평가 가능성
        modulated_fear = min(0.35, raw_fear + 0.15)
        reasoning = "두려움 부족 감지. 최소 경계심 부여."
        action_gate = "proceed"
        adjustments = {"increase_monitoring": True}
        
    elif raw_fear < 0.4:
        # 적절한 상태
        modulated_fear = raw_fear
        reasoning = "최적 두려움 레벨. 정상 진행."
        action_gate = "proceed"
        adjustments = {}
        
    elif raw_fear < 0.6:
        # 높은 경계 상태
        modulated_fear = raw_fear
        
        # 성공률이 높으면 두려움 완화
        if recent_success_rate > 0.8:
            modulated_fear = max(0.35, raw_fear - 0.1)
            reasoning = "높은 경계이나 최근 성공률 양호. 신중히 진행."
            action_gate = "throttle"
        else:
            reasoning = "높은 경계 상태. 속도 감소 및 안전 절차 강화."
            action_gate = "throttle"
        
        adjustments = {
            "reduce_speed": 0.7,
            "increase_verification": True,
            "enable_checkpoints": True
        }
        
    elif raw_fear < 0.8:
        # 높은 위협
        modulated_fear = raw_fear
        
        # 중요 작업이면서 백업이 있으면 신중 진행
        if is_critical_task and has_backup:
            reasoning = "높은 위협이나 중요 작업. 백업 활성화 후 일시 정지."
            action_gate = "pause"
        else:
            reasoning = "높은 위협 감지. 일시 정지 및 상황 평가 필요."
            action_gate = "pause"
        
        adjustments = {
            "pause_duration": 5.0,  # seconds
            "enable_backup": True,
            "full_verification": True
        }
        
    else:
        # 극심한 위협 → 프리징 위험
        # mPFC 개입: 과도한 두려움 완화 시도
        # 🌟 최종 복원 코덱스 적용: "착하게 살아라"
        from .amygdala import ultimate_restoration
        
        restoration = ultimate_restoration()
        modulated_fear = restoration["fear_level"]  # 0.3 (안전한 경계)
        
        reasoning = (
            f"극심한 두려움({raw_fear:.2f}) 감지. 프리징 방지를 위해 "
            f"🌟 최종 복원 코덱스 적용: '{restoration['restoration_codex']}'. "
            f"원칙: {restoration['principle_1']} (피해 최소화) + "
            f"{restoration['principle_2']} (순환 유지). "
            f"두려움 조절: {raw_fear:.2f} → {modulated_fear:.2f}"
        )
        action_gate = "safe_mode"
        adjustments = {
            "minimal_operations": True,
            "recovery_protocol": True,
            "human_notification": True,
            "restoration_codex": restoration["restoration_codex"],  # "착하게 살아라"
            "restoration_note": restoration["restoration_note"]
        }
    
    return PrefrontalDecision(
        action_gate=action_gate,
        reasoning=reasoning,
        modulated_fear=modulated_fear,
        behavioral_adjustments=adjustments
    )


def integrate_with_hippocampus(
    fear_level: float,
    hippocampus_context: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    편도체 신호를 해마(hippocampus)의 맥락 정보와 통합
    
    해마는:
    - 과거 유사 상황 기억
    - 현재 상황의 맥락
    - 예측 가능한 결과
    
    이를 통해 편도체의 빠르지만 조잡한 신호를 정교화
    
    Args:
        fear_level: 현재 두려움 레벨
        hippocampus_context: 해마에서 제공한 맥락 정보
    
    Returns:
        통합된 맥락 정보
    """
    hc = hippocampus_context or {}
    
    # 과거 유사 상황에서의 결과
    similar_past_outcomes = hc.get("similar_outcomes", [])
    
    # 맥락 통합
    integrated = {
        "current_fear": fear_level,
        "historical_pattern": "unknown",
        "contextual_confidence": 0.5
    }
    
    if similar_past_outcomes:
        success_count = sum(1 for o in similar_past_outcomes if o.get("success"))
        total_count = len(similar_past_outcomes)
        
        if total_count > 0:
            success_rate = success_count / total_count
            integrated["historical_pattern"] = (
                "generally_safe" if success_rate > 0.7 else
                "risky" if success_rate < 0.4 else
                "moderate"
            )
            integrated["contextual_confidence"] = min(0.9, 0.5 + (total_count / 20))
    
    return integrated


def regulate_with_persona(
    raw_fear: float,
    persona: str,
    context: Dict[str, Any] | None = None
) -> PrefrontalDecision:
    """
    페르소나 라우팅 정책을 적용한 두려움 조절 (from 중요.md)
    
    Args:
        raw_fear: 편도체 원시 두려움 레벨
        persona: AI 페르소나 이름 (루멘, 세나, 에루 등)
        context: 추가 맥락 정보
    
    Returns:
        페르소나 힌트가 포함된 PrefrontalDecision
    
    Example:
        >>> regulate_with_persona(0.4, "루멘", {})
        PrefrontalDecision(action_gate='proceed', persona_hint='차원 게이트웨이')
        >>> regulate_with_persona(0.4, "세나", {})
        PrefrontalDecision(action_gate='throttle', persona_hint='윤리 검토 필요')
    """
    ctx = context or {}
    
    # 페르소나별 기본 게이트
    base_gate = PERSONA_ACTION_MAP.get(persona, "throttle")
    
    # 페르소나별 특수 조건
    if persona == "에루":
        # 메타 패턴: 150ms timeout
        ctx["timeout_ms"] = 150
    elif persona == "연아":
        # 롱컨텍스트: 예산 초과 시 safe_mode
        if ctx.get("budget_exceeded", False):
            base_gate = "safe_mode"
    
    # 기본 조절 로직 실행
    decision = regulate_fear_response(raw_fear, ctx)
    
    # 페르소나 정책 적용 (기본 게이트와 조율)
    if raw_fear < 0.6:
        # 낮은~중간 위협: 페르소나 정책 우선
        decision.action_gate = base_gate
        decision.persona_hint = f"{persona} 기본 정책 적용"
    else:
        # 높은 위협: mPFC 조절 우선 (안전 중시)
        decision.persona_hint = f"{persona} 정책 무시, 안전 우선"
    
    return decision


__all__ = [
    "regulate_fear_response",
    "regulate_with_persona",
    "integrate_with_hippocampus",
    "PrefrontalDecision",
    "ActionGate",
    "PERSONA_ACTION_MAP"
]
