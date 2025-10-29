"""
Maturity Exporter 테스트 스크립트

Cloud Run 성숙도 측정 테스트 및 검증
"""

import sys
import os

# 부모 디렉터리를 Python path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from exporters.maturity_exporter_cloudrun import MaturityExporterCloudRun
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_maturity_exporter():
    """Maturity Exporter 테스트"""
    print("\n" + "="*60)
    print("  Maturity Exporter Test - Cloud Run Environment")
    print("="*60 + "\n")
    
    # 초기화
    project_id = "naeda-genesis"
    service_name = "ion-api-canary"
    
    print(f"📊 Target Service: {service_name}")
    print(f"🔧 Project: {project_id}\n")
    
    exporter = MaturityExporterCloudRun(project_id, service_name)
    
    # 1. 배포 빈도 테스트
    print("="*60)
    print("1️⃣  Deployment Frequency Test")
    print("="*60)
    deployment_score = exporter.get_deployment_frequency(days=7)
    print(f"✅ Deployment Frequency Score: {deployment_score}/100\n")
    
    # 2. 레이턴시 테스트
    print("="*60)
    print("2️⃣  Latency Test")
    print("="*60)
    latency_score = exporter.get_latency_score(hours=24)
    print(f"✅ Latency Score: {latency_score}/100\n")
    
    # 3. 에러율 테스트
    print("="*60)
    print("3️⃣  Error Rate Test")
    print("="*60)
    error_rate_score = exporter.get_error_rate_score(hours=24)
    print(f"✅ Error Rate Score: {error_rate_score}/100\n")
    
    # 4. 가용성 테스트
    print("="*60)
    print("4️⃣  Availability Test")
    print("="*60)
    availability_score = exporter.get_availability_score(hours=24)
    print(f"✅ Availability Score: {availability_score}/100\n")
    
    # 5. 캐시 히트율 테스트
    print("="*60)
    print("5️⃣  Cache Hit Rate Test")
    print("="*60)
    cache_hit_rate_score = exporter.get_cache_hit_rate_score()
    print(f"✅ Cache Hit Rate Score: {cache_hit_rate_score}/100\n")
    
    # 6. 비용 효율성 테스트
    print("="*60)
    print("6️⃣  Cost Efficiency Test")
    print("="*60)
    cost_efficiency_score = exporter.get_cost_efficiency_score(target_cost=200.0)
    print(f"✅ Cost Efficiency Score: {cost_efficiency_score}/100\n")
    
    # 7. 전체 성숙도 스코어 계산
    print("="*60)
    print("7️⃣  Overall Maturity Score Calculation")
    print("="*60)
    scores = exporter.calculate_maturity_score()
    
    print("\n📊 Final Maturity Report:")
    print(f"{'='*60}")
    print(f"{'Metric':<30} {'Score':<10} {'Grade':<10}")
    print(f"{'-'*60}")
    
    def get_grade(score):
        if score >= 90:
            return "A+ 🏆"
        elif score >= 80:
            return "A  🥇"
        elif score >= 70:
            return "B+ 🥈"
        elif score >= 60:
            return "B  🥉"
        elif score >= 50:
            return "C  ⚠️"
        else:
            return "D  ❌"
    
    print(f"{'Deployment Frequency':<30} {scores['deployment_frequency']:<10.2f} {get_grade(scores['deployment_frequency']):<10}")
    print(f"{'Latency':<30} {scores['latency']:<10.2f} {get_grade(scores['latency']):<10}")
    print(f"{'Error Rate':<30} {scores['error_rate']:<10.2f} {get_grade(scores['error_rate']):<10}")
    print(f"{'Availability':<30} {scores['availability']:<10.2f} {get_grade(scores['availability']):<10}")
    print(f"{'Cache Hit Rate':<30} {scores['cache_hit_rate']:<10.2f} {get_grade(scores['cache_hit_rate']):<10}")
    print(f"{'Cost Efficiency':<30} {scores['cost_efficiency']:<10.2f} {get_grade(scores['cost_efficiency']):<10}")
    print(f"{'-'*60}")
    print(f"{'OVERALL MATURITY':<30} {scores['maturity_score']:<10.2f} {get_grade(scores['maturity_score']):<10}")
    print(f"{'='*60}\n")
    
    # 성숙도 수준 해석
    maturity_level = scores['maturity_score']
    
    print("📈 Maturity Level Interpretation:")
    if maturity_level >= 90:
        print("🏆 Level 5: Optimizing (지속적 개선 및 최적화)")
        print("   - 모든 지표가 우수함")
        print("   - 자동화된 모니터링 및 알림 작동")
        print("   - 비용 효율성 극대화")
    elif maturity_level >= 70:
        print("🥇 Level 4: Managed (관리되는 성숙도)")
        print("   - 대부분의 지표가 양호함")
        print("   - 일부 개선 여지 있음")
        print("   - 안정적인 운영 상태")
    elif maturity_level >= 50:
        print("🥈 Level 3: Defined (정의된 프로세스)")
        print("   - 기본적인 모니터링 작동")
        print("   - 일부 지표 개선 필요")
        print("   - 추가 최적화 권장")
    elif maturity_level >= 30:
        print("🥉 Level 2: Repeatable (반복 가능한 수준)")
        print("   - 기본 기능은 작동")
        print("   - 많은 개선 필요")
        print("   - 모니터링 강화 필요")
    else:
        print("⚠️  Level 1: Initial (초기 수준)")
        print("   - 시스템 개선 시급")
        print("   - 즉각적인 조치 필요")
        print("   - 모니터링 시스템 구축 필요")
    
    print("\n" + "="*60)
    print("✅ Maturity Exporter Test Completed!")
    print("="*60 + "\n")
    
    return scores


if __name__ == "__main__":
    try:
        test_maturity_exporter()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
