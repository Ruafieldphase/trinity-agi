#!/usr/bin/env python3
"""
Stream Observer Dashboard Integration
통합 모니터링 대시보드에 Stream Observer 텔레메트리를 통합
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root

WORKSPACE = get_workspace_root()
OUTPUTS = WORKSPACE / "outputs"
SCRIPTS = WORKSPACE / "scripts"


def run_observer_summary():
    """Stream Observer 요약 생성"""
    print("🔍 Stream Observer 요약 생성 중...")
    summary_script = SCRIPTS / "summarize_stream_observer.py"
    if not summary_script.exists():
        print(f"❌ {summary_script} not found")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(summary_script), "--hours", "24"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORKSPACE
        )
        if result.returncode == 0:
            print("✅ Stream Observer 요약 생성 완료")
            return True
        else:
            print(f"⚠️ Stream Observer 요약 실패: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Stream Observer 요약 오류: {e}")
        return False


def run_monitoring_report():
    """기존 모니터링 리포트 생성"""
    print("📊 모니터링 리포트 생성 중...")
    report_script = SCRIPTS / "generate_monitoring_report.ps1"
    if not report_script.exists():
        print(f"❌ {report_script} not found")
        return False
    
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(report_script),
                "-Hours",
                "24"
            ],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=WORKSPACE
        )
        if result.returncode == 0:
            print("✅ 모니터링 리포트 생성 완료")
            return True
        else:
            print(f"⚠️ 모니터링 리포트 실패: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ 모니터링 리포트 오류: {e}")
        return False


def verify_dashboard():
    """대시보드 파일 검증"""
    print("🔍 대시보드 파일 검증 중...")
    
    required_files = [
        OUTPUTS / "monitoring_dashboard_latest.html",
        OUTPUTS / "stream_observer_summary_latest.json",
        OUTPUTS / "monitoring_metrics_latest.json"
    ]
    
    missing = []
    for f in required_files:
        if not f.exists():
            missing.append(f.name)
    
    if missing:
        print(f"⚠️ 누락된 파일: {', '.join(missing)}")
        return False
    
    print("✅ 모든 필수 파일 존재")
    return True


def generate_integration_report():
    """통합 리포트 생성"""
    print("📝 통합 리포트 생성 중...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "integration_status": "SUCCESS",
        "components": {
            "stream_observer": {
                "enabled": True,
                "data_file": "stream_observer_summary_latest.json"
            },
            "monitoring_dashboard": {
                "enabled": True,
                "html_file": "monitoring_dashboard_latest.html"
            }
        },
        "files_generated": [
            "monitoring_dashboard_latest.html",
            "stream_observer_summary_latest.json",
            "stream_observer_summary_latest.md"
        ]
    }
    
    report_file = OUTPUTS / "dashboard_integration_status.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"✅ 통합 리포트 저장: {report_file}")
    return True


def main():
    """Main integration pipeline"""
    print("=" * 60)
    print("🚀 Stream Observer Dashboard Integration")
    print("=" * 60)
    
    steps = [
        ("Stream Observer 요약", run_observer_summary),
        ("모니터링 리포트", run_monitoring_report),
        ("파일 검증", verify_dashboard),
        ("통합 리포트", generate_integration_report)
    ]
    
    results = []
    for step_name, step_func in steps:
        print(f"\n▶ {step_name}")
        success = step_func()
        results.append((step_name, success))
    
    print("\n" + "=" * 60)
    print("📊 통합 결과")
    print("=" * 60)
    
    for step_name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {step_name}")
    
    all_success = all(r[1] for r in results)
    
    if all_success:
        dashboard_path = OUTPUTS / "monitoring_dashboard_latest.html"
        print(f"\n🎉 통합 완료!")
        print(f"📁 Dashboard: {dashboard_path}")
        print(f"\n💡 열기: code {dashboard_path}")
        return 0
    else:
        print(f"\n⚠️ 일부 단계 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
