"""
API v2 라우트

Week 11: API v2 엔드포인트
- 향상된 스키마
- 더 나은 에러 처리
- 확장 가능한 설계
- v1 호환성 유지
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import JSONResponse

from persona_system.pipeline_optimized import get_optimized_pipeline
from ..core.cache import get_cache_manager

from .v2_schemas import (
    BulkProcessRequest,
    BulkProcessResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    MultiPersonaProcessRequest,
    PersonaCapabilities,
    PersonaProcessRequest,
    PersonaProcessResponse,
    PersonaRecommendRequest,
    PersonaRecommendResponse,
    ServiceStatus,
    convert_persona_response_to_v2,
    to_dict_for_json,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["v2"])

# ==================== Helper Functions ====================


def create_request_id() -> str:
    """요청 ID 생성"""
    return str(uuid.uuid4())


def create_error_response(
    code: str,
    message: str,
    field: Optional[str] = None,
    status_code: int = 400,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """에러 응답 생성"""
    error = ErrorDetail(code=code, message=message, field=field)
    response = ErrorResponse(error=error, request_id=request_id)
    return JSONResponse(status_code=status_code, content=to_dict_for_json(response))


# (구) 멀티 페르소나 로컬 싱글톤 헬퍼는 제거되었습니다.
# 이제 모든 경로는 persona_system.pipeline_optimized.get_optimized_pipeline()
# 을 통해 일관된 캐시/메트릭 경로를 사용합니다.


# ==================== Health & Status ====================


@router.get("/health", response_model=dict)
async def health_check():
    """서비스 헬스 체크"""
    try:
        pipeline = get_optimized_pipeline()
        cache_mgr = get_cache_manager()

        # 간단한 테스트 요청
        pipeline.process("", "calm-medium-learning", use_cache=True)

        status = ServiceStatus(
            status="operational", version="2.0", cached_requests=pipeline.stats["total_requests"]
        )

        response = HealthResponse(
            healthy=True,
            service_status=status,
            dependencies={
                "pipeline": True,
                "cache": pipeline.cache is not None,
                "redis": cache_mgr.health_check() if cache_mgr else False,
                "pipeline_cache": pipeline.cache.l2.available if pipeline.cache else False,
            },
        )

        return to_dict_for_json(response)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"healthy": False, "error": str(e), "timestamp": datetime.now().isoformat()}


@router.get("/status")
async def service_status():
    """서비스 상태 조회"""
    try:
        pipeline = get_optimized_pipeline()
        stats = pipeline.get_cache_stats()

        return {
            "version": "v2.0",
            "status": "operational",
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Core Endpoints ====================


@router.post("/process", response_model=dict)
async def process_persona(request: PersonaProcessRequest, request_id: Optional[str] = None):
    """
    페르소나 처리 (v2)

    향상된 기능:
    - 구조화된 요청/응답
    - 더 나은 메타데이터
    - 성능 정보 포함
    - 캐싱 지원 (Redis)

    Example:
    ```json
    {
        "user_input": "도움이 필요합니다",
        "resonance_key": {
            "tone": "frustrated",
            "pace": "burst",
            "intent": "seeking_advice"
        },
        "use_cache": true
    }
    ```
    """
    req_id = request_id or create_request_id()

    try:
        # 입력 검증
        if not request.user_input or len(request.user_input.strip()) == 0:
            return create_error_response(
                code="INVALID_INPUT",
                message="User input cannot be empty",
                field="user_input",
                request_id=req_id,
            )

        # 캐시 확인 (use_cache가 True인 경우)
        cache_mgr = get_cache_manager()
        cache_status = "MISS"
        
        if request.use_cache and cache_mgr:
            cache_data = {
                "user_input": request.user_input,
                "resonance_key": request.resonance_key.to_string(),
                "context": request.context.to_chat_context() if request.context else None,
            }
            
            cached_response = cache_mgr.get("/api/v2/process", cache_data)
            if cached_response and isinstance(cached_response, dict):
                logger.debug(f"Cache HIT for request {req_id}")
                cache_status = "HIT"
                cached_response["request_id"] = req_id
                cached_response["_cache_status"] = cache_status
                return cached_response

        # 파이프라인 획득
        pipeline = get_optimized_pipeline()

        # 컨텍스트 변환
        context = None
        if request.context:
            context = request.context.to_chat_context()

        # 파동키 문자열 생성
        resonance_key = request.resonance_key.to_string()

        # 처리
        persona_response = pipeline.process(
            user_input=request.user_input,
            resonance_key=resonance_key,
            context=context,
            use_cache=request.use_cache,
            prompt_mode=getattr(request, "prompt_mode", None),
        )

        # v2 응답으로 변환
        response = convert_persona_response_to_v2(persona_response)
        response.request_id = req_id

        # Redis 캐싱 (use_cache가 True인 경우)
        if request.use_cache and cache_mgr:
            cache_data = {
                "user_input": request.user_input,
                "resonance_key": request.resonance_key.to_string(),
                "context": context,
            }
            response_dict = to_dict_for_json(response)
            cache_mgr.set("/api/v2/process", cache_data, response_dict, ttl=3600)
            logger.debug(f"Cached response for request {req_id}")

        # 성능 메트릭이 없을 수도 있으니 안전하게 로깅
        exec_ms = None
        if getattr(response, "performance", None) is not None:
            exec_ms = getattr(response.performance, "execution_time_ms", None)

        exec_str = f"{exec_ms:.0f}ms" if isinstance(exec_ms, (int, float)) else "n/a"
        logger.info(
            f"Process request: persona={response.persona_used}, time={exec_str}, cache={cache_status}, req_id={req_id}"
        )

        result = to_dict_for_json(response)
        result["_cache_status"] = cache_status
        return result

    except Exception as e:
        logger.error(f"Process error: {str(e)}", exc_info=True)
        return create_error_response(
            code="PROCESS_ERROR", message=str(e), status_code=500, request_id=req_id
        )


@router.post("/chat/multi-persona", response_model=dict)
async def process_multi_persona(
    request: MultiPersonaProcessRequest, request_id: Optional[str] = None
):
    """
    멀티 페르소나 처리 (v2)

    - 입력 복잡도를 분석하여 자동으로 Single/Multi 실행 선택
    - force_multi=true로 강제 멀티 실행 가능
    - 결과는 v2 공통 응답 구조(PersonaProcessResponse)에 맞춰 반환
    """
    req_id = request_id or create_request_id()

    try:
        if not request.user_input or len(request.user_input.strip()) == 0:
            return create_error_response(
                code="INVALID_INPUT",
                message="User input cannot be empty",
                field="user_input",
                request_id=req_id,
            )

        # 최적화 파이프라인에 위임 (캐시/메트릭 일관성)
        pipeline = get_optimized_pipeline()

        # 멀티 페르소나 처리 실행
        mp_response = pipeline.process_multi_persona(
            user_input=request.user_input.strip(), force_multi=bool(request.force_multi)
        )

        # v2 응답 스키마로 변환 (수동 매핑)
        v2_resp = PersonaProcessResponse(
            success=True,
            content=mp_response.content,
            persona_used=mp_response.persona_used,
            resonance_key=getattr(mp_response, "resonance_key", "multi-persona-blend"),
            routing=None,
            confidence=getattr(mp_response, "confidence", 0.95),
            performance=None,
            metadata=getattr(mp_response, "metadata", {}),
        )
        v2_resp.request_id = req_id

        logger.info(f"Multi-persona: persona={v2_resp.persona_used}, req_id={req_id}")

        return to_dict_for_json(v2_resp)

    except Exception as e:
        logger.error(f"Multi-persona error: {str(e)}", exc_info=True)
        return create_error_response(
            code="MULTI_PERSONA_ERROR", message=str(e), status_code=500, request_id=req_id
        )


@router.post("/recommend")
async def recommend_persona(request: PersonaRecommendRequest, request_id: Optional[str] = None):
    """
    페르소나 추천 (v2)

    시나리오를 기반으로 최적의 페르소나 추천

    Example:
    ```json
    {
        "scenario": "사용자가 감정적 지원이 필요합니다",
        "context": {
            "user_id": "user123"
        }
    }
    ```
    """
    req_id = request_id or create_request_id()

    try:
        if not request.scenario or len(request.scenario.strip()) == 0:
            return create_error_response(
                code="INVALID_INPUT",
                message="Scenario cannot be empty",
                field="scenario",
                request_id=req_id,
            )

        pipeline = get_optimized_pipeline()

        # 추천 획득
        recommendation = pipeline.recommend_persona(request.scenario)

        # 추천 응답 생성
        persona_name = recommendation["recommended_persona"]
        capabilities = pipeline.get_persona_capabilities(persona_name)

        response = PersonaRecommendResponse(
            recommended_persona=persona_name,
            scores=recommendation["scores"],
            capabilities=PersonaCapabilities(
                name=capabilities["name"],
                traits=capabilities["traits"],
                strengths=capabilities["strengths"],
                best_for_tones=capabilities["best_for_tones"],
                best_for_paces=capabilities["best_for_paces"],
                best_for_intents=capabilities["best_for_intents"],
            ),
            reasoning=f"Best persona for: {request.scenario}",
        )

        logger.info(f"Recommendation: {persona_name}, req_id={req_id}")

        return to_dict_for_json(response)

    except Exception as e:
        logger.error(f"Recommendation error: {str(e)}", exc_info=True)
        return create_error_response(
            code="RECOMMENDATION_ERROR", message=str(e), status_code=500, request_id=req_id
        )


@router.post("/bulk-process")
async def bulk_process(request: BulkProcessRequest, request_id: Optional[str] = None):
    """
    일괄 처리 (v2)

    여러 요청을 한 번에 처리

    Example:
    ```json
    {
        "requests": [
            {
                "user_input": "첫 번째",
                "resonance_key": {"tone": "calm", "pace": "medium", "intent": "learning"}
            },
            {
                "user_input": "두 번째",
                "resonance_key": {"tone": "frustrated", "pace": "burst", "intent": "seeking_advice"}
            }
        ],
        "parallel": true
    }
    ```
    """
    req_id = request_id or create_request_id()

    try:
        if not request.requests or len(request.requests) == 0:
            return create_error_response(
                code="INVALID_INPUT",
                message="Requests list cannot be empty",
                field="requests",
                request_id=req_id,
            )

        if len(request.requests) > 100:
            return create_error_response(
                code="REQUEST_TOO_LARGE",
                message="Maximum 100 requests per batch",
                status_code=413,
                request_id=req_id,
            )

        pipeline = get_optimized_pipeline()
        results = []
        errors = []

        for idx, req in enumerate(request.requests):
            try:
                # 처리
                persona_response = pipeline.process(
                    user_input=req.user_input,
                    resonance_key=req.resonance_key.to_string(),
                    context=req.context.to_chat_context() if req.context else None,
                    use_cache=req.use_cache,
                )

                # v2 응답으로 변환
                response = convert_persona_response_to_v2(persona_response)
                response.request_id = f"{req_id}-{idx}"
                results.append(response)

            except Exception as e:
                logger.error(f"Bulk process error at {idx}: {str(e)}")
                errors.append(f"Request {idx}: {str(e)}")

        # 일괄 응답 생성
        bulk_response = BulkProcessResponse(
            success=len(errors) == 0,
            total=len(request.requests),
            successful=len(results),
            failed=len(errors),
            results=results,
            errors=errors if errors else None,
        )

        logger.info(
            f"Bulk process: total={len(request.requests)}, "
            f"success={len(results)}, failed={len(errors)}, "
            f"req_id={req_id}"
        )

        return to_dict_for_json(bulk_response)

    except Exception as e:
        logger.error(f"Bulk process error: {str(e)}", exc_info=True)
        return create_error_response(
            code="BULK_PROCESS_ERROR", message=str(e), status_code=500, request_id=req_id
        )


# ==================== Info Endpoints ====================


@router.get("/personas")
async def list_personas():
    """
    사용 가능한 페르소나 목록

    모든 페르소나와 그 능력 정보 반환
    """
    try:
        pipeline = get_optimized_pipeline()
        all_info = pipeline.get_all_personas_info()

        personas = []
        for name, info in all_info.items():
            personas.append(
                {
                    "name": name,
                    "traits": info["traits"],
                    "strengths": info["strengths"],
                    "best_for_tones": info["best_for_tones"],
                    "best_for_paces": info["best_for_paces"],
                    "best_for_intents": info["best_for_intents"],
                }
            )

        return {
            "total": len(personas),
            "personas": personas,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"List personas error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personas/{persona_name}")
async def get_persona_info(persona_name: str = Path(...)):
    """
    특정 페르소나 정보 조회

    Args:
        persona_name: 페르소나 이름 (lua, elro, riri, nana)
    """
    try:
        pipeline = get_optimized_pipeline()

        if persona_name.lower() not in ["lua", "elro", "riri", "nana"]:
            return create_error_response(
                code="INVALID_PERSONA",
                message=f"Unknown persona: {persona_name}",
                field="persona_name",
                status_code=404,
            )

        # 첫 글자 대문자로 변환
        persona_key = persona_name.capitalize()
        info = pipeline.get_persona_capabilities(persona_key)

        return {
            "name": info["name"],
            "traits": info["traits"],
            "strengths": info["strengths"],
            "best_for_tones": info["best_for_tones"],
            "best_for_paces": info["best_for_paces"],
            "best_for_intents": info["best_for_intents"],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Get persona info error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache-stats")
async def get_cache_stats():
    """
    캐시 통계 조회

    L1/L2 캐시의 성능 메트릭 + Redis 캐시 메트릭
    """
    try:
        pipeline = get_optimized_pipeline()
        cache_mgr = get_cache_manager()
        
        pipeline_stats = pipeline.get_cache_stats()
        
        result = {
            **pipeline_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        # Redis 캐시 통계 추가
        if cache_mgr:
            redis_stats = cache_mgr.get_stats()
            if redis_stats:
                result["redis_cache"] = redis_stats

        return result

    except Exception as e:
        logger.error(f"Cache stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Admin Endpoints ====================


@router.post("/cache/clear")
async def clear_cache():
    """
    캐시 전체 삭제 (관리자용)
    """
    try:
        pipeline = get_optimized_pipeline()
        pipeline.clear_cache()

        return {
            "success": True,
            "message": "Cache cleared",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Clear cache error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate")
async def invalidate_cache_pattern(pattern: str = Query(...)):
    """
    패턴 기반 캐시 무효화 (관리자용)

    Args:
        pattern: 무효화할 키 패턴 (예: "persona:lua:*")
    """
    try:
        pipeline = get_optimized_pipeline()
        deleted = pipeline.invalidate_cache_pattern(pattern)

        return {
            "success": True,
            "pattern": pattern,
            "deleted_count": deleted,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Invalidate cache error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
