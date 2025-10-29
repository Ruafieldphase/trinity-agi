"""
ROI Gate Exporter for Cloud Run Environment

Cloud Run 환경에서 간단한 ROI(투자수익률) 점수를 추정하는 Exporter

설계 목표 (경량, 무의존성 극소화):
- 복잡한 과금/청구 데이터 없이도 동작 (BigQuery/비용 API 미사용)
- Cloud Monitoring의 request_count 만으로 사용가치(가치) 근사
- 비용(cost)은 월간 예산(MONTHLY_BUDGET_USD) 기반의 일할 계산으로 근사
- 결과는 오케스트레이터가 기대하는 dict 형태 {"roi_score": float, ...}

ROI 정의(간이): ROI(%) = ((가치USD - 비용USD) / 비용USD) * 100
- 가치USD = 성공 요청 수 × VALUE_PER_REQUEST_USD (기본 0.01 USD)
- 비용USD = (MONTHLY_BUDGET_USD / 30) × (hours/24)

주의: 본 계산은 운영 안전을 위한 최소 구현으로, 절대 비용/가치의 정확한 추정이 아님
"""

from __future__ import annotations

import datetime
import logging
import os
from typing import Dict

from google.cloud import monitoring_v3

logger = logging.getLogger(__name__)


class ROIGateCloudRun:
    """Cloud Run 환경에서 간단 ROI 점수를 계산하는 Exporter"""

    def __init__(self, project_id: str, service_name: str = "ion-api-canary"):
        """
        Args:
            project_id: GCP 프로젝트 ID
            service_name: Cloud Run 서비스 이름
        """
        self.project_id = project_id
        self.service_name = service_name
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"

        # 환경 변수에서 파라미터 로드 (없으면 기본값)
        self.monthly_budget_usd = float(os.environ.get("MONTHLY_BUDGET_USD", "200.0"))
        self.value_per_request_usd = float(os.environ.get("VALUE_PER_REQUEST_USD", "0.01"))

    def _query_successful_requests(self, hours: int = 24) -> int:
        """최근 hours 시간 동안의 성공 요청 수(5xx 제외)를 합산"""
        metric_type = "run.googleapis.com/request_count"
        now = datetime.datetime.utcnow()
        interval = monitoring_v3.TimeInterval({
            "start_time": {"seconds": int((now - datetime.timedelta(hours=hours)).timestamp())},
            "end_time": {"seconds": int(now.timestamp())},
        })

        # 전체 요청 수
        total_req = monitoring_v3.ListTimeSeriesRequest({
            "name": self.project_name,
            "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}"',
            "interval": interval,
        })

        # 5xx 실패 요청 수
        failed_req = monitoring_v3.ListTimeSeriesRequest({
            "name": self.project_name,
            "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}" AND metric.labels.response_code_class="5"',
            "interval": interval,
        })

        total_results = self.monitoring_client.list_time_series(request=total_req)
        failed_results = self.monitoring_client.list_time_series(request=failed_req)

        total_count = sum(
            sum(point.value.int64_value for point in series.points)
            for series in total_results
        )
        failed_count = sum(
            sum(point.value.int64_value for point in series.points)
            for series in failed_results
        )
        successful = max(0, total_count - failed_count)
        logger.debug(f"Successful requests (last {hours}h): {successful}")
        return successful

    def _estimate_cost_usd(self, hours: int = 24) -> float:
        """월 예산을 기준으로 시간 비례 비용을 근사"""
        daily_budget = self.monthly_budget_usd / 30.0
        cost = daily_budget * (hours / 24.0)
        return max(0.0, float(cost))

    def _estimate_value_usd(self, successful_requests: int) -> float:
        return max(0.0, float(successful_requests) * self.value_per_request_usd)

    def calculate_roi_score(self, hours: int = 24) -> Dict[str, float]:
        """
        간이 ROI 점수 계산.

        Returns:
            Dict with fields:
                - roi_score: ROI 백분율 (예: 250.0 => 250%)
                - estimated_value_usd: 가치 추정치
                - estimated_cost_usd: 비용 추정치
                - successful_requests: 성공 요청 수
                - assumptions: 계산 가정 정보
        """
        try:
            successful = self._query_successful_requests(hours=hours)
        except Exception as e:
            # 모니터링 API 실패 시 보수적으로 0 처리 (오케스트레이터 중단 방지)
            logger.warning(f"Failed to query request_count: {e}")
            successful = 0

        cost_usd = self._estimate_cost_usd(hours=hours)
        value_usd = self._estimate_value_usd(successful)

        if cost_usd <= 0.0:
            roi_pct = 1000.0  # 비용이 0이면 ROI 무한대 취급 → 상한(1000%)
        else:
            roi_pct = ((value_usd - cost_usd) / cost_usd) * 100.0

        # 안전 범위로 클램프 (보고/게이트 계산 안정화)
        roi_pct = max(-100.0, min(1000.0, roi_pct))

        result = {
            "roi_score": float(roi_pct),
            "estimated_value_usd": round(value_usd, 4),
            "estimated_cost_usd": round(cost_usd, 4),
            "successful_requests": int(successful),
            "assumptions": {
                "value_per_request_usd": self.value_per_request_usd,
                "hours_window": hours,
                "monthly_budget_usd": self.monthly_budget_usd,
                "notes": "Lightweight ROI estimate based on request_count and monthly budget proportion; not an accounting metric.",
            },
        }

        logger.info(
            "ROI Gate: roi=%.2f%%, value=$%.4f, cost=$%.4f, req=%d",
            result["roi_score"], result["estimated_value_usd"], result["estimated_cost_usd"], result["successful_requests"]
        )
        return result
