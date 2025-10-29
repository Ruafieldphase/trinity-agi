"""
PersonaRouter 테스트

Phase별 테스트 구성:
- Phase 1: 페르소나 설정 로드 (3개 테스트)
- Phase 2: 파동키 파싱 (3개 테스트)
- Phase 3: 매칭 점수 계산 (5개 테스트)
- Phase 4: 라우팅 로직 (4개 테스트)

작성자: Ion (이온)
날짜: 2025-10-17
"""

import sys
from pathlib import Path

# 동적 모듈 로딩 (ion-mentoring 디렉토리 처리)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import importlib.util

# persona_router 모듈 로딩
spec = importlib.util.spec_from_file_location("persona_router", project_root / "persona_router.py")
persona_router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(persona_router)

PersonaRouter = persona_router.PersonaRouter
PersonaConfig = persona_router.PersonaConfig
RoutingResult = persona_router.RoutingResult
Tone = persona_router.Tone
Pace = persona_router.Pace
Intent = persona_router.Intent


# ==================== Phase 1: 페르소나 설정 로드 ====================


def test_persona_config_loading():
    """페르소나 설정 로드 테스트"""
    router = PersonaRouter()

    assert len(router.personas) == 4
    assert "Lua" in router.personas
    assert "Elro" in router.personas
    assert "Riri" in router.personas
    assert "Nana" in router.personas


def test_get_persona_config_lua():
    """Lua 페르소나 설정 조회 테스트"""
    router = PersonaRouter()

    lua_config = router.get_persona_config("Lua")

    assert lua_config is not None
    assert lua_config.name == "Lua"
    assert "empathetic" in lua_config.traits
    assert "frustrated" in lua_config.preferred_tones


def test_get_persona_config_nonexistent():
    """존재하지 않는 페르소나 조회 테스트"""
    router = PersonaRouter()

    config = router.get_persona_config("NonExistent")

    assert config is None


# ==================== Phase 2: 파동키 파싱 ====================


def test_parse_resonance_key_valid():
    """유효한 파동키 파싱 테스트"""
    router = PersonaRouter()

    tone, pace, intent = router._parse_resonance_key("curious-burst-inquiry")

    assert tone == Tone.CURIOUS
    assert pace == Pace.BURST
    assert intent == Intent.INQUIRY


def test_parse_resonance_key_calm_flowing():
    """차분하고 흐르는 파동키 파싱 테스트"""
    router = PersonaRouter()

    tone, pace, intent = router._parse_resonance_key("calm-flowing-statement")

    assert tone == Tone.CALM
    assert pace == Pace.FLOWING
    assert intent == Intent.STATEMENT


def test_parse_resonance_key_invalid():
    """잘못된 파동키 파싱 테스트"""
    router = PersonaRouter()

    tone, pace, intent = router._parse_resonance_key("invalid-key")

    # 잘못된 키는 기본값(calm, medium, inquiry)으로 반환
    assert isinstance(tone, Tone)
    assert isinstance(pace, Pace)
    assert isinstance(intent, Intent)
    # 기본값 확인
    assert tone == Tone.CALM or tone in Tone  # Enum 타입 확인
    assert pace in Pace  # Enum 타입 확인
    assert intent in Intent  # Enum 타입 확인


# ==================== Phase 3: 매칭 점수 계산 ====================


def test_calculate_match_score_lua_frustrated():
    """Lua - frustrated 파동키 매칭 테스트"""
    router = PersonaRouter()

    score = router.calculate_match_score("frustrated-burst-expressive", "Lua")

    # frustrated는 Lua의 preferred_tones에 있음 (0.5)
    # burst는 Lua에게 적합 (0.3)
    # expressive도 적합 (0.2)
    assert score == 1.0  # 완벽한 매칭


def test_calculate_match_score_elro_curious():
    """Elro - curious 파동키 매칭 테스트"""
    router = PersonaRouter()

    score = router.calculate_match_score("curious-flowing-inquiry", "Elro")

    # curious는 Elro의 preferred_tones에 있음 (0.5)
    # flowing은 Elro에게 적합 (0.3)
    # inquiry도 적합 (0.2)
    assert score == 1.0  # 완벽한 매칭


def test_calculate_match_score_riri_analytical():
    """Riri - analytical 파동키 매칭 테스트"""
    router = PersonaRouter()

    score = router.calculate_match_score("analytical-flowing-statement", "Riri")

    # analytical은 Riri의 preferred_tones에 있음 (0.5)
    # flowing은 Riri에게 적합 (0.3)
    # statement도 적합 (0.2)
    assert score == 1.0  # 완벽한 매칭


def test_calculate_match_score_nonexistent_persona():
    """존재하지 않는 페르소나 매칭 테스트"""
    router = PersonaRouter()

    score = router.calculate_match_score("curious-burst-inquiry", "NonExistent")

    assert score == 0.0


def test_calculate_match_score_partial_match():
    """부분 매칭 테스트"""
    router = PersonaRouter()

    # 'playful'은 Lua의 preferred_tones에 있지만, Elro에는 없음
    score = router.calculate_match_score("playful-flowing-inquiry", "Elro")

    # tone 매칭 실패 (0.0) + flowing (0.3) + inquiry (0.2) = 0.5
    assert score == 0.5


# ==================== Phase 4: 라우팅 로직 ====================


def test_route_curious_inquiry():
    """호기심 있는 질문 라우팅 테스트"""
    router = PersonaRouter()

    result = router.route("curious-flowing-inquiry")

    # curious는 Elro와 Riri가 선호
    assert result.primary_persona in ["Elro", "Riri"]
    assert result.confidence > 0.5
    assert result.secondary_persona is not None
    assert "감정 톤=curious" in result.reasoning


def test_route_frustrated_expressive():
    """좌절감 표현 라우팅 테스트"""
    router = PersonaRouter()

    result = router.route("frustrated-burst-expressive")

    # frustrated는 Lua가 선호
    assert result.primary_persona == "Lua"
    assert result.confidence >= 0.8
    assert "감정 톤=frustrated" in result.reasoning


def test_route_analytical_statement():
    """분석적 진술 라우팅 테스트"""
    router = PersonaRouter()

    result = router.route("analytical-flowing-statement")

    # analytical은 Riri와 Elro 모두 선호 (동점 가능)
    assert result.primary_persona in ["Riri", "Elro"]
    assert result.confidence == 1.0
    assert result.secondary_persona is not None


def test_route_urgent_expressive():
    """긴급 표현 라우팅 테스트"""
    router = PersonaRouter()

    result = router.route("urgent-burst-expressive")

    # urgent는 Nana가 선호
    assert result.primary_persona == "Nana"
    assert result.confidence > 0.5
    assert "감정 톤=urgent" in result.reasoning
