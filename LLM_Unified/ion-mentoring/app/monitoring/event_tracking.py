"""
사용자 정의 이벤트 추적

Week 12-13: 상세한 모니터링
- 페르소나 처리 추적
- 캐시 성능 모니터링
- API 요청/응답 추적
- 비즈니스 메트릭 추적
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from .sentry_integration import (
    capture_cache_event,
    capture_performance_event,
    capture_persona_event,
    monitor_performance,
    set_context,
    set_tag,
)

logger = logging.getLogger(__name__)


# ==================== 이벤트 데이터 클래스 ====================


@dataclass
class PersonaProcessEvent:
    """페르소나 처리 이벤트"""

    persona: str
    resonance_key: str
    confidence: float
    execution_time_ms: float
    cache_hit: bool
    success: bool = True
    error: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def capture(self):
        """이벤트 캡처"""
        capture_persona_event(
            event_type="process",
            persona=self.persona,
            resonance_key=self.resonance_key,
            confidence=self.confidence,
            execution_time_ms=self.execution_time_ms,
            success=self.success,
            error=self.error,
        )

        # 추가 컨텍스트
        if self.user_id:
            set_tag("user_id", self.user_id)
        if self.cache_hit:
            set_tag("cache_hit", "true")


@dataclass
class APIRequestEvent:
    """API 요청 이벤트"""

    method: str
    path: str
    status_code: int
    execution_time_ms: float
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    error: Optional[str] = None

    def capture(self):
        """이벤트 캡처"""

        capture_performance_event(
            operation_name=f"{self.method} {self.path}",
            execution_time_ms=self.execution_time_ms,
            threshold_ms=2000,  # 2초 이상
            success=self.status_code < 400,
            metadata={
                "method": self.method,
                "path": self.path,
                "status_code": self.status_code,
                "user_id": self.user_id,
                "request_id": self.request_id,
                "error": self.error,
            },
        )

        set_tag("http_method", self.method)
        set_tag("http_status", str(self.status_code))


@dataclass
class CachePerformanceEvent:
    """캐시 성능 이벤트"""

    hit_count: int
    miss_count: int
    hit_rate: float
    size: int
    max_size: int
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def capture(self):
        """이벤트 캡처"""
        capture_cache_event(
            event_type="cache_stats",
            hit_count=self.hit_count,
            miss_count=self.miss_count,
            hit_rate=self.hit_rate,
            size=self.size,
            max_size=self.max_size,
        )

        # 캐시 상태 태그
        if self.hit_rate >= 0.8:
            set_tag("cache_health", "excellent")
        elif self.hit_rate >= 0.6:
            set_tag("cache_health", "good")
        elif self.hit_rate >= 0.4:
            set_tag("cache_health", "fair")
        else:
            set_tag("cache_health", "poor")


@dataclass
class RoutingDecisionEvent:
    """라우팅 결정 이벤트"""

    primary_persona: str
    secondary_persona: str
    confidence: float
    all_scores: Dict[str, float]
    tone: str
    pace: str
    intent: str
    user_id: Optional[str] = None

    def capture(self):
        """이벤트 이벤트 캡처"""
        set_context(
            "routing_decision",
            {
                "primary_persona": self.primary_persona,
                "secondary_persona": self.secondary_persona,
                "confidence": f"{self.confidence:.2f}",
                "tone": self.tone,
                "pace": self.pace,
                "intent": self.intent,
                "all_scores": {k: f"{v:.2f}" for k, v in self.all_scores.items()},
            },
        )

        set_tag("primary_persona", self.primary_persona)
        set_tag("resonance_tone", self.tone)


# ==================== 추적 함수 ====================


def track_persona_process(
    persona: str,
    resonance_key: str,
    confidence: float,
    execution_time_ms: float,
    cache_hit: bool,
    success: bool = True,
    error: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """
    페르소나 처리 추적

    Args:
        persona: 사용된 페르소나
        resonance_key: 파동키
        confidence: 신뢰도
        execution_time_ms: 실행 시간
        cache_hit: 캐시 히트 여부
        success: 성공 여부
        error: 에러 메시지
        user_id: 사용자 ID
        session_id: 세션 ID
    """
    event = PersonaProcessEvent(
        persona=persona,
        resonance_key=resonance_key,
        confidence=confidence,
        execution_time_ms=execution_time_ms,
        cache_hit=cache_hit,
        success=success,
        error=error,
        user_id=user_id,
        session_id=session_id,
    )
    event.capture()

    logger.info(
        f"Persona process tracked: {persona}, "
        f"time={execution_time_ms:.0f}ms, "
        f"cache={cache_hit}, "
        f"success={success}"
    )


def track_api_request(
    method: str,
    path: str,
    status_code: int,
    execution_time_ms: float,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    error: Optional[str] = None,
):
    """
    API 요청 추적

    Args:
        method: HTTP 메서드
        path: 경로
        status_code: 응답 상태 코드
        execution_time_ms: 실행 시간
        user_id: 사용자 ID
        request_id: 요청 ID
        error: 에러 메시지
    """
    event = APIRequestEvent(
        method=method,
        path=path,
        status_code=status_code,
        execution_time_ms=execution_time_ms,
        user_id=user_id,
        request_id=request_id,
        error=error,
    )
    event.capture()

    logger.info(
        f"API request tracked: {method} {path}, "
        f"status={status_code}, "
        f"time={execution_time_ms:.0f}ms"
    )


def track_cache_performance(
    hit_count: int, miss_count: int, hit_rate: float, size: int, max_size: int
):
    """
    캐시 성능 추적

    Args:
        hit_count: 히트 개수
        miss_count: 미스 개수
        hit_rate: 히트율
        size: 현재 크기
        max_size: 최대 크기
    """
    event = CachePerformanceEvent(
        hit_count=hit_count, miss_count=miss_count, hit_rate=hit_rate, size=size, max_size=max_size
    )
    event.capture()

    logger.info(
        f"Cache performance tracked: "
        f"hits={hit_count}, misses={miss_count}, "
        f"rate={hit_rate:.1%}, size={size}/{max_size}"
    )


def track_routing_decision(
    primary_persona: str,
    secondary_persona: str,
    confidence: float,
    all_scores: Dict[str, float],
    tone: str,
    pace: str,
    intent: str,
    user_id: Optional[str] = None,
):
    """
    라우팅 결정 추적

    Args:
        primary_persona: 1순위 페르소나
        secondary_persona: 2순위 페르소나
        confidence: 신뢰도
        all_scores: 모든 점수
        tone: 톤
        pace: 속도
        intent: 의도
        user_id: 사용자 ID
    """
    event = RoutingDecisionEvent(
        primary_persona=primary_persona,
        secondary_persona=secondary_persona,
        confidence=confidence,
        all_scores=all_scores,
        tone=tone,
        pace=pace,
        intent=intent,
        user_id=user_id,
    )
    event.capture()

    logger.info(
        f"Routing decision tracked: {primary_persona} "
        f"(confidence={confidence:.2f}), tone={tone}"
    )


# ==================== 성능 모니터링 ====================


@monitor_performance(threshold_ms=100, op_type="persona.process")
def monitored_persona_process(pipeline_process_func, user_input: str, resonance_key: str, **kwargs):
    """
    모니터링 중인 페르소나 처리

    Args:
        pipeline_process_func: 파이프라인 process 함수
        user_input: 사용자 입력
        resonance_key: 파동키
        **kwargs: 추가 인자

    Returns:
        처리 결과
    """
    return pipeline_process_func(user_input, resonance_key, **kwargs)


@monitor_performance(threshold_ms=50, op_type="cache.get")
def monitored_cache_get(cache_get_func, key: str):
    """
    모니터링 중인 캐시 조회

    Args:
        cache_get_func: 캐시 get 함수
        key: 캐시 키

    Returns:
        캐시된 값
    """
    return cache_get_func(key)


@monitor_performance(threshold_ms=100, op_type="database.query")
def monitored_database_query(query_func, *args, **kwargs):
    """
    모니터링 중인 데이터베이스 쿼리

    Args:
        query_func: 쿼리 함수
        *args: 위치 인자
        **kwargs: 키워드 인자

    Returns:
        쿼리 결과
    """
    return query_func(*args, **kwargs)


# ==================== 분석 함수 ====================


def analyze_persona_patterns(recent_events: list, window_size: int = 100):
    """
    페르소나 사용 패턴 분석

    Args:
        recent_events: 최근 이벤트 목록
        window_size: 분석 윈도우 크기

    Returns:
        패턴 분석 결과
    """
    if not recent_events:
        return {}

    # 최근 N개 이벤트 분석
    events = recent_events[-window_size:]

    # 페르소나별 집계
    persona_stats = {}
    for event in events:
        if isinstance(event, PersonaProcessEvent):
            persona = event.persona
            if persona not in persona_stats:
                persona_stats[persona] = {
                    "count": 0,
                    "total_time": 0,
                    "cache_hits": 0,
                    "success_count": 0,
                    "error_count": 0,
                }

            stats = persona_stats[persona]
            stats["count"] += 1
            stats["total_time"] += event.execution_time_ms
            if event.cache_hit:
                stats["cache_hits"] += 1
            if event.success:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1

    # 통계 계산
    analysis = {}
    for persona, stats in persona_stats.items():
        analysis[persona] = {
            "usage_count": stats["count"],
            "avg_time_ms": stats["total_time"] / stats["count"],
            "cache_hit_rate": stats["cache_hits"] / stats["count"],
            "success_rate": stats["success_count"] / stats["count"],
            "error_rate": stats["error_count"] / stats["count"],
        }

    return analysis


def analyze_performance_metrics(recent_events: list, window_size: int = 100):
    """
    성능 메트릭 분석

    Args:
        recent_events: 최근 이벤트 목록
        window_size: 분석 윈도우 크기

    Returns:
        성능 분석 결과
    """
    api_events = [e for e in recent_events[-window_size:] if isinstance(e, APIRequestEvent)]

    if not api_events:
        return {}

    # 통계
    total_requests = len(api_events)
    successful_requests = sum(1 for e in api_events if e.status_code < 400)
    error_requests = sum(1 for e in api_events if e.status_code >= 400)
    avg_response_time = sum(e.execution_time_ms for e in api_events) / len(api_events)
    max_response_time = max(e.execution_time_ms for e in api_events)
    min_response_time = min(e.execution_time_ms for e in api_events)

    return {
        "total_requests": total_requests,
        "successful": successful_requests,
        "errors": error_requests,
        "success_rate": successful_requests / total_requests,
        "avg_response_time_ms": avg_response_time,
        "max_response_time_ms": max_response_time,
        "min_response_time_ms": min_response_time,
    }


# ==================== 알림 규칙 ====================


class AlertRule:
    """알림 규칙"""

    def __init__(self, name: str, condition: callable, action: callable):
        """
        초기화

        Args:
            name: 규칙 이름
            condition: 조건 함수 (True면 알림)
            action: 알림 함수
        """
        self.name = name
        self.condition = condition
        self.action = action

    def evaluate(self, event: Any) -> bool:
        """
        규칙 평가

        Args:
            event: 이벤트

        Returns:
            조건 만족 여부
        """
        try:
            return self.condition(event)
        except Exception as e:
            logger.error(f"Alert rule evaluation error: {str(e)}")
            return False

    def trigger(self, event: Any):
        """
        알림 트리거

        Args:
            event: 이벤트
        """
        try:
            self.action(event)
            logger.warning(f"Alert triggered: {self.name}")
        except Exception as e:
            logger.error(f"Alert action error: {str(e)}")


# 기본 알림 규칙
ALERT_RULES = [
    AlertRule(
        name="High Error Rate",
        condition=lambda e: isinstance(e, APIRequestEvent) and e.status_code >= 500,
        action=lambda e: logger.error(f"High error rate detected: {e.method} {e.path}"),
    ),
    AlertRule(
        name="Slow Response",
        condition=lambda e: isinstance(e, APIRequestEvent) and e.execution_time_ms > 2000,
        action=lambda e: logger.warning(
            f"Slow response: {e.method} {e.path} ({e.execution_time_ms:.0f}ms)"
        ),
    ),
    AlertRule(
        name="Low Cache Hit Rate",
        condition=lambda e: isinstance(e, CachePerformanceEvent) and e.hit_rate < 0.5,
        action=lambda e: logger.warning(f"Low cache hit rate: {e.hit_rate:.1%}"),
    ),
    AlertRule(
        name="Persona Processing Error",
        condition=lambda e: isinstance(e, PersonaProcessEvent) and not e.success,
        action=lambda e: logger.error(f"Persona processing error: {e.error}"),
    ),
]
