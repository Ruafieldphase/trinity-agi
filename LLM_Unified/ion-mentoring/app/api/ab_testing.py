"""
Phase 4 - A/B 테스트 API 엔드포인트
실험 관리 및 결과 조회
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/experiments", tags=["ab-testing"])


# ==================== Request/Response Models ====================


class RecordMetricRequest(BaseModel):
    """메트릭 기록 요청"""

    user_id: str = Field(..., description="사용자 ID")
    metric_name: str = Field(..., description="메트릭 이름")
    value: float = Field(..., description="메트릭 값")
    session_id: Optional[str] = Field(None, description="세션 ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")


class ExperimentStatusResponse(BaseModel):
    """실험 상태 응답"""

    experiment_id: str = Field(..., description="실험 ID")
    experiment_name: str = Field(..., description="실험 이름")
    status: str = Field(..., description="상태")
    start_date: str = Field(..., description="시작 날짜")
    total_records: int = Field(..., description="총 데이터 개수")
    control_records: int = Field(..., description="컨트롤 그룹 데이터")
    treatment_records: int = Field(..., description="처리 그룹 데이터")
    metrics_count: int = Field(..., description="메트릭 개수")
    traffic_split: Dict[str, str] = Field(..., description="트래픽 분배")


class MetricStatisticsResponse(BaseModel):
    """메트릭 통계 응답"""

    metric_name: str = Field(..., description="메트릭 이름")
    control: Dict[str, Any] = Field(..., description="컨트롤 그룹 통계")
    treatment: Dict[str, Any] = Field(..., description="처리 그룹 통계")
    results: Dict[str, Any] = Field(..., description="분석 결과")


class AnalysisSummaryResponse(BaseModel):
    """분석 요약 응답"""

    experiment_id: str = Field(..., description="실험 ID")
    experiment_name: str = Field(..., description="실험 이름")
    total_metrics_analyzed: int = Field(..., description="분석 메트릭 개수")
    significant_metrics: int = Field(..., description="통계적 유의 메트릭")
    non_significant_metrics: int = Field(..., description="통계적 미유의 메트릭")
    positive_direction: int = Field(..., description="긍정 방향 메트릭")
    negative_direction: int = Field(..., description="부정 방향 메트릭")
    overall_conclusion: str = Field(..., description="전체 결론")
    recommendation: str = Field(..., description="권장사항")


# ==================== 엔드포인트 ====================


@router.post(
    "/record",
    response_model=Dict[str, Any],
    summary="메트릭 기록",
    description="A/B 테스트 메트릭 기록",
)
async def record_metric(request: RecordMetricRequest):
    """
    메트릭 기록

    A/B 테스트 중 사용자 메트릭을 기록합니다.
    사용자는 자동으로 Control 또는 Treatment 그룹에 할당됩니다.

    Args:
        request: 메트릭 기록 요청

    Returns:
        Dict: 기록 결과
    """
    from app.experiments.ab_test_framework import get_ab_test_framework

    try:
        framework = get_ab_test_framework()

        framework.record_data(
            user_id=request.user_id,
            metric_name=request.metric_name,
            value=request.value,
            session_id=request.session_id or "",
            metadata=request.metadata or {},
        )

        return {
            "status": "success",
            "message": "Metric recorded successfully",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error recording metric: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status",
    response_model=ExperimentStatusResponse,
    summary="실험 상태",
    description="A/B 테스트 실험 상태 조회",
)
async def get_experiment_status():
    """
    실험 상태 조회

    현재 진행 중인 A/B 테스트의 상태를 조회합니다.

    Returns:
        ExperimentStatusResponse: 실험 상태
    """
    from app.experiments.ab_test_framework import get_ab_test_framework

    try:
        framework = get_ab_test_framework()
        status = framework.get_experiment_status()

        return ExperimentStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting experiment status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/metrics/{metric_name}",
    response_model=MetricStatisticsResponse,
    summary="메트릭 통계",
    description="특정 메트릭의 통계 분석",
)
async def get_metric_statistics(metric_name: str):
    """
    메트릭 통계 조회

    특정 메트릭의 Control vs Treatment 비교 분석을 조회합니다.

    Args:
        metric_name: 메트릭 이름

    Returns:
        MetricStatisticsResponse: 통계 분석 결과
    """
    from app.experiments.ab_test_framework import get_ab_test_framework

    try:
        framework = get_ab_test_framework()

        if metric_name not in framework.metrics:
            raise HTTPException(status_code=404, detail=f"Metric '{metric_name}' not found")

        stats = framework.calculate_metric_statistics(metric_name)

        if stats.get("status") == "insufficient_data":
            raise HTTPException(status_code=400, detail="Insufficient data for analysis")

        return MetricStatisticsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metric statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis",
    response_model=AnalysisSummaryResponse,
    summary="전체 분석 요약",
    description="모든 메트릭의 종합 분석 요약",
)
async def get_analysis_summary():
    """
    전체 분석 요약

    모든 메트릭의 종합 분석 결과 및 결론을 조회합니다.

    Returns:
        AnalysisSummaryResponse: 분석 요약
    """
    from app.experiments.ab_test_framework import get_ab_test_framework

    try:
        framework = get_ab_test_framework()
        summary = framework.get_analysis_summary()

        return AnalysisSummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Error getting analysis summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/report",
    response_model=Dict[str, Any],
    summary="최종 보고서",
    description="A/B 테스트 최종 분석 보고서",
)
async def get_final_report():
    """
    최종 보고서 조회

    A/B 테스트의 최종 분석 보고서를 조회합니다.

    Returns:
        Dict: 최종 보고서 데이터
    """
    from app.experiments.ab_test_framework import get_ab_test_framework

    try:
        framework = get_ab_test_framework()
        results = framework.export_results()

        return {
            "timestamp": datetime.now().isoformat(),
            "experiment": results["experiment"],
            "analysis": results["analysis"],
            "data_records": results["data_records"],
        }
    except Exception as e:
        logger.error(f"Error generating final report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/metrics/reset",
    response_model=Dict[str, Any],
    summary="데이터 초기화",
    description="수집된 메트릭 데이터 초기화 (관리자용)",
)
async def reset_metrics():
    """
    메트릭 데이터 초기화

    수집된 모든 메트릭 데이터를 초기화합니다. (관리자용)

    Returns:
        Dict: 초기화 결과
    """
    from app.experiments.ab_test_framework import get_ab_test_framework

    try:
        get_ab_test_framework()

        # 새로운 인스턴스로 리셋
        from app.experiments import ab_test_framework

        ab_test_framework._ab_test_instance = None

        logger.info("Metrics data reset by administrator")

        return {
            "status": "success",
            "message": "Metrics data reset successfully",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/metrics/list",
    response_model=Dict[str, Any],
    summary="메트릭 목록",
    description="A/B 테스트에 정의된 메트릭 목록",
)
async def list_metrics():
    """
    메트릭 목록 조회

    A/B 테스트에 정의된 모든 메트릭의 목록을 조회합니다.

    Returns:
        Dict: 메트릭 목록
    """
    from app.experiments.ab_test_framework import get_ab_test_framework

    try:
        framework = get_ab_test_framework()

        metrics_list = [
            {
                "name": metric.name,
                "description": metric.description,
                "type": metric.metric_type,
                "success_direction": metric.success_direction,
                "minimum_change": metric.minimum_change,
                "priority": metric.priority,
            }
            for metric in framework.metrics.values()
        ]

        return {"total_metrics": len(metrics_list), "metrics": metrics_list}
    except Exception as e:
        logger.error(f"Error listing metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/configuration",
    response_model=Dict[str, Any],
    summary="테스트 설정",
    description="A/B 테스트 설정 정보",
)
async def get_test_configuration():
    """
    테스트 설정 조회

    A/B 테스트의 통계적 설정을 조회합니다.

    Returns:
        Dict: 설정 정보
    """
    from app.experiments.ab_test_framework import ABTestFramework

    return {
        "significance_level": ABTestFramework.SIGNIFICANCE_LEVEL,
        "confidence_level": f"{(1 - ABTestFramework.SIGNIFICANCE_LEVEL) * 100}%",
        "statistical_power": ABTestFramework.STATISTICAL_POWER,
        "power_level": f"{ABTestFramework.STATISTICAL_POWER * 100}%",
        "traffic_split": {"control": "50%", "treatment": "50%"},
        "test_type": "Two-sample t-test (independent samples)",
        "alternative_hypothesis": "Two-sided (treatment ≠ control)",
    }
