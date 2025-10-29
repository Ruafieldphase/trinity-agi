"""
SLO Exporter 테스트 스크립트

Cloud Run SLO 측정 테스트 및 검증
"""

import sys
import os

# 부모 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from exporters.slo_exporter_cloudrun import SLOExporterCloudRun
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_slo_exporter():
    """SLO Exporter 테스트"""
    print("\n" + "="*70)
    print("  SLO Exporter Test - Cloud Run Environment")
    print("="*70 + "\n")
    
    # 초기화
    project_id = "naeda-genesis"
    service_name = "ion-api-canary"
    
    print(f"📊 Target Service: {service_name}")
    print(f"🔧 Project: {project_id}\n")
    
    exporter = SLOExporterCloudRun(project_id, service_name)
    
    # SLO 목표 출력
    print("="*70)
    print("🎯 SLO Targets")
    print("="*70)
    print(f"  • Availability: ≥ {exporter.SLO_TARGETS['availability']}%")
    print(f"  • Latency P95: ≤ {exporter.SLO_TARGETS['latency_p95']}ms")
    print(f"  • Latency P99: ≤ {exporter.SLO_TARGETS['latency_p99']}ms")
    print(f"  • Error Rate: ≤ {exporter.SLO_TARGETS['error_rate']}%")
    print()
    
    # 1. 가용성 테스트
    print("="*70)
    print("1️⃣  Availability Test")
    print("="*70)
    availability = exporter.get_availability(hours=24)
    
    icon = "✅" if availability["slo_achieved"] else "❌"
    print(f"\n{icon} Availability: {availability['availability']:.2f}%")
    print(f"   Target: {availability['slo_target']}%")
    print(f"   Total Requests: {availability['total_requests']:,}")
    print(f"   Successful: {availability['successful_requests']:,}")
    print(f"   Failed (5xx): {availability['failed_requests']:,}")
    print(f"   Status: {'PASS ✅' if availability['slo_achieved'] else 'FAIL ❌'}\n")
    
    # 2. 레이턴시 테스트
    print("="*70)
    print("2️⃣  Latency Test")
    print("="*70)
    latency = exporter.get_latency(hours=24)
    
    p95_icon = "✅" if latency["slo_p95_achieved"] else "❌"
    p99_icon = "✅" if latency["slo_p99_achieved"] else "❌"
    
    print(f"\n{p95_icon} P95 Latency: {latency['latency_p95']:.2f}ms")
    print(f"   Target: {latency['slo_p95_target']}ms")
    print(f"   Status: {'PASS ✅' if latency['slo_p95_achieved'] else 'FAIL ❌'}")
    
    print(f"\n{p99_icon} P99 Latency: {latency['latency_p99']:.2f}ms")
    print(f"   Target: {latency['slo_p99_target']}ms")
    print(f"   Status: {'PASS ✅' if latency['slo_p99_achieved'] else 'FAIL ❌'}\n")
    
    # 3. 에러율 테스트
    print("="*70)
    print("3️⃣  Error Rate Test")
    print("="*70)
    error_rate = exporter.get_error_rate(hours=24)
    
    icon = "✅" if error_rate["slo_achieved"] else "❌"
    print(f"\n{icon} Error Rate: {error_rate['error_rate']:.2f}%")
    print(f"   Target: < {error_rate['slo_target']}%")
    print(f"   4xx Errors: {error_rate['error_4xx_count']:,}")
    print(f"   5xx Errors: {error_rate['error_5xx_count']:,}")
    print(f"   Total Requests: {error_rate['total_requests']:,}")
    print(f"   Status: {'PASS ✅' if error_rate['slo_achieved'] else 'FAIL ❌'}\n")
    
    # 4. 전체 SLO 상태 평가
    print("="*70)
    print("4️⃣  Overall SLO Status Evaluation")
    print("="*70)
    status_data = exporter.evaluate_slo_status(hours=24)
    
    # 상태 아이콘
    status_icon_map = {
        "HEALTHY": "✅",
        "WARNING": "⚠️",
        "CRITICAL": "❌",
    }
    status_icon = status_icon_map.get(status_data["overall_status"], "❓")
    
    print(f"\n{status_icon} Overall Status: {status_data['overall_status']}")
    print(f"📊 SLO Compliance: {status_data['slo_compliance']:.1f}%")
    
    if status_data["failed_slos"]:
        print(f"❌ Failed SLOs: {', '.join(status_data['failed_slos'])}")
    else:
        print("✅ All SLOs achieved!")
    
    # 5. SLO 달성 현황표
    print("\n" + "="*70)
    print("5️⃣  SLO Achievement Summary")
    print("="*70)
    print(f"{'SLO':<20} {'Current':<15} {'Target':<15} {'Status':<10}")
    print("-"*70)
    
    # 가용성
    avail_status = "✅ PASS" if availability["slo_achieved"] else "❌ FAIL"
    print(f"{'Availability':<20} {f'{availability['availability']:.2f}%':<15} {f'≥ {availability['slo_target']}%':<15} {avail_status:<10}")
    
    # P95 레이턴시
    p95_status = "✅ PASS" if latency["slo_p95_achieved"] else "❌ FAIL"
    print(f"{'Latency P95':<20} {f'{latency['latency_p95']:.2f}ms':<15} {f'≤ {latency['slo_p95_target']}ms':<15} {p95_status:<10}")
    
    # P99 레이턴시
    p99_status = "✅ PASS" if latency["slo_p99_achieved"] else "❌ FAIL"
    print(f"{'Latency P99':<20} {f'{latency['latency_p99']:.2f}ms':<15} {f'≤ {latency['slo_p99_target']}ms':<15} {p99_status:<10}")
    
    # 에러율
    err_status = "✅ PASS" if error_rate["slo_achieved"] else "❌ FAIL"
    print(f"{'Error Rate':<20} {f'{error_rate['error_rate']:.2f}%':<15} {f'≤ {error_rate['slo_target']}%':<15} {err_status:<10}")
    
    print("-"*70)
    print(f"{'OVERALL':<20} {f'{status_data['slo_compliance']:.1f}%':<15} {'100%':<15} {status_icon + ' ' + status_data['overall_status']:<10}")
    print("="*70 + "\n")
    
    # 6. 상세 리포트
    print("="*70)
    print("6️⃣  Detailed Report")
    print("="*70)
    report = exporter.generate_report(hours=24)
    print(report)
    
    # 7. 권장사항
    print("="*70)
    print("7️⃣  Action Items")
    print("="*70)
    
    if status_data["overall_status"] == "HEALTHY":
        print("\n✅ System Status: HEALTHY")
        print("\nNext Steps:")
        print("  1. Continue monitoring SLO trends")
        print("  2. Maintain current configuration")
        print("  3. Review weekly SLO reports")
        print("  4. Document best practices\n")
    
    elif status_data["overall_status"] == "WARNING":
        print("\n⚠️  System Status: WARNING")
        print("\nNext Steps:")
        print("  1. Review failed SLO metrics")
        print("  2. Investigate root causes:")
        for failed_slo in status_data["failed_slos"]:
            print(f"     - {failed_slo}")
        print("  3. Adjust configuration as needed")
        print("  4. Increase monitoring frequency")
        print("  5. Set up alerts for degradation\n")
    
    else:
        print("\n❌ System Status: CRITICAL")
        print("\nImmediate Actions:")
        print("  1. Check service health")
        print("  2. Review recent deployments")
        print("  3. Failed SLOs:")
        for failed_slo in status_data["failed_slos"]:
            print(f"     - {failed_slo}")
        print("  4. Investigate infrastructure issues")
        print("  5. Consider rollback if necessary")
        print("  6. Alert team and stakeholders\n")
    
    print("="*70)
    print("✅ SLO Exporter Test Completed!")
    print("="*70 + "\n")
    
    return status_data


if __name__ == "__main__":
    try:
        status_data = test_slo_exporter()
        
        # Exit code 설정
        if status_data["overall_status"] == "HEALTHY":
            sys.exit(0)
        elif status_data["overall_status"] == "WARNING":
            sys.exit(1)
        else:
            sys.exit(2)
    
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(3)
