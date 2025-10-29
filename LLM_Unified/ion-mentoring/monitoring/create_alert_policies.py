#!/usr/bin/env python3
"""
Alert Policies 자동 생성 스크립트

Task 1.2: Alert Policies 설정
- Critical Alerts (5xx errors, high latency, instance count)
- Warning Alerts (4xx errors, CPU/Memory usage)

Usage:
    python create_alert_policies.py --project naeda-genesis
    python create_alert_policies.py --project naeda-genesis --create-only
    python create_alert_policies.py --project naeda-genesis --list-only
    python create_alert_policies.py --project naeda-genesis --delete-all
"""

import argparse
import json
import subprocess
import sys
from typing import List, Dict, Any, Optional


class AlertPolicyManager:
    """GCP Alert Policy 관리 클래스"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.notification_channel_id: Optional[str] = None
        
    def get_or_create_notification_channel(self, email: str = "devops@ion-mentoring.com") -> str:
        """알림 채널 생성 또는 기존 채널 ID 가져오기"""
        print(f"📧 Notification Channel 확인 중... (email: {email})")
        
        # 기존 채널 검색
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "channels", "list",
                f"--project={self.project_id}",
                "--filter=type=email",
                "--format=json"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            channels = json.loads(result.stdout)
            
            for channel in channels:
                if channel.get("labels", {}).get("email_address") == email:
                    channel_id = channel["name"]
                    print(f"✅ 기존 Email Channel 발견: {channel_id}")
                    return channel_id
                    
        except subprocess.CalledProcessError as e:
            print(f"⚠️ 채널 검색 실패: {e.stderr}")
            
        # 새 채널 생성
        print(f"📧 새 Email Channel 생성 중: {email}")
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "channels", "create",
                f"--project={self.project_id}",
                "--display-name=ION Team Email",
                "--type=email",
                f"--channel-labels=email_address={email}",
                "--format=json"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            channel = json.loads(result.stdout)
            channel_id = channel["name"]
            print(f"✅ Email Channel 생성 완료: {channel_id}")
            return channel_id
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 채널 생성 실패: {e.stderr}")
            raise
    
    def list_alert_policies(self) -> List[Dict[str, Any]]:
        """현재 Alert Policies 목록 조회"""
        print(f"📋 Alert Policies 조회 중...")
        
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "policies", "list",
                f"--project={self.project_id}",
                "--format=json"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            policies = json.loads(result.stdout)
            
            print(f"✅ 총 {len(policies)}개 Alert Policies 발견")
            for policy in policies:
                print(f"   - {policy.get('displayName', 'Unknown')}")
                
            return policies
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Policies 조회 실패: {e.stderr}")
            return []
    
    def delete_all_ion_policies(self):
        """ION 관련 Alert Policies 모두 삭제"""
        print(f"🗑️ ION 관련 Alert Policies 삭제 중...")
        
        policies = self.list_alert_policies()
        ion_policies = [p for p in policies if "ION" in p.get("displayName", "")]
        
        if not ion_policies:
            print("✅ 삭제할 ION Alert Policy 없음")
            return
        
        for policy in ion_policies:
            policy_name = policy["name"]
            display_name = policy.get("displayName", "Unknown")
            
            try:
                cmd = [
                    "gcloud", "alpha", "monitoring", "policies", "delete",
                    policy_name,
                    f"--project={self.project_id}",
                    "--quiet"
                ]
                subprocess.run(cmd, check=True)
                print(f"   ✅ 삭제: {display_name}")
                
            except subprocess.CalledProcessError as e:
                print(f"   ❌ 삭제 실패: {display_name}")
    
    def create_critical_5xx_error_alert(self, service_name: str = "ion-api"):
        """Critical: 5xx Error Rate > 5% (5분 지속)"""
        print(f"\n🚨 Critical Alert 생성: {service_name} 5xx Error Rate > 5%")
        
        display_name = f"ION Critical - {service_name} 5xx Error > 5%"
        
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "policies", "create",
                f"--project={self.project_id}",
                f"--notification-channels={self.notification_channel_id}",
                f"--display-name={display_name}",
                "--condition-display-name=5xx Error Rate > 5%",
                "--condition-threshold-value=0.05",
                "--condition-threshold-duration=300s",
                "--condition-threshold-filter=" + 
                f'resource.type="cloud_run_revision" AND '
                f'resource.labels.service_name="{service_name}" AND '
                f'metric.type="run.googleapis.com/request_count" AND '
                f'metric.labels.response_code_class="5xx"',
                "--combiner=OR",
                "--format=json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            policy = json.loads(result.stdout)
            print(f"   ✅ 생성 완료: {policy['name']}")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 생성 실패: {e.stderr}")
    
    def create_critical_latency_alert(self, service_name: str = "ion-api"):
        """Critical: P99 Latency > 2000ms (5분 지속)"""
        print(f"\n🚨 Critical Alert 생성: {service_name} P99 Latency > 2000ms")
        
        display_name = f"ION Critical - {service_name} P99 Latency > 2s"
        
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "policies", "create",
                f"--project={self.project_id}",
                f"--notification-channels={self.notification_channel_id}",
                f"--display-name={display_name}",
                "--condition-display-name=P99 Latency > 2000ms",
                "--condition-threshold-value=2000",
                "--condition-threshold-duration=300s",
                "--condition-threshold-filter=" + 
                f'resource.type="cloud_run_revision" AND '
                f'resource.labels.service_name="{service_name}" AND '
                f'metric.type="run.googleapis.com/request_latencies"',
                "--condition-threshold-aggregations=alignment_period=60s,"
                "per_series_aligner=ALIGN_DELTA,"
                "cross_series_reducer=REDUCE_PERCENTILE_99",
                "--combiner=OR",
                "--format=json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            policy = json.loads(result.stdout)
            print(f"   ✅ 생성 완료: {policy['name']}")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 생성 실패: {e.stderr}")
    
    def create_critical_instance_count_alert(self, service_name: str = "ion-api"):
        """Critical: Container Instance Count = 0 (즉시)"""
        print(f"\n🚨 Critical Alert 생성: {service_name} Instance Count = 0")
        
        display_name = f"ION Critical - {service_name} No Instances"
        
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "policies", "create",
                f"--project={self.project_id}",
                f"--notification-channels={self.notification_channel_id}",
                f"--display-name={display_name}",
                "--condition-display-name=No Running Instances",
                "--condition-threshold-value=1",
                "--condition-threshold-duration=60s",
                "--condition-threshold-filter=" + 
                f'resource.type="cloud_run_revision" AND '
                f'resource.labels.service_name="{service_name}" AND '
                f'metric.type="run.googleapis.com/container/instance_count"',
                "--condition-threshold-comparison=COMPARISON_LT",
                "--combiner=OR",
                "--format=json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            policy = json.loads(result.stdout)
            print(f"   ✅ 생성 완료: {policy['name']}")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 생성 실패: {e.stderr}")
    
    def create_warning_4xx_error_alert(self, service_name: str = "ion-api"):
        """Warning: 4xx Error Rate > 10% (10분 지속)"""
        print(f"\n⚠️ Warning Alert 생성: {service_name} 4xx Error Rate > 10%")
        
        display_name = f"ION Warning - {service_name} 4xx Error > 10%"
        
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "policies", "create",
                f"--project={self.project_id}",
                f"--notification-channels={self.notification_channel_id}",
                f"--display-name={display_name}",
                "--condition-display-name=4xx Error Rate > 10%",
                "--condition-threshold-value=0.10",
                "--condition-threshold-duration=600s",
                "--condition-threshold-filter=" + 
                f'resource.type="cloud_run_revision" AND '
                f'resource.labels.service_name="{service_name}" AND '
                f'metric.type="run.googleapis.com/request_count" AND '
                f'metric.labels.response_code_class="4xx"',
                "--combiner=OR",
                "--format=json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            policy = json.loads(result.stdout)
            print(f"   ✅ 생성 완료: {policy['name']}")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 생성 실패: {e.stderr}")
    
    def create_warning_p95_latency_alert(self, service_name: str = "ion-api"):
        """Warning: P95 Latency > 1500ms (10분 지속)"""
        print(f"\n⚠️ Warning Alert 생성: {service_name} P95 Latency > 1500ms")
        
        display_name = f"ION Warning - {service_name} P95 Latency > 1.5s"
        
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "policies", "create",
                f"--project={self.project_id}",
                f"--notification-channels={self.notification_channel_id}",
                f"--display-name={display_name}",
                "--condition-display-name=P95 Latency > 1500ms",
                "--condition-threshold-value=1500",
                "--condition-threshold-duration=600s",
                "--condition-threshold-filter=" + 
                f'resource.type="cloud_run_revision" AND '
                f'resource.labels.service_name="{service_name}" AND '
                f'metric.type="run.googleapis.com/request_latencies"',
                "--condition-threshold-aggregations=alignment_period=60s,"
                "per_series_aligner=ALIGN_DELTA,"
                "cross_series_reducer=REDUCE_PERCENTILE_95",
                "--combiner=OR",
                "--format=json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            policy = json.loads(result.stdout)
            print(f"   ✅ 생성 완료: {policy['name']}")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 생성 실패: {e.stderr}")
    
    def create_warning_cpu_alert(self, service_name: str = "ion-api"):
        """Warning: CPU Utilization > 80% (15분 지속)"""
        print(f"\n⚠️ Warning Alert 생성: {service_name} CPU > 80%")
        
        display_name = f"ION Warning - {service_name} CPU > 80%"
        
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "policies", "create",
                f"--project={self.project_id}",
                f"--notification-channels={self.notification_channel_id}",
                f"--display-name={display_name}",
                "--condition-display-name=CPU Utilization > 80%",
                "--condition-threshold-value=0.80",
                "--condition-threshold-duration=900s",
                "--condition-threshold-filter=" + 
                f'resource.type="cloud_run_revision" AND '
                f'resource.labels.service_name="{service_name}" AND '
                f'metric.type="run.googleapis.com/container/cpu/utilizations"',
                "--combiner=OR",
                "--format=json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            policy = json.loads(result.stdout)
            print(f"   ✅ 생성 완료: {policy['name']}")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 생성 실패: {e.stderr}")
    
    def create_warning_memory_alert(self, service_name: str = "ion-api"):
        """Warning: Memory Utilization > 85% (15분 지속)"""
        print(f"\n⚠️ Warning Alert 생성: {service_name} Memory > 85%")
        
        display_name = f"ION Warning - {service_name} Memory > 85%"
        
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "policies", "create",
                f"--project={self.project_id}",
                f"--notification-channels={self.notification_channel_id}",
                f"--display-name={display_name}",
                "--condition-display-name=Memory Utilization > 85%",
                "--condition-threshold-value=0.85",
                "--condition-threshold-duration=900s",
                "--condition-threshold-filter=" + 
                f'resource.type="cloud_run_revision" AND '
                f'resource.labels.service_name="{service_name}" AND '
                f'metric.type="run.googleapis.com/container/memory/utilizations"',
                "--combiner=OR",
                "--format=json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            policy = json.loads(result.stdout)
            print(f"   ✅ 생성 완료: {policy['name']}")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ 생성 실패: {e.stderr}")
    
    def create_all_alerts(self, services: Optional[List[str]] = None):
        """모든 Alert Policies 생성"""
        if services is None:
            services = ["ion-api", "lumen-gateway"]
        
        print(f"\n{'='*60}")
        print(f"🚀 Alert Policies 생성 시작")
        print(f"{'='*60}")
        print(f"📦 Project: {self.project_id}")
        print(f"📦 Services: {', '.join(services)}")
        print(f"📧 Notification Channel: {self.notification_channel_id}")
        
        for service in services:
            print(f"\n{'─'*60}")
            print(f"📦 Service: {service}")
            print(f"{'─'*60}")
            
            # Critical Alerts
            self.create_critical_5xx_error_alert(service)
            self.create_critical_latency_alert(service)
            self.create_critical_instance_count_alert(service)
            
            # Warning Alerts
            self.create_warning_4xx_error_alert(service)
            self.create_warning_p95_latency_alert(service)
            self.create_warning_cpu_alert(service)
            self.create_warning_memory_alert(service)
        
        print(f"\n{'='*60}")
        print(f"✅ Alert Policies 생성 완료")
        print(f"{'='*60}")
        
        # 최종 확인
        self.list_alert_policies()


def main():
    parser = argparse.ArgumentParser(
        description="GCP Alert Policies 자동 생성 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 모든 Alert Policies 생성
  python create_alert_policies.py --project naeda-genesis
  
  # ION API만 생성
  python create_alert_policies.py --project naeda-genesis --services ion-api
  
  # 현재 Policies 조회만
  python create_alert_policies.py --project naeda-genesis --list-only
  
  # 모든 ION Policies 삭제
  python create_alert_policies.py --project naeda-genesis --delete-all
        """
    )
    
    parser.add_argument(
        "--project",
        required=True,
        help="GCP Project ID (e.g., naeda-genesis)"
    )
    
    parser.add_argument(
        "--services",
        nargs="+",
        default=["ion-api", "lumen-gateway"],
        help="Cloud Run 서비스 이름 (기본: ion-api, lumen-gateway)"
    )
    
    parser.add_argument(
        "--email",
        default="devops@ion-mentoring.com",
        help="알림 수신 이메일 (기본: devops@ion-mentoring.com)"
    )
    
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="현재 Alert Policies만 조회"
    )
    
    parser.add_argument(
        "--delete-all",
        action="store_true",
        help="모든 ION Alert Policies 삭제"
    )
    
    parser.add_argument(
        "--create-only",
        action="store_true",
        help="Notification Channel 생성 없이 Alert만 생성 (Channel ID 미리 설정 필요)"
    )
    
    args = parser.parse_args()
    
    # Manager 초기화
    manager = AlertPolicyManager(args.project)
    
    # List-only 모드
    if args.list_only:
        manager.list_alert_policies()
        return
    
    # Delete-all 모드
    if args.delete_all:
        manager.delete_all_ion_policies()
        return
    
    # Notification Channel 생성/조회
    if not args.create_only:
        manager.notification_channel_id = manager.get_or_create_notification_channel(args.email)
    else:
        # 기존 채널 찾기
        try:
            cmd = [
                "gcloud", "alpha", "monitoring", "channels", "list",
                f"--project={args.project}",
                "--filter=type=email",
                "--format=value(name)",
                "--limit=1"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            manager.notification_channel_id = result.stdout.strip()
            
            if not manager.notification_channel_id:
                print("❌ Notification Channel이 없습니다. --create-only 없이 실행하세요.")
                sys.exit(1)
                
            print(f"✅ 기존 Channel 사용: {manager.notification_channel_id}")
            
        except subprocess.CalledProcessError:
            print("❌ Notification Channel 조회 실패")
            sys.exit(1)
    
    # Alert Policies 생성
    manager.create_all_alerts(args.services)
    
    print("\n✅ 작업 완료!")
    print(f"\n📊 확인:")
    print(f"   https://console.cloud.google.com/monitoring/alerting/policies?project={args.project}")


if __name__ == "__main__":
    main()
