"""
SLO Exporter for Cloud Run Environment

Cloud Run 환경에서 서비스 수준 목표(SLO)를 추적하고 평가하는 Exporter
Kubernetes 기반 원본 Lumen SLO Exporter를 Cloud Run에 맞게 적응

측정 항목:
- 가용성 (Availability): 성공률 기반
- 레이턴시 (Latency): P95, P99 임계값
- 에러율 (Error Rate): 4xx, 5xx 에러
- 처리량 (Throughput): 초당 요청 수
"""

from google.cloud import monitoring_v3
import datetime
from typing import Dict, List, Optional, Tuple
import logging
import os
import json

logger = logging.getLogger(__name__)


class SLOExporterCloudRun:
    """Cloud Run 환경에서 SLO를 추적하고 평가하는 Exporter"""
    
    # SLO 목표 정의
    SLO_TARGETS = {
        "availability": 99.5,  # 99.5% 가용성 (월간 3.6시간 다운타임 허용)
        "latency_p95": 200,    # P95 레이턴시 < 200ms
        "latency_p99": 500,    # P99 레이턴시 < 500ms
        "error_rate": 0.1,     # 에러율 < 0.1%
    }
    
    # 알림 임계값 (SLO 목표 대비)
    ALERT_THRESHOLDS = {
        "critical": 0.95,  # 95% 달성 시 CRITICAL
        "warning": 0.98,   # 98% 달성 시 WARNING
    }
    
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
    
    def get_availability(self, hours: int = 24) -> Dict[str, float]:
        """
        가용성 측정: 성공한 요청 비율
        
        Args:
            hours: 측정 기간 (시간)
        
        Returns:
            Dict with:
                - availability: 가용성 (%)
                - total_requests: 총 요청 수
                - successful_requests: 성공한 요청 수
                - failed_requests: 실패한 요청 수
                - slo_target: SLO 목표
                - slo_achieved: SLO 달성 여부
        """
        try:
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
            
            # 실패 요청 수 (5xx만, 4xx는 클라이언트 에러로 간주)
            failed_request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}" AND metric.labels.response_code_class="5"',
                "interval": interval,
            })
            
            total_results = self.monitoring_client.list_time_series(request=total_request)
            failed_results = self.monitoring_client.list_time_series(request=failed_request)
            
            # 총 요청 수 계산
            total_count = sum(
                sum(point.value.int64_value for point in result.points)
                for result in total_results
            )
            
            # 실패 요청 수 계산
            failed_count = sum(
                sum(point.value.int64_value for point in result.points)
                for result in failed_results
            )
            
            # 가용성 계산
            if total_count == 0:
                availability = 100.0
                successful_count = 0
            else:
                successful_count = total_count - failed_count
                availability = (successful_count / total_count) * 100
            
            # SLO 달성 여부
            slo_target = self.SLO_TARGETS["availability"]
            slo_achieved = availability >= slo_target
            
            result = {
                "availability": availability,
                "total_requests": total_count,
                "successful_requests": successful_count,
                "failed_requests": failed_count,
                "slo_target": slo_target,
                "slo_achieved": slo_achieved,
            }
            
            logger.info(f"Availability: {availability:.2f}% (target: {slo_target}%), achieved: {slo_achieved}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to get availability: {e}")
            return {
                "availability": 0.0,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "slo_target": self.SLO_TARGETS["availability"],
                "slo_achieved": False,
            }
    
    def get_latency(self, hours: int = 24) -> Dict[str, float]:
        """
        레이턴시 측정: P95, P99
        
        Args:
            hours: 측정 기간 (시간)
        
        Returns:
            Dict with:
                - latency_p95: P95 레이턴시 (ms)
                - latency_p99: P99 레이턴시 (ms)
                - slo_p95_target: P95 목표 (ms)
                - slo_p99_target: P99 목표 (ms)
                - slo_p95_achieved: P95 SLO 달성 여부
                - slo_p99_achieved: P99 SLO 달성 여부
        """
        try:
            metric_type = "run.googleapis.com/request_latencies"
            
            now = datetime.datetime.utcnow()
            end_time = now
            start_time = now - datetime.timedelta(hours=hours)
            
            interval = monitoring_v3.TimeInterval({
                "start_time": {"seconds": int(start_time.timestamp())},
                "end_time": {"seconds": int(end_time.timestamp())},
            })
            
            # P95 레이턴시
            p95_aggregation = monitoring_v3.Aggregation({
                "alignment_period": {"seconds": 300},
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_DELTA,
                "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_PERCENTILE_95,
            })
            
            p95_request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}"',
                "interval": interval,
                "aggregation": p95_aggregation,
            })
            
            # P99 레이턴시
            p99_aggregation = monitoring_v3.Aggregation({
                "alignment_period": {"seconds": 300},
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_DELTA,
                "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_PERCENTILE_99,
            })
            
            p99_request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}"',
                "interval": interval,
                "aggregation": p99_aggregation,
            })
            
            p95_results = self.monitoring_client.list_time_series(request=p95_request)
            p99_results = self.monitoring_client.list_time_series(request=p99_request)
            
            # P95 계산
            latency_p95 = 0.0
            for result in p95_results:
                if result.points:
                    latency_p95 = result.points[-1].value.double_value
                    break
            
            # P99 계산
            latency_p99 = 0.0
            for result in p99_results:
                if result.points:
                    latency_p99 = result.points[-1].value.double_value
                    break
            
            # SLO 달성 여부
            slo_p95_target = self.SLO_TARGETS["latency_p95"]
            slo_p99_target = self.SLO_TARGETS["latency_p99"]
            
            slo_p95_achieved = latency_p95 <= slo_p95_target if latency_p95 > 0 else True
            slo_p99_achieved = latency_p99 <= slo_p99_target if latency_p99 > 0 else True
            
            result = {
                "latency_p95": latency_p95,
                "latency_p99": latency_p99,
                "slo_p95_target": slo_p95_target,
                "slo_p99_target": slo_p99_target,
                "slo_p95_achieved": slo_p95_achieved,
                "slo_p99_achieved": slo_p99_achieved,
            }
            
            logger.info(f"Latency P95: {latency_p95:.2f}ms (target: {slo_p95_target}ms), P99: {latency_p99:.2f}ms (target: {slo_p99_target}ms)")
            return result
        
        except Exception as e:
            logger.error(f"Failed to get latency: {e}")
            return {
                "latency_p95": 0.0,
                "latency_p99": 0.0,
                "slo_p95_target": self.SLO_TARGETS["latency_p95"],
                "slo_p99_target": self.SLO_TARGETS["latency_p99"],
                "slo_p95_achieved": False,
                "slo_p99_achieved": False,
            }
    
    def get_error_rate(self, hours: int = 24) -> Dict[str, float]:
        """
        에러율 측정: 4xx, 5xx 비율
        
        Args:
            hours: 측정 기간 (시간)
        
        Returns:
            Dict with:
                - error_rate: 에러율 (%)
                - error_4xx_count: 4xx 에러 수
                - error_5xx_count: 5xx 에러 수
                - total_requests: 총 요청 수
                - slo_target: SLO 목표
                - slo_achieved: SLO 달성 여부
        """
        try:
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
            
            # 4xx 에러
            error_4xx_request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}" AND metric.labels.response_code_class="4"',
                "interval": interval,
            })
            
            # 5xx 에러
            error_5xx_request = monitoring_v3.ListTimeSeriesRequest({
                "name": self.project_name,
                "filter": f'metric.type="{metric_type}" AND resource.labels.service_name="{self.service_name}" AND metric.labels.response_code_class="5"',
                "interval": interval,
            })
            
            total_results = self.monitoring_client.list_time_series(request=total_request)
            error_4xx_results = self.monitoring_client.list_time_series(request=error_4xx_request)
            error_5xx_results = self.monitoring_client.list_time_series(request=error_5xx_request)
            
            # 카운트 계산
            total_count = sum(
                sum(point.value.int64_value for point in result.points)
                for result in total_results
            )
            
            error_4xx_count = sum(
                sum(point.value.int64_value for point in result.points)
                for result in error_4xx_results
            )
            
            error_5xx_count = sum(
                sum(point.value.int64_value for point in result.points)
                for result in error_5xx_results
            )
            
            # 에러율 계산
            if total_count == 0:
                error_rate = 0.0
            else:
                total_errors = error_4xx_count + error_5xx_count
                error_rate = (total_errors / total_count) * 100
            
            # SLO 달성 여부
            slo_target = self.SLO_TARGETS["error_rate"]
            slo_achieved = error_rate <= slo_target
            
            result = {
                "error_rate": error_rate,
                "error_4xx_count": error_4xx_count,
                "error_5xx_count": error_5xx_count,
                "total_requests": total_count,
                "slo_target": slo_target,
                "slo_achieved": slo_achieved,
            }
            
            logger.info(f"Error rate: {error_rate:.2f}% (target: {slo_target}%), achieved: {slo_achieved}")
            return result
        
        except Exception as e:
            logger.error(f"Failed to get error rate: {e}")
            return {
                "error_rate": 0.0,
                "error_4xx_count": 0,
                "error_5xx_count": 0,
                "total_requests": 0,
                "slo_target": self.SLO_TARGETS["error_rate"],
                "slo_achieved": False,
            }
    
    def evaluate_slo_status(self, hours: int = 24) -> Dict[str, any]:
        """
        전체 SLO 상태 평가
        
        Args:
            hours: 측정 기간 (시간)
        
        Returns:
            Dict with:
                - availability: 가용성 데이터
                - latency: 레이턴시 데이터
                - error_rate: 에러율 데이터
                - overall_status: 전체 상태 (HEALTHY/WARNING/CRITICAL)
                - slo_compliance: SLO 준수율 (%)
                - failed_slos: 실패한 SLO 목록
        """
        # 각 메트릭 수집
        availability = self.get_availability(hours)
        latency = self.get_latency(hours)
        error_rate = self.get_error_rate(hours)
        
        # SLO 달성 여부 확인
        slo_checks = {
            "availability": availability["slo_achieved"],
            "latency_p95": latency["slo_p95_achieved"],
            "latency_p99": latency["slo_p99_achieved"],
            "error_rate": error_rate["slo_achieved"],
        }
        
        # 실패한 SLO 목록
        failed_slos = [name for name, achieved in slo_checks.items() if not achieved]
        
        # SLO 준수율
        total_slos = len(slo_checks)
        achieved_slos = sum(1 for achieved in slo_checks.values() if achieved)
        slo_compliance = (achieved_slos / total_slos) * 100
        
        # 전체 상태 결정
        if slo_compliance == 100:
            overall_status = "HEALTHY"
        elif slo_compliance >= 75:
            overall_status = "WARNING"
        else:
            overall_status = "CRITICAL"
        
        result = {
            "availability": availability,
            "latency": latency,
            "error_rate": error_rate,
            "overall_status": overall_status,
            "slo_compliance": slo_compliance,
            "failed_slos": failed_slos,
        }
        
        logger.info(f"SLO Status: {overall_status}, Compliance: {slo_compliance:.1f}%")
        return result
    
    def generate_report(self, hours: int = 24) -> str:
        """
        SLO 리포트 생성
        
        Args:
            hours: 측정 기간 (시간)
        
        Returns:
            Markdown 형식 리포트
        """
        status_data = self.evaluate_slo_status(hours)
        
        # 상태 아이콘
        status_icon_map = {
            "HEALTHY": "✅",
            "WARNING": "⚠️",
            "CRITICAL": "❌",
        }
        status_icon = status_icon_map.get(status_data["overall_status"], "❓")
        
        # 리포트 생성
        report = f"""
# SLO Report

**Date**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Service**: {self.service_name}  
**Project**: {self.project_id}  
**Period**: Last {hours} hours

---

## {status_icon} Overall Status: {status_data["overall_status"]}

**SLO Compliance**: {status_data["slo_compliance"]:.1f}%

"""
        
        if status_data["failed_slos"]:
            report += f"**Failed SLOs**: {', '.join(status_data['failed_slos'])}\n\n"
        else:
            report += "**All SLOs achieved** ✅\n\n"
        
        report += "---\n\n"
        
        # 가용성
        avail = status_data["availability"]
        avail_icon = "✅" if avail["slo_achieved"] else "❌"
        report += f"""
## {avail_icon} Availability

- **Current**: {avail["availability"]:.2f}%
- **Target**: {avail["slo_target"]}%
- **Total Requests**: {avail["total_requests"]:,}
- **Successful**: {avail["successful_requests"]:,}
- **Failed (5xx)**: {avail["failed_requests"]:,}
- **Status**: {'PASS' if avail["slo_achieved"] else 'FAIL'}

"""
        
        # 레이턴시
        lat = status_data["latency"]
        lat_p95_icon = "✅" if lat["slo_p95_achieved"] else "❌"
        lat_p99_icon = "✅" if lat["slo_p99_achieved"] else "❌"
        report += f"""
## Latency

### {lat_p95_icon} P95 Latency
- **Current**: {lat["latency_p95"]:.2f}ms
- **Target**: {lat["slo_p95_target"]}ms
- **Status**: {'PASS' if lat["slo_p95_achieved"] else 'FAIL'}

### {lat_p99_icon} P99 Latency
- **Current**: {lat["latency_p99"]:.2f}ms
- **Target**: {lat["slo_p99_target"]}ms
- **Status**: {'PASS' if lat["slo_p99_achieved"] else 'FAIL'}

"""
        
        # 에러율
        err = status_data["error_rate"]
        err_icon = "✅" if err["slo_achieved"] else "❌"
        report += f"""
## {err_icon} Error Rate

- **Current**: {err["error_rate"]:.2f}%
- **Target**: < {err["slo_target"]}%
- **4xx Errors**: {err["error_4xx_count"]:,}
- **5xx Errors**: {err["error_5xx_count"]:,}
- **Total Requests**: {err["total_requests"]:,}
- **Status**: {'PASS' if err["slo_achieved"] else 'FAIL'}

---

## 💡 Recommendations

"""
        
        # 권장사항
        if status_data["overall_status"] == "HEALTHY":
            report += """
✅ **All systems operational**
- Continue monitoring
- Maintain current configuration
- Review trends weekly
"""
        elif status_data["overall_status"] == "WARNING":
            report += """
⚠️ **Some SLOs need attention**

Actions:
1. Review failed SLO metrics
2. Investigate root causes
3. Adjust configuration if needed
4. Increase monitoring frequency
"""
        else:
            report += """
❌ **Critical: Multiple SLO violations**

Immediate Actions:
1. Check service health
2. Review recent deployments
3. Investigate infrastructure issues
4. Consider rollback if necessary
5. Alert team and stakeholders
"""
        
        report += "\n---\n"
        
        return report
    
    def export_to_cloud_monitoring(self, status_data: Dict[str, any]) -> None:
        """
        SLO 메트릭을 Cloud Monitoring Custom Metric으로 내보내기
        
        Args:
            status_data: SLO 상태 데이터
        """
        try:
            # SLO 준수율 메트릭
            series = monitoring_v3.TimeSeries()
            series.metric.type = "custom.googleapis.com/slo_compliance"
            series.resource.type = "cloud_run_revision"
            series.resource.labels["project_id"] = self.project_id
            series.resource.labels["service_name"] = self.service_name
            
            now = datetime.datetime.utcnow()
            point = monitoring_v3.Point({
                "interval": {
                    "end_time": {"seconds": int(now.timestamp())},
                },
                "value": {"double_value": status_data["slo_compliance"]},
            })
            series.points = [point]
            
            self.monitoring_client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
            
            logger.info(f"Exported SLO compliance to Cloud Monitoring: {status_data['slo_compliance']:.1f}%")
        
        except Exception as e:
            logger.error(f"Failed to export to Cloud Monitoring: {e}")


def main():
    """메인 함수"""
    logging.basicConfig(level=logging.INFO)
    
    project_id = os.getenv("GCP_PROJECT_ID", "naeda-genesis")
    service_name = os.getenv("CLOUD_RUN_SERVICE", "ion-api-canary")
    
    exporter = SLOExporterCloudRun(project_id, service_name)
    
    # SLO 상태 평가
    status_data = exporter.evaluate_slo_status(hours=24)
    
    # 리포트 생성
    report = exporter.generate_report(hours=24)
    print(report)
    
    # Cloud Monitoring에 내보내기
    exporter.export_to_cloud_monitoring(status_data)
    
    # 결과 반환 (모니터링 통합용)
    result = {
        "overall_status": status_data["overall_status"],
        "slo_compliance": status_data["slo_compliance"],
        "failed_slos": status_data["failed_slos"],
    }
    
    # JSON 출력
    print("\n=== SLO Status (JSON) ===")
    print(json.dumps(result, indent=2))
    
    # Exit code 설정
    if status_data["overall_status"] == "HEALTHY":
        exit(0)
    elif status_data["overall_status"] == "WARNING":
        exit(1)
    else:
        exit(2)


if __name__ == "__main__":
    main()
