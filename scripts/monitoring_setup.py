#!/usr/bin/env python3
"""
Production Monitoring Setup Script
Week 15 Implementation

Sets up comprehensive production monitoring for ION Mentoring
Author: Claude AI Agent
Date: 2025-10-18
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, '/app/monitoring')

from monitoring_config import (
    MonitoringConfig,
    AlertSeverity,
    create_monitoring_config,
    create_alert_state_manager
)
from metrics_collector import ProductionMetricsCollector
from dashboard_renderer import DashboardRenderer, DashboardBuilder
from alert_tuning import (
    BaselineAnalyzer,
    AlertTuningReport,
    create_tuning_report_from_baseline_data
)


class MonitoringSetup:
    """Setup and configure production monitoring"""

    def __init__(self):
        self.config = create_monitoring_config()
        self.metrics = ProductionMetricsCollector()
        self.alert_manager = create_alert_state_manager()
        self.setup_time = datetime.now()

    def verify_configuration(self) -> Dict[str, bool]:
        """Verify monitoring configuration"""
        results = {}

        # Check alert rules
        alert_rules = self.config.list_alert_rules(enabled_only=True)
        results["alert_rules_configured"] = len(alert_rules) > 0
        results["alert_rules_count"] = len(alert_rules)

        # Check dashboards
        dashboards = self.config.list_dashboards(enabled_only=True)
        results["dashboards_configured"] = len(dashboards) > 0
        results["dashboards_count"] = len(dashboards)

        # Check metric thresholds
        results["metric_thresholds_configured"] = len(self.config.metric_thresholds) > 0
        results["metric_types_count"] = len(self.config.metric_thresholds)

        # Check notification settings
        notification_enabled = sum(
            1 for ch, settings in self.config.notification_settings.items()
            if settings.get("enabled", False)
        )
        results["notification_channels_enabled"] = notification_enabled
        results["notification_channels_total"] = len(self.config.notification_settings)

        # Check metric collections
        results["metric_collections_created"] = len(self.metrics.collections)

        return results

    def generate_monitoring_summary(self) -> str:
        """Generate monitoring setup summary"""
        lines = []
        lines.append("=" * 80)
        lines.append("PRODUCTION MONITORING SETUP COMPLETE")
        lines.append("=" * 80)
        lines.append(f"Setup Time: {self.setup_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")

        # Configuration status
        verification = self.verify_configuration()
        lines.append("CONFIGURATION STATUS")
        lines.append("-" * 80)
        lines.append(f"Alert Rules Configured: {verification['alert_rules_count']}")
        lines.append(f"Dashboards Configured: {verification['dashboards_count']}")
        lines.append(f"Metric Types Tracked: {verification['metric_types_count']}")
        lines.append(f"Notification Channels: {verification['notification_channels_enabled']}/{verification['notification_channels_total']}")
        lines.append(f"Metric Collections: {verification['metric_collections_created']}")
        lines.append("")

        # Alert rules list
        lines.append("ENABLED ALERT RULES")
        lines.append("-" * 80)
        for rule in self.config.list_alert_rules(enabled_only=True):
            lines.append(f"✓ {rule.name}")
            lines.append(f"  Description: {rule.description}")
            lines.append(f"  Channels: {', '.join(rule.notification_channels)}")
        lines.append("")

        # Dashboards list
        lines.append("AVAILABLE DASHBOARDS")
        lines.append("-" * 80)
        for dashboard in self.config.list_dashboards(enabled_only=True):
            widget_count = len(dashboard.widgets)
            lines.append(f"✓ {dashboard.name} ({widget_count} widgets)")
            lines.append(f"  {dashboard.description}")
        lines.append("")

        # Notification channels
        lines.append("NOTIFICATION CHANNELS")
        lines.append("-" * 80)
        for channel, settings in self.config.notification_settings.items():
            status = "✓" if settings.get("enabled", False) else "✗"
            lines.append(f"{status} {channel.upper()}")
            if settings.get("webhook_url"):
                lines.append(f"  Webhook: {settings.get('webhook_url')[:40]}...")
            if settings.get("recipients"):
                lines.append(f"  Recipients: {len(settings.get('recipients', []))} configured")
        lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def export_configuration_json(self) -> str:
        """Export configuration as JSON"""
        config_data = {
            "setup_time": self.setup_time.isoformat(),
            "alert_rules": [
                {
                    "name": rule.name,
                    "description": rule.description,
                    "metric_type": rule.metric_type.value,
                    "enabled": rule.enabled,
                    "notification_channels": rule.notification_channels,
                }
                for rule in self.config.alert_rules
            ],
            "dashboards": [
                {
                    "name": dashboard.name,
                    "description": dashboard.description,
                    "widget_count": len(dashboard.widgets),
                    "refresh_interval": dashboard.refresh_interval,
                }
                for dashboard in self.config.list_dashboards()
            ],
            "metric_types": [
                {
                    "type": threshold.metric_type.value,
                    "unit": threshold.unit,
                    "critical": threshold.critical_threshold,
                    "high": threshold.high_threshold,
                    "medium": threshold.medium_threshold,
                }
                for threshold in self.config.metric_thresholds.values()
            ],
        }
        return json.dumps(config_data, indent=2, default=str)

    def generate_dashboard_report(self) -> str:
        """Generate sample dashboard report"""
        # Create sample metrics data
        sample_metrics = {
            "availability": 99.95,
            "error_rate": 0.30,
            "response_time_avg": 28.7,
            "response_time_p95": 36.4,
            "cache_hit_rate": 82.3,
            "throughput": 9270,
        }

        # Build dashboard
        metrics = DashboardBuilder.build_overview_dashboard(sample_metrics)

        # Render as text
        renderer = DashboardRenderer()
        text_output = renderer.render_overview_text(metrics)

        return text_output

    def generate_alert_tuning_report(self) -> str:
        """Generate alert tuning report"""
        report = create_tuning_report_from_baseline_data()
        return report.generate_report()


def main():
    """Main setup function"""
    print("=" * 80)
    print("ION MENTORING PRODUCTION MONITORING SETUP")
    print("Week 15 Implementation")
    print("=" * 80)
    print()

    # Initialize setup
    setup = MonitoringSetup()

    # Step 1: Verify configuration
    print("Step 1: Verifying Monitoring Configuration...")
    print("-" * 80)
    verification = setup.verify_configuration()
    for key, value in verification.items():
        status = "✓" if isinstance(value, bool) and value or isinstance(value, int) and value > 0 else "✗"
        print(f"{status} {key}: {value}")
    print()

    # Step 2: Generate setup summary
    print("Step 2: Monitoring Setup Summary")
    print("-" * 80)
    print(setup.generate_monitoring_summary())
    print()

    # Step 3: Generate sample dashboard
    print("Step 3: Sample Production Dashboard")
    print("-" * 80)
    print(setup.generate_dashboard_report())
    print()

    # Step 4: Generate alert tuning report
    print("Step 4: Alert Threshold Tuning Report")
    print("-" * 80)
    print(setup.generate_alert_tuning_report())
    print()

    # Step 5: Export configuration
    print("Step 5: Exporting Configuration Files")
    print("-" * 80)

    # Export monitoring config
    config_json = setup.export_configuration_json()
    config_file = "/tmp/monitoring_config.json"
    with open(config_file, "w") as f:
        f.write(config_json)
    print(f"✓ Configuration exported to: {config_file}")

    # Export alert tuning report
    tuning_report = create_tuning_report_from_baseline_data()
    tuning_json = tuning_report.export_recommendations_json()
    tuning_file = "/tmp/alert_tuning_recommendations.json"
    with open(tuning_file, "w") as f:
        f.write(tuning_json)
    print(f"✓ Alert tuning recommendations exported to: {tuning_file}")

    print()
    print("=" * 80)
    print("MONITORING SETUP COMPLETE ✓")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Review alert configurations in monitoring_config.json")
    print("2. Implement alert tuning recommendations from alert_tuning_recommendations.json")
    print("3. Test notification channels with sample alerts")
    print("4. Start production metrics collection")
    print("5. Monitor dashboards for first 24 hours")
    print()


if __name__ == "__main__":
    main()
