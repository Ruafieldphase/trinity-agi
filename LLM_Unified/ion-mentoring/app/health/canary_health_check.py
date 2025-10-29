"""
Phase 4 - 카나리 배포 헬스 체크 및 자동 롤백
SLA 모니터링 및 문제 자동 감지/해결
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """헬스 상태"""

    HEALTHY = "healthy"  # 모든 지표 정상
    DEGRADED = "degraded"  # 일부 지표 경고 수준
    UNHEALTHY = "unhealthy"  # 여러 지표 임계값 초과
    UNKNOWN = "unknown"  # 데이터 부족


@dataclass
class HealthCheckMetrics:
    """헬스 체크 메트릭"""

    status: HealthStatus
    timestamp: str
    checks: Dict[str, Any]
    failures: list
    recommendations: list


class CanaryHealthCheck:
    """카나리 배포 헬스 체크"""

    # SLA 기준
    SLA_ERROR_RATE = 0.5  # 0.5%
    SLA_P95_RESPONSE_TIME = 100  # ms
    SLA_AVAILABILITY = 99.95  # %
    SLA_MEMORY_USAGE = 2048  # MB

    # 경고 기준 (SLA의 50%)
    WARNING_ERROR_RATE = 0.25  # 0.25%
    WARNING_P95_RESPONSE_TIME = 50  # ms
    WARNING_AVAILABILITY = 99.975  # %

    # 자동 롤백 기준 (SLA의 200%)
    ROLLBACK_ERROR_RATE = 1.0  # 1.0%
    ROLLBACK_P95_RESPONSE_TIME = 200  # ms
    ROLLBACK_MEMORY_USAGE = 4096  # MB

    # 최소 요청 수 (검증을 위한)
    MIN_REQUESTS_FOR_VALIDATION = 10

    def __init__(self, metrics_collector):
        """
        초기화

        Args:
            metrics_collector: CanaryMetricsCollector 인스턴스
        """
        self.metrics = metrics_collector
        self.check_interval = 60  # 1분마다 확인
        self.is_running = False
        self.last_check_time = None
        self.last_status = HealthStatus.UNKNOWN
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3

        logger.info("✅ CanaryHealthCheck initialized")

    async def start_continuous_monitoring(self):
        """지속적인 모니터링 시작"""
        if self.is_running:
            logger.warning("⚠️ Monitoring already running")
            return

        self.is_running = True
        logger.info("🚀 Starting continuous health monitoring...")

        try:
            while self.is_running:
                await self._perform_check_cycle()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"❌ Monitoring error: {str(e)}", exc_info=True)
            self.is_running = False

    async def stop_continuous_monitoring(self):
        """모니터링 중지"""
        self.is_running = False
        logger.info("⏹️ Health monitoring stopped")

    async def _perform_check_cycle(self):
        """헬스 체크 사이클 수행"""
        try:
            health_metrics = await self.perform_health_check()

            # 상태 업데이트
            self.last_check_time = datetime.now()
            self.last_status = health_metrics.status

            # 로깅
            self._log_health_status(health_metrics)

            # 자동 롤백 판단
            if health_metrics.status == HealthStatus.UNHEALTHY:
                self.consecutive_failures += 1
                logger.critical(
                    f"❌ Health check FAILED ({self.consecutive_failures}/{self.max_consecutive_failures})"
                )

                if self.consecutive_failures >= self.max_consecutive_failures:
                    await self.trigger_rollback(health_metrics)
                    self.consecutive_failures = 0
            else:
                self.consecutive_failures = 0

        except Exception as e:
            logger.error(f"Error during health check cycle: {str(e)}", exc_info=True)

    async def perform_health_check(self) -> HealthCheckMetrics:
        """헬스 체크 수행"""
        timestamp = datetime.now().isoformat()
        checks = {}
        failures = []
        recommendations = []

        # 메트릭 수집
        metrics_summary = self.metrics.get_metrics_summary()
        canary_metrics = metrics_summary.get("canary", {})

        # 데이터 충분성 확인
        if (
            not canary_metrics
            or canary_metrics.get("request_count", 0) < self.MIN_REQUESTS_FOR_VALIDATION
        ):
            return HealthCheckMetrics(
                status=HealthStatus.UNKNOWN,
                timestamp=timestamp,
                checks={},
                failures=["Insufficient data for validation"],
                recommendations=["Wait for more requests"],
            )

        # 1. 에러율 확인
        error_rate_str = canary_metrics.get("error_rate", "0%").rstrip("%")
        try:
            error_rate = float(error_rate_str)
        except ValueError:
            error_rate = 0

        checks["error_rate"] = f"{error_rate:.2f}%"
        if error_rate > self.ROLLBACK_ERROR_RATE:
            failures.append(
                f"Error rate {error_rate:.2f}% exceeds rollback threshold {self.ROLLBACK_ERROR_RATE}%"
            )
            recommendations.append("⚠️ CRITICAL: Error rate extremely high - rollback recommended")
        elif error_rate > self.SLA_ERROR_RATE:
            failures.append(f"Error rate {error_rate:.2f}% exceeds SLA {self.SLA_ERROR_RATE}%")
            recommendations.append("⚠️ Monitor error rate closely")
        elif error_rate > self.WARNING_ERROR_RATE:
            recommendations.append("ℹ️ Error rate approaching warning threshold")

        # 2. 응답 시간 확인
        p95_time_str = canary_metrics.get("p95_response_time_ms", "0").rstrip("ms")
        try:
            p95_time = float(p95_time_str)
        except ValueError:
            p95_time = 0

        checks["p95_response_time_ms"] = f"{p95_time:.2f}ms"
        if p95_time > self.ROLLBACK_P95_RESPONSE_TIME:
            failures.append(
                f"P95 response time {p95_time:.2f}ms exceeds rollback threshold {self.ROLLBACK_P95_RESPONSE_TIME}ms"
            )
            recommendations.append(
                "🔥 CRITICAL: Response time extremely high - rollback recommended"
            )
        elif p95_time > self.SLA_P95_RESPONSE_TIME:
            failures.append(
                f"P95 response time {p95_time:.2f}ms exceeds SLA {self.SLA_P95_RESPONSE_TIME}ms"
            )
            recommendations.append("⚠️ Investigate performance bottlenecks")
        elif p95_time > self.WARNING_P95_RESPONSE_TIME:
            recommendations.append("ℹ️ Response time approaching warning threshold")

        # 3. 트래픽 분배 확인
        traffic_split = metrics_summary.get("comparison", {}).get("traffic_split", {})
        canary_pct_str = traffic_split.get("canary_percentage", "0%").rstrip("%")
        try:
            canary_pct = float(canary_pct_str)
        except ValueError:
            canary_pct = 0

        checks["traffic_distribution"] = f"Canary {canary_pct:.1f}%"
        if canary_pct < 2 or canary_pct > 8:  # 5% ± 3%
            recommendations.append(
                f"⚠️ Traffic distribution skewed: {canary_pct:.1f}% (expected ~5%)"
            )

        # 4. 요청 수 확인
        request_count = canary_metrics.get("request_count", 0)
        checks["request_count"] = request_count

        # 상태 결정
        if failures:
            if len(failures) >= 2:
                status = HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
            recommendations.append("✅ All health checks passed")

        return HealthCheckMetrics(
            status=status,
            timestamp=timestamp,
            checks=checks,
            failures=failures,
            recommendations=recommendations,
        )

    def _log_health_status(self, metrics: HealthCheckMetrics):
        """헬스 상태 로깅"""
        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.UNKNOWN: "❓",
        }

        emoji = status_emoji.get(metrics.status, "❓")
        logger.info(f"{emoji} Health Check: {metrics.status.value.upper()}")

        for check_name, check_value in metrics.checks.items():
            logger.info(f"  {check_name}: {check_value}")

        if metrics.failures:
            logger.warning("Failures detected:")
            for failure in metrics.failures:
                logger.warning(f"  • {failure}")

        if metrics.recommendations:
            logger.info("Recommendations:")
            for rec in metrics.recommendations:
                logger.info(f"  • {rec}")

    async def trigger_rollback(self, health_metrics: HealthCheckMetrics):
        """자동 롤백 트리거"""
        logger.critical("🔄 AUTOMATIC ROLLBACK INITIATED")
        logger.critical("Reason: Multiple SLA violations detected")

        # 롤백 액션
        try:
            await self._execute_rollback()
            logger.info("✅ Rollback completed successfully")
        except Exception as e:
            logger.error(f"❌ Rollback failed: {str(e)}", exc_info=True)

        # 알림 전송
        await self._send_critical_alert(
            {
                "type": "AUTO_ROLLBACK",
                "timestamp": datetime.now().isoformat(),
                "health_metrics": {
                    "checks": health_metrics.checks,
                    "failures": health_metrics.failures,
                    "recommendations": health_metrics.recommendations,
                },
            }
        )

    async def _execute_rollback(self):
        """롤백 실행"""
        # 실제 구현은 환경에 따라 다름
        # 예: Kubernetes pod 재시작, 트래픽 라우팅 변경 등

        logger.critical("Executing rollback actions...")
        logger.critical("  1. Disabling canary deployment")
        logger.critical("  2. Routing all traffic to legacy version")
        logger.critical("  3. Preserving canary logs for analysis")

        # 시뮬레이션
        await asyncio.sleep(1)

        logger.critical("✅ Rollback completed")

    async def _send_critical_alert(self, alert_data: Dict[str, Any]):
        """중요 알림 전송"""
        logger.critical("=" * 60)
        logger.critical("🚨 CRITICAL ALERT - CANARY ROLLBACK")
        logger.critical("=" * 60)

        alert_msg = f"""
Type: {alert_data['type']}
Timestamp: {alert_data['timestamp']}

Metrics:
{self._format_dict(alert_data['health_metrics']['checks'])}

Failures:
{self._format_list(alert_data['health_metrics']['failures'])}

Recommendations:
{self._format_list(alert_data['health_metrics']['recommendations'])}
        """

        logger.critical(alert_msg)
        logger.critical("=" * 60)

        # 실제 환경에서는 Slack, PagerDuty 등으로 알림 전송

    @staticmethod
    def _format_dict(d: Dict[str, Any]) -> str:
        """딕셔너리 포매팅"""
        return "\n".join([f"  {k}: {v}" for k, v in d.items()])

    @staticmethod
    def _format_list(lst: list) -> str:
        """리스트 포매팅"""
        return "\n".join([f"  • {item}" for item in lst])

    def get_current_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        return {
            "status": self.last_status.value if self.last_status else "unknown",
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "is_monitoring": self.is_running,
            "consecutive_failures": self.consecutive_failures,
            "sla_thresholds": {
                "error_rate": f"<{self.SLA_ERROR_RATE}%",
                "p95_response_time": f"<{self.SLA_P95_RESPONSE_TIME}ms",
                "availability": f">{self.SLA_AVAILABILITY}%",
            },
        }


# 싱글톤 헬스 체커 제공자
_health_checker: Optional[CanaryHealthCheck] = None


def get_health_checker() -> CanaryHealthCheck:
    """CanaryHealthCheck 싱글톤 인스턴스 반환"""
    global _health_checker

    if _health_checker is None:
        # 지연 로딩으로 순환 참조 방지
        from app.middleware.canary_metrics import get_metrics_collector

        metrics = get_metrics_collector()
        _health_checker = CanaryHealthCheck(metrics_collector=metrics)

    return _health_checker
