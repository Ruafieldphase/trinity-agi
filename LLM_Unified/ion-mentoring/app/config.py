"""
FastAPI 애플리케이션 설정 관리

환경 변수 및 설정 값을 중앙에서 관리합니다.
"""

import threading
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    def __init__(self, **values):
        # cors_origins이 str로 들어오면 콤마 구분 파싱
        co = values.get("cors_origins")
        if isinstance(co, str):
            items = [origin.strip() for origin in co.split(",") if origin.strip()]
            values["cors_origins"] = items or ["*"]
        super().__init__(**values)

    """애플리케이션 설정"""

    # 기본 설정
    app_name: str = Field(
        default="내다AI Ion API",
        description="애플리케이션 이름",  # ENV: APP_NAME
        validation_alias="APP_NAME",
    )
    app_version: str = Field(
        default="1.0.0",
        description="버전",  # ENV: APP_VERSION
        validation_alias="APP_VERSION",
    )
    environment: str = Field(
        default="development",
        description="환경 (development/production)",  # ENV: ENVIRONMENT
        validation_alias="ENVIRONMENT",
    )

    # 배포 버전 구분 (LEGACY / CANARY)
    deployment_version: str = Field(
        default="LEGACY",
        description="배포 버전 (LEGACY/CANARY)",  # ENV: DEPLOYMENT_VERSION
        validation_alias="DEPLOYMENT_VERSION",
    )

    # 서버 설정
    host: str = Field(
        default="0.0.0.0",
        description="서버 호스트",  # ENV: HOST
        validation_alias="HOST",
    )
    port: int = Field(
        default=8080,
        description="서버 포트",  # ENV: PORT
        validation_alias="PORT",
    )
    reload: bool = Field(
        default=True,
        description="Hot reload (개발용)",  # ENV: RELOAD
        validation_alias="RELOAD",
    )

    # CORS 설정
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="허용할 Origin 목록 (프로덕션에서는 제한 필요)",  # ENV: CORS_ORIGINS
    )

    # Vertex AI 설정
    vertex_project_id: Optional[str] = Field(
        default=None,
        description="GCP 프로젝트 ID",  # ENV: VERTEX_PROJECT_ID
        validation_alias="VERTEX_PROJECT_ID",
    )
    vertex_location: str = Field(
        default="us-central1",
        description="Vertex AI 리전",  # ENV: VERTEX_LOCATION
        validation_alias="VERTEX_LOCATION",
    )
    vertex_model: str = Field(
        default="gemini-1.5-flash-002",
        description="사용할 Vertex AI 모델",  # ENV: VERTEX_MODEL
        validation_alias="VERTEX_MODEL",
    )

    # 로깅 설정
    log_level: str = Field(
        default="INFO",
        description="로그 레벨",  # ENV: LOG_LEVEL
        validation_alias="LOG_LEVEL",
    )

    # Rate Limiting 설정
    rate_limit_enabled: bool = Field(
        default=True,
        description="Rate Limiting 활성화",  # ENV: RATE_LIMIT_ENABLED
        validation_alias="RATE_LIMIT_ENABLED",
    )
    rate_limit_calls: int = Field(
        default=10,
        description="분당 요청 제한",  # ENV: RATE_LIMIT_CALLS
        validation_alias="RATE_LIMIT_CALLS",
    )
    rate_limit_period: int = Field(
        default=60,
        description="제한 기간 (초)",  # ENV: RATE_LIMIT_PERIOD
        validation_alias="RATE_LIMIT_PERIOD",
    )

    # Phase 4 카나리 설정
    phase4_enabled: bool = Field(
        default=False,
        description="Phase 4 카나리 기능 활성화 여부",  # ENV: PHASE4_ENABLED
        validation_alias="PHASE4_ENABLED",
    )
    canary_traffic_percentage: int = Field(
        default=5,
        description="카나리 트래픽 비율 (0-100)",  # ENV: CANARY_TRAFFIC_PERCENTAGE
        validation_alias="CANARY_TRAFFIC_PERCENTAGE",
    )

    # Google Cloud Logging 설정 (프로덕션)
    gcp_project_id: Optional[str] = Field(
        default=None,
        description="Google Cloud Project ID (프로덕션 로깅용)",  # ENV: GCP_PROJECT_ID
        validation_alias="GCP_PROJECT_ID",
    )
    use_cloud_logging: bool = Field(
        default=False,
        description="Google Cloud Logging 사용",  # ENV: USE_CLOUD_LOGGING
        validation_alias="USE_CLOUD_LOGGING",
    )

    # Lumen 게이트웨이 통합 (가드레일)
    lumen_gate_enabled: bool = Field(
        default=False,
        description="Lumen 게이트웨이 연동 활성화 (기본 비활성화)",  # ENV: LUMEN_GATE_ENABLED
        validation_alias="LUMEN_GATE_ENABLED",
    )
    lumen_gateway_url: Optional[str] = Field(
        default=None,
        description="Lumen 게이트웨이 기본 엔드포인트 (예: http://localhost:8081/chat)",  # ENV: LUMEN_GATEWAY_URL
        validation_alias="LUMEN_GATEWAY_URL",
    )
    lumen_health_timeout_ms: int = Field(
        default=15000,
        description="Lumen 헬스/스모크 체크 타임아웃(ms)",  # ENV: LUMEN_HEALTH_TIMEOUT_MS
        validation_alias="LUMEN_HEALTH_TIMEOUT_MS",
    )

    # Redis 캐싱 설정 (Phase 5 Priority 2)
    redis_enabled: bool = Field(
        default=False,
        description="Redis 캐싱 활성화 여부",  # ENV: REDIS_ENABLED
        validation_alias="REDIS_ENABLED",
    )
    redis_host: str = Field(
        default="localhost",
        description="Redis 호스트",  # ENV: REDIS_HOST
        validation_alias="REDIS_HOST",
    )
    redis_port: int = Field(
        default=6379,
        description="Redis 포트",  # ENV: REDIS_PORT
        validation_alias="REDIS_PORT",
    )
    redis_db: int = Field(
        default=0,
        description="Redis DB 번호",  # ENV: REDIS_DB
        validation_alias="REDIS_DB",
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis 비밀번호",  # ENV: REDIS_PASSWORD
        validation_alias="REDIS_PASSWORD",
    )
    redis_ttl_seconds: int = Field(
        default=86400,
        description="Redis 기본 TTL (초, 24시간)",  # ENV: REDIS_TTL_SECONDS
        validation_alias="REDIS_TTL_SECONDS",
    )
    cache_l1_max_size: int = Field(
        default=1000,
        description="L1 로컬 캐시 최대 크기",  # ENV: CACHE_L1_MAX_SIZE
        validation_alias="CACHE_L1_MAX_SIZE",
    )

    @property
    def redis_url(self) -> Optional[str]:
        """Redis 연결 URL 생성"""
        if not self.redis_enabled:
            return None
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @field_validator("cors_origins", mode="plain")
    @classmethod
    def parse_cors_origins(cls, value):
        """Allow comma-separated strings or JSON array for CORS_ORIGINS."""
        if isinstance(value, str):
            # 콤마 구분 문자열 처리
            items = [origin.strip() for origin in value.split(",") if origin.strip()]
            return items or ["*"]
        if isinstance(value, list):
            return value
        # 기타 타입은 기본값 반환
        return ["*"]

    @field_validator("canary_traffic_percentage", mode="before")
    @classmethod
    def validate_canary_percentage(cls, value):
        """카나리 트래픽 비율 검증"""
        if value is None:
            return 5
        try:
            percentage = int(value)
        except (TypeError, ValueError):
            raise ValueError("Canary traffic percentage must be an integer between 0 and 100")

        if not 0 <= percentage <= 100:
            raise ValueError("Canary traffic percentage must be between 0 and 100")
        return percentage

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: Optional[str]) -> str:
        if not value:
            return "development"
        v = str(value).strip().lower()
        allowed = {"development", "production", "staging", "test"}
        if v not in allowed:
            return "development"
        return v

    @field_validator("deployment_version", mode="before")
    @classmethod
    def normalize_deployment_version(cls, value: Optional[str]) -> str:
        if not value:
            return "LEGACY"
        v = str(value).strip().upper()
        if v not in {"LEGACY", "CANARY"}:
            return "LEGACY"
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# ===== 모듈 레벨 싱글톤 및 유틸 =====

_settings_instance = None
_settings_lock = threading.Lock()


def get_settings() -> "Settings":
    """
    Settings 싱글톤 인스턴스를 반환합니다. (thread-safe)
    """
    global _settings_instance
    if _settings_instance is None:
        with _settings_lock:
            if _settings_instance is None:
                _settings_instance = Settings()
    return _settings_instance


def reload_settings() -> "Settings":
    """
    환경 변수 변경 후 Settings 인스턴스를 강제로 재생성합니다. (thread-safe)
    """
    global _settings_instance
    with _settings_lock:
        _settings_instance = Settings()
        return _settings_instance


def _normalize_env(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def is_development(current: Optional["Settings"] = None) -> bool:
    """Return True when the active environment is development."""
    settings_obj = current or get_settings()
    return _normalize_env(settings_obj.environment) == "development"


def is_production(current: Optional["Settings"] = None) -> bool:
    """Return True when the active environment is production."""
    settings_obj = current or get_settings()
    return _normalize_env(settings_obj.environment) == "production"


# Singleton settings instance, safe for module-level imports
settings: Settings = get_settings()


# ===== 메인 테스트 블록 =====
if __name__ == "__main__":
    import os

    # .env 파일 존재 여부 안내
    from pathlib import Path

    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print(f"[경고] .env 파일이 존재하지 않습니다: {env_path}")
    else:
        print(f"[.env 파일 경로] {env_path}")

    # 설정 값 출력 (테스트용)
    s = get_settings()
    print("[기본 Settings 값]")
    print(f"App Name: {s.app_name}")
    print(f"Environment: {s.environment}")
    print(f"Port: {s.port}")
    print(f"CORS Origins: {s.cors_origins}")
    print(f"Vertex Model: {s.vertex_model}")
    print(f"Rate Limit: {s.rate_limit_calls} calls/{s.rate_limit_period}s")
    print("[전체 Settings dict]")
    print(s.model_dump() if hasattr(s, "model_dump") else s.dict())

    # 환경 변수 override 예시
    print("\n[환경 변수로 Settings override 예시]")
    os.environ["ENVIRONMENT"] = "production"
    os.environ["PORT"] = "9999"
    os.environ["APP_NAME"] = "테스트앱"
    os.environ["RATE_LIMIT_CALLS"] = "42"
    s2 = reload_settings()
    print(f"App Name: {s2.app_name}")
    print(f"Environment: {s2.environment}")
    print(f"Port: {s2.port}")
    print(f"Rate Limit: {s2.rate_limit_calls} calls/{s2.rate_limit_period}s")

    # robust: 잘못된 ENV 입력 테스트 (예외 처리)
    print("\n[잘못된 ENV 입력 테스트]")
    os.environ["PORT"] = "notanumber"
    os.environ["PHASE4_ENABLED"] = "notabool"
    os.environ["CORS_ORIGINS"] = "잘못된json"
    try:
        s3 = reload_settings()
        print("[실패: 예외가 발생해야 함]")
    except Exception as e:
        print(f"예상된 예외 발생: {e}")

    # 정상 ENV 복구 후 다양한 타입 테스트
    os.environ["PORT"] = "8888"
    os.environ["PHASE4_ENABLED"] = "false"
    os.environ["CORS_ORIGINS"] = '["https://x.com","https://y.com"]'
    s4 = reload_settings()
    print(
        f"[복구 후 Settings] Port: {s4.port}, Phase4 Enabled: {s4.phase4_enabled}, CORS Origins: {s4.cors_origins}"
    )
