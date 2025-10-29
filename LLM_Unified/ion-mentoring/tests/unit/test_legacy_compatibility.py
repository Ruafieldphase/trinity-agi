"""
레거시 호환성 계층 테스트

Week 7: 마이그레이션 지원
기존 PersonaPipeline API와의 호환성 검증
"""

import pytest

from persona_system import ChatContext, PersonaPipeline
from persona_system.legacy import get_legacy_pipeline, reset_legacy_pipeline
from persona_system.models import Intent, Pace, Tone


class TestLegacyCompatibility:
    """레거시 호환성 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_legacy_pipeline()
        self.pipeline = PersonaPipeline()

    def test_legacy_pipeline_import(self):
        """레거시 PersonaPipeline import 가능"""
        assert self.pipeline is not None
        assert hasattr(self.pipeline, "get_persona")
        assert hasattr(self.pipeline, "get_confidence")

    def test_legacy_get_persona(self):
        """기존 get_persona() 메서드 작동"""
        persona = self.pipeline.get_persona("calm-medium-learning")
        assert persona in ["Lua", "Elro", "Riri", "Nana"]

    def test_legacy_get_confidence(self):
        """기존 get_confidence() 메서드 작동"""
        confidence = self.pipeline.get_confidence("calm-medium-learning")
        assert 0.0 <= confidence <= 1.0

    def test_legacy_get_all_scores(self):
        """기존 get_all_scores() 메서드 작동"""
        scores = self.pipeline.get_all_scores("calm-medium-learning")
        assert len(scores) == 4
        assert set(scores.keys()) == {"Lua", "Elro", "Riri", "Nana"}

    def test_legacy_get_secondary_persona(self):
        """기존 get_secondary_persona() 메서드 작동"""
        secondary = self.pipeline.get_secondary_persona("calm-medium-learning")
        assert secondary in ["Lua", "Elro", "Riri", "Nana"]

    def test_legacy_build_prompt(self):
        """기존 build_prompt() 메서드 작동"""
        prompt = self.pipeline.build_prompt(user_input="테스트", persona="Lua")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_legacy_get_system_prompt(self):
        """기존 get_system_prompt() 메서드 작동"""
        for persona in ["Lua", "Elro", "Riri", "Nana"]:
            system_prompt = self.pipeline.get_system_prompt(persona)
            assert isinstance(system_prompt, str)
            assert len(system_prompt) > 0

    def test_legacy_get_user_prompt_template(self):
        """기존 get_user_prompt_template() 메서드 작동"""
        for persona in ["Lua", "Elro", "Riri", "Nana"]:
            template = self.pipeline.get_user_prompt_template(persona)
            assert isinstance(template, str)
            assert "{" in template  # 템플릿 변수 포함

    def test_legacy_process(self):
        """기존 process() 메서드 작동"""
        result = self.pipeline.process(user_input="테스트", resonance_key="calm-medium-learning")
        assert result is not None
        assert hasattr(result, "content")
        assert hasattr(result, "persona_used")


class TestLegacyCaching:
    """레거시 캐싱 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_legacy_pipeline()
        self.pipeline = PersonaPipeline()

    def test_caching_improves_performance(self):
        """캐싱으로 인한 성능 향상"""
        import time

        key = "calm-medium-learning"

        # 첫 호출 (캐시 없음)
        start1 = time.time()
        result1 = self.pipeline.get_confidence(key)
        time1 = time.time() - start1

        # 두 번째 호출 (캐시 있음)
        start2 = time.time()
        result2 = self.pipeline.get_confidence(key)
        time2 = time.time() - start2

        # 캐시된 호출이 더 빠름
        assert result1 == result2
        assert time2 <= time1  # 캐시가 더 빠르거나 동일

    def test_cache_clear(self):
        """캐시 삭제"""
        key = "calm-medium-learning"
        self.pipeline.get_confidence(key)
        assert len(self.pipeline._cache) > 0

        self.pipeline.clear_cache()
        assert len(self.pipeline._cache) == 0


class TestLegacyExtendedAPI:
    """레거시 확장 API 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_legacy_pipeline()
        self.pipeline = PersonaPipeline()

    def test_get_persona_config(self):
        """페르소나 설정 조회"""
        for persona in ["Lua", "Elro", "Riri", "Nana"]:
            config = self.pipeline.get_persona_config(persona)
            assert config["name"] == persona
            assert "traits" in config
            assert "strengths" in config

    def test_get_available_personas(self):
        """사용 가능한 페르소나 조회"""
        personas = self.pipeline.get_available_personas()
        assert len(personas) == 4
        assert set(personas) == {"Lua", "Elro", "Riri", "Nana"}

    def test_validate_resonance_key(self):
        """파동키 검증"""
        assert self.pipeline.validate_resonance_key("calm-medium-learning") is True
        assert self.pipeline.validate_resonance_key("invalid-key") is False

    def test_get_statistics(self):
        """통계 조회"""
        self.pipeline.get_confidence("calm-medium-learning")
        stats = self.pipeline.get_statistics()
        assert "cache_size" in stats
        assert "available_personas" in stats

    def test_get_debug_info(self):
        """디버깅 정보 조회"""
        debug_info = self.pipeline.get_debug_info("calm-medium-learning")
        assert "primary_persona" in debug_info
        assert "secondary_persona" in debug_info
        assert "confidence" in debug_info
        assert "all_scores" in debug_info


class TestLegacyMigrationSupport:
    """마이그레이션 지원 기능 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_legacy_pipeline()
        self.pipeline = PersonaPipeline()

    def test_get_new_pipeline(self):
        """새 파이프라인 접근"""
        new_pipeline = self.pipeline.get_new_pipeline()
        assert new_pipeline is not None
        assert hasattr(new_pipeline, "process")

    def test_get_router(self):
        """라우터 직접 접근"""
        router = self.pipeline.get_router()
        assert router is not None
        assert hasattr(router, "route")

    def test_get_personas(self):
        """페르소나 객체 접근"""
        personas = self.pipeline.get_personas()
        assert len(personas) == 4
        for persona in personas.values():
            assert hasattr(persona, "generate_system_prompt")

    def test_get_prompt_factory(self):
        """프롬프트 팩토리 접근"""
        factory = self.pipeline.get_prompt_factory()
        assert factory is not None
        assert hasattr(factory, "create")

    def test_migrate_to_new_api_guidance(self):
        """마이그레이션 가이드"""
        guidance = self.pipeline.migrate_to_new_api()
        assert isinstance(guidance, str)
        assert "get_pipeline" in guidance
        assert "새 코드" in guidance or "new" in guidance.lower()

    def test_deprecation_warning(self):
        """Deprecation 경고"""
        warning = self.pipeline.get_deprecation_warning()
        assert isinstance(warning, str)
        assert "WARNING" in warning or "경고" in warning


class TestLegacySingleton:
    """싱글톤 패턴 테스트"""

    def test_get_legacy_pipeline_singleton(self):
        """레거시 파이프라인 싱글톤"""
        reset_legacy_pipeline()
        pipeline1 = get_legacy_pipeline()
        pipeline2 = get_legacy_pipeline()
        assert pipeline1 is pipeline2

    def test_reset_legacy_pipeline(self):
        """레거시 파이프라인 리셋"""
        reset_legacy_pipeline()
        pipeline1 = get_legacy_pipeline()
        reset_legacy_pipeline()
        pipeline2 = get_legacy_pipeline()
        assert pipeline1 is not pipeline2


class TestLegacyAllResonanceKeys:
    """모든 파동키 조합 호환성 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_legacy_pipeline()
        self.pipeline = PersonaPipeline()

    def test_all_resonance_combinations_work(self):
        """모든 파동키 조합에서 작동"""
        combinations = 0
        for tone in Tone:
            for pace in Pace:
                for intent in Intent:
                    key = f"{tone.value}-{pace.value}-{intent.value}"

                    # 모든 기존 메서드 호출
                    persona = self.pipeline.get_persona(key)
                    confidence = self.pipeline.get_confidence(key)
                    scores = self.pipeline.get_all_scores(key)

                    assert persona in ["Lua", "Elro", "Riri", "Nana"]
                    assert 0.0 <= confidence <= 1.0
                    assert len(scores) == 4

                    combinations += 1

        # Tone: 9, Pace: 4, Intent: 6 = 216 combinations
        assert combinations == 9 * 4 * 6


class TestLegacyBackwardCompatibility:
    """기존 코드와의 호환성 검증"""

    def test_existing_import_works(self):
        """기존 import 방식 작동"""
        from persona_system import PersonaPipeline as LegacyPipeline

        pipeline = LegacyPipeline()
        assert pipeline is not None

    def test_existing_api_calls_work(self):
        """기존 API 호출 작동"""
        pipeline = PersonaPipeline()

        # 기존 코드 패턴
        persona = pipeline.get_persona("calm-medium-learning")
        confidence = pipeline.get_confidence("calm-medium-learning")

        assert persona in ["Lua", "Elro", "Riri", "Nana"]
        assert 0.0 <= confidence <= 1.0

    def test_legacy_with_context(self):
        """컨텍스트를 포함한 레거시 호출"""
        context = ChatContext(user_id="user123", session_id="session456", message_history=[])
        result = self.pipeline.process(
            user_input="테스트", resonance_key="calm-medium-learning", context=context
        )
        assert result.persona_used is not None

    def test_legacy_with_metadata(self):
        """메타데이터를 포함한 레거시 호출"""
        metadata = {"source": "legacy", "version": "1.0"}
        result = self.pipeline.process(
            user_input="테스트", resonance_key="calm-medium-learning", metadata=metadata
        )
        assert result.metadata is not None

    def setup_method(self):
        """테스트 설정"""
        reset_legacy_pipeline()
        self.pipeline = PersonaPipeline()


class TestLegacyErrorHandling:
    """레거시 에러 처리 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_legacy_pipeline()
        self.pipeline = PersonaPipeline()

    def test_invalid_persona_raises_error(self):
        """유효하지 않은 페르소나 에러"""
        with pytest.raises(ValueError):
            self.pipeline.get_system_prompt("InvalidPersona")

    def test_empty_input_handled(self):
        """빈 입력 처리"""
        result = self.pipeline.process(user_input="", resonance_key="calm-medium-learning")
        assert result is not None

    def test_invalid_resonance_key_handled(self):
        """유효하지 않은 파동키 처리"""
        # 기본값으로 복구되어야 함
        persona = self.pipeline.get_persona("invalid-key")
        assert persona in ["Lua", "Elro", "Riri", "Nana"]


class TestLegacyPerformance:
    """레거시 성능 테스트"""

    def setup_method(self):
        """각 테스트 전 설정"""
        reset_legacy_pipeline()
        self.pipeline = PersonaPipeline()

    def test_get_persona_performance(self):
        """get_persona() 성능 (< 50ms)"""
        import time

        start = time.time()
        for _ in range(10):
            self.pipeline.get_persona("calm-medium-learning")
        elapsed = (time.time() - start) * 1000

        avg = elapsed / 10
        assert avg < 50  # 평균 50ms 이내

    def test_build_prompt_performance(self):
        """build_prompt() 성능 (< 100ms)"""
        import time

        start = time.time()
        for _ in range(5):
            self.pipeline.build_prompt("테스트", "Lua")
        elapsed = (time.time() - start) * 1000

        avg = elapsed / 5
        assert avg < 100  # 평균 100ms 이내


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
