"""
Lumen 시스템 빠른 테스트 스크립트

Maturity Exporter + ROI Gate 통합 테스트
"""

import sys
import os

# 부모 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from exporters.maturity_exporter_cloudrun import MaturityExporterCloudRun
from gates.roi_gate_cloudrun import ROIGateCloudRun
import logging
import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_header(title: str, width: int = 70):
    """헤더 출력"""
    print("\n" + "="*width)
    print(f"  {title}")
    print("="*width + "\n")


def print_section(title: str, width: int = 70):
    """섹션 출력"""
    print("\n" + "-"*width)
    print(f"  {title}")
    print("-"*width)


def quick_test():
    """Lumen 시스템 빠른 테스트"""
    print_header("🚀 Lumen System Quick Test")
    
    # 초기화
    project_id = "naeda-genesis"
    service_name = "ion-api-canary"
    
    print(f"📊 Target: {service_name}")
    print(f"🔧 Project: {project_id}")
    print(f"🕐 Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========================================
    # Phase 1: Maturity Exporter
    # ========================================
    print_section("📊 Phase 1: Maturity Score Measurement")
    
    maturity_exporter = MaturityExporterCloudRun(project_id, service_name)
    maturity_scores = maturity_exporter.calculate_maturity_score()
    
    print(f"\n✅ Maturity Score: {maturity_scores['maturity_score']:.1f}/100")
    
    # 성숙도 수준 판단
    score = maturity_scores['maturity_score']
    if score >= 90:
        level = "🏆 Level 5: Optimizing"
        status = "EXCELLENT"
    elif score >= 70:
        level = "🥇 Level 4: Managed"
        status = "GOOD"
    elif score >= 50:
        level = "🥈 Level 3: Defined"
        status = "FAIR"
    elif score >= 30:
        level = "🥉 Level 2: Repeatable"
        status = "POOR"
    else:
        level = "⚠️  Level 1: Initial"
        status = "CRITICAL"
    
    print(f"   {level}")
    print(f"   Status: {status}\n")
    
    # 세부 항목
    print("   Breakdown:")
    print(f"   • Deployment Frequency: {maturity_scores['deployment_frequency']:.1f}/100")
    print(f"   • Latency: {maturity_scores['latency']:.1f}/100")
    print(f"   • Error Rate: {maturity_scores['error_rate']:.1f}/100")
    print(f"   • Availability: {maturity_scores['availability']:.1f}/100")
    print(f"   • Cache Hit Rate: {maturity_scores['cache_hit_rate']:.1f}/100")
    print(f"   • Cost Efficiency: {maturity_scores['cost_efficiency']:.1f}/100")
    
    # ========================================
    # Phase 2: ROI Gate
    # ========================================
    print_section("💰 Phase 2: ROI Gate Evaluation")
    
    roi_gate = ROIGateCloudRun(project_id, service_name)
    decision, reason, roi_data = roi_gate.evaluate_gate(hours=24)
    
    # 게이트 결과
    icon_map = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
    icon = icon_map.get(decision, "❓")
    
    print(f"\n{icon} Gate Decision: {decision}")
    print(f"   {reason}\n")
    
    # ROI 세부 정보
    print("   ROI Analysis:")
    print(f"   • Redis Cost: ${roi_data['redis_cost']:.2f}/month")
    print(f"   • Cost Savings: ${roi_data['savings']:.2f}/month")
    print(f"   • Net Benefit: ${roi_data['net_benefit']:.2f}/month")
    print(f"   • ROI: {roi_data['roi_percent']:.1f}%")
    print(f"   • Cache Hit Rate: {roi_data['hit_rate']:.1f}%")
    
    # ========================================
    # Phase 3: Summary & Recommendations
    # ========================================
    print_section("📋 Phase 3: Summary & Recommendations")
    
    print("\n📊 System Health Summary:")
    print(f"   • Maturity: {maturity_scores['maturity_score']:.1f}/100 ({status})")
    print(f"   • ROI: {roi_data['roi_percent']:.1f}% ({decision})")
    print(f"   • Cache Hit Rate: {roi_data['hit_rate']:.1f}%")
    print(f"   • Net Monthly Benefit: ${roi_data['net_benefit']:.2f}")
    
    # 통합 권장사항
    print("\n💡 Recommendations:")
    
    if decision == "PASS" and score >= 70:
        print("   ✅ System is performing excellently!")
        print("   • Continue monitoring")
        print("   • Document best practices")
        print("   • Share metrics with team")
    
    elif decision == "PASS" and score >= 50:
        print("   ✅ ROI is good, but maturity needs improvement")
        print("   • Focus on improving deployment frequency")
        print("   • Optimize latency and error handling")
        print("   • Continue monitoring ROI")
    
    elif decision == "WARN":
        print("   ⚠️  System needs attention")
        print("   • Investigate cache performance")
        print("   • Consider TTL optimization")
        print("   • Set up ROI degradation alerts")
        print("   • Monitor maturity trends")
    
    else:
        print("   ❌ Immediate action required")
        print("   • Review deployment configuration")
        print("   • Consider rollback")
        print("   • Investigate root causes")
        print("   • Consult with team")
    
    # ========================================
    # Phase 4: Next Steps
    # ========================================
    print_section("🎯 Phase 4: Next Steps")
    
    print("\n📝 Action Items:")
    
    if decision == "PASS" and score >= 70:
        print("   1. Continue 7-day validation period")
        print("   2. Export metrics to Cloud Monitoring")
        print("   3. Create automated dashboard")
        print("   4. Set up Slack notifications")
    
    elif decision == "PASS" or decision == "WARN":
        print("   1. Improve low-scoring maturity metrics")
        print("   2. Monitor cache hit rate closely")
        print("   3. Optimize cache configuration")
        print("   4. Set up alerts for degradation")
    
    else:
        print("   1. IMMEDIATE: Review system configuration")
        print("   2. Run diagnostic tests")
        print("   3. Prepare rollback plan")
        print("   4. Schedule team discussion")
    
    # ========================================
    # Footer
    # ========================================
    print_header("✅ Lumen System Quick Test Completed")
    
    # 종료 코드 반환
    if decision == "PASS" and score >= 70:
        return 0  # Success
    elif decision == "PASS" or decision == "WARN":
        return 1  # Warning
    else:
        return 2  # Failure


if __name__ == "__main__":
    try:
        exit_code = quick_test()
        sys.exit(exit_code)
    
    except Exception as e:
        logger.error(f"Quick test failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        sys.exit(3)
