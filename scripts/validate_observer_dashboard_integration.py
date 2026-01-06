#!/usr/bin/env python3
"""
Stream Observer Dashboard Integration - E2E Validation
통합 대시보드의 모든 컴포넌트 검증
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()
OUTPUTS = WORKSPACE / "outputs"


def check_file_exists(filepath, description):
    """파일 존재 여부 확인"""
    if filepath.exists():
        print(f"✅ {description}: {filepath.name}")
        return True
    else:
        print(f"❌ {description}: {filepath.name} NOT FOUND")
        return False


def check_file_freshness(filepath, max_age_minutes=30):
    """파일 신선도 확인"""
    if not filepath.exists():
        return False
    
    file_age = (datetime.now() - datetime.fromtimestamp(filepath.stat().st_mtime)).total_seconds() / 60
    is_fresh = file_age <= max_age_minutes
    
    status = "✅" if is_fresh else "⚠️"
    print(f"{status} {filepath.name}: {file_age:.1f}분 전 업데이트")
    return is_fresh


def validate_json_structure(filepath, required_keys):
    """JSON 파일 구조 검증"""
    try:
        data = json.loads(filepath.read_text(encoding='utf-8'))
        missing = [k for k in required_keys if k not in data]
        
        if missing:
            print(f"⚠️ {filepath.name}: 누락된 키 - {', '.join(missing)}")
            return False
        
        print(f"✅ {filepath.name}: 모든 필수 키 존재")
        return True
    except Exception as e:
        print(f"❌ {filepath.name}: JSON 파싱 실패 - {e}")
        return False


def validate_dashboard_html(filepath):
    """대시보드 HTML 검증"""
    try:
        content = filepath.read_text(encoding='utf-8')
        
        required_elements = [
            ("Stream Observer 섹션", "Stream Observer"),
            ("Observer 차트", "observerActivityChart"),
            ("Observer 로드 함수", "loadStreamObserverData"),
            ("Refresh 버튼", "refreshObserverData")
        ]
        
        all_present = True
        for desc, search_str in required_elements:
            if search_str in content:
                print(f"✅ {desc} 존재")
            else:
                print(f"❌ {desc} 누락")
                all_present = False
        
        return all_present
    except Exception as e:
        print(f"❌ HTML 파싱 실패: {e}")
        return False


def main():
    """E2E 검증 실행"""
    print("=" * 60)
    print("🔍 Stream Observer Dashboard - E2E Validation")
    print("=" * 60)
    
    results = []
    
    # 1. 필수 파일 존재 확인
    print("\n▶ 파일 존재 확인")
    files_to_check = [
        (OUTPUTS / "monitoring_dashboard_latest.html", "통합 대시보드 HTML"),
        (OUTPUTS / "stream_observer_summary_latest.json", "Observer Summary JSON"),
        (OUTPUTS / "stream_observer_summary_latest.md", "Observer Summary MD"),
        (OUTPUTS / "monitoring_metrics_latest.json", "모니터링 메트릭 JSON"),
        (OUTPUTS / "dashboard_integration_status.json", "통합 상태 JSON")
    ]
    
    for filepath, desc in files_to_check:
        results.append(("파일:" + desc, check_file_exists(filepath, desc)))
    
    # 2. 파일 신선도 확인
    print("\n▶ 파일 신선도 확인 (30분 이내)")
    for filepath, desc in files_to_check[:3]:  # HTML, JSON, MD만
        if filepath.exists():
            results.append(("신선도:" + desc, check_file_freshness(filepath, 30)))
    
    # 3. JSON 구조 검증
    print("\n▶ JSON 구조 검증")
    observer_json = OUTPUTS / "stream_observer_summary_latest.json"
    if observer_json.exists():
        try:
            data = json.loads(observer_json.read_text(encoding='utf-8'))
            # summary 하위 구조 확인
            summary = data.get("summary", {})
            required_keys = ["total_records", "first_ts_utc", "last_ts_utc", "top_processes"]
            missing = [k for k in required_keys if k not in summary]
            
            if missing:
                print(f"⚠️ {observer_json.name}: 누락된 키 - {', '.join(missing)}")
                results.append(("JSON구조:Observer", False))
            else:
                print(f"✅ {observer_json.name}: 모든 필수 키 존재")
                print(f"   - total_records: {summary.get('total_records', 0)}")
                results.append(("JSON구조:Observer", True))
        except Exception as e:
            print(f"❌ {observer_json.name}: 검증 실패 - {e}")
            results.append(("JSON구조:Observer", False))
    
    # 4. HTML 내용 검증
    print("\n▶ HTML 내용 검증")
    dashboard_html = OUTPUTS / "monitoring_dashboard_latest.html"
    if dashboard_html.exists():
        results.append(("HTML내용:Dashboard", validate_dashboard_html(dashboard_html)))
    
    # 5. 통합 리포트 검증
    print("\n▶ 통합 리포트 검증")
    integration_status = OUTPUTS / "dashboard_integration_status.json"
    if integration_status.exists():
        try:
            data = json.loads(integration_status.read_text(encoding='utf-8'))
            status = data.get("integration_status") == "SUCCESS"
            results.append(("통합상태", status))
            
            if status:
                print("✅ 통합 상태: SUCCESS")
            else:
                print(f"❌ 통합 상태: {data.get('integration_status', 'UNKNOWN')}")
        except:
            results.append(("통합상태", False))
            print("❌ 통합 상태 파싱 실패")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 검증 결과 요약")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"합격률: {passed}/{total} ({pass_rate:.1f}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 모든 검증 통과!")
        print("\n💡 다음 단계:")
        print("  1. 브라우저에서 대시보드 열기")
        print("  2. Stream Observer 섹션 확인")
        print("  3. 차트 로딩 확인")
        print(f"\n📁 Dashboard: {OUTPUTS / 'monitoring_dashboard_latest.html'}")
        return 0
    else:
        print(f"\n⚠️ {total - passed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
