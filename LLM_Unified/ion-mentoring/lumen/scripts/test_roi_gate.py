"""
ROI Gate 테스트 스크립트

Cloud Run ROI Gate 측정 테스트 및 검증
"""

import sys
import os

# 부모 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gates.roi_gate_cloudrun import ROIGateCloudRun
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_roi_gate():
    """ROI Gate 테스트"""
    print("\n" + "="*70)
    print("  ROI Gate Test - Cloud Run Environment")
    print("="*70 + "\n")
    
    # 초기화
    project_id = "naeda-genesis"
    service_name = "ion-api-canary"
    
    print(f"📊 Target Service: {service_name}")
    print(f"🔧 Project: {project_id}\n")
    
    gate = ROIGateCloudRun(project_id, service_name)
    
    # 1. 캐시 히트율 조회
    print("="*70)
    print("1️⃣  Cache Hit Rate Query")
    print("="*70)
    hit_rate = gate.get_cache_hit_rate(hours=24)
    print(f"✅ Cache Hit Rate: {hit_rate:.2f}%\n")
    
    # 2. 요청 수 조회
    print("="*70)
    print("2️⃣  Request Count Query")
    print("="*70)
    request_count = gate.get_request_count(hours=24)
    print(f"✅ Total Requests (24h): {request_count:,}\n")
    
    # 3. 캐시 절감 효과 계산
    print("="*70)
    print("3️⃣  Cache Savings Calculation")
    print("="*70)
    savings = gate.calculate_cache_savings(hours=24)
    print(f"📊 Cache Performance:")
    print(f"   - Hit Rate: {savings['hit_rate']:.1f}%")
    print(f"   - Total Requests (24h): {savings['total_requests']:,}")
    print(f"   - Cached Requests (24h): {savings['cached_requests']:,}")
    print(f"   - Monthly Requests (est): {savings['monthly_requests']:,}")
    print(f"   - Monthly Cached (est): {savings['monthly_cached_requests']:,}")
    print(f"   - Latency Saved: {savings['latency_saved_ms']:,} ms")
    print(f"   - Cost Saved (monthly): ${savings['cost_saved_monthly']:.2f}\n")
    
    # 4. ROI 계산
    print("="*70)
    print("4️⃣  ROI Calculation")
    print("="*70)
    roi_data = gate.calculate_roi(hours=24)
    print(f"💰 Cost Analysis:")
    print(f"   - Redis Cost: ${roi_data['redis_cost']:.2f}/month")
    print(f"   - Cost Savings: ${roi_data['savings']:.2f}/month")
    print(f"   - Net Benefit: ${roi_data['net_benefit']:.2f}/month")
    print(f"   - ROI: {roi_data['roi_percent']:.1f}%\n")
    
    # 5. Gate 평가
    print("="*70)
    print("5️⃣  Gate Evaluation")
    print("="*70)
    decision, reason, roi_data_full = gate.evaluate_gate(hours=24)
    
    # 게이트 결과 출력
    icon_map = {
        "PASS": "✅",
        "WARN": "⚠️",
        "FAIL": "❌",
    }
    icon = icon_map.get(decision, "❓")
    
    print(f"\n{icon} Gate Decision: {decision}")
    print(f"📝 Reason: {reason}\n")
    
    # 임계값 비교표
    print("="*70)
    print("6️⃣  Threshold Comparison")
    print("="*70)
    print(f"{'Threshold':<20} {'Percentage':<15} {'Decision':<15} {'Status':<10}")
    print("-"*70)
    
    roi = roi_data_full['roi_percent']
    
    def get_status(threshold_min, threshold_max=None):
        if threshold_max is None:
            return "✅" if roi >= threshold_min else "  "
        else:
            return "✅" if threshold_min <= roi < threshold_max else "  "
    
    print(f"{'Excellent':<20} {'≥ 500%':<15} {'PASS ✅':<15} {get_status(500):<10}")
    print(f"{'Acceptable':<20} {'300-500%':<15} {'WARN ⚠️':<15} {get_status(300, 500):<10}")
    print(f"{'Insufficient':<20} {'< 300%':<15} {'FAIL ❌':<15} {get_status(0, 300):<10}")
    print("-"*70)
    print(f"{'Current ROI':<20} {f'{roi:.1f}%':<15} {f'{decision} {icon}':<15}")
    print("="*70 + "\n")
    
    # 7. 상세 리포트 생성
    print("="*70)
    print("7️⃣  Detailed Report")
    print("="*70)
    report = gate.generate_report(hours=24)
    print(report)
    
    # 8. 권장사항 요약
    print("="*70)
    print("8️⃣  Recommendations Summary")
    print("="*70)
    
    if decision == "PASS":
        print("✅ System Status: EXCELLENT")
        print("\nNext Steps:")
        print("  1. Continue monitoring ROI trends")
        print("  2. Consider cache TTL optimization")
        print("  3. Document best practices")
        print("  4. Share success metrics with team\n")
    elif decision == "WARN":
        print("⚠️  System Status: NEEDS ATTENTION")
        print("\nNext Steps:")
        print("  1. Monitor cache hit rate closely")
        print("  2. Investigate cache inefficiencies")
        print("  3. Adjust cache configuration:")
        print("     - Increase TTL")
        print("     - Optimize cache keys")
        print("     - Review invalidation logic")
        print("  4. Set up ROI degradation alerts\n")
    else:
        print("❌ System Status: CRITICAL")
        print("\nNext Steps:")
        print("  1. IMMEDIATE: Review deployment")
        print("  2. Consider rollback to previous config")
        print("  3. Root cause analysis:")
        print("     - Check cache hit rate < 50%")
        print("     - Verify Redis connectivity")
        print("     - Review request patterns")
        print("  4. Consult with team before changes\n")
    
    print("="*70)
    print("✅ ROI Gate Test Completed!")
    print("="*70 + "\n")
    
    return decision, roi_data_full


if __name__ == "__main__":
    try:
        decision, roi_data = test_roi_gate()
        
        # Exit code 설정
        if decision == "PASS":
            sys.exit(0)
        elif decision == "WARN":
            sys.exit(1)
        else:
            sys.exit(2)
    
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(3)
