"""
Phase 4 - A/B 테스트 프레임워크
통계 분석 기반 실험 관리 및 결과 분석
"""

import hashlib
import logging
import math
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """실험 상태"""

    PLANNED = "planned"  # 계획됨
    RUNNING = "running"  # 진행 중
    PAUSED = "paused"  # 일시 정지
    COMPLETED = "completed"  # 완료
    ARCHIVED = "archived"  # 보관됨


class TreatmentGroup(Enum):
    """처리 그룹"""

    CONTROL = "control"  # 컨트롤 (기존)
    TREATMENT = "treatment"  # 처리 (신규)


@dataclass
class Metric:
    """메트릭 기본 정보"""

    name: str  # 메트릭 이름
    description: str  # 설명
    metric_type: str  # 타입: "continuous" 또는 "categorical"
    success_direction: str  # 방향: "higher" 또는 "lower"
    minimum_change: float  # 최소 의미 있는 변화
    priority: int  # 우선순위 (1=높음, 5=낮음)


@dataclass
class MetricResult:
    """메트릭 결과"""

    metric_name: str
    control_value: float
    treatment_value: float
    absolute_change: float  # treatment - control
    relative_change: float  # (treatment - control) / control * 100
    p_value: float  # p-값
    confidence_interval: Tuple[float, float]  # 95% CI
    effect_size: float  # Cohen's d
    is_significant: bool  # 통계적으로 유의한가


@dataclass
class ExperimentData:
    """실험 데이터"""

    metric_name: str
    treatment_group: str
    value: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    user_id: str = ""
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


class ABTestFramework:
    """A/B 테스트 프레임워크"""

    # 통계 기준
    SIGNIFICANCE_LEVEL = 0.05  # α = 0.05 (95% 신뢰도)
    STATISTICAL_POWER = 0.80  # 1 - β = 0.80 (80% 통계력)

    def __init__(self, experiment_name: str, experiment_id: str, start_date: datetime):
        """
        초기화

        Args:
            experiment_name: 실험 이름
            experiment_id: 실험 ID
            start_date: 시작 날짜
        """
        self.experiment_name = experiment_name
        self.experiment_id = experiment_id
        self.start_date = start_date
        self.status = ExperimentStatus.PLANNED

        # 메트릭 정의
        self.metrics: Dict[str, Metric] = {}

        # 데이터 저장소
        self.data: List[ExperimentData] = []

        # 그룹별 메트릭 데이터
        self.group_data: Dict[str, Dict[str, List[float]]] = {
            TreatmentGroup.CONTROL.value: defaultdict(list),
            TreatmentGroup.TREATMENT.value: defaultdict(list),
        }

        logger.info(f"✅ ABTestFramework initialized: {experiment_name} ({experiment_id})")

    def add_metric(self, metric: Metric):
        """메트릭 추가"""
        self.metrics[metric.name] = metric
        logger.info(f"Added metric: {metric.name}")

    def record_data(
        self,
        user_id: str,
        metric_name: str,
        value: float,
        treatment_group: str = None,
        session_id: str = "",
        metadata: Dict[str, Any] = None,
    ):
        """
        데이터 기록

        Args:
            user_id: 사용자 ID
            metric_name: 메트릭 이름
            value: 메트릭 값
            treatment_group: 처리 그룹 (None이면 user_id로 자동 결정)
            session_id: 세션 ID
            metadata: 추가 메타데이터
        """
        # 그룹 결정 (없으면 자동 결정)
        if treatment_group is None:
            treatment_group = self._assign_group(user_id)

        # 데이터 기록
        experiment_data = ExperimentData(
            metric_name=metric_name,
            treatment_group=treatment_group,
            value=value,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
        )

        self.data.append(experiment_data)
        self.group_data[treatment_group][metric_name].append(value)

        logger.debug(f"Recorded: {metric_name}={value} for {treatment_group} ({user_id})")

    def _assign_group(self, user_id: str) -> str:
        """
        사용자를 그룹에 할당 (결정적)

        Args:
            user_id: 사용자 ID

        Returns:
            str: "control" 또는 "treatment"
        """
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100

        if hash_value < 50:
            return TreatmentGroup.CONTROL.value
        else:
            return TreatmentGroup.TREATMENT.value

    def get_experiment_status(self) -> Dict[str, Any]:
        """실험 상태 조회"""
        total_records = len(self.data)
        control_records = len(self.group_data[TreatmentGroup.CONTROL.value])
        treatment_records = len(self.group_data[TreatmentGroup.TREATMENT.value])

        return {
            "experiment_id": self.experiment_id,
            "experiment_name": self.experiment_name,
            "status": self.status.value,
            "start_date": self.start_date.isoformat(),
            "total_records": total_records,
            "control_records": control_records,
            "treatment_records": treatment_records,
            "metrics_count": len(self.metrics),
            "traffic_split": {
                "control": f"{control_records / total_records * 100:.1f}%",
                "treatment": f"{treatment_records / total_records * 100:.1f}%",
            },
        }

    def calculate_metric_statistics(self, metric_name: str) -> Dict[str, Any]:
        """메트릭별 통계 계산"""
        if metric_name not in self.metrics:
            raise ValueError(f"Metric {metric_name} not found")

        control_values = self.group_data[TreatmentGroup.CONTROL.value][metric_name]
        treatment_values = self.group_data[TreatmentGroup.TREATMENT.value][metric_name]

        if not control_values or not treatment_values:
            return {"metric_name": metric_name, "status": "insufficient_data"}

        # 통계 계산
        control_mean = statistics.mean(control_values)
        treatment_mean = statistics.mean(treatment_values)
        control_std = statistics.stdev(control_values) if len(control_values) > 1 else 0
        treatment_std = statistics.stdev(treatment_values) if len(treatment_values) > 1 else 0

        # t-검정
        t_stat, p_value = self._t_test(control_values, treatment_values)

        # 신뢰 구간
        ci_lower, ci_upper = self._confidence_interval(
            control_mean,
            treatment_mean,
            control_std,
            treatment_std,
            len(control_values),
            len(treatment_values),
        )

        # 효과 크기 (Cohen's d)
        cohens_d = self._cohens_d(
            control_mean,
            treatment_mean,
            control_std,
            treatment_std,
            len(control_values),
            len(treatment_values),
        )

        # 절대/상대 변화
        absolute_change = treatment_mean - control_mean
        relative_change = (absolute_change / control_mean * 100) if control_mean != 0 else 0

        # 유의성 판정
        is_significant = p_value < self.SIGNIFICANCE_LEVEL

        return {
            "metric_name": metric_name,
            "control": {
                "mean": round(control_mean, 4),
                "std": round(control_std, 4),
                "n": len(control_values),
            },
            "treatment": {
                "mean": round(treatment_mean, 4),
                "std": round(treatment_std, 4),
                "n": len(treatment_values),
            },
            "results": {
                "absolute_change": round(absolute_change, 4),
                "relative_change": f"{relative_change:+.2f}%",
                "p_value": f"{p_value:.4f}",
                "confidence_interval_95": [round(ci_lower, 4), round(ci_upper, 4)],
                "effect_size_cohens_d": round(cohens_d, 4),
                "is_significant": is_significant,
            },
        }

    def _t_test(self, group1: List[float], group2: List[float]) -> Tuple[float, float]:
        """
        독립표본 t-검정 (스튜던트 t-검정)

        Returns:
            Tuple[float, float]: (t-통계량, p-값)
        """
        mean1 = statistics.mean(group1)
        mean2 = statistics.mean(group2)
        n1 = len(group1)
        n2 = len(group2)

        var1 = statistics.variance(group1) if len(group1) > 1 else 0
        var2 = statistics.variance(group2) if len(group2) > 1 else 0

        # 표준오차
        se = math.sqrt(var1 / n1 + var2 / n2) if (var1 + var2) > 0 else 0.0001

        # t-통계량
        t_stat = (mean2 - mean1) / se if se > 0 else 0

        # p-값 (양측)
        from scipy import stats

        _, p_value = stats.ttest_ind(group1, group2)

        return t_stat, p_value

    def _confidence_interval(
        self,
        mean1: float,
        mean2: float,
        std1: float,
        std2: float,
        n1: int,
        n2: int,
        confidence: float = 0.95,
    ) -> Tuple[float, float]:
        """
        95% 신뢰 구간 계산

        Returns:
            Tuple[float, float]: (하한, 상한)
        """
        # 자유도
        df = n1 + n2 - 2

        # t-분포의 임계값 (df=∞일 때 ≈ 1.96)
        try:
            from scipy import stats

            t_critical = stats.t.ppf((1 + confidence) / 2, df)
        except:
            t_critical = 1.96  # 기본값

        # 표준오차
        se = math.sqrt(std1**2 / n1 + std2**2 / n2) if (std1**2 / n1 + std2**2 / n2) > 0 else 0.0001

        # 차이
        mean_diff = mean2 - mean1

        # 신뢰 구간
        ci_lower = mean_diff - t_critical * se
        ci_upper = mean_diff + t_critical * se

        return ci_lower, ci_upper

    def _cohens_d(
        self, mean1: float, mean2: float, std1: float, std2: float, n1: int, n2: int
    ) -> float:
        """
        Cohen's d (효과 크기) 계산

        Returns:
            float: Cohen's d
        """
        # 풀링된 표준편차
        if n1 == 1 and n2 == 1:
            pooled_std = 0
        else:
            pooled_std = math.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return 0

        # Cohen's d
        cohens_d = (mean2 - mean1) / pooled_std

        return cohens_d

    def analyze_all_metrics(self) -> List[MetricResult]:
        """모든 메트릭 분석"""
        results = []

        for metric_name, metric in self.metrics.items():
            stats = self.calculate_metric_statistics(metric_name)

            if stats.get("status") == "insufficient_data":
                continue

            result = MetricResult(
                metric_name=metric_name,
                control_value=stats["control"]["mean"],
                treatment_value=stats["treatment"]["mean"],
                absolute_change=stats["results"]["absolute_change"],
                relative_change=float(stats["results"]["relative_change"].rstrip("%")),
                p_value=float(stats["results"]["p_value"]),
                confidence_interval=tuple(stats["results"]["confidence_interval_95"]),
                effect_size=stats["results"]["effect_size_cohens_d"],
                is_significant=stats["results"]["is_significant"],
            )

            results.append(result)

        return results

    def get_analysis_summary(self) -> Dict[str, Any]:
        """분석 요약"""
        results = self.analyze_all_metrics()

        significant_metrics = [r for r in results if r.is_significant]
        non_significant_metrics = [r for r in results if not r.is_significant]

        # 방향성 확인
        positive_metrics = [
            r
            for r in results
            if (r.relative_change > 0 and self.metrics[r.metric_name].success_direction == "higher")
            or (r.relative_change < 0 and self.metrics[r.metric_name].success_direction == "lower")
        ]

        negative_metrics = [r for r in results if r not in positive_metrics]

        return {
            "experiment_id": self.experiment_id,
            "experiment_name": self.experiment_name,
            "status": self.status.value,
            "total_metrics_analyzed": len(results),
            "significant_metrics": len(significant_metrics),
            "non_significant_metrics": len(non_significant_metrics),
            "positive_direction": len(positive_metrics),
            "negative_direction": len(negative_metrics),
            "overall_conclusion": self._determine_conclusion(results),
            "recommendation": self._get_recommendation(results),
            "detailed_results": [
                {
                    "metric": r.metric_name,
                    "control": round(r.control_value, 4),
                    "treatment": round(r.treatment_value, 4),
                    "relative_change": f"{r.relative_change:+.2f}%",
                    "p_value": f"{r.p_value:.4f}",
                    "significant": r.is_significant,
                    "direction": "✓" if r.relative_change > 0 else "✗",
                }
                for r in sorted(results, key=lambda x: x.p_value)
            ],
        }

    def _determine_conclusion(self, results: List[MetricResult]) -> str:
        """결론 결정"""
        significant_count = sum(1 for r in results if r.is_significant)
        positive_count = sum(
            1
            for r in results
            if (r.relative_change > 0 and self.metrics[r.metric_name].success_direction == "higher")
            or (r.relative_change < 0 and self.metrics[r.metric_name].success_direction == "lower")
        )

        if significant_count >= 3 and positive_count >= significant_count * 0.8:
            return "SUCCESS: Treatment significantly outperforms control"
        elif significant_count >= 1 and positive_count >= significant_count:
            return "CONDITIONAL_SUCCESS: Some metrics show improvement"
        elif positive_count > len(results) / 2:
            return "PARTIAL_SUCCESS: Most metrics show improvement but not significant"
        else:
            return "NO_SIGNIFICANT_IMPROVEMENT: Insufficient evidence for deployment"

    def _get_recommendation(self, results: List[MetricResult]) -> str:
        """권장사항"""
        conclusion = self._determine_conclusion(results)

        recommendations = {
            "SUCCESS: Treatment significantly outperforms control": "DEPLOY to 100% users",
            "CONDITIONAL_SUCCESS: Some metrics show improvement": "Optimize and retest or partial deployment",
            "PARTIAL_SUCCESS: Most metrics show improvement but not significant": "Investigate and retest with more users",
            "NO_SIGNIFICANT_IMPROVEMENT: Insufficient evidence for deployment": "Rollback and improve experiment",
        }

        return recommendations.get(conclusion, "Review analysis manually")

    def export_results(self) -> Dict[str, Any]:
        """결과 내보내기"""
        return {
            "timestamp": datetime.now().isoformat(),
            "experiment": self.get_experiment_status(),
            "analysis": self.get_analysis_summary(),
            "data_records": len(self.data),
        }


# 글로벌 AB 테스트 인스턴스
_ab_test_instance: Optional[ABTestFramework] = None


def get_ab_test_framework(
    experiment_name: str = "Phase4_vs_Phase3",
    experiment_id: str = "exp_2025_10_29",
    start_date: datetime = None,
) -> ABTestFramework:
    """A/B 테스트 프레임워크 싱글톤"""
    global _ab_test_instance

    if _ab_test_instance is None:
        if start_date is None:
            start_date = datetime.now()

        _ab_test_instance = ABTestFramework(
            experiment_name=experiment_name, experiment_id=experiment_id, start_date=start_date
        )

        # 메트릭 추가
        _ab_test_instance.add_metric(
            Metric(
                name="recommendation_accuracy",
                description="Top-2 recommendation accuracy (%)",
                metric_type="continuous",
                success_direction="higher",
                minimum_change=3.0,
                priority=1,
            )
        )

        _ab_test_instance.add_metric(
            Metric(
                name="user_satisfaction",
                description="User satisfaction score (1-5)",
                metric_type="continuous",
                success_direction="higher",
                minimum_change=0.3,
                priority=1,
            )
        )

        _ab_test_instance.add_metric(
            Metric(
                name="conversation_adoption",
                description="Conversation feature adoption rate (%)",
                metric_type="categorical",
                success_direction="higher",
                minimum_change=10.0,
                priority=2,
            )
        )

        _ab_test_instance.add_metric(
            Metric(
                name="session_duration",
                description="Average session duration (minutes)",
                metric_type="continuous",
                success_direction="higher",
                minimum_change=2.0,
                priority=2,
            )
        )

        _ab_test_instance.add_metric(
            Metric(
                name="completion_rate",
                description="Task completion rate (%)",
                metric_type="categorical",
                success_direction="higher",
                minimum_change=5.0,
                priority=2,
            )
        )

        _ab_test_instance.add_metric(
            Metric(
                name="return_rate",
                description="Return rate within 7 days (%)",
                metric_type="categorical",
                success_direction="higher",
                minimum_change=5.0,
                priority=3,
            )
        )

    return _ab_test_instance
