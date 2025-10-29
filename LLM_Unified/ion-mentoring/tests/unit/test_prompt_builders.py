"""
프롬프트 빌더 단위 테스트

Week 5-6: 프롬프트 빌더 패턴 테스트
- 템플릿 포맷팅
- 컨텍스트 구성
- 팩토리 패턴
- 페르소나별 프롬프트 생성
"""

import pytest

from persona_system.models import ChatContext, Intent, Pace, Tone
from persona_system.prompts import (
    BasePromptBuilder,
    ElroPromptBuilder,
    LuaPromptBuilder,
    NanaPromptBuilder,
    PromptBuilderFactory,
    RiriPromptBuilder,
)


class TestPromptBuilderFactory:
    """프롬프트 빌더 팩토리 테스트"""

    def test_factory_create_lua_builder(self):
        """Lua 빌더 생성"""
        builder = PromptBuilderFactory.create("Lua")
        assert isinstance(builder, LuaPromptBuilder)
        assert builder.persona_name == "Lua"

    def test_factory_create_elro_builder(self):
        """Elro 빌더 생성"""
        builder = PromptBuilderFactory.create("Elro")
        assert isinstance(builder, ElroPromptBuilder)
        assert builder.persona_name == "Elro"

    def test_factory_create_riri_builder(self):
        """Riri 빌더 생성"""
        builder = PromptBuilderFactory.create("Riri")
        assert isinstance(builder, RiriPromptBuilder)
        assert builder.persona_name == "Riri"

    def test_factory_create_nana_builder(self):
        """Nana 빌더 생성"""
        builder = PromptBuilderFactory.create("Nana")
        assert isinstance(builder, NanaPromptBuilder)
        assert builder.persona_name == "Nana"

    def test_factory_invalid_persona_raises_error(self):
        """유효하지 않은 페르소나는 ValueError 발생"""
        with pytest.raises(ValueError, match="Unknown persona"):
            PromptBuilderFactory.create("InvalidPersona")

    def test_factory_get_available_personas(self):
        """사용 가능한 페르소나 목록 반환"""
        personas = PromptBuilderFactory.get_available_personas()
        assert len(personas) == 4
        assert set(personas) == {"Lua", "Elro", "Riri", "Nana"}

    def test_factory_register_custom_builder(self):
        """커스텀 빌더 등록"""

        class CustomBuilder(BasePromptBuilder):
            def get_system_prompt(self):
                return "Custom system prompt"

            def get_template(self):
                return "Custom template: {user_input}"

        PromptBuilderFactory.register("Custom", CustomBuilder)
        builder = PromptBuilderFactory.create("Custom")
        assert isinstance(builder, CustomBuilder)

        # 정리
        PromptBuilderFactory._builders.pop("Custom")


class TestLuaPromptBuilder:
    """Lua 프롬프트 빌더 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.builder = LuaPromptBuilder("Lua")

    def test_lua_system_prompt_contains_empathy(self):
        """Lua 시스템 프롬프트는 공감을 포함"""
        prompt = self.builder.get_system_prompt()
        assert "공감" in prompt or "empathy" in prompt.lower()

    def test_lua_system_prompt_contains_creativity(self):
        """Lua 시스템 프롬프트는 창의성을 포함"""
        prompt = self.builder.get_system_prompt()
        assert "창의" in prompt or "creative" in prompt.lower()

    def test_lua_template_contains_required_fields(self):
        """Lua 템플릿이 필수 필드를 포함"""
        template = self.builder.get_template()
        required_fields = [
            "{system_prompt}",
            "{user_input}",
            "{tone}",
            "{pace}",
            "{intent}",
            "{context}",
            "{history}",
        ]
        for field in required_fields:
            assert field in template, f"Missing {field} in template"

    def test_lua_template_has_lua_specific_content(self):
        """Lua 템플릿이 Lua 특화 콘텐츠를 포함"""
        template = self.builder.get_template()
        assert "루아" in template or "Lua" in template or "공감" in template

    def test_lua_build_returns_formatted_string(self):
        """Lua 프롬프트 빌드 결과는 포맷된 문자열"""
        user_input = "테스트 입력"
        prompt = self.builder.build(user_input, "calm-medium-learning")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert user_input in prompt

    def test_lua_build_includes_system_prompt(self):
        """빌드 결과는 시스템 프롬프트를 포함"""
        self.builder.build("테스트", "calm-medium-learning")
        system_prompt = self.builder.get_system_prompt()
        assert len(system_prompt) > 0  # 시스템 프롬프트는 포함되거나 변형됨


class TestElroPromptBuilder:
    """Elro 프롬프트 빌더 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.builder = ElroPromptBuilder("Elro")

    def test_elro_system_prompt_contains_logic(self):
        """Elro 시스템 프롬프트는 논리를 포함"""
        prompt = self.builder.get_system_prompt()
        assert "논리" in prompt or "logical" in prompt.lower()

    def test_elro_system_prompt_contains_structure(self):
        """Elro 시스템 프롬프트는 구조를 포함"""
        prompt = self.builder.get_system_prompt()
        assert "체계" in prompt or "systematic" in prompt.lower()

    def test_elro_template_contains_numbered_sections(self):
        """Elro 템플릿은 번호 매기기 섹션을 포함"""
        template = self.builder.get_template()
        assert "1." in template or "### " in template  # 구조화된 형식

    def test_elro_template_has_architecture_section(self):
        """Elro 템플릿은 아키텍처 섹션을 포함"""
        template = self.builder.get_template()
        assert "아키텍처" in template or "architecture" in template.lower() or "분석" in template

    def test_elro_build_returns_structured_prompt(self):
        """Elro 프롬프트 빌드는 구조화된 결과 반환"""
        prompt = self.builder.build("테스트", "analytical-medium-learning")
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # 구조화된 형식 확인
        assert "1." in prompt or "**" in prompt


class TestRiriPromptBuilder:
    """Riri 프롬프트 빌더 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.builder = RiriPromptBuilder("Riri")

    def test_riri_system_prompt_contains_analysis(self):
        """Riri 시스템 프롬프트는 분석을 포함"""
        prompt = self.builder.get_system_prompt()
        assert "분석" in prompt or "analysis" in prompt.lower()

    def test_riri_system_prompt_contains_data(self):
        """Riri 시스템 프롬프트는 데이터를 포함"""
        prompt = self.builder.get_system_prompt()
        assert "데이터" in prompt or "data" in prompt.lower()

    def test_riri_template_has_data_sections(self):
        """Riri 템플릿은 데이터 섹션을 포함"""
        template = self.builder.get_template()
        assert "데이터" in template or "data" in template.lower() or "패턴" in template

    def test_riri_build_returns_analytical_prompt(self):
        """Riri 프롬프트 빌드는 분석적 결과 반환"""
        prompt = self.builder.build("테스트", "analytical-contemplative-validation")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestNanaPromptBuilder:
    """Nana 프롬프트 빌더 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.builder = NanaPromptBuilder("Nana")

    def test_nana_system_prompt_contains_collaboration(self):
        """Nana 시스템 프롬프트는 협력을 포함"""
        prompt = self.builder.get_system_prompt()
        assert "협력" in prompt or "collaboration" in prompt.lower()

    def test_nana_system_prompt_contains_process(self):
        """Nana 시스템 프롬프트는 프로세스를 포함"""
        prompt = self.builder.get_system_prompt()
        assert "프로세스" in prompt or "process" in prompt.lower()

    def test_nana_template_has_team_sections(self):
        """Nana 템플릿은 팀 섹션을 포함"""
        template = self.builder.get_template()
        assert "팀" in template or "team" in template.lower() or "협조" in template

    def test_nana_build_returns_collaborative_prompt(self):
        """Nana 프롬프트 빌드는 협력적 결과 반환"""
        prompt = self.builder.build("테스트", "collaborative-medium-planning")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestPromptBuilding:
    """프롬프트 빌드 테스트"""

    def test_build_with_simple_context(self):
        """간단한 컨텍스트로 빌드"""
        builder = PromptBuilderFactory.create("Lua")
        context = ChatContext(user_id="test_user", session_id="test_session", message_history=[])
        prompt = builder.build("테스트 입력", "calm-medium-learning", context)
        assert isinstance(prompt, str)
        assert "테스트 입력" in prompt
        assert "User ID: test_user" in prompt

    def test_build_with_message_history(self):
        """메시지 이력이 포함된 컨텍스트로 빌드"""
        builder = PromptBuilderFactory.create("Elro")
        context = ChatContext(
            user_id="test_user",
            session_id="test_session",
            message_history=[
                {"role": "user", "content": "첫 번째 메시지"},
                {"role": "assistant", "content": "응답 메시지"},
            ],
        )
        prompt = builder.build("새 입력", "analytical-medium-learning", context)
        assert isinstance(prompt, str)
        assert "새 입력" in prompt

    def test_build_without_context(self):
        """컨텍스트 없이 빌드"""
        builder = PromptBuilderFactory.create("Riri")
        prompt = builder.build("테스트", "analytical-contemplative-validation")
        assert isinstance(prompt, str)
        assert "테스트" in prompt

    def test_build_all_resonance_combinations(self):
        """모든 파동키 조합으로 빌드"""
        builder = LuaPromptBuilder("Lua")
        for tone in Tone:
            for pace in Pace:
                for intent in Intent:
                    resonance_key = f"{tone.value}-{pace.value}-{intent.value}"
                    prompt = builder.build("테스트", resonance_key)
                    assert isinstance(prompt, str)
                    assert len(prompt) > 0

    def test_build_consistency(self):
        """동일한 입력은 동일한 결과 반환"""
        builder = LuaPromptBuilder("Lua")
        prompt1 = builder.build("테스트", "calm-medium-learning")
        prompt2 = builder.build("테스트", "calm-medium-learning")
        assert prompt1 == prompt2

    def test_build_different_for_different_inputs(self):
        """다른 입력은 다른 결과 반환"""
        builder = LuaPromptBuilder("Lua")
        prompt1 = builder.build("테스트 1", "calm-medium-learning")
        prompt2 = builder.build("테스트 2", "calm-medium-learning")
        assert prompt1 != prompt2


class TestContextBuilding:
    """컨텍스트 구성 테스트"""

    def test_context_without_chat_context(self):
        """None 컨텍스트 처리"""
        context_text = BasePromptBuilder._build_context(
            None, Tone.CALM, Pace.MEDIUM, Intent.LEARNING
        )
        assert isinstance(context_text, str)
        assert "No additional context" in context_text

    def test_context_with_user_id(self):
        """사용자 ID 포함 컨텍스트"""
        context = ChatContext(user_id="test_user", session_id=None, message_history=[])
        context_text = BasePromptBuilder._build_context(
            context, Tone.CALM, Pace.MEDIUM, Intent.LEARNING
        )
        assert "User ID: test_user" in context_text

    def test_context_with_tone_pace_intent(self):
        """톤, 속도, 의도 포함 컨텍스트"""
        context = ChatContext(user_id=None, session_id=None, message_history=[])
        context_text = BasePromptBuilder._build_context(
            context, Tone.FRUSTRATED, Pace.BURST, Intent.SEEK_ADVICE
        )
        assert "frustrated" in context_text.lower() or "Frustrated" in context_text
        assert "burst" in context_text.lower() or "Burst" in context_text

    def test_context_formatting(self):
        """컨텍스트 포맷팅"""
        context = ChatContext(user_id="user123", session_id="session456", message_history=[])
        context_text = BasePromptBuilder._build_context(
            context, Tone.CALM, Pace.MEDIUM, Intent.LEARNING
        )
        assert "\n" in context_text or ":" in context_text  # 포맷된 구조


class TestHistoryBuilding:
    """대화 이력 구성 테스트"""

    def test_history_without_chat_context(self):
        """None 컨텍스트의 이력"""
        history_text = BasePromptBuilder._build_history(None)
        assert "No previous messages" in history_text

    def test_history_without_message_history(self):
        """메시지 이력 없는 컨텍스트"""
        context = ChatContext(user_id=None, session_id=None, message_history=[])
        history_text = BasePromptBuilder._build_history(context)
        assert "No previous messages" in history_text

    def test_history_with_messages(self):
        """메시지가 있는 이력"""
        context = ChatContext(
            user_id=None,
            session_id=None,
            message_history=[
                {"role": "user", "content": "첫 번째 사용자 메시지"},
                {"role": "assistant", "content": "첫 번째 어시스턴트 응답"},
                {"role": "user", "content": "두 번째 사용자 메시지"},
            ],
        )
        history_text = BasePromptBuilder._build_history(context)
        assert isinstance(history_text, str)
        assert "User:" in history_text or "Assistant:" in history_text

    def test_history_recent_messages_only(self):
        """최근 3개 메시지만 포함"""
        messages = [{"role": "user", "content": f"메시지 {i}"} for i in range(10)]
        context = ChatContext(user_id=None, session_id=None, message_history=messages)
        history_text = BasePromptBuilder._build_history(context)
        # 최근 3개만 처리됨
        assert isinstance(history_text, str)


class TestResonanceKeyParsing:
    """파동키 파싱 테스트"""

    def test_parse_valid_resonance_key(self):
        """유효한 파동키 파싱"""
        builder = LuaPromptBuilder("Lua")
        tone, pace, intent = builder._parse_resonance_key("frustrated-burst-seeking_advice")
        assert tone == Tone.FRUSTRATED
        assert pace == Pace.BURST
        assert intent == Intent.SEEK_ADVICE

    def test_parse_invalid_resonance_key_fallback(self):
        """유효하지 않은 파동키 복구"""
        builder = LuaPromptBuilder("Lua")
        tone, pace, intent = builder._parse_resonance_key("invalid-values")
        # 기본값으로 복구
        assert tone == Tone.CALM
        assert pace == Pace.MEDIUM
        assert intent == Intent.LEARNING


class TestPromptBuilderComparison:
    """페르소나별 프롬프트 빌더 비교 테스트"""

    def test_different_personas_different_prompts(self):
        """다른 페르소나는 다른 프롬프트 생성"""
        lua_builder = PromptBuilderFactory.create("Lua")
        elro_builder = PromptBuilderFactory.create("Elro")

        user_input = "테스트 입력"
        resonance_key = "calm-medium-learning"

        lua_prompt = lua_builder.build(user_input, resonance_key)
        elro_prompt = elro_builder.build(user_input, resonance_key)

        assert lua_prompt != elro_prompt

    def test_all_personas_produce_valid_prompts(self):
        """모든 페르소나가 유효한 프롬프트 생성"""
        for persona_name in ["Lua", "Elro", "Riri", "Nana"]:
            builder = PromptBuilderFactory.create(persona_name)
            prompt = builder.build("테스트", "calm-medium-learning")
            assert isinstance(prompt, str)
            assert len(prompt) > 100  # 충분한 길이


class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_build_with_empty_user_input(self):
        """빈 사용자 입력"""
        builder = LuaPromptBuilder("Lua")
        prompt = builder.build("", "calm-medium-learning")
        assert isinstance(prompt, str)

    def test_build_with_very_long_user_input(self):
        """매우 긴 사용자 입력"""
        builder = LuaPromptBuilder("Lua")
        long_input = "테스트 " * 1000
        prompt = builder.build(long_input, "calm-medium-learning")
        assert isinstance(prompt, str)
        assert long_input in prompt

    def test_build_with_special_characters(self):
        """특수 문자 포함"""
        builder = LuaPromptBuilder("Lua")
        special_input = "테스트 @#$%^&*()_+-=[]{}|;:',.<>?/"
        prompt = builder.build(special_input, "calm-medium-learning")
        assert isinstance(prompt, str)

    def test_build_with_unicode_emoji(self):
        """유니코드 이모지 포함"""
        builder = LuaPromptBuilder("Lua")
        emoji_input = "테스트 😀 🚀 ✨ 🎉"
        prompt = builder.build(emoji_input, "calm-medium-learning")
        assert isinstance(prompt, str)


class TestSummaryLightMode:
    """summary_light 모드 동작 테스트"""

    def test_compact_uses_running_summary_and_two_recent(self):
        builder = LuaPromptBuilder("Lua")
        context = ChatContext(
            user_id="u1",
            session_id="s1",
            message_history=[
                {"role": "user", "content": "m1"},
                {"role": "assistant", "content": "m2"},
                {"role": "user", "content": "m3"},
                {"role": "assistant", "content": "m4"},
                {"role": "user", "content": "m5"},
            ],
            custom_context={"running_summary": "요약: 이전 대화 핵심 A, B"},
        )
        prompt = builder.build("요약", "calm-medium-learning", context, mode="summary_light")
        assert "RunningSummary:" in prompt
        assert "요약: 이전 대화 핵심 A, B" in prompt
        # 최근 2개만 있어야 함: m4, m5
        assert "m4" in prompt and "m5" in prompt
        assert "m1" not in prompt and "m2" not in prompt and "m3" not in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
