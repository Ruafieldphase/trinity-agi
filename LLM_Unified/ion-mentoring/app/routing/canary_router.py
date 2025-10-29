"""
Phase 4 - 카나리 배포 라우터
사용자를 카나리(5%) 또는 레거시(95%) 배포로 결정적 라우팅
"""

import hashlib
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class DeploymentVersion(Enum):
    """배포 버전"""

    LEGACY = "legacy"  # Phase 3 (95%)
    CANARY = "canary"  # Phase 4 (5%)


class CanaryRouter:
    """카나리 배포 라우터"""

    # 카나리 트래픽 비율 (%)
    CANARY_TRAFFIC_PERCENTAGE = 5

    @classmethod
    def get_deployment_version(
        cls, user_id: str, canary_percentage: Optional[int] = None
    ) -> DeploymentVersion:
        """
        사용자 ID 기반 배포 버전 결정

        결정적 해싱을 사용하여 동일 사용자는 항상 같은 버전으로 라우팅됨

        Args:
            user_id: 사용자 고유 ID
            canary_percentage: 카나리 트래픽 비율 (0-100, None이면 기본값 사용)

        Returns:
            DeploymentVersion: LEGACY 또는 CANARY
        """
        if not user_id:
            logger.warning("user_id is empty, defaulting to LEGACY")
            return DeploymentVersion.LEGACY

        if canary_percentage is None:
            canary_percentage = cls.CANARY_TRAFFIC_PERCENTAGE

        # 사용자 ID를 해싱하여 0-99 범위의 값 생성
        hash_value = cls._consistent_hash(user_id)

        # 카나리 트래픽 비율로 분배
        if hash_value < canary_percentage:
            version = DeploymentVersion.CANARY
            logger.debug(f"User {user_id} → CANARY (hash: {hash_value})")
        else:
            version = DeploymentVersion.LEGACY
            logger.debug(f"User {user_id} → LEGACY (hash: {hash_value})")

        return version

    @classmethod
    def _consistent_hash(cls, user_id: str) -> int:
        """
        일관된 해싱으로 0-99 범위의 값 생성

        동일한 user_id는 항상 동일한 값을 반환함

        Args:
            user_id: 사용자 고유 ID

        Returns:
            int: 0-99 범위의 정수
        """
        hash_obj = hashlib.md5(user_id.encode("utf-8"))
        hash_int = int(hash_obj.hexdigest(), 16)
        return hash_int % 100

    @classmethod
    def is_canary_user(cls, user_id: str) -> bool:
        """
        사용자가 카나리 배포 대상인지 확인

        Args:
            user_id: 사용자 고유 ID

        Returns:
            bool: 카나리 사용자면 True
        """
        version = cls.get_deployment_version(user_id)
        return version == DeploymentVersion.CANARY

    @classmethod
    def get_version_string(cls, user_id: str) -> str:
        """
        배포 버전을 문자열로 반환

        Args:
            user_id: 사용자 고유 ID

        Returns:
            str: "legacy" 또는 "canary"
        """
        version = cls.get_deployment_version(user_id)
        return version.value


class CanaryDeploymentConfig:
    """카나리 배포 설정"""

    def __init__(
        self, enabled: bool = True, canary_percentage: int = 5, endpoints_to_canary: list = None
    ):
        """
        초기화

        Args:
            enabled: 카나리 배포 활성화 여부
            canary_percentage: 카나리 트래픽 비율 (%)
            endpoints_to_canary: 카나리 배포를 적용할 엔드포인트 목록
        """
        self.enabled = enabled
        if not 0 <= canary_percentage <= 100:
            raise ValueError(
                f"Canary percentage must be between 0 and 100, got {canary_percentage}"
            )
        self.canary_percentage = canary_percentage
        self.endpoints_to_canary = endpoints_to_canary or [
            "/api/v2/recommend/personalized",
            "/api/v2/recommend/compare",
            "/api/v2/conversations/start",
            "/api/v2/conversations/{session_id}/turn",
            "/api/v2/conversations/{session_id}",
            "/api/v2/conversations/{session_id}/close",
            "/api/v2/conversations",
        ]

        logger.info(
            f"✅ CanaryDeploymentConfig initialized: "
            f"enabled={enabled}, canary_percentage={canary_percentage}%"
        )

    def should_route_to_canary(self, endpoint: str, user_id: str) -> bool:
        """
        주어진 엔드포인트와 사용자에 대해 카나리로 라우팅할지 결정

        Args:
            endpoint: 엔드포인트 경로
            user_id: 사용자 고유 ID

        Returns:
            bool: 카나리로 라우팅하면 True
        """
        if not self.enabled:
            logger.debug("Canary deployment disabled")
            return False

        # 엔드포인트 확인
        if endpoint not in self.endpoints_to_canary:
            logger.debug(f"Endpoint {endpoint} not in canary list")
            return False

        # 사용자 결정
        should_route = CanaryRouter.is_canary_user(user_id)
        return should_route

    def update_canary_percentage(self, new_percentage: int):
        """
        카나리 트래픽 비율 업데이트

        Args:
            new_percentage: 새로운 카나리 트래픽 비율 (0-100)
        """
        if not 0 <= new_percentage <= 100:
            raise ValueError(f"Percentage must be between 0 and 100, got {new_percentage}")

        old_percentage = self.canary_percentage
        self.canary_percentage = new_percentage
        logger.info(f"Canary percentage updated: {old_percentage}% → {new_percentage}%")

    def enable(self):
        """카나리 배포 활성화"""
        self.enabled = True
        logger.info("✅ Canary deployment enabled")

    def disable(self):
        """카나리 배포 비활성화"""
        self.enabled = False
        logger.info("❌ Canary deployment disabled")

    def add_endpoint(self, endpoint: str):
        """카나리 배포 엔드포인트 추가"""
        if endpoint not in self.endpoints_to_canary:
            self.endpoints_to_canary.append(endpoint)
            logger.info(f"Added endpoint to canary: {endpoint}")

    def remove_endpoint(self, endpoint: str):
        """카나리 배포 엔드포인트 제거"""
        if endpoint in self.endpoints_to_canary:
            self.endpoints_to_canary.remove(endpoint)
            logger.info(f"Removed endpoint from canary: {endpoint}")

    def get_config_dict(self) -> dict:
        """설정 딕셔너리로 반환"""
        return {
            "enabled": self.enabled,
            "canary_percentage": self.canary_percentage,
            "endpoints_count": len(self.endpoints_to_canary),
            "endpoints": self.endpoints_to_canary,
        }


# 글로벌 설정 인스턴스
_canary_config: CanaryDeploymentConfig = None


def get_canary_config() -> CanaryDeploymentConfig:
    """카나리 배포 설정 싱글톤"""
    global _canary_config

    if _canary_config is None:
        _canary_config = CanaryDeploymentConfig(enabled=True, canary_percentage=5)
        CanaryRouter.CANARY_TRAFFIC_PERCENTAGE = _canary_config.canary_percentage

    return _canary_config


def configure_canary(
    enabled: bool = True, canary_percentage: int = 5, endpoints_to_canary: list = None
) -> CanaryDeploymentConfig:
    """
    카나리 배포 설정 (앱 시작 시 호출)

    Args:
        enabled: 카나리 배포 활성화 여부
        canary_percentage: 카나리 트래픽 비율 (%)
        endpoints_to_canary: 카나리 배포를 적용할 엔드포인트 목록

    Returns:
        CanaryDeploymentConfig: 설정 객체
    """
    global _canary_config

    _canary_config = CanaryDeploymentConfig(
        enabled=enabled,
        canary_percentage=canary_percentage,
        endpoints_to_canary=endpoints_to_canary,
    )
    CanaryRouter.CANARY_TRAFFIC_PERCENTAGE = _canary_config.canary_percentage

    return _canary_config
