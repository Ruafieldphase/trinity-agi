# -*- coding: utf-8 -*-
"""
Lumen Gateway Integration Routes

ION API에서 Lumen Gateway를 호출하는 통합 라우터
"""

import logging
import os
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/lumen",
    tags=["lumen"],
    responses={503: {"description": "Lumen Gateway unavailable"}},
)

# Lumen Gateway URL (환경변수로 설정 가능)
LUMEN_GATEWAY_URL = os.getenv(
    "LUMEN_GATEWAY_URL", "https://lumen-gateway-staging-64076350717.us-central1.run.app"
)


# Request/Response Models
class LumenChatRequest(BaseModel):
    """Lumen 채팅 요청"""

    message: str = Field(..., min_length=1, description="User message")
    persona: Optional[str] = Field(
        None, description="Force specific persona (moon/square/earth/pen)"
    )
    user_id: Optional[str] = Field(None, description="User ID for tracking")


class LumenChatResponse(BaseModel):
    """Lumen 채팅 응답"""

    success: bool
    persona: Dict
    response: str
    sources: List[str]
    timestamp: str
    error: Optional[str] = None


class LumenHealthResponse(BaseModel):
    """Lumen 헬스 체크 응답"""

    status: str
    service: str
    version: str
    google_ai: str
    timestamp: str


class LumenPersonasResponse(BaseModel):
    """Lumen 페르소나 목록 응답"""

    available_personas: Dict
    current_default: str
    auto_detection: str
    count: int


# HTTP Client (재사용)
http_client = httpx.AsyncClient(timeout=30.0)


@router.get("/health", response_model=LumenHealthResponse)
async def lumen_health_check():
    """
    Lumen Gateway 헬스 체크

    Lumen Gateway의 상태를 확인합니다.
    """
    try:
        response = await http_client.get(f"{LUMEN_GATEWAY_URL}/health")
        response.raise_for_status()

        data = response.json()
        logger.info(f"Lumen health check successful: {data}")

        return LumenHealthResponse(**data)

    except httpx.HTTPError as e:
        logger.error(f"Lumen health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Lumen Gateway unavailable: {str(e)}")


@router.get("/personas", response_model=LumenPersonasResponse)
async def lumen_personas():
    """
    Lumen 페르소나 목록 조회

    사용 가능한 모든 Lumen 페르소나와 설정을 반환합니다.
    """
    try:
        response = await http_client.get(f"{LUMEN_GATEWAY_URL}/personas")
        response.raise_for_status()

        data = response.json()
        logger.info(f"Lumen personas retrieved: {data.get('count', 0)} personas")

        return LumenPersonasResponse(**data)

    except httpx.HTTPError as e:
        logger.error(f"Failed to get Lumen personas: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Lumen Gateway unavailable: {str(e)}")


@router.post("/chat", response_model=LumenChatResponse)
async def lumen_chat(request: LumenChatRequest):
    """
    Lumen Gateway를 통한 AI 채팅

    Lumen의 4개 페르소나 네트워크를 활용한 대화:
    - 🌙 Lua (루아): 감성형 - 직관, 창의
    - 🔲 Elo (엘로): 구조형 - 논리, 체계
    - 🌍 Nuri (누리): 관찰형 - 메타, 균형
    - ✒️ Sena (세나): 브리지형 - 연결, 통합

    **자동 페르소나 감지**: 메시지 내용에 따라 최적의 페르소나 자동 선택
    **명시적 지정**: persona 파라미터로 특정 페르소나 강제 지정 가능
    """
    try:
        # Lumen Gateway에 요청
        payload = {"message": request.message}
        if request.persona:
            payload["persona"] = request.persona

        logger.info(
            "Sending request to Lumen Gateway",
            message_length=len(request.message),
            persona=request.persona,
            user_id=request.user_id,
        )

        response = await http_client.post(
            f"{LUMEN_GATEWAY_URL}/chat", json=payload, timeout=60.0  # 더 긴 타임아웃 (AI 응답 대기)
        )
        response.raise_for_status()

        data = response.json()
        logger.info(
            "Lumen response received",
            success=data.get("success"),
            persona=data.get("persona", {}).get("name"),
        )

        return LumenChatResponse(**data)

    except httpx.HTTPError as e:
        logger.error(f"Lumen chat request failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Lumen Gateway error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in lumen chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/status")
async def lumen_status():
    """
    Lumen Gateway 상세 상태

    시스템 정보, 페르소나 네트워크, 하이브리드 소스 정보 반환
    """
    try:
        response = await http_client.get(f"{LUMEN_GATEWAY_URL}/status")
        response.raise_for_status()

        data = response.json()
        logger.info("Lumen status retrieved successfully")

        return data

    except httpx.HTTPError as e:
        logger.error(f"Failed to get Lumen status: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Lumen Gateway unavailable: {str(e)}")


# Cleanup on shutdown
@router.on_event("shutdown")
async def shutdown_event():
    """HTTP 클라이언트 정리"""
    await http_client.aclose()
    logger.info("Lumen integration HTTP client closed")
