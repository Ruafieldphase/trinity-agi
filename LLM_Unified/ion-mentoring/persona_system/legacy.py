"""
PersonaOrchestrator 레거시 호환성 레이어

Week 7: 마이그레이션 지원
기존 PersonaPipeline API를 새로운 구조로 매핑
- 기존 코드 100% 작동
- 점진적 마이그레이션 경로 제공
- 모든 기존 메서드 지원
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import ChatContext, PersonaResponse
from .pipeline import PersonaPipeline as NewPersonaPipeline

logger = logging.getLogger(__name__)


class PersonaPipeline:
    """
    레거시 호환성을 위한 PersonaPipeline 래퍼

    기존 코드와 100% 호환되면서 새로운 구조를 사용합니다.

    사용 예시:
    ```python
    # 기존 코드 (변경 없음)
    from persona_system import PersonaPipeline
    pipeline = PersonaPipeline()
    persona = pipeline.get_persona("calm-medium-learning")

    # 또는 새 방식 (권장)
    from persona_system import get_pipeline
    pipeline = get_pipeline()
    result = pipeline.process(input, key, context)
    ```
    """

    def __init__(self):
        """레거시 파이프라인 초기화"""
        self._pipeline = NewPersonaPipeline()
        self._cache = {}  # 최근 라우팅 결과 캐시
        logger.info("Legacy PersonaPipeline initialized")

    # ==================== 기존 API 메서드 ====================

    def process(
        self,
        user_input: str,
        resonance_key: str,
        context: Optional[ChatContext] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PersonaResponse:
        """
        기존 process() 메서드 - 새 파이프라인 사용

        Args:
            user_input: 사용자 입력
            resonance_key: 파동키
            context: 대화 컨텍스트
            metadata: 추가 메타데이터

        Returns:
            PersonaResponse: 처리 결과
        """
        return self._pipeline.process(user_input, resonance_key, context, metadata)

    def get_persona(self, resonance_key: str) -> str:
        """
        기존 get_persona() 메서드

        파동키로부터 최적의 페르소나 이름 반환

        Args:
            resonance_key: 파동키 (tone-pace-intent)

        Returns:
            페르소나 이름 (Lua, Elro, Riri, Nana)
        """
        result = self._pipeline.router.route(resonance_key)
        self._cache[resonance_key] = result
        return result.primary_persona

    def get_confidence(self, resonance_key: str) -> float:
        """
        기존 get_confidence() 메서드

        라우팅의 신뢰도 반환

        Args:
            resonance_key: 파동키

        Returns:
            신뢰도 (0.0-1.0)
        """
        # 캐시 확인
        if resonance_key in self._cache:
            return self._cache[resonance_key].confidence

        result = self._pipeline.router.route(resonance_key)
        self._cache[resonance_key] = result
        return result.confidence

    def get_all_scores(self, resonance_key: str) -> Dict[str, float]:
        """
        기존 get_all_scores() 메서드

        모든 페르소나의 점수 반환

        Args:
            resonance_key: 파동키

        Returns:
            점수 딕셔너리 {페르소나: 점수}
        """
        # 캐시 확인
        if resonance_key in self._cache:
            return self._cache[resonance_key].all_scores

        result = self._pipeline.router.route(resonance_key)
        self._cache[resonance_key] = result
        return result.all_scores

    def get_secondary_persona(self, resonance_key: str) -> str:
        """
        기존 get_secondary_persona() 메서드

        차선 페르소나 반환

        Args:
            resonance_key: 파동키

        Returns:
            차선 페르소나 이름
        """
        # 캐시 확인
        if resonance_key in self._cache:
            return self._cache[resonance_key].secondary_persona

        result = self._pipeline.router.route(resonance_key)
        self._cache[resonance_key] = result
        return result.secondary_persona

    def build_prompt(
        self, user_input: str, persona: str, context: Optional[ChatContext] = None
    ) -> str:
        """
        기존 build_prompt() 메서드

        페르소나별 프롬프트 생성

        Args:
            user_input: 사용자 입력
            persona: 페르소나 이름
            context: 대화 컨텍스트

        Returns:
            생성된 프롬프트
        """
        from .prompts import PromptBuilderFactory

        builder = PromptBuilderFactory.create(persona)
        # 기본 파동키 생성 (persona 기반)
        resonance_key = "calm-medium-learning"  # 기본값
        return builder.build(user_input, resonance_key, context)

    def get_system_prompt(self, persona: str) -> str:
        """
        기존 get_system_prompt() 메서드

        페르소나의 시스템 프롬프트 반환

        Args:
            persona: 페르소나 이름

        Returns:
            시스템 프롬프트 텍스트
        """
        persona_obj = self._pipeline.personas.get(persona)
        if not persona_obj:
            raise ValueError(f"Unknown persona: {persona}")
        return persona_obj.generate_system_prompt()

    def get_user_prompt_template(self, persona: str) -> str:
        """
        기존 get_user_prompt_template() 메서드

        페르소나의 사용자 프롬프트 템플릿 반환

        Args:
            persona: 페르소나 이름

        Returns:
            프롬프트 템플릿
        """
        from .prompts import PromptBuilderFactory

        builder = PromptBuilderFactory.create(persona)
        return builder.get_template()

    # ==================== 호환성 확장 메서드 ====================

    def get_persona_config(self, persona: str) -> Dict[str, Any]:
        """
        기존 코드 지원: 페르소나 설정 반환

        Args:
            persona: 페르소나 이름

        Returns:
            설정 딕셔너리
        """
        if persona not in self._pipeline.personas:
            raise ValueError(f"Unknown persona: {persona}")

        config = self._pipeline.personas[persona].config
        return {
            "name": persona,
            "traits": config.traits,
            "strengths": config.strengths,
            "description": config.description if hasattr(config, "description") else "",
        }

    def get_available_personas(self) -> List[str]:
        """
        사용 가능한 모든 페르소나 반환

        Returns:
            페르소나 이름 리스트
        """
        return list(self._pipeline.personas.keys())

    def validate_resonance_key(self, resonance_key: str) -> bool:
        """
        파동키 유효성 검증

        Args:
            resonance_key: 파동키

        Returns:
            유효 여부
        """
        return self._pipeline.validate_resonance_key(resonance_key)

    def clear_cache(self) -> None:
        """라우팅 결과 캐시 삭제"""
        self._cache.clear()
        logger.info("Cache cleared")

    # ==================== 새 API로의 마이그레이션 지원 ====================

    def get_new_pipeline(self) -> NewPersonaPipeline:
        """
        새로운 PersonaPipeline 획득

        마이그레이션을 위해 새 API 직접 접근 가능

        Returns:
            새 PersonaPipeline 인스턴스
        """
        logger.warning("Direct access to new pipeline. Consider using get_pipeline() instead.")
        return self._pipeline

    def get_router(self):
        """
        ResonanceBasedRouter 직접 접근

        고급 사용자용: 라우팅 알고리즘 세부 제어

        Returns:
            ResonanceBasedRouter 인스턴스
        """
        return self._pipeline.router

    def get_personas(self) -> Dict[str, Any]:
        """
        모든 페르소나 객체 반환

        고급 사용자용: 페르소나 직접 조작

        Returns:
            페르소나 딕셔너리
        """
        return self._pipeline.personas

    def get_prompt_factory(self):
        """
        PromptBuilderFactory 직접 접근

        고급 사용자용: 프롬프트 빌더 커스터마이징

        Returns:
            PromptBuilderFactory 인스턴스
        """
        return self._pipeline.prompt_factory

    # ==================== 마이그레이션 유틸리티 ====================

    def migrate_to_new_api(self) -> str:
        """
        마이그레이션 가이드 반환

        Returns:
            마이그레이션 제안사항
        """
        return """
# PersonaOrchestrator 마이그레이션 가이드

## 기존 코드
```python
from persona_system import PersonaPipeline
pipeline = PersonaPipeline()
persona = pipeline.get_persona(key)
```

## 새 코드 (권장)
```python
from persona_system import get_pipeline
pipeline = get_pipeline()
routing_result = pipeline.router.route(key)
print(routing_result.primary_persona)
print(routing_result.all_scores)
```

## 장점
- 모든 라우팅 점수 확인 가능
- 신뢰도 수준 파악
- 더 나은 성능
- 확장성 증가

## 단계적 마이그레이션
1. 호환성 유지하면서 새 코드 학습
2. 필요한 부분부터 점진적 전환
3. 최종적으로 새 API로 완전 전환
"""

    def get_deprecation_warning(self) -> str:
        """
        deprecation 경고 반환

        Returns:
            경고 메시지
        """
        return """
⚠️  WARNING: PersonaPipeline() 직접 호출은 레거시 방식입니다.

권장 방식:
  from persona_system import get_pipeline
  pipeline = get_pipeline()

이 호환성 레이어는 2024년 말까지 지원됩니다.
마이그레이션 가이드: pipeline.migrate_to_new_api()
"""

    # ==================== 디버깅 메서드 ====================

    def get_statistics(self) -> Dict[str, Any]:
        """
        파이프라인 통계 반환

        Returns:
            통계 정보
        """
        return {
            "cache_size": len(self._cache),
            "cached_keys": list(self._cache.keys()),
            "available_personas": self.get_available_personas(),
            "total_personas": len(self._pipeline.personas),
        }

    def get_debug_info(self, resonance_key: str) -> Dict[str, Any]:
        """
        디버깅 정보 반환

        Args:
            resonance_key: 파동키

        Returns:
            디버깅 정보
        """
        result = self._pipeline.router.route(resonance_key)
        return {
            "resonance_key": resonance_key,
            "primary_persona": result.primary_persona,
            "secondary_persona": result.secondary_persona,
            "confidence": result.confidence,
            "all_scores": result.all_scores,
            "reasoning": result.reasoning if hasattr(result, "reasoning") else "N/A",
            "timestamp": datetime.now().isoformat(),
        }


# ==================== 싱글톤 인스턴스 ====================

_legacy_instance: Optional[PersonaPipeline] = None


def get_legacy_pipeline() -> PersonaPipeline:
    """
    레거시 파이프라인 싱글톤 반환

    Note: 권장하지 않습니다. get_pipeline()을 사용하세요.

    Returns:
        PersonaPipeline 레거시 인스턴스
    """
    global _legacy_instance
    if _legacy_instance is None:
        _legacy_instance = PersonaPipeline()
        logger.warning("Using legacy PersonaPipeline. Consider migrating to get_pipeline()")
    return _legacy_instance


def reset_legacy_pipeline() -> None:
    """
    레거시 파이프라인 리셋 (테스트용)
    """
    global _legacy_instance
    _legacy_instance = None
    logger.info("Legacy pipeline reset")
