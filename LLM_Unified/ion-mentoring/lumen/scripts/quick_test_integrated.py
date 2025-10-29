"""
Lumen 시스템 통합 테스트 스크립트 (Phase 2 포함)

Maturity Exporter + ROI Gate + SLO Exporter 통합 테스트
"""

import sys
import os

# 부모 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from exporters.maturity_exporter_cloudrun import MaturityExporterCloudRun
from exporters.slo_exporter_cloudrun import SLOExporterCloudRun
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
    """Lumen 시스템 통합 테스트"""
    print_header("🚀 Lumen System Integrated Test (Phase 1 + Phase 2)")
    
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
    print(f"📈 Maturity Level: {maturity_scores['maturity_level']}")
    print(f"\n개별 점수:")
    for metric, score in maturity_scores['individual_scores'].items():
        icon = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
        print(f"  {icon} {metric}: {score:.1f}")
    
    # ========================================
    # Phase 1: ROI Gate
    # ========================================
    print_section("💰 Phase 1: ROI Gate Evaluation")
    
    roi_gate = ROIGateCloudRun(project_id, service_name)
    gate_result = roi_gate.evaluate_gate()
    
    print(f"\n✅ ROI: {gate_result['roi_percentage']:.1f}%")
    print(f"🚦 Gate Status: {gate_result['gate_status']}")
    print(f"💾 Cache Hit Rate: {gate_result['cache_hit_rate']:.1f}%")
    print(f"💰 Redis Cost: ${gate_result['redis_cost']:.2f}/month")
    print(f"💵 Savings: ${gate_result['total_savings']:.2f}/month")
    
    # ========================================
    # Phase 2: SLO Exporter
    # ========================================
    print_section("🎯 Phase 2: SLO Compliance Check")
    
    slo_exporter = SLOExporterCloudRun(project_id, service_name)
    slo_status = slo_exporter.evaluate_slo_status()
    
    print(f"\n✅ Overall SLO Status: {slo_status['overall_status']}")
    print(f"📊 Compliance Rate: {slo_status['compliance_rate']:.1f}%")
    print(f"\n개별 SLO 상태:")
    
    for slo_name, slo_data in slo_status['slos'].items():
        status_icon = {
            "HEALTHY": "✅",
            "WARNING": "⚠️",
            "CRITICAL": "❌",
        }[slo_data['status']]
        
        print(f"  {status_icon} {slo_name}:")
        print(f"      Current: {slo_data['current_value']:.2f}")
        print(f"      Target: {slo_data['target']}")
        print(f"      Met: {slo_data['met']}")
    
    # ========================================
    # 종합 결과 요약
    # ========================================
    print_header("📋 System Health Summary")
    
    print("┌─────────────────────────────────────────────────────────┐")
    print("│                   System Metrics                        │")
    print("├─────────────────────────────────────────────────────────┤")
    print(f"│ Maturity Score      │ {maturity_scores['maturity_score']:>6.1f} / 100        │")
    print(f"│ Maturity Level      │ {maturity_scores['maturity_level']:>21} │")
    print(f"│ ROI                 │ {gate_result['roi_percentage']:>6.1f}%              │")
    print(f"│ ROI Gate Status     │ {gate_result['gate_status']:>21} │")
    print(f"│ SLO Compliance      │ {slo_status['compliance_rate']:>6.1f}%              │")
    print(f"│ SLO Overall Status  │ {slo_status['overall_status']:>21} │")
    print("└─────────────────────────────────────────────────────────┘")
    
    # ========================================
    # 종합 건강도 평가
    # ========================================
    print_section("🏥 Overall System Health Assessment")
    
    # 점수 기반 종합 평가
    overall_health_score = (
        maturity_scores['maturity_score'] * 0.3 +  # 30% weight
        min(gate_result['roi_percentage'] / 10, 100) * 0.3 +  # 30% weight (ROI 1000% = 100점)
        slo_status['compliance_rate'] * 0.4  # 40% weight
    )
    
    health_status = "EXCELLENT" if overall_health_score >= 90 else \
                    "GOOD" if overall_health_score >= 70 else \
                    "FAIR" if overall_health_score >= 50 else \
                    "POOR"
    
    health_icon = {
        "EXCELLENT": "🟢",
        "GOOD": "🟡",
        "FAIR": "🟠",
        "POOR": "🔴",
    }[health_status]
    
    print(f"\n{health_icon} Overall Health: {health_status} ({overall_health_score:.1f}/100)")
    print(f"\n가중치:")
    print(f"  - Maturity Score: 30%")
    print(f"  - ROI: 30%")
    print(f"  - SLO Compliance: 40%")
    
    # ========================================
    # 권장 조치사항
    # ========================================
    print_section("📝 Recommended Actions")
    
    actions = []
    
    # Maturity 기반 권장사항
    if maturity_scores['maturity_score'] < 70:
        actions.append({
            "priority": "HIGH",
            "category": "Maturity",
            "action": f"Improve system maturity (current: {maturity_scores['maturity_score']:.1f})",
            "details": "Focus on low-scoring metrics from Maturity Exporter report",
        })
    
    # ROI 기반 권장사항
    if gate_result['gate_status'] == "WARN":
        actions.append({
            "priority": "MEDIUM",
            "category": "ROI",
            "action": "Monitor ROI closely (below recommended threshold)",
            "details": f"Current ROI: {gate_result['roi_percentage']:.1f}%, Target: 500%+",
        })
    elif gate_result['gate_status'] == "FAIL":
        actions.append({
            "priority": "CRITICAL",
            "category": "ROI",
            "action": "⚠️  Immediate action required: ROI too low",
            "details": f"Current ROI: {gate_result['roi_percentage']:.1f}%, Minimum: 300%",
        })
    
    # SLO 기반 권장사항
    if slo_status['overall_status'] == "WARNING":
        actions.append({
            "priority": "MEDIUM",
            "category": "SLO",
            "action": "Investigate SLO violations",
            "details": f"Compliance: {slo_status['compliance_rate']:.1f}%, Target: 100%",
        })
    elif slo_status['overall_status'] == "CRITICAL":
        actions.append({
            "priority": "CRITICAL",
            "category": "SLO",
            "action": "⚠️  Critical SLO violations detected",
            "details": f"Compliance: {slo_status['compliance_rate']:.1f}%, Minimum: 75%",
        })
    
    if not actions:
        print("\n✅ No immediate actions required. System is healthy!")
    else:
        print()
        for i, action in enumerate(actions, 1):
            priority_icon = "🔴" if action['priority'] == "CRITICAL" else \
                            "🟠" if action['priority'] == "HIGH" else \
                            "🟡"
            print(f"{priority_icon} {i}. [{action['category']}] {action['action']}")
            print(f"   {action['details']}")
            print()
    
    # ========================================
    # Exit Code 결정
    # ========================================
    if health_status in ["EXCELLENT", "GOOD"]:
        exit_code = 0
    elif health_status == "FAIR":
        exit_code = 1
    else:
        exit_code = 2
    
    print_section("🎯 Test Result")
    print(f"\nExit Code: {exit_code}")
    print(f"  0 = Healthy (EXCELLENT/GOOD)")
    print(f"  1 = Warning (FAIR)")
    print(f"  2 = Critical (POOR)")
    
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = quick_test()
        print("\n" + "="*70)
        print("✅ Test completed successfully")
        print("="*70 + "\n")
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print("\n" + "="*70)
        print("❌ Test failed with error")
        print("="*70 + "\n")
        sys.exit(3)
