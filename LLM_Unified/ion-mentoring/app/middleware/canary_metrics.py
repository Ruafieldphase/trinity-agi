"""
Phase 4 - 카나리 배포 메트릭 수집 미들웨어
5% 트래픽 모니터링 및 성능 메트릭 기록
"""

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DeploymentVersion(Enum):
    """배포 버전"""

    LEGACY = "legacy"  # Phase 3 (95%)
    CANARY = "canary"  # Phase 4 (5%)


@dataclass
class RequestMetric:
    """개별 요청 메트릭"""

    timestamp: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    user_id: str = ""
    error_message: str = ""
    version: str = "legacy"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


@dataclass
class VersionMetrics:
    """배포 버전별 메트릭"""

    version: str
    request_count: int = 0
    error_count: int = 0
    total_response_time_ms: float = 0.0
    response_times: List[float] = field(default_factory=list)
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    last_updated: str = ""

    def get_error_rate(self) -> float:
        """에러율 계산 (%)"""
        if self.request_count == 0:
            return 0.0
        return (self.error_count / self.request_count) * 100

    def get_avg_response_time(self) -> float:
        """평균 응답 시간 (ms)"""
        if self.request_count == 0:
            return 0.0
        return self.total_response_time_ms / self.request_count

    def get_p95_response_time(self) -> float:
        """P95 응답 시간 (ms)"""
        if not self.response_times:
            return 0.0

        sorted_times = sorted(self.response_times)
        p95_index = int(len(sorted_times) * 0.95)
        return sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]

    def get_p99_response_time(self) -> float:
        """P99 응답 시간 (ms)"""
        if not self.response_times:
            return 0.0

        sorted_times = sorted(self.response_times)
        p99_index = int(len(sorted_times) * 0.99)
        return sorted_times[p99_index] if p99_index < len(sorted_times) else sorted_times[-1]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "version": self.version,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": f"{self.get_error_rate():.2f}%",
            "avg_response_time_ms": f"{self.get_avg_response_time():.2f}",
            "p95_response_time_ms": f"{self.get_p95_response_time():.2f}",
            "p99_response_time_ms": f"{self.get_p99_response_time():.2f}",
            "last_updated": self.last_updated,
        }


class CanaryMetricsCollector:
    """카나리 배포 메트릭 수집기"""

    def __init__(self, max_metrics_history: int = 10000):
        """
        초기화

        Args:
            max_metrics_history: 저장할 최대 메트릭 개수
        """
        self.max_metrics_history = max_metrics_history

        # 버전별 메트릭
        self.metrics: Dict[str, VersionMetrics] = {
            DeploymentVersion.LEGACY.value: VersionMetrics(version="legacy"),
            DeploymentVersion.CANARY.value: VersionMetrics(version="canary"),
        }

        # 모든 요청 메트릭 히스토리
        self.request_history: List[RequestMetric] = []

        # 엔드포인트별 메트릭
        self.endpoint_metrics: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"legacy": {"count": 0, "errors": 0}, "canary": {"count": 0, "errors": 0}}
        )

        logger.info("✅ CanaryMetricsCollector initialized")

    def record_request(
        self,
        endpoint: str,
        method: str,
        user_id: str,
        version: str,
        status_code: int,
        response_time_ms: float,
        error_message: str = "",
    ):
        """
        요청 기록

        Args:
            endpoint: 엔드포인트 경로
            method: HTTP 메서드
            user_id: 사용자 ID
            version: 배포 버전 ("legacy" 또는 "canary")
            status_code: HTTP 상태 코드
            response_time_ms: 응답 시간 (ms)
            error_message: 에러 메시지 (있는 경우)
        """
        # 메트릭 기록
        metric = RequestMetric(
            timestamp=datetime.now().isoformat(),
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_message=error_message,
            version=version,
        )

        # 버전별 메트릭 업데이트
        if version in self.metrics:
            self.metrics[version].request_count += 1
            self.metrics[version].total_response_time_ms += response_time_ms
            self.metrics[version].response_times.append(response_time_ms)
            self.metrics[version].status_codes[status_code] += 1
            self.metrics[version].last_updated = datetime.now().isoformat()

            if status_code >= 400:
                self.metrics[version].error_count += 1

        # 엔드포인트별 메트릭 업데이트
        self.endpoint_metrics[endpoint][version]["count"] += 1
        if status_code >= 400:
            self.endpoint_metrics[endpoint][version]["errors"] += 1

        # 히스토리에 추가
        self.request_history.append(metric)

        # 히스토리 크기 제한
        if len(self.request_history) > self.max_metrics_history:
            self.request_history.pop(0)

        logger.debug(
            f"Recorded: {version} {method} {endpoint} - "
            f"Status: {status_code}, Time: {response_time_ms:.2f}ms"
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """메트릭 요약 조회"""
        return {
            "legacy": self.metrics[DeploymentVersion.LEGACY.value].to_dict(),
            "canary": self.metrics[DeploymentVersion.CANARY.value].to_dict(),
            "comparison": self._get_comparison(),
        }

    def _get_comparison(self) -> Dict[str, Any]:
        """버전 간 비교"""
        legacy = self.metrics[DeploymentVersion.LEGACY.value]
        canary = self.metrics[DeploymentVersion.CANARY.value]

        if legacy.request_count == 0 or canary.request_count == 0:
            return {"status": "insufficient_data", "message": "Need more data for comparison"}

        legacy_error_rate = legacy.get_error_rate()
        canary_error_rate = canary.get_error_rate()
        error_rate_diff = canary_error_rate - legacy_error_rate

        legacy_avg_time = legacy.get_avg_response_time()
        canary_avg_time = canary.get_avg_response_time()
        time_improvement = (
            ((legacy_avg_time - canary_avg_time) / legacy_avg_time * 100)
            if legacy_avg_time > 0
            else 0
        )

        return {
            "error_rate_difference": f"{error_rate_diff:+.2f}%",
            "response_time_improvement": f"{time_improvement:+.2f}%",
            "canary_p95_response_time": f"{canary.get_p95_response_time():.2f}ms",
            "legacy_p95_response_time": f"{legacy.get_p95_response_time():.2f}ms",
            "traffic_split": {
                "legacy_requests": legacy.request_count,
                "canary_requests": canary.request_count,
                "legacy_percentage": f"{legacy.request_count / (legacy.request_count + canary.request_count) * 100:.1f}%",
                "canary_percentage": f"{canary.request_count / (legacy.request_count + canary.request_count) * 100:.1f}%",
            },
        }

    def get_endpoint_metrics(self) -> Dict[str, Any]:
        """엔드포인트별 메트릭"""
        return dict(self.endpoint_metrics)

    def get_recent_errors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """최근 에러 조회"""
        errors = [m for m in self.request_history if m.status_code >= 400]
        return [m.to_dict() for m in errors[-limit:]]

    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = {
            DeploymentVersion.LEGACY.value: VersionMetrics(version="legacy"),
            DeploymentVersion.CANARY.value: VersionMetrics(version="canary"),
        }
        self.request_history = []
        self.endpoint_metrics = defaultdict(
            lambda: {"legacy": {"count": 0, "errors": 0}, "canary": {"count": 0, "errors": 0}}
        )
        logger.info("✅ Metrics reset")

    def export_metrics_json(self) -> str:
        """메트릭을 JSON으로 내보내기"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_metrics_summary(),
            "endpoints": self.get_endpoint_metrics(),
            "recent_errors": self.get_recent_errors(50),
        }
        return json.dumps(data, indent=2)

    def log_metrics_summary(self):
        """메트릭 요약 로깅"""
        summary = self.get_metrics_summary()

        logger.info("=" * 60)
        logger.info("📊 CANARY METRICS SUMMARY")
        logger.info("=" * 60)

        for version, metrics in [("legacy", summary["legacy"]), ("canary", summary["canary"])]:
            logger.info(f"\n{version.upper()}:")
            for key, value in metrics.items():
                logger.info(f"  {key}: {value}")

        logger.info("\nCOMPARISON:")
        for key, value in summary["comparison"].items():
            logger.info(f"  {key}: {value}")

        logger.info("=" * 60)


# 글로벌 메트릭 수집기 인스턴스
_metrics_collector: CanaryMetricsCollector = None


def get_metrics_collector() -> CanaryMetricsCollector:
    """메트릭 수집기 싱글톤"""
    global _metrics_collector

    if _metrics_collector is None:
        _metrics_collector = CanaryMetricsCollector()

    return _metrics_collector
