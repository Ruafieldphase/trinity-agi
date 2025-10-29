"""
Maturity Exporter for Cloud Run Environment

Cloud Run 환경에서 시스템 성숙도를 측정하는 Exporter
Kubernetes 기반 원본 Lumen Maturity Exporter를 Cloud Run에 맞게 적응

측정 항목:
- 배포 빈도 (Deployment Frequency)
- 평균 레이턴시 (Latency)
- 에러율 (Error Rate)
- 가용성 (Availability)
- 캐시 히트율 (Cache Hit Rate)
- 비용 효율성 (Cost Efficiency)
"""

from google.cloud import monitoring_v3
from google.cloud import run_v2
import datetime
from typing import Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)


class MaturityExporterCloudRun:
    """Cloud Run 환경에서 시스템 성숙도를 측정하는 Exporter"""
    
    def __init__(self, project_id: str, service_name: str = "ion-api-canary"):
        """
        Args:
            project_id: GCP 프로젝트 ID
            service_name: Cloud Run 서비스 이름
        """
        self.project_id = project_id
        self.service_name = service_name
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.run_client = run_v2.ServicesClient()
        self.revisions_client = run_v2.RevisionsClient()
        self.project_name = f"projects/{project_id}"
    
    def get_deployment_frequency(self, days: int = 7) -> float:
        """
        배포 빈도 측정: 지난 N일 동안 생성된 리비전 수
        
        Args:
            days: 측정 기간 (일)
        
        Returns:
            배포 빈도 스코어 (0-100)
            - 0-20: 매우 낮음 (월 1회 미만)
            - 21-40: 낮음 (주 1회 미만)
            - 41-60: 보통 (주 1-2회)
            - 61-80: 높음 (주 3-5회)
            - 81-100: 매우 높음 (일 1회 이상)
        """
        try:
            # Cloud Run 리비전 목록 조회
            parent = f"projects/{self.project_id}/locations/us-central1/services/{self.service_name}"
            revisions = self.revisions_client.list_revisions(parent=parent)
            
            # 지난 N일 동안 생성된 리비전 수 계산
            now = datetime.datetime.now(datetime.timezone.utc)
            start_time = now - datetime.timedelta(days=days)
            
            recent_revisions = [
                r for r in revisions
                if r.create_time.replace(tzinfo=datetime.timezone.utc) >= start_time
            ]
            
            revision_count = len(recent_revisions)
            
            # 배포 빈도 스코어 계산
            # 일평균 배포 횟수로 스코어 산정
            avg_per_day = revision_count / days
            
            if avg_per_day >= 1.0:
                score = 100
            elif avg_per_day >= 0.5:
                score = 80
            elif avg_per_day >= 0.3:
                score = 60
            elif avg_per_day >= 0.15:
                score = 40
            else:
                score = 20
            
            logger.info(f"Deployment frequency: {revision_count} revisions in {days} days, score: {score}")
            return score
        
        except Exception as e:
            logger.error(f"Failed to get deployment frequency: {e}")
            return 0.0
    
    def get_latency_score(self, hours: int = 24) -> float:
        """
        레이턴시 스코어 측정: 지난 N시간 동안의 P95 레이턴시
        
        Args:
            hours: 측정 기간 (시간)
        
        Returns:
            레이턴시 스코어 (0-100)
            - 0-20: 매우 느림 (>1000ms)
            - 21-40: 느림 (500-1000ms)
            - 41-60: 보통 (200-500ms)
            - 61-80: 빠름 (100-200ms)
            - 81-100: 매우 빠름 (<100ms)
        """
        try:
            # Cloud Run 레이턴시 메트릭 조회
            # run.googleapis.com/request_latencies
            metric_type = "run.googleapis.com/request_latencies"
            
            now = datetime.datetime.utcnow()
            end_time = now
            start_time = now - datetime.timedelta(hours=hours)
            
            interval = monitoring_v3.TimeInterval({
                "start_time": {"seconds": int(start_time.timestamp())},
                "end_time": {"seconds": int(end_time.timestamp())},
            })
            
            aggregation = monitoring_v3.Aggregation({
                "alignment_period": {"seconds": 300},  # 5분 단위
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_DELTA,
                "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_PERCENTILE_95,
            })
            
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}"',
                "interval": interval,
                "aggregation": aggregation,
            })
            
            results = self.monitoring_client.list_time_series(request=request)
            
            # P95 레이턴시 계산 (최근 값 사용)
            p95_latency_ms = 0
            for result in results:
                if result.points:
                    # 마지막 포인트의 값 사용
                    p95_latency_ms = result.points[-1].value.double_value
                    break
            
            # 스코어 계산
            if p95_latency_ms == 0:
                score = 50  # 데이터 없음 (중간값)
            elif p95_latency_ms < 100:
                score = 100
            elif p95_latency_ms < 200:
                score = 80
            elif p95_latency_ms < 500:
                score = 60
            elif p95_latency_ms < 1000:
                score = 40
            else:
                score = 20
            
            logger.info(f"Latency P95: {p95_latency_ms:.2f}ms, score: {score}")
            return score
        
        except Exception as e:
            logger.error(f"Failed to get latency score: {e}")
            return 50.0  # 중간값 반환
    
    def get_error_rate_score(self, hours: int = 24) -> float:
        """
        에러율 스코어 측정: 지난 N시간 동안의 4xx/5xx 에러율
        
        Args:
            hours: 측정 기간 (시간)
        
        Returns:
            에러율 스코어 (0-100)
            - 0-20: 매우 높음 (>5%)
            - 21-40: 높음 (1-5%)
            - 41-60: 보통 (0.5-1%)
            - 61-80: 낮음 (0.1-0.5%)
            - 81-100: 매우 낮음 (<0.1%)
        """
        try:
            # Cloud Run 요청 수 메트릭 조회
            metric_type = "run.googleapis.com/request_count"
            
            now = datetime.datetime.utcnow()
            end_time = now
            start_time = now - datetime.timedelta(hours=hours)
            
            interval = monitoring_v3.TimeInterval({
                "start_time": {"seconds": int(start_time.timestamp())},
                "end_time": {"seconds": int(end_time.timestamp())},
            })
            
            # 전체 요청 수
            total_request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}"',
                "interval": interval,
            })
            
            # 에러 요청 수 (4xx)
            error_4xx_request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}" AND metric.labels.response_code_class="4"',
                "interval": interval,
            })
            
            # 에러 요청 수 (5xx)
            error_5xx_request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}" AND metric.labels.response_code_class="5"',
                "interval": interval,
            })
            
            total_results = self.monitoring_client.list_time_series(request=total_request)
            error_4xx_results = self.monitoring_client.list_time_series(request=error_4xx_request)
            error_5xx_results = self.monitoring_client.list_time_series(request=error_5xx_request)
            
            # 총 요청 수 계산
            total_count = sum(
                sum(point.value.int64_value for point in result.points)
                for result in total_results
            )
            
            # 에러 요청 수 계산 (4xx + 5xx)
            error_4xx_count = sum(
                sum(point.value.int64_value for point in result.points)
                for result in error_4xx_results
            )
            error_5xx_count = sum(
                sum(point.value.int64_value for point in result.points)
                for result in error_5xx_results
            )
            error_count = error_4xx_count + error_5xx_count
            
            # 에러율 계산
            if total_count == 0:
                error_rate = 0.0
            else:
                error_rate = (error_count / total_count) * 100
            
            # 스코어 계산
            if error_rate == 0:
                score = 100
            elif error_rate < 0.1:
                score = 90
            elif error_rate < 0.5:
                score = 70
            elif error_rate < 1.0:
                score = 50
            elif error_rate < 5.0:
                score = 30
            else:
                score = 10
            
            logger.info(f"Error rate: {error_rate:.2f}% ({error_count}/{total_count}), score: {score}")
            return score
        
        except Exception as e:
            logger.error(f"Failed to get error rate score: {e}")
            return 50.0  # 중간값 반환
    
    def get_availability_score(self, hours: int = 24) -> float:
        """
        가용성 스코어 측정: 지난 N시간 동안의 가용성
        
        Args:
            hours: 측정 기간 (시간)
        
        Returns:
            가용성 스코어 (0-100)
            - 0-20: 매우 낮음 (<95%)
            - 21-40: 낮음 (95-97%)
            - 41-60: 보통 (97-99%)
            - 61-80: 높음 (99-99.5%)
            - 81-100: 매우 높음 (>99.5%)
        """
        try:
            # Cloud Run 가용성은 에러율의 반대 개념
            error_score = self.get_error_rate_score(hours)
            
            # 에러율이 낮으면 가용성이 높음
            # error_score가 높으면 availability_score도 높음
            availability_score = error_score
            
            logger.info(f"Availability score: {availability_score}")
            return availability_score
        
        except Exception as e:
            logger.error(f"Failed to get availability score: {e}")
            return 50.0  # 중간값 반환
    
    def get_cache_hit_rate_score(self) -> float:
        """
        캐시 히트율 스코어 측정: Redis 캐시 히트율
        
        Returns:
            캐시 히트율 스코어 (0-100)
            - 0-20: 매우 낮음 (<40%)
            - 21-40: 낮음 (40-60%)
            - 41-60: 보통 (60-70%)
            - 61-80: 높음 (70-80%)
            - 81-100: 매우 높음 (>80%)
        """
        try:
            # Custom metric: custom/cache_hit_rate
            metric_type = "custom.googleapis.com/cache_hit_rate"
            
            now = datetime.datetime.utcnow()
            end_time = now
            start_time = now - datetime.timedelta(hours=1)  # 최근 1시간
            
            interval = monitoring_v3.TimeInterval({
                "start_time": {"seconds": int(start_time.timestamp())},
                "end_time": {"seconds": int(end_time.timestamp())},
            })
            
            request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}"',
                "interval": interval,
            })
            
            results = self.monitoring_client.list_time_series(request=request)
            
            # 최근 캐시 히트율 조회
            hit_rate = 0.0
            for result in results:
                if result.points:
                    hit_rate = result.points[-1].value.double_value
                    break
            
            # 스코어 계산
            if hit_rate >= 80:
                score = 100
            elif hit_rate >= 70:
                score = 80
            elif hit_rate >= 60:
                score = 60
            elif hit_rate >= 40:
                score = 40
            else:
                score = 20
            
            logger.info(f"Cache hit rate: {hit_rate:.2f}%, score: {score}")
            return score
        
        except Exception as e:
            logger.error(f"Failed to get cache hit rate score: {e}")
            # 캐시 메트릭이 없으면 기본값 (Phase 14에서 측정된 60% 사용)
            return 60.0
    
    def get_cost_efficiency_score(self, target_cost: float = 200.0) -> float:
        """
        비용 효율성 스코어 측정: 목표 비용 대비 실제 비용
        
        Args:
            target_cost: 목표 월간 비용 ($)
        
        Returns:
            비용 효율성 스코어 (0-100)
            - 0-20: 매우 나쁨 (>200% 초과)
            - 21-40: 나쁨 (150-200% 초과)
            - 41-60: 보통 (100-150%)
            - 61-80: 좋음 (80-100%)
            - 81-100: 매우 좋음 (<80%)
        """
        try:
            # TODO: GCP Billing API 연동
            # 현재는 임시로 고정값 사용
            # Phase 14에서 측정된 $9.36/month Redis 비용 사용
            
            # 임시 비용 (Redis만 고려)
            current_cost = 9.36  # Redis 월간 비용
            
            # 비용 비율 계산
            cost_ratio = (current_cost / target_cost) * 100
            
            # 스코어 계산
            if cost_ratio < 5:  # <$10
                score = 100
            elif cost_ratio < 10:  # <$20
                score = 90
            elif cost_ratio < 20:  # <$40
                score = 80
            elif cost_ratio < 50:  # <$100
                score = 60
            elif cost_ratio < 100:  # <$200
                score = 40
            else:  # >$200
                score = 20
            
            logger.info(f"Cost efficiency: ${current_cost:.2f} / ${target_cost:.2f} ({cost_ratio:.1f}%), score: {score}")
            return score
        
        except Exception as e:
            logger.error(f"Failed to get cost efficiency score: {e}")
            return 50.0  # 중간값 반환
    
    def calculate_maturity_score(self) -> Dict[str, float]:
        """
        전체 성숙도 스코어 계산
        
        Returns:
            Dict with:
                - maturity_score: 전체 성숙도 스코어 (0-100)
                - deployment_frequency: 배포 빈도 스코어
                - latency: 레이턴시 스코어
                - error_rate: 에러율 스코어
                - availability: 가용성 스코어
                - cache_hit_rate: 캐시 히트율 스코어
                - cost_efficiency: 비용 효율성 스코어
        """
        logger.info("Calculating maturity score...")
        
        # 각 항목별 스코어 계산
        deployment_score = self.get_deployment_frequency(days=7)
        latency_score = self.get_latency_score(hours=24)
        error_rate_score = self.get_error_rate_score(hours=24)
        availability_score = self.get_availability_score(hours=24)
        cache_hit_rate_score = self.get_cache_hit_rate_score()
        cost_efficiency_score = self.get_cost_efficiency_score(target_cost=200.0)
        
        # 가중치 적용 평균
        # 안정성 관련 항목에 더 높은 가중치
        weights = {
            "deployment_frequency": 0.10,
            "latency": 0.20,
            "error_rate": 0.25,
            "availability": 0.25,
            "cache_hit_rate": 0.10,
            "cost_efficiency": 0.10,
        }
        
        maturity_score = (
            deployment_score * weights["deployment_frequency"] +
            latency_score * weights["latency"] +
            error_rate_score * weights["error_rate"] +
            availability_score * weights["availability"] +
            cache_hit_rate_score * weights["cache_hit_rate"] +
            cost_efficiency_score * weights["cost_efficiency"]
        )
        
        result = {
            "maturity_score": round(maturity_score, 2),
            "deployment_frequency": round(deployment_score, 2),
            "latency": round(latency_score, 2),
            "error_rate": round(error_rate_score, 2),
            "availability": round(availability_score, 2),
            "cache_hit_rate": round(cache_hit_rate_score, 2),
            "cost_efficiency": round(cost_efficiency_score, 2),
        }
        
        logger.info(f"Maturity score calculated: {result}")
        return result
    
    def export_to_cloud_monitoring(self, scores: Dict[str, float]) -> None:
        """
        성숙도 스코어를 Cloud Monitoring Custom Metric으로 내보내기
        
        Args:
            scores: 성숙도 스코어 딕셔너리
        """
        try:
            # Custom metric 생성: custom.googleapis.com/maturity_score
            series = monitoring_v3.TimeSeries()
            series.metric.type = "custom.googleapis.com/maturity_score"
            series.resource.type = "cloud_run_revision"
            series.resource.labels["project_id"] = self.project_id
            series.resource.labels["service_name"] = self.service_name
            
            now = datetime.datetime.utcnow()
            point = monitoring_v3.Point({
                "interval": {
                    "end_time": {"seconds": int(now.timestamp())},
                },
                "value": {"double_value": scores["maturity_score"]},
            })
            series.points = [point]
            
            self.monitoring_client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
            
            logger.info(f"Exported maturity score to Cloud Monitoring: {scores['maturity_score']}")
        
        except Exception as e:
            logger.error(f"Failed to export to Cloud Monitoring: {e}")


def main():
    """메인 함수"""
    logging.basicConfig(level=logging.INFO)
    
    project_id = os.getenv("GCP_PROJECT_ID", "naeda-genesis")
    service_name = os.getenv("CLOUD_RUN_SERVICE", "ion-api-canary")
    
    exporter = MaturityExporterCloudRun(project_id, service_name)
    scores = exporter.calculate_maturity_score()
    
    print("\n=== Maturity Score Report ===")
    print(f"Overall Maturity: {scores['maturity_score']}/100")
    print(f"  - Deployment Frequency: {scores['deployment_frequency']}/100")
    print(f"  - Latency: {scores['latency']}/100")
    print(f"  - Error Rate: {scores['error_rate']}/100")
    print(f"  - Availability: {scores['availability']}/100")
    print(f"  - Cache Hit Rate: {scores['cache_hit_rate']}/100")
    print(f"  - Cost Efficiency: {scores['cost_efficiency']}/100")
    print("============================\n")
    
    # Cloud Monitoring에 내보내기
    exporter.export_to_cloud_monitoring(scores)


if __name__ == "__main__":
    main()
