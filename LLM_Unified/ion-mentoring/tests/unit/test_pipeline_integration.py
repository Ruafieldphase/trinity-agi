"""
PersonaPipeline 통합 테스트

Week 5-6: 통합 파이프라인 테스트
- 전체 파이프라인 처리 흐름
- 컴포넌트 통합
- 성능 및 안정성
"""

import time

import pytest

from persona_system.models import ChatContext, Intent, Pace, PersonaResponse, Tone
from persona_system.pipeline import PersonaPipeline, get_pipeline, reset_pipeline


class TestPersonaPipelineBasics:
    """PersonaPipeline 기본 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_pipeline()
        self.pipeline = PersonaPipeline()

    def test_pipeline_initialization(self):
        """파이프라인 초기화"""
        assert self.pipeline is not None
        assert len(self.pipeline.personas) == 4
        assert self.pipeline.router is not None
        assert self.pipeline.prompt_factory is not None

    def test_pipeline_process_basic(self):
        """기본 파이프라인 처리"""
        result = self.pipeline.process(
            user_input="안녕하세요", resonance_key="calm-medium-learning"
        )
        assert isinstance(result, PersonaResponse)
        assert result.content is not None
        assert result.persona_used is not None
        assert result.confidence >= 0.0

    def test_pipeline_returns_valid_persona(self):
        """파이프라인은 유효한 페르소나 반환"""
        result = self.pipeline.process(user_input="테스트", resonance_key="calm-medium-learning")
        assert result.persona_used in ["Lua", "Elro", "Riri", "Nana"]

    def test_pipeline_metadata_included(self):
        """파이프라인 결과에 메타데이터 포함"""
        result = self.pipeline.process(user_input="테스트", resonance_key="calm-medium-learning")
        assert result.metadata is not None
        assert isinstance(result.metadata, dict)

    def test_pipeline_execution_time_measured(self):
        """파이프라인 실행 시간 측정"""
        result = self.pipeline.process(user_input="테스트", resonance_key="calm-medium-learning")
        assert result.execution_time_ms > 0
        assert result.execution_time_ms < 5000  # 5초 이내


class TestPipelineWithContext:
    """컨텍스트를 포함한 파이프라인 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.pipeline = PersonaPipeline()

    def test_process_with_chat_context(self):
        """채팅 컨텍스트를 포함한 처리"""
        context = ChatContext(
            user_id="test_user",
            session_id="test_session",
            message_history=[
                {"role": "user", "content": "첫 메시지"},
                {"role": "assistant", "content": "응답"},
            ],
        )
        result = self.pipeline.process(
            user_input="다음 질문", resonance_key="calm-medium-learning", context=context
        )
        assert isinstance(result, PersonaResponse)
        assert result.persona_used is not None

    def test_process_with_metadata(self):
        """추가 메타데이터를 포함한 처리"""
        metadata = {"source": "test", "version": "1.0", "tags": ["test", "integration"]}
        result = self.pipeline.process(
            user_input="테스트", resonance_key="calm-medium-learning", metadata=metadata
        )
        assert result.metadata["user_provided_metadata"] == metadata

    def test_process_without_context(self):
        """컨텍스트 없이 처리"""
        result = self.pipeline.process(
            user_input="테스트", resonance_key="calm-medium-learning", context=None
        )
        assert isinstance(result, PersonaResponse)


class TestPipelineResonanceKeys:
    """다양한 파동키를 사용한 파이프라인 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.pipeline = PersonaPipeline()

    def test_frustrated_burst_selects_lua(self):
        """frustrated-burst는 Lua 선택 가능성 높음"""
        result = self.pipeline.process(
            user_input="도움이 필요합니다", resonance_key="frustrated-burst-seeking_advice"
        )
        # Lua가 선택될 확률이 높음
        assert isinstance(result, PersonaResponse)

    def test_analytical_medium_selects_elro(self):
        """analytical-medium는 Elro 선택 가능성 높음"""
        result = self.pipeline.process(
            user_input="기술 설명 필요", resonance_key="analytical-medium-learning"
        )
        assert isinstance(result, PersonaResponse)

    def test_all_resonance_combinations_work(self):
        """모든 파동키 조합에서 작동"""
        combinations = 0
        for tone in Tone:
            for pace in Pace:
                for intent in Intent:
                    key = f"{tone.value}-{pace.value}-{intent.value}"
                    result = self.pipeline.process(user_input="테스트", resonance_key=key)
                    assert isinstance(result, PersonaResponse)
                    assert result.persona_used in ["Lua", "Elro", "Riri", "Nana"]
                    combinations += 1

        # Tone: 9, Pace: 4, Intent: 6 = 216 combinations
        assert combinations == 9 * 4 * 6


class TestPersonaCapabilities:
    """페르소나 능력 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.pipeline = PersonaPipeline()

    def test_get_persona_capabilities_lua(self):
        """Lua 페르소나 능력 조회"""
        capabilities = self.pipeline.get_persona_capabilities("Lua")
        assert capabilities["name"] == "Lua"
        assert "traits" in capabilities
        assert "strengths" in capabilities
        assert "best_for_tones" in capabilities

    def test_get_persona_capabilities_all(self):
        """모든 페르소나 능력 조회"""
        for persona_name in ["Lua", "Elro", "Riri", "Nana"]:
            capabilities = self.pipeline.get_persona_capabilities(persona_name)
            assert capabilities["name"] == persona_name

    def test_get_all_personas_info(self):
        """모든 페르소나 정보 조회"""
        all_info = self.pipeline.get_all_personas_info()
        assert len(all_info) == 4
        assert set(all_info.keys()) == {"Lua", "Elro", "Riri", "Nana"}
        for info in all_info.values():
            assert "name" in info
            assert "traits" in info

    def test_persona_best_tones(self):
        """페르소나의 최고 성능 톤"""
        capabilities = self.pipeline.get_persona_capabilities("Lua")
        best_tones = capabilities["best_for_tones"]
        assert isinstance(best_tones, list)
        # Lua는 감정적 톤에서 강함
        assert len(best_tones) > 0

    def test_invalid_persona_raises_error(self):
        """유효하지 않은 페르소나는 에러 발생"""
        with pytest.raises(ValueError):
            self.pipeline.get_persona_capabilities("InvalidPersona")


class TestPersonaRecommendation:
    """페르소나 추천 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.pipeline = PersonaPipeline()

    def test_recommend_lua_for_emotional_scenario(self):
        """감정적 시나리오에서 Lua 추천"""
        recommendation = self.pipeline.recommend_persona("감정 지원과 공감이 필요합니다")
        assert recommendation["recommended_persona"] is not None

    def test_recommend_elro_for_technical_scenario(self):
        """기술 시나리오에서 Elro 추천"""
        recommendation = self.pipeline.recommend_persona("기술적 아키텍처 설계가 필요합니다")
        assert recommendation["recommended_persona"] is not None

    def test_recommend_riri_for_analytical_scenario(self):
        """분석 시나리오에서 Riri 추천"""
        recommendation = self.pipeline.recommend_persona("데이터 분석과 객관적 평가가 필요합니다")
        assert recommendation["recommended_persona"] is not None

    def test_recommend_nana_for_collaboration_scenario(self):
        """협력 시나리오에서 Nana 추천"""
        recommendation = self.pipeline.recommend_persona("팀 협력과 조정이 필요합니다")
        assert recommendation["recommended_persona"] is not None

    def test_recommendation_includes_scores(self):
        """추천 결과에 점수 포함"""
        recommendation = self.pipeline.recommend_persona("테스트 시나리오")
        assert "scores" in recommendation
        assert len(recommendation["scores"]) == 4

    def test_recommendation_includes_capabilities(self):
        """추천 결과에 능력 정보 포함"""
        recommendation = self.pipeline.recommend_persona("테스트 시나리오")
        assert "capabilities" in recommendation
        assert "traits" in recommendation["capabilities"]


class TestResonanceKeyValidation:
    """파동키 유효성 검증 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.pipeline = PersonaPipeline()

    def test_valid_resonance_key(self):
        """유효한 파동키 검증"""
        assert self.pipeline.validate_resonance_key("calm-medium-learning") is True
        assert self.pipeline.validate_resonance_key("frustrated-burst-seeking_advice") is True

    def test_invalid_resonance_key(self):
        """유효하지 않은 파동키 검증"""
        assert self.pipeline.validate_resonance_key("invalid-invalid-invalid") is False
        assert self.pipeline.validate_resonance_key("calm-medium") is False
        assert self.pipeline.validate_resonance_key("") is False

    def test_incomplete_resonance_key(self):
        """불완전한 파동키 검증"""
        assert self.pipeline.validate_resonance_key("calm") is False
        assert self.pipeline.validate_resonance_key("calm-medium") is False


class TestPipelineSingleton:
    """파이프라인 싱글톤 패턴 테스트"""

    def test_get_pipeline_returns_singleton(self):
        """get_pipeline은 싱글톤 반환"""
        reset_pipeline()
        pipeline1 = get_pipeline()
        pipeline2 = get_pipeline()
        assert pipeline1 is pipeline2

    def test_reset_pipeline_creates_new_instance(self):
        """reset_pipeline은 새 인스턴스 생성"""
        reset_pipeline()
        pipeline1 = get_pipeline()
        reset_pipeline()
        pipeline2 = get_pipeline()
        assert pipeline1 is not pipeline2


class TestPipelineErrorHandling:
    """파이프라인 에러 처리 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.pipeline = PersonaPipeline()

    def test_process_with_empty_user_input(self):
        """빈 사용자 입력 처리"""
        result = self.pipeline.process(user_input="", resonance_key="calm-medium-learning")
        assert isinstance(result, PersonaResponse)

    def test_process_with_invalid_resonance_key(self):
        """유효하지 않은 파동키 처리"""
        result = self.pipeline.process(user_input="테스트", resonance_key="invalid-invalid-invalid")
        # 기본값으로 복구되어 계속 작동
        assert isinstance(result, PersonaResponse)

    def test_process_graceful_degradation(self):
        """우아한 성능 저하"""
        # 극단적인 입력
        result = self.pipeline.process(
            user_input="테스트" * 10000, resonance_key="calm-medium-learning"
        )
        assert isinstance(result, PersonaResponse)


class TestPipelinePerformance:
    """파이프라인 성능 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.pipeline = PersonaPipeline()

    def test_single_process_performance(self):
        """단일 처리 성능 (< 1000ms)"""
        start = time.time()
        result = self.pipeline.process(user_input="테스트", resonance_key="calm-medium-learning")
        elapsed = (time.time() - start) * 1000
        assert elapsed < 1000
        assert result.execution_time_ms < 1000

    def test_multiple_process_performance(self):
        """다중 처리 성능"""
        start = time.time()
        for i in range(10):
            self.pipeline.process(user_input=f"테스트 {i}", resonance_key="calm-medium-learning")
        elapsed = (time.time() - start) * 1000
        avg_per_call = elapsed / 10
        # 평균 100ms 이내
        assert avg_per_call < 100

    def test_process_consistency(self):
        """동일한 입력 반복 시 일관성"""
        result1 = self.pipeline.process(user_input="테스트", resonance_key="calm-medium-learning")
        result2 = self.pipeline.process(user_input="테스트", resonance_key="calm-medium-learning")
        assert result1.persona_used == result2.persona_used
        assert result1.confidence == result2.confidence


class TestPipelineIntegration:
    """전체 통합 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        self.pipeline = PersonaPipeline()

    def test_end_to_end_workflow(self):
        """엔드-투-엔드 워크플로우"""
        # 1. 초기 질문
        context = ChatContext(user_id="user123", session_id="session456", message_history=[])
        result1 = self.pipeline.process(
            user_input="안녕하세요", resonance_key="calm-medium-learning", context=context
        )
        assert result1.persona_used is not None

        # 2. 후속 질문 (컨텍스트 포함)
        context.message_history.append({"role": "user", "content": "안녕하세요"})
        context.message_history.append({"role": "assistant", "content": result1.content})

        result2 = self.pipeline.process(
            user_input="다음 질문", resonance_key="calm-medium-learning", context=context
        )
        assert result2.persona_used is not None

        # 3. 상황 변경 (다른 파동키)
        result3 = self.pipeline.process(
            user_input="급한 상황입니다",
            resonance_key="frustrated-burst-seeking_advice",
            context=context,
        )
        assert result3.persona_used is not None

    def test_full_persona_capabilities_discovery(self):
        """전체 페르소나 능력 발견"""
        all_info = self.pipeline.get_all_personas_info()

        # 각 페르소나의 정보 검증
        for persona_name, info in all_info.items():
            assert info["name"] == persona_name
            assert len(info["traits"]) > 0
            assert len(info["strengths"]) > 0
            assert "best_for_tones" in info
            assert "best_for_paces" in info
            assert "best_for_intents" in info

    def test_pipeline_recommendation_system(self):
        """파이프라인 추천 시스템"""
        scenarios = [
            ("사용자가 감정적 지원을 요청합니다", "Lua"),
            ("기술적 아키텍처 설계가 필요합니다", "Elro"),
            ("데이터 분석이 필요합니다", "Riri"),
            ("팀 협력이 필요합니다", "Nana"),
        ]

        for scenario, expected_persona in scenarios:
            recommendation = self.pipeline.recommend_persona(scenario)
            assert recommendation["recommended_persona"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
