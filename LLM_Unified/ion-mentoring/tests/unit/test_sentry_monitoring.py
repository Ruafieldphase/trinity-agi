"""
Sentry 모니터링 테스트

Week 12-13: 에러 추적 및 성능 모니터링
- 이벤트 캡처 테스트
- 성능 추적 테스트
- 알림 규칙 테스트
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from app.monitoring.event_tracking import (
    ALERT_RULES,
    AlertRule,
    APIRequestEvent,
    CachePerformanceEvent,
    PersonaProcessEvent,
    RoutingDecisionEvent,
    analyze_performance_metrics,
    analyze_persona_patterns,
    track_api_request,
    track_cache_performance,
    track_persona_process,
)
from app.monitoring.sentry_integration import (
    SentryConfig,
    monitor_performance,
    trace_operation,
)


class TestSentryConfig:
    """Sentry 설정 테스트"""

    def test_sentry_config_initialization(self):
        """Sentry 설정 초기화"""
        config = SentryConfig(dsn="https://test@sentry.io/123")
        assert config.dsn == "https://test@sentry.io/123"
        assert config.environment == "production"

    def test_sentry_config_with_environment(self):
        """환경 설정"""
        config = SentryConfig(dsn="https://test@sentry.io/123", environment="staging")
        assert config.environment == "staging"

    def test_sentry_config_without_dsn(self):
        """DSN 없이 설정"""
        config = SentryConfig()
        assert config.dsn is None


class TestPersonaProcessEvent:
    """페르소나 처리 이벤트 테스트"""

    def test_persona_process_event_creation(self):
        """이벤트 생성"""
        event = PersonaProcessEvent(
            persona="Lua",
            resonance_key="calm-medium-learning",
            confidence=0.95,
            execution_time_ms=45.5,
            cache_hit=True,
            success=True,
        )

        assert event.persona == "Lua"
        assert event.confidence == 0.95
        assert event.cache_hit is True

    def test_persona_process_event_with_error(self):
        """에러와 함께 이벤트 생성"""
        event = PersonaProcessEvent(
            persona="Lua",
            resonance_key="calm-medium-learning",
            confidence=0.0,
            execution_time_ms=0,
            cache_hit=False,
            success=False,
            error="Test error",
        )

        assert event.success is False
        assert event.error == "Test error"

    @patch("app.monitoring.event_tracking.capture_persona_event")
    def test_persona_process_event_capture(self, mock_capture):
        """이벤트 캡처"""
        event = PersonaProcessEvent(
            persona="Lua",
            resonance_key="calm-medium-learning",
            confidence=0.95,
            execution_time_ms=45.5,
            cache_hit=True,
        )
        event.capture()

        mock_capture.assert_called_once()


class TestAPIRequestEvent:
    """API 요청 이벤트 테스트"""

    def test_api_request_event_success(self):
        """성공 요청 이벤트"""
        event = APIRequestEvent(
            method="POST", path="/api/v2/process", status_code=200, execution_time_ms=45.5
        )

        assert event.method == "POST"
        assert event.status_code == 200

    def test_api_request_event_error(self):
        """에러 요청 이벤트"""
        event = APIRequestEvent(
            method="GET",
            path="/api/v2/invalid",
            status_code=404,
            execution_time_ms=10.0,
            error="Not found",
        )

        assert event.status_code == 404
        assert event.error == "Not found"


class TestCachePerformanceEvent:
    """캐시 성능 이벤트 테스트"""

    def test_cache_performance_event_high_hit_rate(self):
        """높은 히트율"""
        event = CachePerformanceEvent(
            hit_count=800, miss_count=200, hit_rate=0.8, size=42, max_size=1000
        )

        assert event.hit_rate == 0.8

    def test_cache_performance_event_low_hit_rate(self):
        """낮은 히트율"""
        event = CachePerformanceEvent(
            hit_count=100, miss_count=900, hit_rate=0.1, size=50, max_size=1000
        )

        assert event.hit_rate == 0.1


class TestTrackingFunctions:
    """추적 함수 테스트"""

    @patch("app.monitoring.event_tracking.capture_persona_event")
    def test_track_persona_process(self, mock_capture):
        """페르소나 처리 추적"""
        track_persona_process(
            persona="Lua",
            resonance_key="calm-medium-learning",
            confidence=0.95,
            execution_time_ms=45.5,
            cache_hit=True,
        )

        mock_capture.assert_called_once()

    @patch("app.monitoring.event_tracking.capture_performance_event")
    def test_track_api_request(self, mock_capture):
        """API 요청 추적"""
        track_api_request(
            method="POST", path="/api/v2/process", status_code=200, execution_time_ms=45.5
        )

        mock_capture.assert_called_once()

    @patch("app.monitoring.event_tracking.capture_cache_event")
    def test_track_cache_performance(self, mock_capture):
        """캐시 성능 추적"""
        track_cache_performance(hit_count=800, miss_count=200, hit_rate=0.8, size=42, max_size=1000)

        mock_capture.assert_called_once()


class TestEventAnalysis:
    """이벤트 분석 테스트"""

    def test_analyze_persona_patterns(self):
        """페르소나 패턴 분석"""
        events = [
            PersonaProcessEvent(
                persona="Lua",
                resonance_key="calm-medium-learning",
                confidence=0.95,
                execution_time_ms=45.5,
                cache_hit=True,
                success=True,
            ),
            PersonaProcessEvent(
                persona="Lua",
                resonance_key="calm-medium-learning",
                confidence=0.90,
                execution_time_ms=40.0,
                cache_hit=True,
                success=True,
            ),
            PersonaProcessEvent(
                persona="Elro",
                resonance_key="analytical-medium-learning",
                confidence=0.85,
                execution_time_ms=50.0,
                cache_hit=False,
                success=True,
            ),
        ]

        analysis = analyze_persona_patterns(events)

        assert "Lua" in analysis
        assert "Elro" in analysis
        assert analysis["Lua"]["usage_count"] == 2
        assert analysis["Elro"]["usage_count"] == 1

    def test_analyze_performance_metrics(self):
        """성능 메트릭 분석"""
        events = [
            APIRequestEvent(
                method="POST", path="/api/v2/process", status_code=200, execution_time_ms=45.5
            ),
            APIRequestEvent(
                method="GET", path="/api/v2/personas", status_code=200, execution_time_ms=10.0
            ),
            APIRequestEvent(
                method="POST",
                path="/api/v2/process",
                status_code=500,
                execution_time_ms=100.0,
                error="Internal Server Error",
            ),
        ]

        analysis = analyze_performance_metrics(events)

        assert analysis["total_requests"] == 3
        assert analysis["successful"] == 2
        assert analysis["errors"] == 1
        assert analysis["success_rate"] == pytest.approx(2 / 3, rel=0.01)


class TestAlertRules:
    """알림 규칙 테스트"""

    def test_alert_rule_creation(self):
        """알림 규칙 생성"""
        rule = AlertRule(name="Test Alert", condition=lambda e: True, action=lambda e: None)

        assert rule.name == "Test Alert"

    def test_alert_rule_evaluation_true(self):
        """알림 규칙: 조건 만족"""
        rule = AlertRule(name="Test", condition=lambda e: True, action=lambda e: None)

        event = APIRequestEvent(
            method="GET", path="/test", status_code=500, execution_time_ms=100.0
        )

        assert rule.evaluate(event) is True

    def test_alert_rule_evaluation_false(self):
        """알림 규칙: 조건 불만족"""
        rule = AlertRule(name="Test", condition=lambda e: False, action=lambda e: None)

        event = APIRequestEvent(method="GET", path="/test", status_code=200, execution_time_ms=10.0)

        assert rule.evaluate(event) is False

    def test_high_error_rate_alert(self):
        """높은 에러율 알림"""
        rule = ALERT_RULES[0]  # High Error Rate

        # 500 에러
        event = APIRequestEvent(method="GET", path="/test", status_code=500, execution_time_ms=10.0)

        assert rule.evaluate(event) is True

        # 200 성공
        event = APIRequestEvent(method="GET", path="/test", status_code=200, execution_time_ms=10.0)

        assert rule.evaluate(event) is False

    def test_slow_response_alert(self):
        """느린 응답 알림"""
        rule = ALERT_RULES[1]  # Slow Response

        # 느린 응답
        event = APIRequestEvent(method="GET", path="/test", status_code=200, execution_time_ms=3000)

        assert rule.evaluate(event) is True

        # 빠른 응답
        event = APIRequestEvent(method="GET", path="/test", status_code=200, execution_time_ms=50.0)

        assert rule.evaluate(event) is False

    def test_low_cache_hit_rate_alert(self):
        """낮은 캐시 히트율 알림"""
        rule = ALERT_RULES[2]  # Low Cache Hit Rate

        # 낮은 히트율
        event = CachePerformanceEvent(
            hit_count=100, miss_count=900, hit_rate=0.1, size=50, max_size=1000
        )

        assert rule.evaluate(event) is True

        # 높은 히트율
        event = CachePerformanceEvent(
            hit_count=800, miss_count=200, hit_rate=0.8, size=100, max_size=1000
        )

        assert rule.evaluate(event) is False


class TestMonitorPerformanceDecorator:
    """성능 모니터링 데코레이터 테스트"""

    def test_monitor_performance_basic(self):
        """기본 성능 모니터링"""

        @monitor_performance(threshold_ms=100)
        def slow_function():
            time.sleep(0.05)
            return "result"

        result = slow_function()
        assert result == "result"

    def test_monitor_performance_with_args(self):
        """인자와 함께 성능 모니터링"""

        @monitor_performance(threshold_ms=100)
        def function_with_args(a, b):
            return a + b

        result = function_with_args(1, 2)
        assert result == 3

    def test_monitor_performance_exception(self):
        """예외 처리"""

        @monitor_performance(threshold_ms=100)
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()


class TestTraceOperation:
    """작업 추적 컨텍스트 매니저 테스트"""

    def test_trace_operation_success(self):
        """성공 추적"""
        with patch("sentry_sdk.start_span") as mock_start_span:
            span_context = MagicMock()
            mock_start_span.return_value.__enter__.return_value = span_context
            mock_start_span.return_value.__exit__.return_value = None

            with trace_operation("test_operation", "custom"):
                pass

            span_context.set_data.assert_called()

    def test_trace_operation_with_exception(self):
        """예외 처리"""
        with pytest.raises(ValueError):
            with patch("sentry_sdk.start_span") as mock_start_span:
                span_context = MagicMock()
                mock_start_span.return_value.__enter__.return_value = span_context
                mock_start_span.return_value.__exit__.return_value = None

                with trace_operation("test_operation", "custom"):
                    raise ValueError("Test error")


class TestRoutingDecisionEvent:
    """라우팅 결정 이벤트 테스트"""

    def test_routing_decision_event(self):
        """라우팅 결정 이벤트"""
        event = RoutingDecisionEvent(
            primary_persona="Lua",
            secondary_persona="Elro",
            confidence=0.95,
            all_scores={"Lua": 0.95, "Elro": 0.80, "Riri": 0.70, "Nana": 0.75},
            tone="calm",
            pace="medium",
            intent="learning",
        )

        assert event.primary_persona == "Lua"
        assert event.confidence == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
