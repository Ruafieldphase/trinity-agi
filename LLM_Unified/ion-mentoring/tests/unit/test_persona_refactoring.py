"""
PersonaOrchestrator 리팩토링 테스트

Week 1-4 리팩토링 테스트
- 데이터 모델 검증
- 페르소나 구현 검증
- 추상 기본 클래스 호환성
"""

import pytest

from persona_system import (
    ChatContext,
    ElroPersona,
    LuaPersona,
    NanaPersona,
    Pace,
    PersonaConfig,
    PersonaResponse,
    RhythmAnalysis,
    RiriPersona,
    RoutingResult,
    Tone,
    ToneAnalysis,
)


class TestPersonaModels:
    """데이터 모델 테스트"""

    def test_persona_response_creation(self):
        """PersonaResponse 생성 테스트"""
        response = PersonaResponse(
            content="루아의 응답입니다",
            persona_used="Lua",
            resonance_key="frustrated-burst-seeking_advice",
            confidence=0.92,
            execution_time_ms=1250,
        )
        assert response.persona_used == "Lua"
        assert response.confidence == 0.92
        assert response.execution_time_ms == 1250

    def test_persona_response_validation(self):
        """PersonaResponse 검증"""
        with pytest.raises(ValueError):
            PersonaResponse(content="", persona_used="Lua", resonance_key="test", confidence=0.5)

    def test_confidence_validation(self):
        """신뢰도 범위 검증"""
        with pytest.raises(ValueError):
            PersonaResponse(
                content="Test",
                persona_used="Lua",
                resonance_key="test",
                confidence=1.5,  # 유효 범위 초과
            )

    def test_tone_analysis(self):
        """톤 분석 데이터 모델"""
        tone = ToneAnalysis(
            primary=Tone.FRUSTRATED,
            confidence=0.85,
            secondary=Tone.ANXIOUS,
            secondary_confidence=0.45,
        )
        assert tone.primary == Tone.FRUSTRATED
        assert tone.secondary == Tone.ANXIOUS

    def test_rhythm_analysis(self):
        """리듬 분석 데이터 모델"""
        rhythm = RhythmAnalysis(
            pace=Pace.BURST, avg_sentence_length=12.5, punctuation_density=0.35, energy_level=0.85
        )
        assert rhythm.pace == Pace.BURST
        assert 0.0 <= rhythm.energy_level <= 1.0

    def test_chat_context(self):
        """대화 컨텍스트"""
        context = ChatContext(user_id="user123", session_id="session456")
        context.add_message("user", "안녕하세요")
        context.add_message("assistant", "안녕하세요!")

        recent = context.get_recent_messages(1)
        assert len(recent) == 1
        assert recent[0]["role"] == "assistant"


class TestLuaPersona:
    """루아 페르소나 테스트"""

    def test_lua_config(self):
        """루아 설정"""
        lua = LuaPersona()
        config = lua.config

        assert config.name == "Lua"
        assert "empathetic" in config.traits
        assert Tone.FRUSTRATED in config.preferred_tones

    def test_lua_system_prompt(self):
        """루아 시스템 프롬프트"""
        lua = LuaPersona()
        prompt = lua.generate_system_prompt()

        assert "Lua" in prompt
        assert "공감" in prompt or "empathetic" in prompt

    def test_lua_user_prompt_building(self):
        """루아 사용자 프롬프트 구성"""
        lua = LuaPersona()
        prompt = lua.build_user_prompt(
            user_input="도와주세요!", resonance_key="frustrated-burst-seeking_advice"
        )

        assert "도와주세요" in prompt
        assert "공감" in prompt or "루아" in prompt


class TestElroPersona:
    """엘로 페르소나 테스트"""

    def test_elro_config(self):
        """엘로 설정"""
        elro = ElroPersona()
        config = elro.config

        assert config.name == "Elro"
        assert "logical" in config.traits
        assert "technical_architecture" in config.strengths

    def test_elro_system_prompt(self):
        """엘로 시스템 프롬프트"""
        elro = ElroPersona()
        prompt = elro.generate_system_prompt()

        assert "Elro" in prompt
        assert "논리적" in prompt or "logical" in prompt


class TestRiriPersona:
    """리리 페르소나 테스트"""

    def test_riri_config(self):
        """리리 설정"""
        riri = RiriPersona()
        config = riri.config

        assert config.name == "Riri"
        assert "analytical" in config.traits
        assert "metric_analysis" in config.strengths


class TestNanaPersona:
    """나나 페르소나 테스트"""

    def test_nana_config(self):
        """나나 설정"""
        nana = NanaPersona()
        config = nana.config

        assert config.name == "Nana"
        assert "collaborative" in config.traits
        assert "cross_team_collaboration" in config.strengths


class TestPersonaHierarchy:
    """페르소나 계층 구조 테스트"""

    @pytest.mark.parametrize(
        "persona_class",
        [
            LuaPersona,
            ElroPersona,
            RiriPersona,
            NanaPersona,
        ],
    )
    def test_all_personas_have_required_methods(self, persona_class):
        """모든 페르소나의 필수 메서드 확인"""
        persona = persona_class()

        assert hasattr(persona, "config")
        assert hasattr(persona, "generate_system_prompt")
        assert hasattr(persona, "build_user_prompt")
        assert hasattr(persona, "post_process_response")

    @pytest.mark.parametrize(
        "persona_class",
        [
            LuaPersona,
            ElroPersona,
            RiriPersona,
            NanaPersona,
        ],
    )
    def test_all_personas_callable(self, persona_class):
        """모든 페르소나 생성 및 기본 작동"""
        persona = persona_class()
        config = persona.config

        assert config.name is not None
        assert len(config.traits) > 0
        assert len(config.strengths) > 0


class TestBackwardCompatibility:
    """기존 코드와의 호환성 테스트"""

    def test_persona_response_old_interface(self):
        """기존 PersonaResponse 인터페이스 호환성"""
        # 기존 방식
        response = PersonaResponse(
            content="응답", persona_used="Lua", resonance_key="test-key", confidence=0.9
        )

        # 기존 속성 접근 가능
        assert response.content == "응답"
        assert response.persona_used == "Lua"

    def test_routing_result_backward_compat(self):
        """RoutingResult 호환성"""
        result = RoutingResult(
            primary_persona="Lua",
            confidence=0.95,
            secondary_persona="Elro",
            reasoning="frustrated tone matched Lua",
        )

        assert result.primary_persona == "Lua"
        assert result.confidence == 0.95


class TestModelValidation:
    """데이터 모델 검증 테스트"""

    def test_invalid_confidence(self):
        """유효하지 않은 신뢰도"""
        with pytest.raises(ValueError):
            ToneAnalysis(primary=Tone.CALM, confidence=1.5)  # 범위 초과

    def test_invalid_energy_level(self):
        """유효하지 않은 에너지 수준"""
        with pytest.raises(ValueError):
            RhythmAnalysis(
                pace=Pace.FLOWING,
                avg_sentence_length=10,
                punctuation_density=0.5,
                energy_level=1.5,  # 범위 초과
            )

    def test_empty_persona_config(self):
        """빈 페르소나 설정"""
        with pytest.raises(ValueError):
            PersonaConfig(
                name="",  # 빈 이름
                traits=[],
                strengths=[],
                prompt_style="test",
                preferred_tones=[],
                description="",
            )


# 성능 테스트
class TestPerformance:
    """성능 테스트"""

    def test_persona_instantiation_speed(self):
        """페르소나 인스턴스화 속도"""
        import time

        personas = [LuaPersona, ElroPersona, RiriPersona, NanaPersona]

        start = time.time()
        for persona_class in personas:
            persona = persona_class()
            _ = persona.config

        elapsed = time.time() - start

        # 4개 페르소나 인스턴스화 < 100ms
        assert elapsed < 0.1, f"Persona instantiation too slow: {elapsed:.3f}s"

    def test_prompt_building_speed(self):
        """프롬프트 구성 속도"""
        import time

        lua = LuaPersona()
        context = ChatContext(user_id="test", session_id="test")

        start = time.time()
        for _ in range(100):
            _ = lua.build_user_prompt(
                user_input="테스트 입력", resonance_key="calm-flowing-learning", context=context
            )

        elapsed = time.time() - start

        # 100개 프롬프트 구성 < 500ms
        assert elapsed < 0.5, f"Prompt building too slow: {elapsed:.3f}s"
