"""
Slack Notifications Handler

Prometheus/Alertmanager 알림을 Slack으로 전달
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .slack_client import SlackClient

logger = logging.getLogger(__name__)


class NotificationHandler:
    """알림 핸들러"""
    
    def __init__(self, slack_client: SlackClient):
        """
        초기화
        
        Args:
            slack_client: SlackClient 인스턴스
        """
        self.client = slack_client
        
        # 채널 설정
        self.channel_critical = os.getenv("SLACK_CHANNEL_CRITICAL", "#ion-alerts-critical")
        self.channel_warning = os.getenv("SLACK_CHANNEL_WARNING", "#ion-alerts-warning")
        self.channel_info = os.getenv("SLACK_CHANNEL_INFO", "#ion-alerts-info")
        self.channel_deployments = os.getenv("SLACK_CHANNEL_DEPLOYMENTS", "#ion-deployments")
    
    def handle_alertmanager_webhook(self, payload: Dict[str, Any]) -> None:
        """
        Alertmanager 웹훅 처리
        
        Args:
            payload: Alertmanager 페이로드
        """
        alerts = payload.get("alerts", [])
        
        for alert in alerts:
            self.send_alert_notification(alert)
    
    def send_alert_notification(self, alert: Dict[str, Any]) -> None:
        """
        개별 알림 전송
        
        Args:
            alert: 알림 데이터
        """
        status = alert.get("status", "unknown")
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        
        alert_name = labels.get("alertname", "Unknown Alert")
        severity = labels.get("severity", "info").lower()
        instance = labels.get("instance", "unknown")
        
        summary = annotations.get("summary", "")
        description = annotations.get("description", "")
        
        # 채널 결정
        if severity == "critical":
            channel = self.channel_critical
        elif severity == "warning":
            channel = self.channel_warning
        else:
            channel = self.channel_info
        
        # 상태별 아이콘
        status_icon = "🔥" if status == "firing" else "✅"
        
        # 세부 정보
        details = {
            "Instance": instance,
            "Status": status.upper(),
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 추가 라벨
        for key, value in labels.items():
            if key not in ["alertname", "severity", "instance"]:
                details[key.capitalize()] = value
        
        # 액션 버튼
        actions = []
        
        # GCP 로그 링크
        if "gcp_project" in labels:
            project_id = labels["gcp_project"]
            actions.append({
                "text": "View Logs",
                "url": f"https://console.cloud.google.com/logs/query?project={project_id}"
            })
        
        # 알림 전송
        title = f"{status_icon} {alert_name}"
        message = f"*Summary:* {summary}\n\n{description}"
        
        self.client.send_alert(
            channel=channel,
            severity=severity,
            title=title,
            message=message,
            details=details,
            actions=actions if actions else None
        )
    
    def send_deployment_notification(
        self,
        stage: str,
        service: str,
        version: str,
        percentage: Optional[int] = None,
        status: str = "started",
        details: Optional[Dict[str, str]] = None
    ) -> None:
        """
        배포 알림 전송
        
        Args:
            stage: 배포 단계 (started, progress, completed, failed)
            service: 서비스 이름 (canary, main)
            version: 버전
            percentage: 트래픽 비율 (선택)
            status: 상태
            details: 추가 세부 정보
        """
        # 아이콘 결정
        icon_map = {
            "started": "🚀",
            "progress": "🔄",
            "completed": "✅",
            "failed": "❌",
            "rollback": "🔙"
        }
        icon = icon_map.get(stage, "📢")
        
        # 제목
        title = f"{icon} Deployment {stage.capitalize()}: ion-api-{service}"
        
        # 메시지
        message = f"*Version:* {version}\n"
        if percentage is not None:
            message += f"*Traffic:* {percentage}%\n"
        message += f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 세부 정보
        notification_details = details or {}
        notification_details["Service"] = f"ion-api-{service}"
        notification_details["Version"] = version
        if percentage is not None:
            notification_details["Traffic"] = f"{percentage}%"
        
        # 심각도 결정
        if stage == "failed":
            severity = "critical"
        elif stage in ["started", "progress"]:
            severity = "info"
        else:
            severity = "info"
        
        # 알림 전송
        self.client.send_alert(
            channel=self.channel_deployments,
            severity=severity,
            title=title,
            message=message,
            details=notification_details
        )
    
    def send_performance_alert(
        self,
        service: str,
        metric: str,
        current_value: float,
        threshold: float,
        severity: str = "warning"
    ) -> None:
        """
        성능 알림 전송
        
        Args:
            service: 서비스 이름
            metric: 메트릭 이름
            current_value: 현재 값
            threshold: 임계값
            severity: 심각도
        """
        channel = self.channel_critical if severity == "critical" else self.channel_warning
        
        title = f"⚠️ Performance Alert: {service}"
        message = f"*Metric:* {metric}\n*Current Value:* {current_value:.2f}\n*Threshold:* {threshold:.2f}"
        
        details = {
            "Service": service,
            "Metric": metric,
            "Current": f"{current_value:.2f}",
            "Threshold": f"{threshold:.2f}",
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.client.send_alert(
            channel=channel,
            severity=severity,
            title=title,
            message=message,
            details=details
        )
    
    def send_system_status(
        self,
        status: str,
        health_score: str,
        services: List[Dict[str, Any]],
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        시스템 상태 요약 전송
        
        Args:
            status: 전체 상태 (healthy, degraded, down)
            health_score: 건강도 (예: "5/5")
            services: 서비스 리스트
            metrics: 추가 메트릭
        """
        # 아이콘 결정
        icon_map = {
            "healthy": "✅",
            "degraded": "⚠️",
            "down": "❌"
        }
        icon = icon_map.get(status, "📊")
        
        # 채널 결정
        if status == "down":
            channel = self.channel_critical
        elif status == "degraded":
            channel = self.channel_warning
        else:
            channel = self.channel_info
        
        # 제목
        title = f"{icon} System Status: {status.upper()}"
        
        # 메시지
        message = f"*Health Score:* {health_score}\n*Services:* {len(services)}\n*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 세부 정보
        details = {}
        for service in services:
            service_name = service.get("name", "unknown")
            service_status = service.get("status", "unknown")
            service_icon = "✅" if service_status == "healthy" else "❌"
            details[service_name] = f"{service_icon} {service_status}"
        
        # 메트릭 추가
        if metrics:
            for key, value in metrics.items():
                details[key] = str(value)
        
        # 알림 전송
        severity = "critical" if status == "down" else "warning" if status == "degraded" else "info"
        
        self.client.send_alert(
            channel=channel,
            severity=severity,
            title=title,
            message=message,
            details=details
        )
    
    def send_custom_notification(
        self,
        channel: str,
        title: str,
        message: str,
        severity: str = "info",
        details: Optional[Dict[str, str]] = None
    ) -> None:
        """
        커스텀 알림 전송
        
        Args:
            channel: 채널 ID 또는 이름
            title: 제목
            message: 메시지
            severity: 심각도
            details: 세부 정보
        """
        self.client.send_alert(
            channel=channel,
            severity=severity,
            title=title,
            message=message,
            details=details
        )


def format_alertmanager_payload(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Alertmanager 페이로드 포맷
    
    Args:
        alerts: 알림 리스트
    
    Returns:
        포맷된 페이로드
    """
    return {
        "receiver": "slack",
        "status": "firing",
        "alerts": alerts,
        "groupLabels": {},
        "commonLabels": {},
        "commonAnnotations": {},
        "externalURL": "",
        "version": "4",
        "groupKey": ""
    }


def create_test_alert(
    alert_name: str = "TestAlert",
    severity: str = "warning",
    summary: str = "Test alert",
    description: str = "This is a test alert"
) -> Dict[str, Any]:
    """
    테스트 알림 생성
    
    Args:
        alert_name: 알림 이름
        severity: 심각도
        summary: 요약
        description: 설명
    
    Returns:
        알림 딕셔너리
    """
    return {
        "status": "firing",
        "labels": {
            "alertname": alert_name,
            "severity": severity,
            "instance": "test-instance"
        },
        "annotations": {
            "summary": summary,
            "description": description
        },
        "startsAt": datetime.now().isoformat(),
        "endsAt": "0001-01-01T00:00:00Z",
        "generatorURL": "http://localhost:9090/graph"
    }
