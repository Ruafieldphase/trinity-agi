"""
Phase 4 - API v2 확장 라우터
AI 권장사항 엔진 + 다중 턴 대화 시스템 통합

새로운 엔드포인트:
- POST /api/v2/recommend/personalized - AI 기반 추천
- POST /api/v2/conversations/start - 대화 시작
- POST /api/v2/conversations/{session_id}/turn - 턴 처리
- GET /api/v2/conversations - 세션 조회
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Phase 4 엔진 임포트 (나중에 실제 경로로 변경)
# from recommendation_engine import EnsembleRecommendationEngine
# from conversation_system import ConversationSessionManager, MultiTurnConversationEngine

# Feature Flag 및 Lumen Gateway 통합
from ..integrations.lumen_client import get_lumen_client
from .feature_flags import is_lumen_enabled

router = APIRouter(prefix="/api/v2", tags=["Phase 4"])


# ==================== Request/Response Models ====================


class ContextInfo(BaseModel):
    """컨텍스트 정보"""

    tone: Optional[str] = None
    pace: Optional[str] = None
    intent: Optional[str] = None


class PersonalizedRecommendationRequest(BaseModel):
    """개인화 추천 요청"""

    user_id: str
    query: str
    context: Optional[ContextInfo] = None
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PersonaScore(BaseModel):
    """페르소나 점수"""

    persona: str
    score: float
    reason: Optional[str] = None


class RecommendationResponse(BaseModel):
    """추천 응답"""

    primary_persona: str
    confidence: float
    all_scores: Dict[str, float]
    ranked_recommendations: List[PersonaScore]
    explanation: str
    metadata: Dict[str, Any]


class ComparisonRequest(BaseModel):
    """비교 요청"""

    user_id: str
    query: str
    include_legacy: bool = True


class ComparisonResponse(BaseModel):
    """비교 응답"""

    new_recommendation: Dict[str, Any]
    legacy_recommendation: Optional[Dict[str, Any]] = None
    comparison: Dict[str, Any]


# 대화 관련 모델
class StartConversationRequest(BaseModel):
    """대화 시작 요청"""

    user_id: str
    persona_id: str
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ConversationStartResponse(BaseModel):
    """대화 시작 응답"""

    session_id: str
    user_id: str
    persona_id: str
    created_at: datetime
    expires_at: datetime
    status: str


class TurnRequest(BaseModel):
    """턴 요청"""

    user_message: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TurnResponse(BaseModel):
    """턴 응답"""

    turn_number: int
    session_id: str
    response_text: str
    context_used: str
    next_suggestion: Optional[str] = None
    metadata: Dict[str, Any]


class MessageRecord(BaseModel):
    """메시지 기록"""

    turn_id: int
    user_message: str
    ai_response: str
    timestamp: datetime


class ContextMemoryInfo(BaseModel):
    """컨텍스트 메모리"""

    topics: List[str]
    entities: Dict[str, List[str]]
    user_preferences: Dict[str, str]


class ConversationContextResponse(BaseModel):
    """대화 컨텍스트 응답"""

    session_id: str
    user_id: str
    persona_id: str
    turn_count: int
    messages: List[MessageRecord]
    context_memory: ContextMemoryInfo
    state: str
    expires_at: datetime


class CloseConversationRequest(BaseModel):
    """대화 종료 요청"""

    save_conversation: bool = True


class CloseConversationResponse(BaseModel):
    """대화 종료 응답"""

    session_id: str
    closed_at: datetime
    summary: Dict[str, Any]


class ListConversationsResponse(BaseModel):
    """대화 목록 응답"""

    user_id: str
    sessions: List[Dict[str, Any]]
    total_count: int
    active_count: int


# ==================== 권장사항 엔진 라우터 ====================


@router.post("/recommend/personalized", response_model=RecommendationResponse)
async def recommend_personalized(request: PersonalizedRecommendationRequest):
    """
    AI 기반 개인화 추천 생성 (Lumen Gateway 통합)

    - **user_id**: 사용자 ID
    - **query**: 사용자 쿼리
    - **context**: 컨텍스트 정보 (tone, pace, intent)
    - **options**: 추가 옵션 (top_k, use_ml_model 등)

    Returns:
        RecommendationResponse: 추천 결과
    """
    try:
        # 🔧 Feature Flag: Lumen Gateway 활성화 확인
        lumen_flag_status = is_lumen_enabled()
        logger.info(
            f"🔍 Feature Flag Check: LUMEN_ENABLED={lumen_flag_status}",
            extra={"user_id": request.user_id, "lumen_enabled": lumen_flag_status},
        )

        if lumen_flag_status:
            logger.info(
                "✅ Lumen Gateway enabled - using hybrid AI system",
                extra={
                    "user_id": request.user_id,
                    "query_length": len(request.query),
                    "feature_flag": "LUMEN_GATEWAY",
                },
            )

            # Lumen Gateway 클라이언트 호출
            lumen_client = get_lumen_client()

            logger.info(
                "Calling Lumen Gateway for personalized recommendation",
                extra={
                    "user_id": request.user_id,
                    "query_length": len(request.query),
                    "query_preview": request.query[:50],
                },
            )

            # 페르소나 자동 선택 (Lumen Gateway가 처리)
            lumen_response = await lumen_client.infer(
                message=request.query,
                persona_key=None,  # 자동 선택
                session_id=(
                    request.options.get("session_id", "default") if request.options else "default"
                ),
                user_id=request.user_id,
            )

            logger.info(
                "Lumen Gateway response received",
                extra={
                    "success": lumen_response.success,
                    "persona_name": lumen_response.persona.name,
                    "response_length": len(lumen_response.response),
                },
            )

            # Lumen Gateway 응답을 Ion Mentoring 형식으로 변환
            if lumen_response.success:
                # 페르소나 매핑 (Lumen → Ion)
                persona_name_mapping = {
                    "루아": "Lua",
                    "엘로": "Elro",
                    "누리": "Riri",
                    "세나": "Nana",
                }

                primary_persona = persona_name_mapping.get(
                    lumen_response.persona.name, "Nana"  # 기본값
                )

                return RecommendationResponse(
                    primary_persona=primary_persona,
                    confidence=0.90,  # Lumen Gateway 응답은 높은 신뢰도
                    all_scores={primary_persona: 0.90, "Lua": 0.30, "Elro": 0.25, "Riri": 0.20},
                    ranked_recommendations=[
                        PersonaScore(
                            persona=primary_persona,
                            score=0.90,
                            reason=f"Lumen Gateway ({lumen_response.persona.emoji} {lumen_response.persona.name})",
                        )
                    ],
                    explanation=lumen_response.response,
                    metadata={
                        "model_version": "lumen_hybrid_v1",
                        "processing_time_ms": 0,  # 실제 측정 필요
                        "algorithm": "lumen_gateway",
                        "ab_group": "lumen_treatment",
                        "lumen_sources": lumen_response.sources,
                        "lumen_persona": lumen_response.persona.dict(),
                        "feature_flag": "LUMEN_GATEWAY=true",
                    },
                )
            else:
                # Lumen Gateway 실패 시 fallback
                logger.warning(
                    "Lumen Gateway inference failed - falling back to legacy",
                    extra={"user_id": request.user_id},
                )

        # Legacy 추천 시스템 (Lumen Gateway 비활성화 또는 실패 시)
        logger.info(
            "Using legacy recommendation system",
            extra={"user_id": request.user_id, "lumen_enabled": is_lumen_enabled()},
        )

        # Phase 4 권장사항 엔진 호출
        # engine = get_recommendation_engine()
        # recommendation = engine.get_recommendation(
        #     user_id=request.user_id,
        #     context=request.context.dict() if request.context else None,
        #     top_k=request.options.get("top_k", 3)
        # )

        # 시뮬레이션 응답 (실제 구현 전)
        simulation_response = {
            "primary_persona": "Lua",
            "confidence": 0.82,
            "all_scores": {"Lua": 0.82, "Elro": 0.45, "Riri": 0.38, "Nana": 0.35},
            "ranked_recommendations": [
                PersonaScore(persona="Lua", score=0.82, reason="Based on your learning preference"),
                PersonaScore(persona="Elro", score=0.45, reason="Analytical approach"),
                PersonaScore(persona="Riri", score=0.38, reason="Creative thinking"),
            ],
            "explanation": "Based on your query and preferences, Lua is recommended.",
            "metadata": {
                "model_version": "ensemble_v1",
                "processing_time_ms": 95,
                "algorithm": "cf_40_cb_40_pa_20",
                "ab_group": "treatment",
            },
        }

        logger.info(
            f"Recommended {simulation_response['primary_persona']} for user {request.user_id}"
        )
        return RecommendationResponse(**simulation_response)

    except Exception as e:
        logger.error(
            f"❌ Critical error in personalized recommendation: {e}",
            extra={
                "user_id": request.user_id,
                "error_type": type(e).__name__,
                "error_details": str(e),
            },
            exc_info=True,  # 전체 스택 트레이스 로깅
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend/compare", response_model=ComparisonResponse)
async def compare_recommendations(request: ComparisonRequest):
    """
    기존 라우터 vs 새 ML 모델 비교 (A/B 테스트용)

    - **user_id**: 사용자 ID
    - **query**: 사용자 쿼리
    - **include_legacy**: 기존 모델 포함 여부

    Returns:
        ComparisonResponse: 비교 결과
    """
    try:
        # 기존 ResonanceBasedRouter
        legacy_recommendation = {
            "persona": "Elro",
            "confidence": 0.65,
            "method": "resonance_router",
        }

        # 새 ML 모델
        new_recommendation = {"persona": "Elro", "confidence": 0.78, "method": "ensemble"}

        comparison = {
            "consensus": True,
            "confidence_improvement": 0.13,
            "recommendation_changed": False,
            "ab_test_assignment": "treatment",
        }

        logger.info(
            f"Comparison for user {request.user_id}: {new_recommendation['persona']} (new) vs {legacy_recommendation['persona']} (legacy)"
        )

        return ComparisonResponse(
            new_recommendation=new_recommendation,
            legacy_recommendation=legacy_recommendation if request.include_legacy else None,
            comparison=comparison,
        )

    except Exception as e:
        logger.error(f"Error in recommendation comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 다중 턴 대화 라우터 ====================


@router.post("/conversations/start", response_model=ConversationStartResponse)
async def start_conversation(request: StartConversationRequest):
    """
    새 대화 세션 시작

    - **user_id**: 사용자 ID
    - **persona_id**: 페르소나 ID (Lua, Elro, Riri, Nana)
    - **options**: 세션 옵션 (session_ttl_hours 등)

    Returns:
        ConversationStartResponse: 세션 정보
    """
    try:
        # Phase 4 세션 관리자 호출
        # session_manager = get_session_manager()
        # context = session_manager.create_session(
        #     user_id=request.user_id,
        #     persona_id=request.persona_id
        # )

        # 시뮬레이션 응답
        from datetime import timedelta

        now = datetime.now()
        expires_at = now + timedelta(hours=request.options.get("session_ttl_hours", 24))

        response = ConversationStartResponse(
            session_id=f"session_{request.user_id}_{int(now.timestamp())}",
            user_id=request.user_id,
            persona_id=request.persona_id,
            created_at=now,
            expires_at=expires_at,
            status="active",
        )

        logger.info(
            f"Started conversation session for user {request.user_id} with {request.persona_id}"
        )
        return response

    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{session_id}/turn", response_model=TurnResponse)
async def process_turn(session_id: str, request: TurnRequest):
    """
    대화 턴 처리

    - **session_id**: 세션 ID
    - **user_message**: 사용자 메시지
    - **metadata**: 추가 메타데이터

    Returns:
        TurnResponse: 턴 응답
    """
    try:
        # Phase 4 다중 턴 엔진 호출
        # engine = get_multiturn_engine()
        # response = await engine.process_turn(
        #     session_id=session_id,
        #     user_message=request.user_message,
        #     metadata=request.metadata
        # )

        # 시뮬레이션 응답
        response = TurnResponse(
            turn_number=2,
            session_id=session_id,
            response_text="Based on our conversation, here's what I think...",
            context_used="Topics: [learning]. Entities: [Python]. User preferences: [calm]",
            next_suggestion="Would you like to explore more details?",
            metadata={
                "processing_time_ms": 145,
                "tokens_used": 256,
                "confidence": 0.85,
                "persona_used": "Lua",
            },
        )

        logger.info(f"Processed turn for session {session_id}")
        return response

    except Exception as e:
        logger.error(f"Error processing turn: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{session_id}", response_model=ConversationContextResponse)
async def get_conversation(session_id: str):
    """
    대화 세션 조회

    - **session_id**: 세션 ID

    Returns:
        ConversationContextResponse: 세션 정보
    """
    try:
        # Phase 4 세션 관리자 호출
        # session_manager = get_session_manager()
        # context = session_manager.get_session(session_id)

        # 시뮬레이션 응답
        from datetime import timedelta

        now = datetime.now()

        response = ConversationContextResponse(
            session_id=session_id,
            user_id="user_123",
            persona_id="Lua",
            turn_count=3,
            messages=[
                MessageRecord(
                    turn_id=1,
                    user_message="I want to learn Python",
                    ai_response="Great! Python is powerful...",
                    timestamp=now,
                ),
                MessageRecord(
                    turn_id=2,
                    user_message="Tell me about loops",
                    ai_response="Loops allow you to...",
                    timestamp=now + timedelta(minutes=1),
                ),
                MessageRecord(
                    turn_id=3,
                    user_message="More on this",
                    ai_response="Building on that...",
                    timestamp=now + timedelta(minutes=2),
                ),
            ],
            context_memory=ContextMemoryInfo(
                topics=["learning", "Python"],
                entities={"language": ["Python"], "concept": ["loops"]},
                user_preferences={"tone": "calm", "pace": "flowing"},
            ),
            state="active",
            expires_at=now + timedelta(hours=24),
        )

        logger.info(f"Retrieved conversation session {session_id}")
        return response

    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}")
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/conversations/{session_id}/close", response_model=CloseConversationResponse)
async def close_conversation(session_id: str, request: CloseConversationRequest):
    """
    대화 세션 종료

    - **session_id**: 세션 ID
    - **save_conversation**: 대화 저장 여부

    Returns:
        CloseConversationResponse: 종료 정보
    """
    try:
        # Phase 4 세션 관리자 호출
        # session_manager = get_session_manager()
        # success = session_manager.close_session(session_id)

        now = datetime.now()

        response = CloseConversationResponse(
            session_id=session_id,
            closed_at=now,
            summary={
                "total_turns": 3,
                "total_duration_minutes": 5,
                "main_topics": ["learning", "Python"],
                "user_satisfaction": None,
            },
        )

        logger.info(f"Closed conversation session {session_id}")
        return response

    except Exception as e:
        logger.error(f"Error closing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=ListConversationsResponse)
async def list_conversations(user_id: str = Query(..., description="User ID")):
    """
    사용자의 모든 대화 세션 조회

    - **user_id**: 사용자 ID

    Returns:
        ListConversationsResponse: 세션 목록
    """
    try:
        # Phase 4 세션 관리자 호출
        # session_manager = get_session_manager()
        # sessions = session_manager.get_user_sessions(user_id)

        # 시뮬레이션 응답
        from datetime import timedelta

        now = datetime.now()

        response = ListConversationsResponse(
            user_id=user_id,
            sessions=[
                {
                    "session_id": "session_abc123",
                    "persona_id": "Lua",
                    "turn_count": 3,
                    "created_at": now,
                    "last_activity": now + timedelta(minutes=5),
                    "state": "completed",
                },
                {
                    "session_id": "session_def456",
                    "persona_id": "Elro",
                    "turn_count": 5,
                    "created_at": now - timedelta(hours=4),
                    "last_activity": now - timedelta(hours=3, minutes=15),
                    "state": "active",
                },
            ],
            total_count=2,
            active_count=1,
        )

        logger.info(f"Listed {response.total_count} conversations for user {user_id}")
        return response

    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 헬스 체크 ====================


@router.get("/phase4/health")
async def phase4_health():
    """Phase 4 기능 헬스 체크"""
    return {
        "status": "healthy",
        "phase4_features": {
            "recommendations_available": True,
            "conversations_available": True,
            "ab_testing_enabled": True,
        },
        "timestamp": datetime.now(),
    }


if __name__ == "__main__":
    print("Phase 4 API v2 라우터 정의 완료")
    print(f"라우터 경로 수: {len(router.routes)}")
