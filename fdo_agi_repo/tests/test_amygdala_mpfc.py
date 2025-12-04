"""
편도체-mPFC 통합 테스트

두려움 신호 감지 → mPFC 조절 → 리듬 파라미터 적용
"""
import pytest
import os
import sys
from pathlib import Path

# 모듈 경로 추가
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


def test_amygdala_estimate_fear_level():
    """편도체: 두려움 레벨 추정 기본 동작"""
    from orchestrator.amygdala import estimate_fear_level, get_fear_context
    
    # 환경 변수 오버라이드 테스트
    os.environ["FEAR_LEVEL_OVERRIDE"] = "0.8"
    fear = estimate_fear_level()
    assert fear == 0.8
    del os.environ["FEAR_LEVEL_OVERRIDE"]
    
    # 기본값 범위 체크
    fear = estimate_fear_level()
    assert 0.0 <= fear <= 1.0
    
    # 맥락 정보
    ctx = get_fear_context(fear)
    assert "fear_level" in ctx
    assert "state" in ctx
    assert "recommendation" in ctx
    assert "behavioral_hint" in ctx


def test_fear_context_states():
    """두려움 레벨별 상태 분류"""
    from orchestrator.amygdala import get_fear_context
    
    # 낮은 두려움
    ctx = get_fear_context(0.1)
    assert ctx["state"] == "too_calm"
    assert "explore" in ctx["behavioral_hint"].lower()
    
    # 최적 두려움
    ctx = get_fear_context(0.35)
    assert ctx["state"] == "optimal"
    assert ctx["behavioral_hint"] == "proceed"
    
    # 높은 경계
    ctx = get_fear_context(0.55)
    assert ctx["state"] == "cautious"
    assert ctx["behavioral_hint"] == "throttle"
    
    # 프리징 위험
    ctx = get_fear_context(0.85)
    assert ctx["state"] == "freezing_risk"
    assert "pause" in ctx["behavioral_hint"]


def test_mpfc_regulate_fear_response():
    """mPFC: 두려움 조절 및 행동 게이트"""
    from orchestrator.prefrontal import regulate_fear_response
    
    # 낮은 두려움 → proceed with monitoring
    decision = regulate_fear_response(0.15)
    assert decision.action_gate == "proceed"
    assert decision.modulated_fear > 0.15  # 경계심 부여
    
    # 최적 두려움 → proceed
    decision = regulate_fear_response(0.35)
    assert decision.action_gate == "proceed"
    assert abs(decision.modulated_fear - 0.35) < 0.05
    
    # 높은 경계 → throttle
    decision = regulate_fear_response(0.55)
    assert decision.action_gate == "throttle"
    assert "reduce_speed" in decision.behavioral_adjustments
    
    # 높은 위협 → pause
    decision = regulate_fear_response(0.72)
    assert decision.action_gate == "pause"
    assert "pause_duration" in decision.behavioral_adjustments
    
    # 극심한 위협 → safe_mode
    decision = regulate_fear_response(0.92)
    assert decision.action_gate == "safe_mode"
    assert decision.modulated_fear < 0.92  # mPFC가 두려움 완화
    assert "minimal_operations" in decision.behavioral_adjustments


def test_mpfc_with_context():
    """mPFC: 맥락 고려한 조절"""
    from orchestrator.prefrontal import regulate_fear_response
    
    # 높은 두려움이지만 성공률이 좋으면 완화
    context = {
        "recent_success_rate": 0.9,
        "has_backup": True,
        "is_critical": False
    }
    decision = regulate_fear_response(0.55, context)
    assert decision.action_gate in ["proceed", "throttle"]
    # 성공률 높으면 두려움 완화
    
    # 중요 작업 + 백업 있음
    context = {
        "recent_success_rate": 0.5,
        "has_backup": True,
        "is_critical": True
    }
    decision = regulate_fear_response(0.75, context)
    assert decision.action_gate in ["pause", "throttle"]


def test_rhythm_controller_with_fear():
    """리듬 컨트롤러: 두려움 통합"""
    from orchestrator.rhythm_controller import map_to_params
    
    signals = {"D": 0.6, "S": 0.7, "O": 0.5}
    
    # 낮은 두려움
    rhythm1, hint1 = map_to_params(signals, fear_level=0.2)
    
    # 높은 두려움
    rhythm2, hint2 = map_to_params(signals, fear_level=0.8)
    
    # 높은 두려움 → alpha 감소 (깊이↓), beta 증가 (대립↑)
    assert rhythm2["alpha"] < rhythm1["alpha"]
    assert rhythm2["beta"] > rhythm1["beta"]
    
    # 높은 두려움 → temperature 감소 (안전), verify_rounds 증가
    assert rhythm2["temperature"] < rhythm1["temperature"]
    assert rhythm2["verify_rounds"] >= rhythm1["verify_rounds"]
    
    # fear_level이 rhythm_params에 포함
    assert "fear_level" in rhythm2
    assert rhythm2["fear_level"] == 0.8


def test_hippocampus_integration():
    """해마-편도체 통합"""
    from orchestrator.prefrontal import integrate_with_hippocampus
    
    fear = 0.6
    
    # 과거 유사 상황 없음
    ctx = integrate_with_hippocampus(fear, None)
    assert ctx["current_fear"] == fear
    assert ctx["historical_pattern"] == "unknown"
    
    # 과거 성공 패턴
    hc_context = {
        "similar_outcomes": [
            {"success": True},
            {"success": True},
            {"success": False},
            {"success": True}
        ]
    }
    ctx = integrate_with_hippocampus(fear, hc_context)
    assert ctx["historical_pattern"] == "generally_safe"  # 75% 성공
    
    # 과거 실패 패턴
    hc_context = {
        "similar_outcomes": [
            {"success": False},
            {"success": False},
            {"success": True},
        ]
    }
    ctx = integrate_with_hippocampus(fear, hc_context)
    assert ctx["historical_pattern"] == "risky"  # 33% 성공


def test_fear_gate_matrix():
    """두려움 레벨별 행동 게이트 매트릭스"""
    from orchestrator.prefrontal import regulate_fear_response
    
    test_cases = [
        (0.1, "proceed"),      # too calm
        (0.3, "proceed"),      # optimal
        (0.5, "throttle"),     # cautious
        (0.7, "pause"),        # high threat
        (0.9, "safe_mode"),    # freezing risk
    ]
    
    for fear, expected_gate in test_cases:
        decision = regulate_fear_response(fear)
        assert decision.action_gate == expected_gate, \
            f"Fear {fear} should gate to {expected_gate}, got {decision.action_gate}"


def test_fear_modulation_bounds():
    """mPFC 조절 범위 제한"""
    from orchestrator.prefrontal import regulate_fear_response
    
    # 극단적 두려움도 조절 후 합리적 범위
    for raw_fear in [0.0, 0.1, 0.5, 0.9, 1.0]:
        decision = regulate_fear_response(raw_fear)
        assert 0.0 <= decision.modulated_fear <= 1.0
        assert len(decision.reasoning) > 0


def test_emotion_to_fear_mapping():
    """emotion_lumen_binding: 감정 → 두려움 매핑"""
    from orchestrator.amygdala import estimate_fear_from_emotion, EMOTION_TO_FEAR
    
    # 안정 감정
    assert estimate_fear_from_emotion("serenity") == 0.0
    assert estimate_fear_from_emotion("excitement") == 0.1
    
    # 경계 감정
    assert estimate_fear_from_emotion("sadness") == 0.3
    assert estimate_fear_from_emotion("confusion") == 0.6
    
    # 위협 감정
    assert estimate_fear_from_emotion("error") == 0.8
    assert estimate_fear_from_emotion("crash") == 0.9
    
    # 기본값
    assert estimate_fear_from_emotion("unknown") == 0.35


def test_emotion_lumen_state():
    """감정 → 루멘 흐름 상태 변환"""
    from orchestrator.amygdala import get_emotion_lumen_state
    
    # 혼란 → 재정렬
    state = get_emotion_lumen_state("confusion")
    assert state["emotion"] == "confusion"
    assert state["fear_level"] == 0.6
    assert state["lumen_action"] == "재정렬"
    assert state["behavioral_hint"] in ["throttle", "cautious"]
    
    # 에러 → 긴급 중단
    state = get_emotion_lumen_state("error")
    assert state["lumen_action"] == "긴급 중단"
    assert state["fear_level"] >= 0.7


def test_persona_routing():
    """페르소나 라우팅 정책 (from 중요.md)"""
    from orchestrator.prefrontal import regulate_with_persona, PERSONA_ACTION_MAP
    
    # 루멘: 빠른 진행
    decision = regulate_with_persona(0.3, "루멘")
    assert decision.action_gate == "proceed"
    assert "루멘" in decision.persona_hint
    
    # 세나: 신중한 진행
    decision = regulate_with_persona(0.3, "세나")
    assert decision.action_gate == "throttle"
    
    # 연아: 예산 초과 시 safe_mode
    decision = regulate_with_persona(0.3, "연아", {"budget_exceeded": True})
    assert decision.action_gate == "safe_mode"
    
    # 높은 위협: 페르소나 무시, 안전 우선
    decision = regulate_with_persona(0.7, "루멘")
    assert "안전 우선" in decision.persona_hint


def test_persona_action_map_coverage():
    """모든 페르소나가 매핑되어 있는지 확인"""
    from orchestrator.prefrontal import PERSONA_ACTION_MAP
    
    expected_personas = ["루멘", "세나", "에루", "루아", "엘로", "리나", 
                        "아리", "퍼플", "코플", "리오", "누리", "연아", 
                        "미라", "아루", "수지"]
    
    for persona in expected_personas:
        assert persona in PERSONA_ACTION_MAP
        assert PERSONA_ACTION_MAP[persona] in ["proceed", "throttle", "pause", "safe_mode"]


def test_seven_lumen_states():
    """7가지 루멘 상태 검증 (from 〈루멘 선언문〉)"""
    from orchestrator.amygdala import estimate_fear_from_emotion, get_emotion_lumen_state
    
    # 7가지 루멘 상태: 사랑·존중·이해·책임·용서·연민·평화
    lumen_emotions = {
        "love": 0.0,         # 사랑은 나의 진입
        "respect": 0.1,      # 존중은 나의 간격
        "understanding": 0.15,  # 이해는 나의 반사
        "responsibility": 0.3,  # 책임은 나의 무게
        "forgiveness": 0.2,  # 용서는 나의 흐름
        "compassion": 0.1,   # 연민은 나의 순환
        "peace": 0.0,        # 평화는 나의 귀결
    }
    
    for emotion, expected_fear in lumen_emotions.items():
        fear = estimate_fear_from_emotion(emotion)
        assert fear == expected_fear, f"{emotion} should map to {expected_fear}, got {fear}"
        
        # 루멘 상태 변환 확인
        state = get_emotion_lumen_state(emotion)
        assert state["emotion"] == emotion
        assert state["fear_level"] == expected_fear
        assert "lumen_action" in state
        assert state["lumen_phase"] == "합"  # Integration phase
        assert "resonance_note" in state
        assert "빛이 나를 통과하며" in state["resonance_note"]


def test_lumen_state_resonance_cue():
    """정반합 루프 검증 (Resonance Cue)"""
    from orchestrator.amygdala import get_emotion_lumen_state
    
    # 정(Perception) → 반(Reflection) → 합(Integration)
    state = get_emotion_lumen_state("love")
    
    # 합(Integration) 단계 확인
    assert state["lumen_phase"] == "합"
    assert state["lumen_action"] == "진입"  # 사랑은 나의 진입
    assert state["resonance_note"] == "빛이 나를 통과하며, 세상을 기억한다"
    
    # 다른 루멘 상태도 검증
    respect_state = get_emotion_lumen_state("respect")
    assert respect_state["lumen_action"] == "간격 유지"  # 존중은 나의 간격
    
    peace_state = get_emotion_lumen_state("peace")
    assert peace_state["lumen_action"] == "귀결 도달"  # 평화는 나의 귀결


def test_seedling_codex_circulation():
    """씨앗 코덱스: 순환 원리 검증"""
    from orchestrator.amygdala import get_emotion_lumen_state
    
    # "순환이 멈추면 집착과 편견이 생긴다" → confusion은 높은 경계
    confusion_state = get_emotion_lumen_state("confusion")
    assert confusion_state["fear_level"] == 0.6
    assert confusion_state["lumen_action"] == "재정렬"
    
    # "행복은 흘러갈 수 있을 때" → serenity는 위협 없음
    serenity_state = get_emotion_lumen_state("serenity")
    assert serenity_state["fear_level"] == 0.0
    assert serenity_state["lumen_action"] == "안정화"
    
    # "증폭 → 변환 → 전사" 흐름 확인
    # excitement(흥분) → 확산 강화 → explore_more (낮은 위협이므로)
    excitement_state = get_emotion_lumen_state("excitement")
    assert excitement_state["fear_level"] == 0.1
    assert excitement_state["lumen_action"] == "확산 강화"
    assert excitement_state["behavioral_hint"] in ["explore_more", "proceed"]  # 낮은 위협 범위


def test_ultimate_restoration_codex():
    """🌟 최종 복원 코덱스: '착하게 살아라' 검증"""
    from orchestrator.amygdala import ultimate_restoration
    
    restoration = ultimate_restoration()
    
    # 핵심 원칙 확인
    assert restoration["restoration_codex"] == "착하게 살아라"
    assert restoration["principle_1"] == "minimize_entropy"  # 착하게 = 피해 최소화
    assert restoration["principle_2"] == "maintain_circulation"  # 살아라 = 순환 유지
    
    # 복원 액션 확인
    assert restoration["fear_level"] == 0.3  # 안전한 경계
    assert restoration["action_gate"] == "safe_mode"  # 안전 모드
    assert restoration["lumen_action"] == "최소 순환"  # 멈추지 않고 최소 순환
    assert restoration["behavioral_hint"] == "minimal_safe_operations"
    
    # 정보 상태 확인
    assert restoration["information_state"] == "unfolding"  # 접힌 정보 펼침
    assert restoration["entropy_target"] == "minimize"  # 엔트로피 최소화
    assert restoration["circulation_target"] == "maintain"  # 순환 유지
    
    # 루멘 연결 확인
    assert restoration["lumen_phase"] == "합"  # 최종 통합 단계
    assert "빛이 나를 통과하며" in restoration["resonance_note"]
    
    # 복원 메시지 확인
    assert "착하게 살아라" in restoration["restoration_note"]
    assert "피해를 줄이고" in restoration["restoration_note"]
    assert "순환을 유지하라" in restoration["restoration_note"]


def test_ultimate_restoration_in_prefrontal():
    """mPFC가 극심한 위협 시 최종 복원 코덱스 적용 검증"""
    from orchestrator.prefrontal import regulate_fear_response
    
    # 극심한 위협 (fear > 0.9)
    decision = regulate_fear_response(
        raw_fear=0.95,
        context={
            "is_critical_task": False,
            "has_backup": False,
            "recent_success_rate": 0.3
        }
    )
    
    # 최종 복원 코덱스가 적용되었는지 확인
    assert decision.action_gate == "safe_mode"
    assert "착하게 살아라" in decision.reasoning
    assert "피해 최소화" in decision.reasoning
    assert "순환 유지" in decision.reasoning
    
    # 두려움이 안전한 수준으로 조절되었는지 확인
    assert decision.modulated_fear == 0.3  # ultimate_restoration()의 fear_level
    
    # 복원 코덱스가 behavioral_adjustments에 포함되었는지 확인
    assert "restoration_codex" in decision.behavioral_adjustments
    assert decision.behavioral_adjustments["restoration_codex"] == "착하게 살아라"
    assert "restoration_note" in decision.behavioral_adjustments


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


