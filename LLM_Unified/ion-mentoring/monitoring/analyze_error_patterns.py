#!/usr/bin/env python3
"""
Error Pattern Analysis for Cloud Run Logs

Analyzes BigQuery logs to identify:
1. Top error patterns (by frequency)
2. Error trends over time
3. Affected endpoints
4. Error type distribution
5. Anomalies and spikes

Usage:
    python analyze_error_patterns.py --project naeda-genesis
    python analyze_error_patterns.py --project naeda-genesis --hours 168  # Last week
    python analyze_error_patterns.py --project naeda-genesis --output errors.md --json errors.json
"""

import argparse
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
from google.cloud import bigquery
from google.api_core import exceptions


@dataclass
class ErrorPattern:
    """Represents a recurring error pattern"""
    error_type: str
    message: str
    severity: str
    count: int
    first_seen: str
    last_seen: str
    affected_service: str
    affected_paths: List[str]
    sample_trace_id: Optional[str] = None


@dataclass
class ErrorAnalysisReport:
    """Complete error analysis report"""
    analysis_period: str
    period_start: str
    period_end: str
    total_errors: int
    error_rate: float  # Errors per hour
    unique_patterns: int
    top_patterns: List[ErrorPattern]
    service_breakdown: Dict[str, int]
    severity_breakdown: Dict[str, int]
    hourly_distribution: Dict[str, int]
    anomalies: List[str]
    recommendations: List[str]


class ErrorAnalyzer:
    """Analyzes error patterns from BigQuery logs"""
    
    def __init__(self, project_id: str, dataset_id: str = "cloud_run_logs"):
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
        
    def get_table_names(self) -> List[str]:
        """Get all log table names"""
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        try:
            tables = list(self.client.list_tables(dataset_ref))
            return [f"`{self.project_id}.{self.dataset_id}.{table.table_id}`" 
                    for table in tables]
        except exceptions.NotFound:
            return []
    
    def analyze_error_patterns(self, hours: int = 24) -> ErrorAnalysisReport:
        """
        Analyze error patterns from logs.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            ErrorAnalysisReport with complete analysis
        """
        print(f"🔍 Analyzing error patterns (last {hours} hours)...")
        
        # Get table names
        tables = self.get_table_names()
        if not tables:
            print("⚠️  No log tables found. Logs may not have accumulated yet.")
            return self._empty_report(hours)
        
        print(f"📊 Found {len(tables)} log tables")
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Query 1: Top error patterns
        patterns = self._query_error_patterns(tables, start_time, end_time)
        
        # Query 2: Service breakdown
        service_breakdown = self._query_service_breakdown(tables, start_time, end_time)
        
        # Query 3: Severity breakdown
        severity_breakdown = self._query_severity_breakdown(tables, start_time, end_time)
        
        # Query 4: Hourly distribution
        hourly_dist = self._query_hourly_distribution(tables, start_time, end_time)
        
        # Calculate metrics
        total_errors = sum(service_breakdown.values())
        error_rate = total_errors / hours if hours > 0 else 0
        
        # Detect anomalies
        anomalies = self._detect_anomalies(hourly_dist, error_rate)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(patterns, total_errors)
        
        return ErrorAnalysisReport(
            analysis_period=f"{hours} hours",
            period_start=start_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            period_end=end_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            total_errors=total_errors,
            error_rate=round(error_rate, 2),
            unique_patterns=len(patterns),
            top_patterns=patterns[:20],  # Top 20 patterns
            service_breakdown=service_breakdown,
            severity_breakdown=severity_breakdown,
            hourly_distribution=hourly_dist,
            anomalies=anomalies,
            recommendations=recommendations
        )
    
    def _query_error_patterns(
        self, 
        tables: List[str], 
        start_time: datetime, 
        end_time: datetime
    ) -> List[ErrorPattern]:
        """Query and group error patterns"""
        
        # Union all tables
        table_union = " UNION ALL ".join([
            f"SELECT * FROM {table}" for table in tables
        ])
        
        query = f"""
        WITH all_logs AS (
            {table_union}
        )
        SELECT
            severity,
            COALESCE(
                jsonPayload.message,
                textPayload,
                'Unknown error'
            ) as error_message,
            COALESCE(jsonPayload.path, httpRequest.requestUrl, 'Unknown') as path,
            resource.labels.service_name as service,
            COUNT(*) as count,
            MIN(timestamp) as first_seen,
            MAX(timestamp) as last_seen,
            ANY_VALUE(trace) as sample_trace
        FROM all_logs
        WHERE timestamp >= TIMESTAMP('{start_time.isoformat()}')
          AND timestamp < TIMESTAMP('{end_time.isoformat()}')
          AND severity >= 'ERROR'
        GROUP BY severity, error_message, path, service
        ORDER BY count DESC
        LIMIT 50
        """
        
        try:
            results = self.client.query(query).result()
            
            # Group by error message (combine similar paths)
            pattern_groups = defaultdict(lambda: {
                'count': 0,
                'paths': set(),
                'first_seen': None,
                'last_seen': None,
                'sample_trace': None,
                'severity': None,
                'service': None
            })
            
            for row in results:
                key = (row.error_message, row.service)
                group = pattern_groups[key]
                
                group['count'] += row['count']
                group['paths'].add(row.path)
                group['severity'] = row.severity
                group['service'] = row.service
                group['sample_trace'] = row.sample_trace
                
                if group['first_seen'] is None or row.first_seen < group['first_seen']:
                    group['first_seen'] = row.first_seen
                if group['last_seen'] is None or row.last_seen > group['last_seen']:
                    group['last_seen'] = row.last_seen
            
            # Convert to ErrorPattern objects
            patterns = []
            for (message, service), data in pattern_groups.items():
                patterns.append(ErrorPattern(
                    error_type=self._classify_error(message),
                    message=message[:200],  # Truncate long messages
                    severity=data['severity'],
                    count=data['count'],
                    first_seen=data['first_seen'].strftime("%Y-%m-%d %H:%M:%S UTC"),
                    last_seen=data['last_seen'].strftime("%Y-%m-%d %H:%M:%S UTC"),
                    affected_service=service,
                    affected_paths=list(data['paths'])[:10],  # Top 10 paths
                    sample_trace_id=data['sample_trace']
                ))
            
            # Sort by count
            patterns.sort(key=lambda p: p.count, reverse=True)
            return patterns
            
        except Exception as e:
            print(f"❌ Error querying patterns: {e}")
            return []
    
    def _query_service_breakdown(
        self, 
        tables: List[str], 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, int]:
        """Query error count by service"""
        
        table_union = " UNION ALL ".join([
            f"SELECT * FROM {table}" for table in tables
        ])
        
        query = f"""
        WITH all_logs AS (
            {table_union}
        )
        SELECT
            resource.labels.service_name as service,
            COUNT(*) as error_count
        FROM all_logs
        WHERE timestamp >= TIMESTAMP('{start_time.isoformat()}')
          AND timestamp < TIMESTAMP('{end_time.isoformat()}')
          AND severity >= 'ERROR'
        GROUP BY service
        ORDER BY error_count DESC
        """
        
        try:
            results = self.client.query(query).result()
            return {row.service: row.error_count for row in results}
        except Exception as e:
            print(f"❌ Error querying service breakdown: {e}")
            return {}
    
    def _query_severity_breakdown(
        self, 
        tables: List[str], 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, int]:
        """Query error count by severity"""
        
        table_union = " UNION ALL ".join([
            f"SELECT * FROM {table}" for table in tables
        ])
        
        query = f"""
        WITH all_logs AS (
            {table_union}
        )
        SELECT
            severity,
            COUNT(*) as count
        FROM all_logs
        WHERE timestamp >= TIMESTAMP('{start_time.isoformat()}')
          AND timestamp < TIMESTAMP('{end_time.isoformat()}')
          AND severity >= 'ERROR'
        GROUP BY severity
        ORDER BY count DESC
        """
        
        try:
            results = self.client.query(query).result()
            return {row.severity: row['count'] for row in results}
        except Exception as e:
            print(f"❌ Error querying severity breakdown: {e}")
            return {}
    
    def _query_hourly_distribution(
        self, 
        tables: List[str], 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, int]:
        """Query error count by hour"""
        
        table_union = " UNION ALL ".join([
            f"SELECT * FROM {table}" for table in tables
        ])
        
        query = f"""
        WITH all_logs AS (
            {table_union}
        )
        SELECT
            FORMAT_TIMESTAMP('%Y-%m-%d %H:00', timestamp) as hour,
            COUNT(*) as count
        FROM all_logs
        WHERE timestamp >= TIMESTAMP('{start_time.isoformat()}')
          AND timestamp < TIMESTAMP('{end_time.isoformat()}')
          AND severity >= 'ERROR'
        GROUP BY hour
        ORDER BY hour
        """
        
        try:
            results = self.client.query(query).result()
            return {row.hour: row['count'] for row in results}
        except Exception as e:
            print(f"❌ Error querying hourly distribution: {e}")
            return {}
    
    def _classify_error(self, message: str) -> str:
        """Classify error by message content"""
        message_lower = message.lower()
        
        if '404' in message or 'not found' in message_lower:
            return "404_NOT_FOUND"
        elif '503' in message or 'unavailable' in message_lower:
            return "503_SERVICE_UNAVAILABLE"
        elif '500' in message or 'internal server' in message_lower:
            return "500_INTERNAL_ERROR"
        elif '401' in message or 'unauthorized' in message_lower:
            return "401_UNAUTHORIZED"
        elif '403' in message or 'forbidden' in message_lower:
            return "403_FORBIDDEN"
        elif 'timeout' in message_lower:
            return "TIMEOUT"
        elif 'connection' in message_lower:
            return "CONNECTION_ERROR"
        else:
            return "OTHER"
    
    def _detect_anomalies(
        self, 
        hourly_dist: Dict[str, int], 
        baseline_rate: float
    ) -> List[str]:
        """Detect anomalous error spikes"""
        anomalies = []
        
        for hour, count in hourly_dist.items():
            # Spike detection: > 3x baseline rate
            if count > baseline_rate * 3:
                anomalies.append(
                    f"🚨 Spike detected at {hour}: {count} errors "
                    f"({count / baseline_rate:.1f}x baseline)"
                )
        
        return anomalies
    
    def _generate_recommendations(
        self, 
        patterns: List[ErrorPattern], 
        total_errors: int
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if not patterns:
            return ["✅ No errors detected in the analysis period"]
        
        # Top error pattern
        top_pattern = patterns[0]
        recommendations.append(
            f"🔥 **Priority**: Fix '{top_pattern.error_type}' "
            f"({top_pattern.count} occurrences, {top_pattern.count/total_errors*100:.1f}% of errors)"
        )
        
        # 404 errors
        not_found_errors = sum(p.count for p in patterns if '404' in p.error_type)
        if not_found_errors > total_errors * 0.5:
            recommendations.append(
                f"🔍 **High 404 Rate**: {not_found_errors} not found errors "
                f"({not_found_errors/total_errors*100:.1f}%) - review endpoint configurations"
            )
        
        # 503 errors (service unavailable)
        unavailable_errors = sum(p.count for p in patterns if '503' in p.error_type)
        if unavailable_errors > 10:
            recommendations.append(
                f"⚠️  **Service Availability**: {unavailable_errors} 503 errors - "
                f"check downstream service health"
            )
        
        # Frequent paths
        path_counts = defaultdict(int)
        for pattern in patterns:
            for path in pattern.affected_paths:
                path_counts[path] += pattern.count
        
        if path_counts:
            top_path = max(path_counts.items(), key=lambda x: x[1])
            recommendations.append(
                f"📍 **Hotspot**: '{top_path[0]}' has {top_path[1]} errors - "
                f"investigate this endpoint"
            )
        
        return recommendations
    
    def _empty_report(self, hours: int) -> ErrorAnalysisReport:
        """Return empty report when no data"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        return ErrorAnalysisReport(
            analysis_period=f"{hours} hours",
            period_start=start_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            period_end=end_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            total_errors=0,
            error_rate=0.0,
            unique_patterns=0,
            top_patterns=[],
            service_breakdown={},
            severity_breakdown={},
            hourly_distribution={},
            anomalies=[],
            recommendations=["⏳ No log data available yet. Wait 5-10 minutes for logs to accumulate."]
        )


class ReportFormatter:
    """Format error analysis reports"""
    
    @staticmethod
    def to_markdown(report: ErrorAnalysisReport) -> str:
        """Format report as Markdown"""
        lines = [
            "# 🔍 Error Pattern Analysis Report",
            "",
            f"**Analysis Period**: {report.analysis_period}",
            f"**Period**: {report.period_start} to {report.period_end}",
            f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "---",
            "",
            "## 📊 Summary",
            "",
            f"- **Total Errors**: {report.total_errors:,}",
            f"- **Error Rate**: {report.error_rate:.2f} errors/hour",
            f"- **Unique Patterns**: {report.unique_patterns}",
            "",
            "### Service Breakdown",
            ""
        ]
        
        if report.service_breakdown:
            lines.append("| Service | Error Count | Percentage |")
            lines.append("|---------|-------------|------------|")
            total = report.total_errors
            for service, count in sorted(report.service_breakdown.items(), 
                                         key=lambda x: x[1], reverse=True):
                pct = (count / total * 100) if total > 0 else 0
                lines.append(f"| {service} | {count:,} | {pct:.1f}% |")
        else:
            lines.append("*No errors found*")
        
        lines.extend([
            "",
            "### Severity Breakdown",
            ""
        ])
        
        if report.severity_breakdown:
            lines.append("| Severity | Count | Percentage |")
            lines.append("|----------|-------|------------|")
            total = report.total_errors
            for severity, count in sorted(report.severity_breakdown.items(), 
                                          key=lambda x: x[1], reverse=True):
                pct = (count / total * 100) if total > 0 else 0
                lines.append(f"| {severity} | {count:,} | {pct:.1f}% |")
        else:
            lines.append("*No errors found*")
        
        # Top error patterns
        lines.extend([
            "",
            "---",
            "",
            "## 🔥 Top Error Patterns",
            ""
        ])
        
        if report.top_patterns:
            for i, pattern in enumerate(report.top_patterns[:10], 1):
                lines.extend([
                    f"### {i}. {pattern.error_type} ({pattern.count:,} occurrences)",
                    "",
                    f"**Message**: {pattern.message}",
                    "",
                    f"- **Severity**: {pattern.severity}",
                    f"- **Service**: {pattern.affected_service}",
                    f"- **First Seen**: {pattern.first_seen}",
                    f"- **Last Seen**: {pattern.last_seen}",
                    "",
                    f"**Affected Paths** ({len(pattern.affected_paths)}):",
                    ""
                ])
                for path in pattern.affected_paths[:5]:
                    lines.append(f"- `{path}`")
                if len(pattern.affected_paths) > 5:
                    lines.append(f"- *... and {len(pattern.affected_paths) - 5} more*")
                
                if pattern.sample_trace_id:
                    lines.append(f"\n**Sample Trace**: `{pattern.sample_trace_id}`")
                
                lines.append("")
        else:
            lines.append("✅ No error patterns detected")
        
        # Hourly distribution
        if report.hourly_distribution:
            lines.extend([
                "",
                "---",
                "",
                "## 📈 Hourly Distribution",
                "",
                "| Hour | Error Count |",
                "|------|-------------|"
            ])
            for hour, count in sorted(report.hourly_distribution.items()):
                lines.append(f"| {hour} | {count:,} |")
        
        # Anomalies
        if report.anomalies:
            lines.extend([
                "",
                "---",
                "",
                "## 🚨 Anomalies Detected",
                ""
            ])
            for anomaly in report.anomalies:
                lines.append(f"- {anomaly}")
        
        # Recommendations
        lines.extend([
            "",
            "---",
            "",
            "## 💡 Recommendations",
            ""
        ])
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        
        lines.extend([
            "",
            "---",
            "",
            f"*Generated by ION Error Pattern Analyzer v1.0*"
        ])
        
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze error patterns from Cloud Run logs in BigQuery"
    )
    parser.add_argument(
        "--project",
        required=True,
        help="GCP project ID"
    )
    parser.add_argument(
        "--dataset",
        default="cloud_run_logs",
        help="BigQuery dataset name (default: cloud_run_logs)"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours to analyze (default: 24)"
    )
    parser.add_argument(
        "--output",
        default="error_analysis_report.md",
        help="Output markdown file (default: error_analysis_report.md)"
    )
    parser.add_argument(
        "--json",
        help="Optional JSON output file"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔍 ION Error Pattern Analysis")
    print("=" * 60)
    print(f"Project: {args.project}")
    print(f"Dataset: {args.dataset}")
    print(f"Analysis Period: Last {args.hours} hours")
    print()
    
    # Analyze
    analyzer = ErrorAnalyzer(args.project, args.dataset)
    report = analyzer.analyze_error_patterns(args.hours)
    
    # Generate markdown
    print(f"\n📝 Generating report...")
    markdown = ReportFormatter.to_markdown(report)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(markdown)
    print(f"✅ Markdown report saved: {args.output}")
    
    # Save JSON if requested
    if args.json:
        report_dict = asdict(report)
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON data saved: {args.json}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Analysis Summary:")
    print(f"   Total Errors: {report.total_errors:,}")
    print(f"   Error Rate: {report.error_rate:.2f}/hour")
    print(f"   Unique Patterns: {report.unique_patterns}")
    if report.anomalies:
        print(f"   Anomalies: {len(report.anomalies)}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
