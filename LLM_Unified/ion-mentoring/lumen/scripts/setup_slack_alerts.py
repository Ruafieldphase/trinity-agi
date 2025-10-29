#!/usr/bin/env python3
"""
Slack 알림 채널 설정 스크립트

Phase 2: Slack Webhook 알림 채널 생성
- ROI Gate 알림
- SLO 위반 알림
- Maturity Score 저하 알림
"""

import sys
import os
import json
from pathlib import Path
from google.cloud import monitoring_v3
from google.protobuf import duration_pb2

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# GCP 설정
PROJECT_ID = os.getenv("GCP_PROJECT", "naeda-genesis")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# 알림 채널 이름 (중복 방지)
CHANNEL_DISPLAY_NAME = "Lumen System Alerts"

# Alert Policy 설정
ALERT_POLICIES = [
    {
        "display_name": "ROI Gate - Critical (< 300%)",
        "documentation": {
            "content": """
## ROI Gate Critical Alert

ROI가 300% 이하로 떨어졌습니다.

**조치사항:**
1. Redis 캐싱 성능 확인
2. 비용 대비 효과 분석
3. 캐시 설정 튜닝 고려

**확인 대시보드:**
https://console.cloud.google.com/monitoring/dashboards/
""",
            "mime_type": "text/markdown",
        },
        "conditions": [
            {
                "display_name": "ROI < 300%",
                "condition_threshold": {
                    "filter": 'metric.type="custom.googleapis.com/roi_percentage" resource.type="cloud_run_revision"',
                    "comparison": "COMPARISON_LT",
                    "threshold_value": 300,
                    "duration": {"seconds": 300},  # 5분 동안 지속
                    "aggregations": [
                        {
                            "alignment_period": {"seconds": 60},
                            "per_series_aligner": "ALIGN_MEAN",
                        }
                    ],
                },
            }
        ],
        "combiner": "AND",
        "enabled": True,
    },
    {
        "display_name": "SLO Compliance - Warning (< 98%)",
        "documentation": {
            "content": """
## SLO Compliance Warning

SLO 준수율이 98% 이하로 떨어졌습니다.

**조치사항:**
1. SLO Exporter 상세 리포트 확인
2. Availability / Latency / Error Rate 개별 확인
3. 최근 배포 이력 확인

**확인 명령:**
```
python lumen/scripts/test_slo_exporter.py
```
""",
            "mime_type": "text/markdown",
        },
        "conditions": [
            {
                "display_name": "SLO Compliance < 98%",
                "condition_threshold": {
                    "filter": 'metric.type="custom.googleapis.com/slo_compliance" resource.type="cloud_run_revision"',
                    "comparison": "COMPARISON_LT",
                    "threshold_value": 98,
                    "duration": {"seconds": 180},  # 3분 동안 지속
                    "aggregations": [
                        {
                            "alignment_period": {"seconds": 60},
                            "per_series_aligner": "ALIGN_MEAN",
                        }
                    ],
                },
            }
        ],
        "combiner": "AND",
        "enabled": True,
    },
    {
        "display_name": "Maturity Score - Poor (< 50)",
        "documentation": {
            "content": """
## System Maturity Score Poor

시스템 성숙도 점수가 50점 이하로 떨어졌습니다.

**조치사항:**
1. Maturity Exporter 상세 리포트 확인
2. 6가지 메트릭 개별 분석
3. 개선 우선순위 결정

**확인 명령:**
```
python lumen/scripts/test_maturity_exporter.py
```
""",
            "mime_type": "text/markdown",
        },
        "conditions": [
            {
                "display_name": "Maturity Score < 50",
                "condition_threshold": {
                    "filter": 'metric.type="custom.googleapis.com/maturity_score" resource.type="cloud_run_revision"',
                    "comparison": "COMPARISON_LT",
                    "threshold_value": 50,
                    "duration": {"seconds": 600},  # 10분 동안 지속
                    "aggregations": [
                        {
                            "alignment_period": {"seconds": 300},
                            "per_series_aligner": "ALIGN_MEAN",
                        }
                    ],
                },
            }
        ],
        "combiner": "AND",
        "enabled": True,
    },
    {
        "display_name": "Cache Hit Rate - Low (< 60%)",
        "documentation": {
            "content": """
## Cache Hit Rate Low

캐시 히트율이 60% 이하로 떨어졌습니다.

**조치사항:**
1. Redis 연결 상태 확인
2. 캐시 TTL 설정 검토
3. Cold Start 빈도 확인

**확인 명령:**
```
gcloud redis instances describe ion-redis --region=us-central1
```
""",
            "mime_type": "text/markdown",
        },
        "conditions": [
            {
                "display_name": "Cache Hit Rate < 60%",
                "condition_threshold": {
                    "filter": 'metric.type="custom.googleapis.com/cache_hit_rate" resource.type="cloud_run_revision"',
                    "comparison": "COMPARISON_LT",
                    "threshold_value": 60,
                    "duration": {"seconds": 300},  # 5분 동안 지속
                    "aggregations": [
                        {
                            "alignment_period": {"seconds": 60},
                            "per_series_aligner": "ALIGN_MEAN",
                        }
                    ],
                },
            }
        ],
        "combiner": "AND",
        "enabled": True,
    },
]


def create_slack_notification_channel(project_id: str, webhook_url: str) -> str:
    """
    Slack 알림 채널 생성 또는 기존 채널 반환
    
    Args:
        project_id: GCP 프로젝트 ID
        webhook_url: Slack Webhook URL
        
    Returns:
        알림 채널 이름 (projects/{project}/notificationChannels/{channel_id})
    """
    client = monitoring_v3.NotificationChannelServiceClient()
    project_name = f"projects/{project_id}"
    
    # 기존 채널 확인
    print(f"🔍 기존 Slack 채널 검색: {CHANNEL_DISPLAY_NAME}")
    for channel in client.list_notification_channels(name=project_name):
        if (
            channel.display_name == CHANNEL_DISPLAY_NAME
            and channel.type_ == "slack"
        ):
            print(f"✅ 기존 채널 발견: {channel.name}")
            return channel.name
    
    # 새 채널 생성
    print(f"🆕 새 Slack 채널 생성 중...")
    notification_channel = monitoring_v3.NotificationChannel(
        type_="slack",
        display_name=CHANNEL_DISPLAY_NAME,
        description="Lumen System automated alerts",
        labels={
            "url": webhook_url,
        },
        enabled=True,
    )
    
    created = client.create_notification_channel(
        name=project_name, notification_channel=notification_channel
    )
    print(f"✅ Slack 채널 생성 완료: {created.name}")
    return created.name


def create_alert_policy(
    project_id: str,
    policy_config: dict,
    notification_channel_name: str,
) -> str:
    """
    Alert Policy 생성 또는 업데이트
    
    Args:
        project_id: GCP 프로젝트 ID
        policy_config: Alert Policy 설정
        notification_channel_name: 알림 채널 이름
        
    Returns:
        Alert Policy 이름
    """
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"
    
    # 기존 Policy 확인
    display_name = policy_config["display_name"]
    print(f"🔍 기존 Alert Policy 검색: {display_name}")
    
    for policy in client.list_alert_policies(name=project_name):
        if policy.display_name == display_name:
            # 기존 정책 삭제 (업데이트가 복잡하므로)
            print(f"🗑️  기존 정책 삭제: {policy.name}")
            client.delete_alert_policy(name=policy.name)
            break
    
    # 새 Policy 생성
    print(f"🆕 새 Alert Policy 생성 중...")
    
    # Condition 생성
    conditions = []
    for cond_config in policy_config["conditions"]:
        condition = monitoring_v3.AlertPolicy.Condition(
            display_name=cond_config["display_name"],
            condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                filter=cond_config["condition_threshold"]["filter"],
                comparison=getattr(
                    monitoring_v3.ComparisonType,
                    cond_config["condition_threshold"]["comparison"],
                ),
                threshold_value=cond_config["condition_threshold"]["threshold_value"],
                duration=duration_pb2.Duration(
                    seconds=cond_config["condition_threshold"]["duration"]["seconds"]
                ),
                aggregations=[
                    monitoring_v3.Aggregation(
                        alignment_period=duration_pb2.Duration(
                            seconds=agg["alignment_period"]["seconds"]
                        ),
                        per_series_aligner=getattr(
                            monitoring_v3.Aggregation.Aligner,
                            agg["per_series_aligner"],
                        ),
                    )
                    for agg in cond_config["condition_threshold"]["aggregations"]
                ],
            ),
        )
        conditions.append(condition)
    
    # Documentation 생성
    documentation = monitoring_v3.AlertPolicy.Documentation(
        content=policy_config["documentation"]["content"],
        mime_type=policy_config["documentation"]["mime_type"],
    )
    
    # Alert Policy 생성
    alert_policy = monitoring_v3.AlertPolicy(
        display_name=display_name,
        conditions=conditions,
        combiner=getattr(
            monitoring_v3.AlertPolicy.ConditionCombinerType,
            policy_config["combiner"],
        ),
        documentation=documentation,
        notification_channels=[notification_channel_name],
        enabled=policy_config["enabled"],
    )
    
    created = client.create_alert_policy(name=project_name, alert_policy=alert_policy)
    print(f"✅ Alert Policy 생성 완료: {created.name}")
    return created.name


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("Slack 알림 채널 & Alert Policy 설정")
    print("=" * 70)
    print()
    
    # 1. Slack Webhook URL 확인
    if not SLACK_WEBHOOK_URL:
        print("❌ 오류: SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
        print()
        print("다음 명령으로 설정하세요:")
        print('  $env:SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"')
        print()
        sys.exit(1)
    
    print(f"✅ Slack Webhook URL 확인됨")
    print(f"📍 프로젝트: {PROJECT_ID}")
    print()
    
    # 2. Slack 채널 생성
    try:
        notification_channel_name = create_slack_notification_channel(
            PROJECT_ID, SLACK_WEBHOOK_URL
        )
        print()
    except Exception as e:
        print(f"❌ Slack 채널 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 3. Alert Policy 생성
    print("=" * 70)
    print("Alert Policy 생성 중...")
    print("=" * 70)
    print()
    
    created_policies = []
    for policy_config in ALERT_POLICIES:
        try:
            policy_name = create_alert_policy(
                PROJECT_ID, policy_config, notification_channel_name
            )
            created_policies.append(policy_name)
            print()
        except Exception as e:
            print(f"❌ Alert Policy 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            # 계속 진행 (일부 실패해도 나머지는 생성)
    
    # 4. 결과 요약
    print("=" * 70)
    print("✅ 설정 완료!")
    print("=" * 70)
    print(f"Notification Channel: {notification_channel_name}")
    print(f"Alert Policies: {len(created_policies)}개 생성됨")
    print()
    print("생성된 Alert Policies:")
    for i, policy_name in enumerate(created_policies, 1):
        print(f"  {i}. {policy_name}")
    print()
    print("📊 확인 URL:")
    print(f"  https://console.cloud.google.com/monitoring/alerting/policies?project={PROJECT_ID}")
    print()
    print("🧪 테스트 방법:")
    print("  1. python lumen/scripts/test_slo_exporter.py")
    print("  2. python lumen/scripts/test_roi_gate.py")
    print("  3. python lumen/scripts/test_maturity_exporter.py")
    print()


if __name__ == "__main__":
    main()
