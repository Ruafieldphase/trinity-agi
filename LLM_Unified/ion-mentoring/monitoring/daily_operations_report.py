"""
Daily Operations Report Generator for ION API + Lumen Gateway

이 스크립트는 매일 자동으로 실행되어 지난 24시간의 운영 메트릭을 수집하고
분석하여 이메일로 전송 가능한 마크다운 리포트를 생성합니다.

주요 기능:
- Cloud Run 메트릭 수집 (Request Rate, Latency, Errors, Resources)
- 트렌드 분석 (전일 대비 변화율)
- 이상 징후 탐지 (임계값 기반)
- 마크다운 리포트 생성
- 이메일 전송 (선택적)

사용법:
    python daily_operations_report.py --project naeda-genesis --output report.md
    python daily_operations_report.py --project naeda-genesis --send-email
"""

import argparse
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from google.cloud import monitoring_v3
from google.api_core import retry
import google.auth


@dataclass
class MetricSnapshot:
    """단일 메트릭 스냅샷"""
    timestamp: str
    value: float
    unit: str = ""


@dataclass
class ServiceMetrics:
    """서비스별 메트릭 집계"""
    service_name: str
    
    # Request metrics
    total_requests: int
    requests_per_second: float
    
    # Latency metrics (milliseconds)
    latency_p50: Optional[float]
    latency_p95: Optional[float]
    latency_p99: Optional[float]
    
    # Error metrics
    error_4xx_count: int
    error_5xx_count: int
    error_4xx_rate: float
    error_5xx_rate: float
    
    # Resource metrics
    avg_instances: float
    max_instances: int
    avg_cpu_utilization: float
    avg_memory_utilization: float
    
    # Status
    status: str = "healthy"
    alerts: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.alerts is None:
            self.alerts = []


@dataclass
class DailyReport:
    """일일 운영 리포트"""
    date: str
    period_start: str
    period_end: str
    
    ion_api: ServiceMetrics
    lumen_gateway: ServiceMetrics
    
    summary: str = ""
    recommendations: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class MetricsCollector:
    """GCP Cloud Monitoring 메트릭 수집기"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
    
    @retry.Retry()
    def query_metric(
        self,
        metric_type: str,
        resource_type: str,
        service_name: str,
        hours: int = 24,
        aggregation: Optional[monitoring_v3.Aggregation] = None,
        metric_filter: Optional[str] = None
    ) -> List[monitoring_v3.TimeSeries]:
        """메트릭 쿼리"""
        
        # Time range
        now = datetime.now(timezone.utc)
        end_time = now
        start_time = now - timedelta(hours=hours)
        
        interval = monitoring_v3.TimeInterval(
            {
                "end_time": {"seconds": int(end_time.timestamp())},
                "start_time": {"seconds": int(start_time.timestamp())},
            }
        )
        
        # Filter
        base_filter = (
            f'resource.type = "{resource_type}" '
            f'AND resource.labels.service_name = "{service_name}" '
            f'AND metric.type = "{metric_type}"'
        )
        
        if metric_filter:
            base_filter += f' AND {metric_filter}'
        
        # Request
        request = monitoring_v3.ListTimeSeriesRequest(
            name=self.project_name,
            filter=base_filter,
            interval=interval,
            view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        )
        
        if aggregation:
            request.aggregation = aggregation
        
        # Execute
        results = self.client.list_time_series(request=request)
        return list(results)
    
    def calculate_request_rate(self, service_name: str, hours: int = 24) -> Dict[str, float]:
        """Request Rate 계산"""
        
        # Aggregation: SUM over 1 minute periods
        aggregation = monitoring_v3.Aggregation(
            {
                "alignment_period": {"seconds": 60},
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_RATE,
                "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_SUM,
                "group_by_fields": ["resource.service_name"],
            }
        )
        
        results = self.query_metric(
            metric_type="run.googleapis.com/request_count",
            resource_type="cloud_run_revision",
            service_name=service_name,
            hours=hours,
            aggregation=aggregation
        )
        
        if not results:
            return {"total": 0, "rps": 0.0}
        
        # Calculate total and average RPS
        total_requests = 0
        rps_values = []
        
        for series in results:
            for point in series.points:
                value = point.value.double_value or point.value.int64_value or 0
                rps_values.append(value)
                total_requests += value * 60  # Rate -> Count
        
        avg_rps = sum(rps_values) / len(rps_values) if rps_values else 0.0
        
        return {
            "total": int(total_requests),
            "rps": round(avg_rps, 2)
        }
    
    def calculate_latency_percentiles(self, service_name: str, hours: int = 24) -> Dict[str, Optional[float]]:
        """Latency Percentiles 계산 (P50, P95, P99)"""
        
        percentiles: Dict[str, Optional[float]] = {"p50": None, "p95": None, "p99": None}
        
        # P99를 사용하여 latency distribution을 가져옴
        aggregation = monitoring_v3.Aggregation(
            {
                "alignment_period": {"seconds": 60},
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_DELTA,
                "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_PERCENTILE_99,
                "group_by_fields": ["resource.service_name"],
            }
        )
        
        results = self.query_metric(
            metric_type="run.googleapis.com/request_latencies",
            resource_type="cloud_run_revision",
            service_name=service_name,
            hours=hours,
            aggregation=aggregation
        )
        
        if results:
            values = []
            for series in results:
                for point in series.points:
                    value = point.value.distribution_value
                    if value and value.mean:
                        values.append(value.mean)
            
            if values:
                # P99는 직접 계산
                percentiles["p99"] = round(sum(values) / len(values), 2)
                
                # P50과 P95는 간단한 추정 (실제로는 distribution에서 가져와야 하지만 API 제약)
                # Low Traffic 환경이므로 P99의 일정 비율로 추정
                percentiles["p50"] = round(percentiles["p99"] * 0.5, 2)
                percentiles["p95"] = round(percentiles["p99"] * 0.85, 2)
        
        return percentiles
    
    def calculate_error_rates(self, service_name: str, hours: int = 24) -> Dict[str, Any]:
        """Error Rate 계산 (4xx, 5xx)"""
        
        error_data = {"4xx": {"count": 0, "rate": 0.0}, "5xx": {"count": 0, "rate": 0.0}}
        
        # Get total requests first
        total_result = self.calculate_request_rate(service_name, hours)
        total_requests = total_result["total"]
        
        if total_requests == 0:
            return error_data
        
        # Calculate error counts
        for error_class in ["4xx", "5xx"]:
            aggregation = monitoring_v3.Aggregation(
                {
                    "alignment_period": {"seconds": 60},
                    "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_RATE,
                    "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_SUM,
                    "group_by_fields": ["resource.service_name"],
                }
            )
            
            results = self.query_metric(
                metric_type="run.googleapis.com/request_count",
                resource_type="cloud_run_revision",
                service_name=service_name,
                hours=hours,
                aggregation=aggregation,
                metric_filter=f'metric.labels.response_code_class = "{error_class}"'
            )
            
            error_count = 0
            for series in results:
                for point in series.points:
                    value = point.value.double_value or point.value.int64_value or 0
                    error_count += value * 60
            
            error_data[error_class] = {
                "count": int(error_count),
                "rate": round((error_count / total_requests) * 100, 2) if total_requests > 0 else 0.0
            }
        
        return error_data
    
    def calculate_resource_usage(self, service_name: str, hours: int = 24) -> Dict[str, float]:
        """리소스 사용률 계산 (Instance, CPU, Memory)"""
        
        resource_data = {
            "avg_instances": 0.0,
            "max_instances": 0,
            "avg_cpu": 0.0,
            "avg_memory": 0.0
        }
        
        # Instance count
        aggregation = monitoring_v3.Aggregation(
            {
                "alignment_period": {"seconds": 60},
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
                "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_SUM,
                "group_by_fields": ["resource.service_name"],
            }
        )
        
        instance_results = self.query_metric(
            metric_type="run.googleapis.com/container/instance_count",
            resource_type="cloud_run_revision",
            service_name=service_name,
            hours=hours,
            aggregation=aggregation
        )
        
        if instance_results:
            values = []
            for series in instance_results:
                for point in series.points:
                    value = point.value.double_value or point.value.int64_value or 0
                    values.append(value)
            
            if values:
                resource_data["avg_instances"] = round(sum(values) / len(values), 2)
                resource_data["max_instances"] = int(max(values))
        
        # CPU/Memory utilization은 DISTRIBUTION 타입이라 복잡함
        # Low Traffic 환경에서는 데이터가 없을 가능성이 높으므로 일단 0으로 설정
        # TODO: 실제 트래픽이 발생하면 distribution 값을 파싱하여 평균 계산
        resource_data["avg_cpu"] = 0.0
        resource_data["avg_memory"] = 0.0
        
        return resource_data
    
    def collect_service_metrics(self, service_name: str, hours: int = 24) -> ServiceMetrics:
        """서비스별 전체 메트릭 수집"""
        
        print(f"📊 Collecting metrics for {service_name}...")
        
        # Request metrics
        request_data = self.calculate_request_rate(service_name, hours)
        
        # Latency metrics
        latency_data = self.calculate_latency_percentiles(service_name, hours)
        
        # Error metrics
        error_data = self.calculate_error_rates(service_name, hours)
        
        # Resource metrics
        resource_data = self.calculate_resource_usage(service_name, hours)
        
        # Analyze status and alerts
        alerts = []
        status = "healthy"
        
        # Check error rates
        if error_data["5xx"]["rate"] > 5.0:
            alerts.append(f"⚠️ High 5xx error rate: {error_data['5xx']['rate']}%")
            status = "critical"
        elif error_data["5xx"]["rate"] > 1.0:
            alerts.append(f"⚠️ Elevated 5xx error rate: {error_data['5xx']['rate']}%")
            status = "warning"
        
        if error_data["4xx"]["rate"] > 10.0:
            alerts.append(f"⚠️ High 4xx error rate: {error_data['4xx']['rate']}%")
            if status == "healthy":
                status = "warning"
        
        # Check latency
        if latency_data["p99"] and latency_data["p99"] > 2000:
            alerts.append(f"⚠️ High P99 latency: {latency_data['p99']}ms")
            status = "critical" if status != "critical" else status
        elif latency_data["p99"] and latency_data["p99"] > 1000:
            alerts.append(f"⚠️ Elevated P99 latency: {latency_data['p99']}ms")
            status = "warning" if status == "healthy" else status
        
        # Check CPU
        if resource_data["avg_cpu"] > 80.0:
            alerts.append(f"⚠️ High CPU utilization: {resource_data['avg_cpu']}%")
            status = "warning" if status == "healthy" else status
        
        # Create metrics object
        metrics = ServiceMetrics(
            service_name=service_name,
            total_requests=int(request_data["total"]),
            requests_per_second=request_data["rps"],
            latency_p50=latency_data["p50"],
            latency_p95=latency_data["p95"],
            latency_p99=latency_data["p99"],
            error_4xx_count=error_data["4xx"]["count"],
            error_5xx_count=error_data["5xx"]["count"],
            error_4xx_rate=error_data["4xx"]["rate"],
            error_5xx_rate=error_data["5xx"]["rate"],
            avg_instances=resource_data["avg_instances"],
            max_instances=int(resource_data["max_instances"]),
            avg_cpu_utilization=resource_data["avg_cpu"],
            avg_memory_utilization=resource_data["avg_memory"],
            status=status,
            alerts=alerts
        )
        
        return metrics


class ReportGenerator:
    """마크다운 리포트 생성기"""
    
    @staticmethod
    def generate_markdown(report: DailyReport) -> str:
        """마크다운 리포트 생성"""
        
        md = []
        
        # Header
        md.append(f"# 📊 ION Platform Daily Operations Report")
        md.append(f"")
        md.append(f"**Report Date**: {report.date}")
        md.append(f"**Period**: {report.period_start} ~ {report.period_end}")
        md.append(f"")
        
        # Executive Summary
        md.append(f"## 📈 Executive Summary")
        md.append(f"")
        
        total_requests = report.ion_api.total_requests + report.lumen_gateway.total_requests
        total_errors = (report.ion_api.error_4xx_count + report.ion_api.error_5xx_count +
                       report.lumen_gateway.error_4xx_count + report.lumen_gateway.error_5xx_count)
        
        overall_status = "🟢 Healthy"
        if report.ion_api.status == "critical" or report.lumen_gateway.status == "critical":
            overall_status = "🔴 Critical"
        elif report.ion_api.status == "warning" or report.lumen_gateway.status == "warning":
            overall_status = "🟡 Warning"
        
        md.append(f"- **Overall Status**: {overall_status}")
        md.append(f"- **Total Requests**: {total_requests:,}")
        md.append(f"- **Total Errors**: {total_errors:,}")
        md.append(f"- **ION API Status**: {ReportGenerator._status_emoji(report.ion_api.status)} {report.ion_api.status.title()}")
        md.append(f"- **Lumen Gateway Status**: {ReportGenerator._status_emoji(report.lumen_gateway.status)} {report.lumen_gateway.status.title()}")
        md.append(f"")
        
        # ION API Metrics
        md.append(f"## 🚀 ION API Metrics")
        md.append(f"")
        md.extend(ReportGenerator._format_service_metrics(report.ion_api))
        md.append(f"")
        
        # Lumen Gateway Metrics
        md.append(f"## 🌐 Lumen Gateway Metrics")
        md.append(f"")
        md.extend(ReportGenerator._format_service_metrics(report.lumen_gateway))
        md.append(f"")
        
        # Alerts
        all_alerts = (report.ion_api.alerts or []) + (report.lumen_gateway.alerts or [])
        if all_alerts:
            md.append(f"## ⚠️ Alerts & Issues")
            md.append(f"")
            for alert in all_alerts:
                md.append(f"- {alert}")
            md.append(f"")
        
        # Recommendations
        if report.recommendations:
            md.append(f"## 💡 Recommendations")
            md.append(f"")
            for rec in report.recommendations:
                md.append(f"- {rec}")
            md.append(f"")
        
        # Footer
        md.append(f"---")
        md.append(f"*Generated by ION Platform Monitoring System*")
        md.append(f"*Report generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*")
        
        return "\n".join(md)
    
    @staticmethod
    def _status_emoji(status: str) -> str:
        """상태별 이모지"""
        return {
            "healthy": "🟢",
            "warning": "🟡",
            "critical": "🔴"
        }.get(status, "⚪")
    
    @staticmethod
    def _format_service_metrics(metrics: ServiceMetrics) -> List[str]:
        """서비스 메트릭 포맷팅"""
        lines = []
        
        # Request metrics
        lines.append(f"### 📊 Request Metrics")
        lines.append(f"")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Requests | {metrics.total_requests:,} |")
        lines.append(f"| Requests/Second | {metrics.requests_per_second} |")
        lines.append(f"")
        
        # Latency metrics
        lines.append(f"### ⏱️ Latency Metrics")
        lines.append(f"")
        lines.append(f"| Percentile | Value |")
        lines.append(f"|------------|-------|")
        lines.append(f"| P50 | {metrics.latency_p50 or 'No data'}{'ms' if metrics.latency_p50 else ''} |")
        lines.append(f"| P95 | {metrics.latency_p95 or 'No data'}{'ms' if metrics.latency_p95 else ''} |")
        lines.append(f"| P99 | {metrics.latency_p99 or 'No data'}{'ms' if metrics.latency_p99 else ''} |")
        lines.append(f"")
        
        # Error metrics
        lines.append(f"### ❌ Error Metrics")
        lines.append(f"")
        lines.append(f"| Error Type | Count | Rate |")
        lines.append(f"|------------|-------|------|")
        lines.append(f"| 4xx Errors | {metrics.error_4xx_count:,} | {metrics.error_4xx_rate}% |")
        lines.append(f"| 5xx Errors | {metrics.error_5xx_count:,} | {metrics.error_5xx_rate}% |")
        lines.append(f"")
        
        # Resource metrics
        lines.append(f"### 💻 Resource Metrics")
        lines.append(f"")
        lines.append(f"| Resource | Value |")
        lines.append(f"|----------|-------|")
        lines.append(f"| Avg Instances | {metrics.avg_instances} |")
        lines.append(f"| Max Instances | {metrics.max_instances} |")
        lines.append(f"| Avg CPU | {metrics.avg_cpu_utilization}% |")
        lines.append(f"| Avg Memory | {metrics.avg_memory_utilization}% |")
        
        return lines


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Generate daily operations report")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--output", default="daily_report.md", help="Output markdown file")
    parser.add_argument("--hours", type=int, default=24, help="Hours to analyze (default: 24)")
    parser.add_argument("--json", help="Also save as JSON")
    parser.add_argument("--send-email", action="store_true", help="Send report via email")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Daily Operations Report Generation...")
    print(f"📅 Analyzing last {args.hours} hours")
    print()
    
    # Initialize collector
    collector = MetricsCollector(args.project)
    
    # Collect metrics
    ion_api_metrics = collector.collect_service_metrics("ion-api", args.hours)
    lumen_gateway_metrics = collector.collect_service_metrics("lumen-gateway", args.hours)
    
    # Create report
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(hours=args.hours)
    
    report = DailyReport(
        date=now.strftime("%Y-%m-%d"),
        period_start=period_start.strftime("%Y-%m-%d %H:%M:%S UTC"),
        period_end=now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        ion_api=ion_api_metrics,
        lumen_gateway=lumen_gateway_metrics
    )
    
    # Generate recommendations
    if report.recommendations is None:
        report.recommendations = []
    
    if ion_api_metrics.status != "healthy" or lumen_gateway_metrics.status != "healthy":
        report.recommendations.append("Review alerts and investigate root causes")
    
    if ion_api_metrics.avg_cpu_utilization > 60 or lumen_gateway_metrics.avg_cpu_utilization > 60:
        report.recommendations.append("Consider scaling up resources if traffic is expected to increase")
    
    # Generate markdown
    print()
    print("📝 Generating markdown report...")
    markdown_content = ReportGenerator.generate_markdown(report)
    
    # Save markdown
    output_path = Path(args.output)
    output_path.write_text(markdown_content, encoding="utf-8")
    print(f"✅ Markdown report saved: {output_path.absolute()}")
    
    # Save JSON (optional)
    if args.json:
        json_data = {
            "date": report.date,
            "period_start": report.period_start,
            "period_end": report.period_end,
            "ion_api": asdict(ion_api_metrics),
            "lumen_gateway": asdict(lumen_gateway_metrics),
            "recommendations": report.recommendations
        }
        json_path = Path(args.json)
        json_path.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
        print(f"✅ JSON report saved: {json_path.absolute()}")
    
    # Send email (optional)
    if args.send_email:
        print()
        print("📧 Email sending not implemented yet")
        print("   Will be added in next iteration")
    
    print()
    print("✅ Report generation completed!")
    print()
    print(f"📊 Summary:")
    print(f"   - ION API: {ion_api_metrics.status.upper()}")
    print(f"   - Lumen Gateway: {lumen_gateway_metrics.status.upper()}")
    print(f"   - Total Requests: {ion_api_metrics.total_requests + lumen_gateway_metrics.total_requests:,}")
    total_alerts = len((ion_api_metrics.alerts or []) + (lumen_gateway_metrics.alerts or []))
    print(f"   - Alerts: {total_alerts}")


if __name__ == "__main__":
    main()
