#!/usr/bin/env python3
"""
Cloud Monitoring Dashboard 배포 스크립트

Phase 2: Cloud Monitoring 대시보드 자동 생성
"""

import sys
import os
import json
import yaml
from pathlib import Path
from google.cloud import monitoring_dashboard_v1
from google.protobuf import json_format

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# GCP 설정
PROJECT_ID = os.getenv("GCP_PROJECT", "naeda-genesis")
DASHBOARD_YAML = PROJECT_ROOT / "lumen/dashboards/cloud_monitoring_dashboard.yaml"


def yaml_to_dashboard_json(yaml_path: Path) -> dict:
    """
    YAML 대시보드 정의를 Cloud Monitoring JSON으로 변환
    
    Args:
        yaml_path: YAML 파일 경로
        
    Returns:
        Cloud Monitoring Dashboard JSON
    """
    with open(yaml_path, 'r', encoding='utf-8') as f:
        dashboard_yaml = yaml.safe_load(f)
    
    # Cloud Monitoring Dashboard 형식으로 변환
    dashboard_json = {
        "displayName": dashboard_yaml.get("displayName", "Lumen System Dashboard"),
        "mosaicLayout": dashboard_yaml.get("mosaicLayout", {}),
    }
    
    return dashboard_json


def create_or_update_dashboard(project_id: str, dashboard_json: dict) -> str:
    """
    Cloud Monitoring 대시보드 생성 또는 업데이트
    
    Args:
        project_id: GCP 프로젝트 ID
        dashboard_json: 대시보드 JSON 정의
        
    Returns:
        생성/업데이트된 대시보드 이름
    """
    client = monitoring_dashboard_v1.DashboardsServiceClient()
    project_name = f"projects/{project_id}"
    
    # 기존 대시보드 확인
    display_name = dashboard_json.get("displayName", "Lumen System Dashboard")
    existing_dashboard = None
    
    print(f"🔍 기존 대시보드 검색: {display_name}")
    for dashboard in client.list_dashboards(parent=project_name):
        if dashboard.display_name == display_name:
            existing_dashboard = dashboard
            print(f"✅ 기존 대시보드 발견: {dashboard.name}")
            break
    
    # Dashboard proto 생성
    dashboard = monitoring_dashboard_v1.Dashboard()
    json_format.ParseDict(dashboard_json, dashboard)
    
    if existing_dashboard:
        # 업데이트
        print(f"🔄 대시보드 업데이트 중...")
        dashboard.name = existing_dashboard.name
        updated = client.update_dashboard(dashboard=dashboard)
        print(f"✅ 대시보드 업데이트 완료: {updated.name}")
        return updated.name
    else:
        # 생성
        print(f"🆕 새 대시보드 생성 중...")
        created = client.create_dashboard(parent=project_name, dashboard=dashboard)
        print(f"✅ 대시보드 생성 완료: {created.name}")
        return created.name


def get_dashboard_url(dashboard_name: str) -> str:
    """
    대시보드 콘솔 URL 생성
    
    Args:
        dashboard_name: 대시보드 리소스 이름
        
    Returns:
        Cloud Console URL
    """
    # dashboard_name 형식: projects/{project}/dashboards/{dashboard_id}
    parts = dashboard_name.split("/")
    project = parts[1]
    dashboard_id = parts[3]
    
    return f"https://console.cloud.google.com/monitoring/dashboards/custom/{dashboard_id}?project={project}"


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("Cloud Monitoring Dashboard 배포")
    print("=" * 70)
    print()
    
    # 1. YAML 로드
    print(f"📄 YAML 파일 로드: {DASHBOARD_YAML}")
    if not DASHBOARD_YAML.exists():
        print(f"❌ 오류: YAML 파일을 찾을 수 없습니다: {DASHBOARD_YAML}")
        sys.exit(1)
    
    try:
        dashboard_json = yaml_to_dashboard_json(DASHBOARD_YAML)
        print(f"✅ YAML 파싱 완료")
        print(f"   Display Name: {dashboard_json.get('displayName')}")
        print(f"   Tiles: {len(dashboard_json.get('mosaicLayout', {}).get('tiles', []))}")
        print()
    except Exception as e:
        print(f"❌ YAML 파싱 실패: {e}")
        sys.exit(1)
    
    # 2. 대시보드 배포
    print(f"🚀 프로젝트: {PROJECT_ID}")
    try:
        dashboard_name = create_or_update_dashboard(PROJECT_ID, dashboard_json)
        dashboard_url = get_dashboard_url(dashboard_name)
        print()
        print("=" * 70)
        print("✅ 배포 완료!")
        print("=" * 70)
        print(f"Dashboard Name: {dashboard_name}")
        print(f"Dashboard URL: {dashboard_url}")
        print()
        print("📊 다음 단계:")
        print("  1. 대시보드 URL을 브라우저에서 확인")
        print("  2. Slack 알림 설정 (setup_slack_alerts.py)")
        print("  3. 테스트 데이터 생성 (test_slo_exporter.py)")
        print()
    except Exception as e:
        print(f"❌ 대시보드 배포 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
