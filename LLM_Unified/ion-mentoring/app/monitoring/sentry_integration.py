"""
Sentry 에러 추적 통합

Week 12-13: 실시간 모니터링
- 에러 캡처 및 추적
- 성능 프로파일링
- 사용자 세션 추적
- 커스텀 이벤트
"""

import functools
import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, TypeVar

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

try:
    from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration
except ImportError:  # pragma: no cover - optional dependency
    SqlAlchemyIntegration = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SentryConfig:
    """Sentry 설정"""

    def __init__(
        self,
        dsn: Optional[str] = None,
        environment: str = "production",
        enable_performance_monitoring: bool = True,
        traces_sample_rate: float = 0.1,
        profiles_sample_rate: float = 0.1,
        debug: bool = False,
    ):
        """
        초기화

        Args:
            dsn: Sentry DSN URL
            environment: 환경 (development, staging, production)
            enable_performance_monitoring: 성능 모니터링 활성화
            traces_sample_rate: 성능 추적 샘플 비율
            profiles_sample_rate: 프로파일링 샘플 비율
            debug: 디버그 모드
        """
        self.dsn = dsn or os.getenv("SENTRY_DSN")
        self.environment = environment
        self.enable_performance_monitoring = enable_performance_monitoring
        self.traces_sample_rate = traces_sample_rate
        self.profiles_sample_rate = profiles_sample_rate
        self.debug = debug
        self.initialized = False

    def initialize(self) -> bool:
        """
        Sentry 초기화

        Returns:
            성공 여부
        """
        if not self.dsn:
            logger.warning("Sentry DSN not configured")
            return False

        if self.initialized:
            logger.warning("Sentry already initialized")
            return False

        try:
            # Sentry SDK 초기화
            integrations = [
                FastApiIntegration(),
                StarletteIntegration(),
                RedisIntegration(),
                HttpxIntegration(),
                LoggingIntegration(
                    level=logging.INFO,  # 최소 로그 레벨
                    event_level=logging.ERROR,  # 이벤트 전송 레벨
                ),
            ]
            if SqlAlchemyIntegration is not None:
                integrations.insert(2, SqlAlchemyIntegration())
            else:
                logger.debug("SqlAlchemy integration unavailable; skipping SQL instrumentation")

            sentry_sdk.init(
                dsn=self.dsn,
                environment=self.environment,
                debug=self.debug,
                # 성능 모니터링
                enable_tracing=self.enable_performance_monitoring,
                traces_sample_rate=self.traces_sample_rate,
                profiles_sample_rate=self.profiles_sample_rate,
                # 통합 설정
                integrations=integrations,
                # 추가 옵션
                attach_stacktrace=True,
                include_source_context=True,
                send_default_pii=False,  # PII 전송은 기본 비활성화
            )
            self.initialized = True
            logger.info(f"Sentry initialized: {self.environment}")
            return True

        except Exception as e:
            logger.error(f"Sentry initialization failed: {str(e)}")
            return False

    def set_user(self, user_id: str, email: Optional[str] = None, username: Optional[str] = None):
        """사용자 정보 설정"""
        sentry_sdk.set_user(
            {
                "id": user_id,
                "email": email,
                "username": username,
            }
        )

    def clear_user(self):
        """사용자 정보 제거"""
        sentry_sdk.set_user(None)

    def set_tag(self, key: str, value: str):
        """태그 설정"""
        sentry_sdk.set_tag(key, value)

    def set_context(self, name: str, context: Dict[str, Any]):
        """컨텍스트 설정"""
        sentry_sdk.set_context(name, context)

    def capture_exception(self, exception: Exception, level: str = "error"):
        """예외 캡처"""
        sentry_sdk.capture_exception(exception)

    def capture_message(self, message: str, level: str = "info"):
        """메시지 캡처"""
        sentry_sdk.capture_message(message, level=level)

    def capture_event(self, event: Dict[str, Any]):
        """커스텀 이벤트 캡처"""
        sentry_sdk.capture_event(event)


# 싱글톤 인스턴스
_sentry_config: Optional[SentryConfig] = None


def get_sentry_config() -> SentryConfig:
    """Sentry 설정 싱글톤 반환"""
    global _sentry_config
    if _sentry_config is None:
        _sentry_config = SentryConfig()
    return _sentry_config


def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "production",
    enable_performance_monitoring: bool = True,
) -> bool:
    """
    Sentry 초기화 (편의 함수)

    Args:
        dsn: Sentry DSN
        environment: 환경
        enable_performance_monitoring: 성능 모니터링 활성화

    Returns:
        성공 여부
    """
    config = get_sentry_config()
    if dsn:
        config.dsn = dsn
    config.environment = environment
    config.enable_performance_monitoring = enable_performance_monitoring
    return config.initialize()


# ==================== 성능 추적 ====================


@contextmanager
def trace_operation(operation_name: str, op_type: str = "custom"):
    """
    작업 추적 컨텍스트 매니저

    Usage:
    ```python
    with trace_operation("process_request", "http.request"):
        # 작업 수행
        pass
    ```
    """
    with sentry_sdk.start_span(op=op_type, description=operation_name) as span:
        try:
            start_time = time.time()
            yield span
            elapsed = time.time() - start_time
            span.set_data("duration_ms", elapsed * 1000)
            span.set_data("status", "success")
        except Exception as e:
            span.set_data("status", "error")
            span.set_data("error", str(e))
            raise


def monitor_performance(threshold_ms: Optional[float] = None, op_type: str = "custom") -> Callable:
    """
    함수 성능 모니터링 데코레이터

    Args:
        threshold_ms: 경고 임계값 (ms)
        op_type: 작업 타입

    Usage:
    ```python
    @monitor_performance(threshold_ms=100, op_type="database.query")
    def expensive_function():
        ...
    ```
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            with trace_operation(func.__name__, op_type) as span:
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000

                # 임계값 확인
                if threshold_ms and elapsed > threshold_ms:
                    logger.warning(
                        f"{func.__name__} exceeded threshold: "
                        f"{elapsed:.0f}ms > {threshold_ms}ms"
                    )
                    span.set_data("threshold_exceeded", True)

                return result

        return wrapper

    return decorator


# ==================== 에러 처리 ====================


def capture_error(
    exception: Exception, context: Optional[Dict[str, Any]] = None, level: str = "error"
):
    """
    에러 캡처

    Args:
        exception: 예외 객체
        context: 추가 컨텍스트
        level: 심각도 (debug, info, warning, error, critical)
    """
    config = get_sentry_config()

    if context:
        config.set_context("error_context", context)

    config.capture_exception(exception)
    logger.log(
        getattr(logging, level.upper(), logging.ERROR),
        f"Captured error: {str(exception)}",
        exc_info=exception,
    )


def capture_message(message: str, level: str = "info", context: Optional[Dict[str, Any]] = None):
    """
    메시지 캡처

    Args:
        message: 메시지 텍스트
        level: 심각도
        context: 추가 컨텍스트
    """
    config = get_sentry_config()

    if context:
        config.set_context("message_context", context)

    config.capture_message(message, level=level)
    logger.log(getattr(logging, level.upper(), logging.INFO), message)


# ==================== 커스텀 이벤트 ====================


def capture_persona_event(
    event_type: str,
    persona: str,
    resonance_key: str,
    confidence: float,
    execution_time_ms: float,
    success: bool = True,
    error: Optional[str] = None,
):
    """
    페르소나 처리 이벤트 캡처

    Args:
        event_type: 이벤트 타입 (process, recommend, bulk_process)
        persona: 사용된 페르소나
        resonance_key: 파동키
        confidence: 신뢰도
        execution_time_ms: 실행 시간
        success: 성공 여부
        error: 에러 메시지
    """
    config = get_sentry_config()

    event = {
        "type": "persona_event",
        "message": f"Persona {event_type}: {persona}",
        "level": "info" if success else "error",
        "tags": {
            "event_type": event_type,
            "persona": persona,
            "success": str(success),
        },
        "contexts": {
            "persona": {
                "event_type": event_type,
                "persona": persona,
                "resonance_key": resonance_key,
                "confidence": f"{confidence:.2f}",
                "execution_time_ms": f"{execution_time_ms:.1f}",
            }
        },
    }

    if error:
        event["extra"] = {"error": error}

    config.capture_event(event)


def capture_cache_event(
    event_type: str, hit_count: int, miss_count: int, hit_rate: float, size: int, max_size: int
):
    """
    캐시 통계 이벤트 캡처

    Args:
        event_type: 이벤트 타입 (cache_stats)
        hit_count: 히트 개수
        miss_count: 미스 개수
        hit_rate: 히트율
        size: 현재 크기
        max_size: 최대 크기
    """
    config = get_sentry_config()

    event = {
        "type": "cache_event",
        "message": f"Cache stats: {hit_rate:.1f}% hit rate",
        "level": "info",
        "tags": {
            "event_type": event_type,
            "hit_rate_percent": f"{hit_rate * 100:.0f}",
        },
        "contexts": {
            "cache": {
                "hit_count": hit_count,
                "miss_count": miss_count,
                "hit_rate": f"{hit_rate:.2f}",
                "size": size,
                "max_size": max_size,
            }
        },
    }

    config.capture_event(event)


def capture_performance_event(
    operation_name: str,
    execution_time_ms: float,
    threshold_ms: Optional[float] = None,
    success: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    성능 이벤트 캡처

    Args:
        operation_name: 작업명
        execution_time_ms: 실행 시간
        threshold_ms: 임계값
        success: 성공 여부
        metadata: 추가 정보
    """
    config = get_sentry_config()

    level = "info"
    if threshold_ms and execution_time_ms > threshold_ms:
        level = "warning"

    event = {
        "type": "performance_event",
        "message": f"{operation_name}: {execution_time_ms:.1f}ms",
        "level": level,
        "tags": {
            "operation": operation_name,
            "success": str(success),
        },
        "contexts": {
            "performance": {
                "operation_name": operation_name,
                "execution_time_ms": f"{execution_time_ms:.1f}",
                "threshold_exceeded": threshold_ms and execution_time_ms > threshold_ms,
                **(metadata or {}),
            }
        },
    }

    config.capture_event(event)


# ==================== 미들웨어 ====================


class SentryMiddleware:
    """Sentry 통합 미들웨어"""

    def __init__(self, app):
        self.app = app
        self.config = get_sentry_config()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 요청 정보 캡처
        path = scope.get("path", "")
        method = scope.get("method", "")

        with trace_operation(f"{method} {path}", "http.request") as span:
            try:
                # 사용자 정보 설정 (가능하면)
                headers = dict(scope.get("headers", []))
                if b"x-user-id" in headers:
                    user_id = headers[b"x-user-id"].decode()
                    self.config.set_user(user_id)

                await self.app(scope, receive, send)

            except Exception as e:
                span.set_data("status", "error")
                capture_error(e, {"path": path, "method": method})
                raise


# ==================== FastAPI 통합 ====================


def setup_sentry_for_fastapi(app, dsn: Optional[str] = None, environment: str = "production"):
    """
    FastAPI 앱에 Sentry 설정

    Args:
        app: FastAPI 애플리케이션
        dsn: Sentry DSN
        environment: 환경
    """
    # Sentry 초기화
    if not init_sentry(dsn=dsn, environment=environment):
        logger.warning("Sentry initialization failed")
        return

    # 미들웨어 추가
    app.add_middleware(SentryMiddleware)

    logger.info("Sentry middleware added to FastAPI app")


# ==================== 유틸리티 ====================


def set_user_context(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    """사용자 컨텍스트 설정"""
    config = get_sentry_config()
    config.set_user(user_id, email=email, username=username)


def clear_user_context():
    """사용자 컨텍스트 제거"""
    config = get_sentry_config()
    config.clear_user()


def set_tag(key: str, value: str):
    """태그 설정"""
    config = get_sentry_config()
    config.set_tag(key, value)


def set_context(name: str, context: Dict[str, Any]):
    """컨텍스트 설정"""
    config = get_sentry_config()
    config.set_context(name, context)


def get_sentry_client():
    """Sentry 클라이언트 직접 접근"""
    return sentry_sdk
