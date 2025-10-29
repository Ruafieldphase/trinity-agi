"""
Phase 4 - 카나리 배포 모니터링 API 엔드포인트
메트릭 조회, 헬스 체크, 배포 제어
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/canary", tags=["canary-monitoring"])


# ==================== Request/Response Models ====================


class MetricsResponse(BaseModel):
    """메트릭 응답"""

    timestamp: str = Field(..., description="타임스탬프")
    legacy: Dict[str, Any] = Field(..., description="레거시 메트릭")
    canary: Dict[str, Any] = Field(..., description="카나리 메트릭")
    comparison: Dict[str, Any] = Field(..., description="비교 메트릭")


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답"""

    status: Literal["healthy", "degraded", "unhealthy", "unknown"] = Field(
        ..., description="헬스 상태"
    )
    timestamp: str = Field(..., description="체크 시간")
    checks: Dict[str, Any] = Field(..., description="각 항목별 체크 결과")
    failures: List[str] = Field(default_factory=list, description="실패한 항목")
    recommendations: List[str] = Field(default_factory=list, description="권장사항")


class CanaryStatusResponse(BaseModel):
    """카나리 배포 상태 응답"""

    enabled: bool = Field(..., description="카나리 배포 활성화 여부")
    traffic_percentage: int = Field(..., description="카나리 트래픽 비율 (%)")
    health_status: str = Field(..., description="헬스 상태")
    last_check: Optional[str] = Field(None, description="마지막 체크 시간")
    consecutive_failures: int = Field(..., description="연속 실패 횟수")
    endpoints: List[str] = Field(..., description="카나리 배포 대상 엔드포인트")


class ConfigUpdateRequest(BaseModel):
    """설정 업데이트 요청"""

    canary_percentage: Optional[int] = Field(
        None, description="카나리 트래픽 비율 (%)", ge=0, le=100
    )
    enabled: Optional[bool] = Field(None, description="카나리 배포 활성화 여부")


# ==================== 엔드포인트 ====================


@router.get(
    "/ping",
    summary="카나리 모니터링 API 핑 테스트",
    description="라우터가 정상적으로 마운트되었는지 확인",
)
async def ping_canary_api():
    """간단한 핑 테스트 - 의존성 없음"""
    return {
        "status": "ok",
        "message": "Canary monitoring API is mounted and working",
        "timestamp": datetime.now().isoformat(),
    }


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="카나리 배포 메트릭",
    description="현재 카나리 배포 메트릭 조회 (옵션: legacy_url을 제공하면 레거시 서비스 메트릭 병합)",
)
async def get_canary_metrics(
    legacy_url: Optional[str] = Query(
        None, description="레거시 서비스의 베이스 URL (예: https://ion-api-...)"
    )
):
    """
    카나리 배포 메트릭 조회

    레거시 및 카나리 버전의 성능 메트릭을 비교 분석합니다.

    Returns:
        MetricsResponse: 메트릭 데이터
    """
    from app.middleware.canary_metrics import get_metrics_collector

    try:
        collector = get_metrics_collector()
        metrics = collector.get_metrics_summary()

        legacy_metrics_local = metrics.get("legacy", {}) or {}
        canary_metrics_local = metrics.get("canary", {}) or {}

        # 선택적으로 레거시 서비스에서 메트릭 가져와 병합
        legacy_metrics_final = dict(legacy_metrics_local)

        if legacy_url:
            try:
                import json as _json
                import urllib.request as _urlreq

                legacy_metrics_endpoint = legacy_url.rstrip("/") + "/api/v2/canary/metrics"
                req = _urlreq.Request(legacy_metrics_endpoint, method="GET")
                with _urlreq.urlopen(req, timeout=5) as resp:
                    raw = resp.read().decode("utf-8", errors="ignore")
                    parsed = _json.loads(raw)
                    # 레거시 서비스의 /metrics 응답에서 legacy 파트만 사용
                    if isinstance(parsed, dict) and "legacy" in parsed:
                        legacy_remote = parsed.get("legacy") or {}
                        if isinstance(legacy_remote, dict):
                            legacy_metrics_final = legacy_remote
                            logger.info(f"Merged legacy metrics from {legacy_metrics_endpoint}")
            except Exception as merge_err:
                logger.warning(f"Could not fetch legacy metrics from {legacy_url}: {merge_err}")

        # 비교 메트릭 재계산 (병합된 legacy + 로컬 canary 기반)
        def _to_float(val: Any, strip: str = "") -> float:
            try:
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, str):
                    v = val
                    if strip and v.endswith(strip):
                        v = v[: -len(strip)]
                    v = v.replace("%", "").strip()
                    return float(v)
            except Exception:
                return 0.0
            return 0.0

        def _compute_comparison(
            legacy_d: Dict[str, Any], canary_d: Dict[str, Any]
        ) -> Dict[str, Any]:
            lc = int(legacy_d.get("request_count", 0) or 0)
            cc = int(canary_d.get("request_count", 0) or 0)
            if lc == 0 or cc == 0:
                return {"status": "insufficient_data", "message": "Need more data for comparison"}

            le = _to_float(legacy_d.get("error_rate", "0%"))
            ce = _to_float(canary_d.get("error_rate", "0%"))
            err_diff = ce - le

            lavg = _to_float(legacy_d.get("avg_response_time_ms", "0"))
            cavg = _to_float(canary_d.get("avg_response_time_ms", "0"))
            improvement = ((lavg - cavg) / lavg * 100) if lavg > 0 else 0.0

            lp95 = _to_float(legacy_d.get("p95_response_time_ms", "0"))
            cp95 = _to_float(canary_d.get("p95_response_time_ms", "0"))

            total = lc + cc
            return {
                "error_rate_difference": f"{err_diff:+.2f}%",
                "response_time_improvement": f"{improvement:+.2f}%",
                "canary_p95_response_time": f"{cp95:.2f}ms",
                "legacy_p95_response_time": f"{lp95:.2f}ms",
                "traffic_split": {
                    "legacy_requests": lc,
                    "canary_requests": cc,
                    "legacy_percentage": f"{(lc/total*100):.1f}%",
                    "canary_percentage": f"{(cc/total*100):.1f}%",
                },
            }

        comparison = _compute_comparison(legacy_metrics_final, canary_metrics_local)

        return MetricsResponse(
            timestamp=datetime.now().isoformat(),
            legacy=legacy_metrics_final,
            canary=canary_metrics_local,
            comparison=comparison,
        )
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="카나리 헬스 체크",
    description="현재 카나리 배포의 헬스 상태 확인",
)
async def get_canary_health():
    """
    카나리 배포 헬스 체크

    SLA 기준에 따른 헬스 상태를 확인합니다:
    - Error Rate: < 0.5%
    - P95 Response Time: < 100ms
    - Availability: > 99.95%

    Returns:
        HealthCheckResponse: 헬스 체크 결과
    """
    from app.health.canary_health_check import get_health_checker

    try:
        health_checker = get_health_checker()
        health_metrics = await health_checker.perform_health_check()

        return HealthCheckResponse(
            status=health_metrics.status.value,
            timestamp=health_metrics.timestamp,
            checks=health_metrics.checks,
            failures=health_metrics.failures,
            recommendations=health_metrics.recommendations,
        )
    except Exception as e:
        logger.error(f"Error during health check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status",
    response_model=CanaryStatusResponse,
    summary="카나리 배포 상태",
    description="카나리 배포의 전체 상태 확인",
)
async def get_canary_status():
    """
    카나리 배포 상태 조회

    배포 활성화 여부, 트래픽 비율, 헬스 상태 등을 확인합니다.

    Returns:
        CanaryStatusResponse: 배포 상태
    """
    from app.health.canary_health_check import get_health_checker
    from app.routing.canary_router import get_canary_config

    try:
        config = get_canary_config()
        health_checker = get_health_checker()
        health_status = health_checker.get_current_status()

        return CanaryStatusResponse(
            enabled=config.enabled,
            traffic_percentage=config.canary_percentage,
            health_status=health_status.get("status", "unknown"),
            last_check=health_status.get("last_check"),
            consecutive_failures=health_status.get("consecutive_failures", 0),
            endpoints=config.endpoints_to_canary,
        )
    except Exception as e:
        logger.error(f"Error getting canary status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/config",
    response_model=Dict[str, Any],
    summary="카나리 배포 설정 업데이트",
    description="카나리 배포 설정 변경",
)
async def update_canary_config(request: ConfigUpdateRequest):
    """
    카나리 배포 설정 업데이트

    트래픽 비율, 활성화 여부 등을 변경할 수 있습니다.

    Args:
        request: 업데이트할 설정

    Returns:
        Dict: 업데이트된 설정
    """
    from app.routing.canary_router import get_canary_config

    try:
        config = get_canary_config()

        if request.canary_percentage is not None:
            config.update_canary_percentage(request.canary_percentage)
            logger.info(f"Updated canary percentage to {request.canary_percentage}%")

        if request.enabled is not None:
            if request.enabled:
                config.enable()
            else:
                config.disable()

        return {
            "status": "success",
            "message": "Canary configuration updated",
            "config": config.get_config_dict(),
        }
    except Exception as e:
        logger.error(f"Error updating canary config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/rollback",
    response_model=Dict[str, Any],
    summary="수동 롤백",
    description="카나리 배포 수동 롤백",
)
async def manual_rollback():
    """
    카나리 배포 수동 롤백

    긴급 상황에서 카나리 배포를 즉시 롤백합니다.

    Returns:
        Dict: 롤백 결과
    """
    from app.health.canary_health_check import HealthCheckMetrics, HealthStatus, get_health_checker

    try:
        health_checker = get_health_checker()
        logger.critical("Manual rollback requested")

        # 롤백 실행 (필수 매개변수 형식에 맞춘 더미 메트릭 전달)
        dummy_metrics = HealthCheckMetrics(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.now().isoformat(),
            checks={},
            failures=["Manual rollback requested"],
            recommendations=[],
        )
        await health_checker.trigger_rollback(dummy_metrics)

        return {
            "status": "success",
            "message": "Canary deployment rolled back",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error during manual rollback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/errors",
    response_model=Dict[str, Any],
    summary="최근 에러 조회",
    description="카나리 배포에서 발생한 최근 에러 조회",
)
async def get_recent_errors(limit: int = Query(50, ge=1, le=500)):
    """
    최근 에러 조회

    카나리 배포에서 발생한 최근 에러를 확인합니다.

    Args:
        limit: 조회할 에러 개수 (기본: 50, 최대: 500)

    Returns:
        Dict: 최근 에러 목록
    """
    from app.middleware.canary_metrics import get_metrics_collector

    try:
        collector = get_metrics_collector()
        errors = collector.get_recent_errors(limit)

        return {"count": len(errors), "errors": errors}
    except Exception as e:
        logger.error(f"Error fetching recent errors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/metrics/reset",
    response_model=Dict[str, Any],
    summary="메트릭 초기화",
    description="수집된 메트릭 초기화",
)
async def reset_metrics():
    """
    메트릭 초기화

    수집된 메트릭을 초기화합니다. (관리자용)

    Returns:
        Dict: 초기화 결과
    """
    from app.middleware.canary_metrics import get_metrics_collector

    try:
        collector = get_metrics_collector()
        collector.reset_metrics()

        logger.info("Metrics reset by administrator")

        return {
            "status": "success",
            "message": "Metrics reset successfully",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/export/json",
    response_model=Dict[str, Any],
    summary="메트릭 JSON 내보내기",
    description="모든 메트릭을 JSON 형식으로 내보내기",
)
async def export_metrics_json():
    """
    메트릭 JSON 내보내기

    모든 수집된 메트릭을 JSON 형식으로 제공합니다.

    Returns:
        Dict: 모든 메트릭 데이터
    """
    from app.middleware.canary_metrics import get_metrics_collector

    try:
        collector = get_metrics_collector()
        return collector.get_metrics_summary()
    except Exception as e:
        logger.error(f"Error exporting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
