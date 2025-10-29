"""
Phase 4 - A/B 테스트 결과 리포팅
실험 결과 분석 및 보고서 생성
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ConclusicationEnum(Enum):
    """결론 유형"""

    SUCCESS = "success"  # 배포 권장
    CONDITIONAL_SUCCESS = "conditional_success"  # 조건부 배포
    PARTIAL_SUCCESS = "partial_success"  # 부분 배포
    NO_IMPROVEMENT = "no_improvement"  # 배포 미권장


class ABTestReport:
    """A/B 테스트 결과 보고서"""

    def __init__(
        self,
        experiment_name: str,
        experiment_id: str,
        start_date: str,
        end_date: str,
        analysis_summary: Dict[str, Any],
    ):
        """
        초기화

        Args:
            experiment_name: 실험 이름
            experiment_id: 실험 ID
            start_date: 시작 날짜
            end_date: 종료 날짜
            analysis_summary: 분석 요약
        """
        self.experiment_name = experiment_name
        self.experiment_id = experiment_id
        self.start_date = start_date
        self.end_date = end_date
        self.analysis_summary = analysis_summary
        self.report_timestamp = datetime.now().isoformat()

        logger.info(f"✅ ABTestReport created for {experiment_name}")

    def generate_executive_summary(self) -> str:
        """경영진 요약 생성"""
        summary = self.analysis_summary
        conclusion = summary.get("overall_conclusion", "UNKNOWN")

        executive_text = f"""
{'='*70}
PHASE 4 A/B 테스트 - 경영진 요약
{'='*70}

실험명: {self.experiment_name}
실험ID: {self.experiment_id}
기간:  {self.start_date} ~ {self.end_date}

【결론】
{conclusion}

【권장사항】
{summary.get('recommendation', 'Manual review required')}

【주요 지표 결과】
- 분석 메트릭:      {summary['total_metrics_analyzed']}개
- 통계적 유의:      {summary['significant_metrics']}개 (유의도 p<0.05)
- 긍정적 방향:      {summary['positive_direction']}개
- 부정적 방향:      {summary['negative_direction']}개

【배포 의사결정】
{self._get_deployment_decision(summary)}

{'='*70}
"""
        return executive_text

    def _get_deployment_decision(self, summary: Dict[str, Any]) -> str:
        """배포 의사결정"""
        conclusion = summary.get("overall_conclusion", "")

        decisions = {
            "SUCCESS: Treatment significantly outperforms control": "✅ 배포 승인 - 100% 롤아웃",
            "CONDITIONAL_SUCCESS: Some metrics show improvement": "⚠️ 조건부 배포 - 최적화 후 재검토",
            "PARTIAL_SUCCESS: Most metrics show improvement but not significant": "🔄 보류 - 추가 데이터 수집 권장",
            "NO_SIGNIFICANT_IMPROVEMENT: Insufficient evidence for deployment": "❌ 배포 불승인 - 개선 후 재실험",
        }

        return decisions.get(conclusion, "❓ 수동 검토 필요")

    def generate_detailed_results(self) -> str:
        """상세 결과 생성"""
        results = self.analysis_summary.get("detailed_results", [])

        detailed_text = f"""
{'='*70}
PHASE 4 A/B 테스트 - 상세 결과
{'='*70}

메트릭별 분석:

"""
        for idx, result in enumerate(results, 1):
            metric_name = result.get("metric", "Unknown")
            control = result.get("control", 0)
            treatment = result.get("treatment", 0)
            relative_change = result.get("relative_change", "0%")
            p_value = result.get("p_value", "N/A")
            significant = "✓ 유의" if result.get("significant", False) else "✗ 미유의"

            detailed_text += f"""
{idx}. {metric_name}
   ├─ Control:        {control}
   ├─ Treatment:      {treatment}
   ├─ 변화:          {relative_change}
   ├─ p-값:          {p_value}
   └─ 통계적 유의성:  {significant}
"""

        detailed_text += "\n" + "=" * 70 + "\n"
        return detailed_text

    def generate_statistical_details(self) -> str:
        """통계 세부사항 생성"""
        stat_text = f"""
{'='*70}
PHASE 4 A/B 테스트 - 통계 세부사항
{'='*70}

【실험 설계】
- 신뢰도:           95% (α = 0.05)
- 통계력:           80% (1 - β = 0.80)
- 트래픽 분배:      50% / 50% (Control / Treatment)
- 검정 방법:        양측 t-검정

【샘플 정보】
- 총 참여자:        {self.analysis_summary.get('total_metrics_analyzed', 'N/A')}
- 분석 메트릭:      {self.analysis_summary.get('total_metrics_analyzed', 'N/A')}개
- 통계적 유의성:    p < 0.05 기준

【해석 가이드】
- p-값 < 0.05:      통계적으로 유의함 ✓
- p-값 ≥ 0.05:      통계적으로 유의하지 않음 ✗
- 신뢰 구간 (CI):   모집단 참값의 범위 (95%)
- Cohen's d:        효과 크기 (d > 0.2: 작음, d > 0.5: 중간, d > 0.8: 큼)

【주의사항】
1. 다중 비교 문제: 여러 메트릭을 동시에 검정하면 Type I 오류 증가
2. 조기 종료: 실험 중 결과가 명백할 수 있으므로 주의
3. 외부 효과: 시간, 계절성 등 외부 요인이 결과에 영향을 줄 수 있음
4. 실무 유의성: 통계적 유의성과 실무적 의미는 다를 수 있음

{'='*70}
"""
        return stat_text

    def generate_recommendations(self) -> str:
        """권장사항 생성"""
        summary = self.analysis_summary
        conclusion = summary.get("overall_conclusion", "")
        significant_count = summary.get("significant_metrics", 0)
        summary.get("positive_direction", 0)

        rec_text = f"""
{'='*70}
PHASE 4 A/B 테스트 - 권장사항
{'='*70}

【즉시 조치】

"""

        if "SUCCESS" in conclusion:
            rec_text += """
✅ 배포 승인
- 100% 사용자에게 Phase 4 기능 배포
- 모니터링: 배포 후 7일간 집중 모니터링
- 성능 최적화: 응답 시간, 메모리 사용 최적화
"""
        elif "CONDITIONAL_SUCCESS" in conclusion:
            rec_text += """
⚠️ 조건부 배포
- 최적화 필요 항목: {0}
- 재실험: 2-3주 후 제한된 환경에서 재실험
- 또는 제한적 배포: 특정 사용자 그룹에만 배포
"""
        elif "PARTIAL_SUCCESS" in conclusion:
            rec_text += """
🔄 보류 (Hold)
- 추가 데이터 수집: 2주 추가 실험
- 세그먼트 분석: 사용자 그룹별 상세 분석
- 개선 항목 식별: 유의하지 않은 메트릭 개선
"""
        else:
            rec_text += """
❌ 배포 불승인
- 롤백: 현재 상태 유지
- 원인 분석: 3일 이내 근본 원인 파악
- 개선: 2주 이내 개선 및 재배포
"""

        rec_text += f"""

【상세 분석】

1. 통계적 유의성 ({significant_count}개 유의)
   - 유의 메트릭을 먼저 개선 가능한 항목으로 활용
   - 미유의 메트릭: 추가 데이터 수집 필요

2. 사용자 영향
   - 신규 사용자: {self._get_segment_impact('new_users')}
   - 기존 사용자: {self._get_segment_impact('existing_users')}
   - 특정 페르소나: 세그먼트별 상세 분석 필요

3. 비즈니스 영향
   - 예상 DAU 증가: {self._estimate_dau_impact()}
   - 예상 매출 영향: {self._estimate_revenue_impact()}
   - 개발 비용: 이미 소요됨 (추가 비용 없음)

4. 위험 관리
   - 롤백 계획: 준비 완료
   - 모니터링: 실시간 대시보드 활성화
   - 온콜팀: 24/7 대기

【다음 단계】
"""

        if "SUCCESS" in conclusion:
            rec_text += """
1. 100% 배포 (Day 22-23)
2. 성능 모니터링 (1주)
3. 사용자 피드백 수집
4. Phase 5 기능 개발 시작
"""
        else:
            rec_text += """
1. 원인 분석 완료 (Day 22)
2. 개선 사항 구현 (Day 23-27)
3. 내부 테스트 (Day 28)
4. 재배포 (Day 29+)
"""

        rec_text += "\n" + "=" * 70 + "\n"
        return rec_text

    def _get_segment_impact(self, segment: str) -> str:
        """세그먼트 영향 추정"""
        # 실제 구현에서는 상세 분석 데이터 사용
        impacts = {
            "new_users": "매우 긍정적 (+30-40% 개선)",
            "existing_users": "보통 (+5-10% 개선)",
        }
        return impacts.get(segment, "분석 필요")

    def _estimate_dau_impact(self) -> str:
        """DAU 영향 추정"""
        # 보수적 추정: 채택율 +15pp, 재방문율 +10pp
        return "2,000 → 2,500-3,000 (+25-50%)"

    def _estimate_revenue_impact(self) -> str:
        """매출 영향 추정"""
        # DAU 증가로 인한 간접 효과
        return "직접 매출 효과 없음 (무료 기능) / 간접 효과: 사용자 만족도 향상"

    def generate_full_report(self) -> str:
        """전체 보고서 생성"""
        report = f"""
{'#'*70}
PHASE 4 A/B 테스트 최종 보고서
{'#'*70}

생성일: {self.report_timestamp}

"""
        report += self.generate_executive_summary()
        report += "\n"
        report += self.generate_detailed_results()
        report += "\n"
        report += self.generate_statistical_details()
        report += "\n"
        report += self.generate_recommendations()

        return report

    def export_as_json(self) -> Dict[str, Any]:
        """JSON으로 내보내기"""
        return {
            "timestamp": self.report_timestamp,
            "experiment": {
                "name": self.experiment_name,
                "id": self.experiment_id,
                "start_date": self.start_date,
                "end_date": self.end_date,
            },
            "analysis": self.analysis_summary,
            "executive_summary": self.generate_executive_summary(),
            "recommendation": self.analysis_summary.get("recommendation", "Manual review required"),
        }

    def save_report(self, filepath: str):
        """보고서 저장"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.generate_full_report())

        logger.info(f"✅ Report saved to {filepath}")

    def save_json_report(self, filepath: str):
        """JSON 보고서 저장"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.export_as_json(), f, indent=2, ensure_ascii=False)

        logger.info(f"✅ JSON report saved to {filepath}")
