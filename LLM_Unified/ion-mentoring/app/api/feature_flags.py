"""
Feature Flag 관리 시스템

Lumen Gateway 통합 등 새로운 기능을 안전하게 배포하고 테스트하기 위한 Feature Flag 관리
"""

import logging
import os
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FeatureFlagName(str, Enum):
    """사용 가능한 Feature Flag 목록"""

    LUMEN_GATEWAY = "LUMEN_GATEWAY"
    ADVANCED_ANALYTICS = "ADVANCED_ANALYTICS"
    A_B_TESTING = "A_B_TESTING"
    PERFORMANCE_OPTIMIZATION = "PERFORMANCE_OPTIMIZATION"


class FeatureFlag(BaseModel):
    """Feature Flag 모델"""

    name: str
    enabled: bool
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureFlagManager:
    """
    Feature Flag 관리자

    환경 변수 기반으로 Feature Flag를 관리합니다.
    - 프로덕션 안전성: 기본값은 항상 False (비활성화)
    - 명시적 활성화: 환경 변수로만 활성화 가능
    - 런타임 오버라이드: 특수한 경우 런타임에서 토글 가능
    """

    _instance = None
    _flags: Dict[str, FeatureFlag] = {}
    _runtime_overrides: Dict[str, bool] = {}

    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_flags()
        return cls._instance

    def _initialize_flags(self):
        """환경 변수에서 Feature Flag 초기화"""

        # Lumen Gateway Feature Flag (config.py와 동일한 환경 변수명 사용)
        lumen_enabled = os.getenv("LUMEN_GATE_ENABLED", "false").lower() in ["true", "1", "yes"]
        self._flags[FeatureFlagName.LUMEN_GATEWAY] = FeatureFlag(
            name=FeatureFlagName.LUMEN_GATEWAY,
            enabled=lumen_enabled,
            description="Lumen Gateway 하이브리드 AI 시스템 통합",
            metadata={
                "version": "1.0.0",
                "personas": ["🌙 루아", "📐 엘로", "🌏 누리", "✒️ 세나"],
                "inference_modes": ["google_ai", "local_llm", "naeda_cloud"],
            },
        )

        # Advanced Analytics Feature Flag
        analytics_enabled = os.getenv("ADVANCED_ANALYTICS_ENABLED", "false").lower() in [
            "true",
            "1",
            "yes",
        ]
        self._flags[FeatureFlagName.ADVANCED_ANALYTICS] = FeatureFlag(
            name=FeatureFlagName.ADVANCED_ANALYTICS,
            enabled=analytics_enabled,
            description="고급 분석 및 사용자 행동 추적",
            metadata={"tracking_level": "detailed"},
        )

        # A/B Testing Feature Flag
        ab_testing_enabled = os.getenv("AB_TESTING_ENABLED", "false").lower() in [
            "true",
            "1",
            "yes",
        ]
        self._flags[FeatureFlagName.A_B_TESTING] = FeatureFlag(
            name=FeatureFlagName.A_B_TESTING,
            enabled=ab_testing_enabled,
            description="A/B 테스트 프레임워크",
            metadata={"test_groups": ["control", "variant_a", "variant_b"]},
        )

        # Performance Optimization Feature Flag
        perf_optimization_enabled = os.getenv(
            "PERFORMANCE_OPTIMIZATION_ENABLED", "false"
        ).lower() in ["true", "1", "yes"]
        self._flags[FeatureFlagName.PERFORMANCE_OPTIMIZATION] = FeatureFlag(
            name=FeatureFlagName.PERFORMANCE_OPTIMIZATION,
            enabled=perf_optimization_enabled,
            description="성능 최적화 (토큰 절약, 캐싱 등)",
            metadata={"optimizations": ["token_saver", "response_cache", "request_batching"]},
        )

        logger.info(
            f"Feature flags initialized: {len(self._flags)} flags loaded",
            extra={
                "lumen_enabled": lumen_enabled,
                "analytics_enabled": analytics_enabled,
                "ab_testing_enabled": ab_testing_enabled,
                "perf_optimization_enabled": perf_optimization_enabled,
            },
        )

    def is_enabled(self, flag_name: FeatureFlagName) -> bool:
        """
        Feature Flag가 활성화되었는지 확인

        Args:
            flag_name: 확인할 Feature Flag 이름

        Returns:
            bool: 활성화 여부
        """
        # 런타임 오버라이드 우선 적용
        if flag_name in self._runtime_overrides:
            return self._runtime_overrides[flag_name]

        # 환경 변수 기반 Flag 확인
        flag = self._flags.get(flag_name)
        if flag is None:
            logger.warning(f"Unknown feature flag: {flag_name}, defaulting to False")
            return False

        return flag.enabled

    def get_flag(self, flag_name: FeatureFlagName) -> Optional[FeatureFlag]:
        """
        Feature Flag 전체 정보 조회

        Args:
            flag_name: 조회할 Feature Flag 이름

        Returns:
            FeatureFlag: Flag 정보 (없으면 None)
        """
        return self._flags.get(flag_name)

    def set_runtime_override(self, flag_name: FeatureFlagName, enabled: bool):
        """
        런타임에서 Feature Flag 오버라이드 설정

        주의: 이 메서드는 테스트나 긴급 상황에서만 사용해야 합니다.
        프로덕션에서는 환경 변수를 사용하세요.

        Args:
            flag_name: Feature Flag 이름
            enabled: 활성화 여부
        """
        self._runtime_overrides[flag_name] = enabled
        logger.warning(
            f"Runtime override set for {flag_name}: {enabled}",
            extra={"flag_name": flag_name, "enabled": enabled},
        )

    def clear_runtime_override(self, flag_name: FeatureFlagName):
        """
        런타임 오버라이드 제거

        Args:
            flag_name: Feature Flag 이름
        """
        if flag_name in self._runtime_overrides:
            del self._runtime_overrides[flag_name]
            logger.info(f"Runtime override cleared for {flag_name}")

    def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """
        모든 Feature Flag 조회

        Returns:
            Dict[str, FeatureFlag]: 모든 Flag 정보
        """
        return self._flags.copy()

    def get_enabled_flags(self) -> Dict[str, FeatureFlag]:
        """
        활성화된 Feature Flag만 조회

        Returns:
            Dict[str, FeatureFlag]: 활성화된 Flag 정보
        """
        return {name: flag for name, flag in self._flags.items() if self.is_enabled(name)}


# 싱글톤 인스턴스 생성
feature_flags = FeatureFlagManager()


# 편의 함수들
def is_lumen_enabled() -> bool:
    """Lumen Gateway가 활성화되었는지 확인"""
    return feature_flags.is_enabled(FeatureFlagName.LUMEN_GATEWAY)


def is_analytics_enabled() -> bool:
    """고급 분석이 활성화되었는지 확인"""
    return feature_flags.is_enabled(FeatureFlagName.ADVANCED_ANALYTICS)


def is_ab_testing_enabled() -> bool:
    """A/B 테스트가 활성화되었는지 확인"""
    return feature_flags.is_enabled(FeatureFlagName.A_B_TESTING)


def is_performance_optimization_enabled() -> bool:
    """성능 최적화가 활성화되었는지 확인"""
    return feature_flags.is_enabled(FeatureFlagName.PERFORMANCE_OPTIMIZATION)


# 디버그용 함수
def print_feature_flags_status():
    """현재 Feature Flag 상태를 출력 (디버그용)"""
    all_flags = feature_flags.get_all_flags()
    print("\n" + "=" * 50)
    print("Feature Flags Status")
    print("=" * 50)
    for name, flag in all_flags.items():
        status = "✅ ENABLED" if flag.enabled else "❌ DISABLED"
        print(f"{status} | {name}")
        if flag.description:
            print(f"  Description: {flag.description}")
        if flag.metadata:
            print(f"  Metadata: {flag.metadata}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    # 테스트 실행
    print_feature_flags_status()

    # 런타임 오버라이드 테스트
    print("\n🔧 Testing runtime override...")
    print(f"Before: LUMEN_GATEWAY = {is_lumen_enabled()}")
    feature_flags.set_runtime_override(FeatureFlagName.LUMEN_GATEWAY, True)
    print(f"After override: LUMEN_GATEWAY = {is_lumen_enabled()}")
    feature_flags.clear_runtime_override(FeatureFlagName.LUMEN_GATEWAY)
    print(f"After clear: LUMEN_GATEWAY = {is_lumen_enabled()}")
