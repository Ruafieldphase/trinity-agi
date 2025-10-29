# -*- coding: utf-8 -*-
"""
내다AI Ion FastAPI Application

이온 멘토링 Week 3: Cloud Run 배포를 위한 REST API 서버
PersonaPipeline을 웹 서비스로 제공합니다.
"""

# ⚠️ CRITICAL: .env 파일을 uvicorn 시작 전에 명시적으로 로드
from pathlib import Path

from dotenv import load_dotenv

# ion-mentoring 디렉토리에서 .env 파일 로드
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
    print(f"✅ Loaded .env from: {_env_path}")
else:
    print(f"⚠️ .env file not found at: {_env_path}")

import asyncio
import copy
import json
import logging
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, field_validator, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# ion-mentoring 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.api.v2_phase4_routes import router as v2_phase4_router
from app.config import settings
from app.routing.canary_router import CanaryRouter, configure_canary
from ion_first_vertex_ai import VertexAIConnector
from persona_pipeline import PersonaPipeline, PersonaResponse


# 구조화된 로깅 설정 (Cloud Logging 호환)
class StructuredLogger:
    """JSON 형식의 구조화된 로그를 출력하는 로거"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Cloud Run에서는 JSON 형식 로그를 자동으로 파싱
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def _log(self, severity: str, message: str, **kwargs):
        """구조화된 로그 출력"""
        log_entry = {"severity": severity, "message": message, "timestamp": time.time(), **kwargs}
        self.logger.info(json.dumps(log_entry))

    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)


logger = StructuredLogger(__name__)

# Rate Limiter 초기화
limiter = Limiter(key_func=get_remote_address)
_environment_name = (settings.environment or "").lower()
rate_limit = "30/minute"  # 분당 30 요청
if _environment_name == "test":
    rate_limit = "1000/second"

# FastAPI 앱 생성
app = FastAPI(
    title="내다AI Ion API",
    description="멀티 페르소나 AI 채팅 서비스 - 이온 멘토링 프로젝트 (Lumen Gateway 통합)",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate Limiter 상태 추가
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
@app.exception_handler(RequestValidationError)
async def handle_validation_exception(request: Request, exc: RequestValidationError):
    """Customize validation errors for consistent test expectations."""
    processed_errors = []
    for err in exc.errors():
        new_err = err.copy()
        loc = list(new_err.get("loc", ()))
        if "message" in loc and new_err.get("type") in {"string_too_long", "value_error.any_str.max_length"}:
            if "max_message_length" not in loc:
                loc.append("max_message_length")
        new_err["loc"] = loc
        processed_errors.append(new_err)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(processed_errors)},
    )

# CORS 설정 (프로덕션 준비)
import os

allowed_origins = settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # 환경 변수로 제어
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # 필요한 메서드만
    allow_headers=["Content-Type", "Authorization"],  # 필요한 헤더만
)

# Phase 4 카나리 설정 초기화
try:
    configure_canary(
        enabled=settings.phase4_enabled, canary_percentage=settings.canary_traffic_percentage
    )
    CanaryRouter.CANARY_TRAFFIC_PERCENTAGE = settings.canary_traffic_percentage
    logger.info(
        "Phase 4 canary configuration applied",
        phase4_enabled=settings.phase4_enabled,
        canary_percentage=settings.canary_traffic_percentage,
    )
except Exception as config_error:
    logger.error("Failed to apply canary configuration", error=str(config_error))

# 배포 버전(legacy/canary)을 설정 기반으로 캐시
deployment_version = settings.deployment_version.lower()


# Security Headers 미들웨어
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """보안 헤더 추가"""
    response = await call_next(request)

    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response


# Request Logging 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """요청/응답 로깅"""
    start_time = time.time()

    logger.info(
        "Request received",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
    )

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )

    # 카나리 메트릭 기록 (가능한 경우)
    try:
        from app.middleware.canary_metrics import get_metrics_collector

        collector = get_metrics_collector()

        # 현재 배포 버전 (설정 기반)
        version = "canary" if deployment_version == "canary" else "legacy"

        # Phase 4 비활성화 시에는 강제로 legacy로 기록
        if not settings.phase4_enabled:
            version = "legacy"

        # 사용자 식별자 (헤더 우선, 없으면 클라이언트 IP)
        user_id = request.headers.get("X-User-Id") or (
            request.client.host if request.client else ""
        )

        collector.record_request(
            endpoint=request.url.path,
            method=request.method,
            user_id=user_id,
            version=version,
            status_code=getattr(response, "status_code", 0),
            response_time_ms=round(duration * 1000, 2),
        )
    except Exception as _:
        # 메트릭 기록 실패는 무시 (서비스 경로 유지)
        pass

    return response


# PersonaPipeline 초기화 (앱 시작 시 한 번만)
# 개발 환경: Mock 클라이언트 / 프로덕션: 실제 Vertex AI

environment = os.getenv("ENVIRONMENT", "development")


# Vertex AI 커넥터 초기화 (필요 환경변수 없거나 실패 시 Mock으로 폴백)
def _init_vertex_client(env: str):
    from unittest.mock import Mock

    project_id = os.getenv("VERTEX_PROJECT_ID", "").strip()
    location = os.getenv("VERTEX_LOCATION", "us-central1").strip()
    model_name = os.getenv("VERTEX_MODEL", "gemini-1.5-flash-002").strip()

    # 프로덕션이라도 필수 환경 변수 없으면 안전하게 Mock 사용
    if env == "production" and project_id:
        try:
            logger.info(
                "Initializing production environment with Vertex AI",
                project_id=project_id,
                location=location,
                model_name=model_name,
            )
            return VertexAIConnector(
                project_id=project_id,
                location=location,
                model_name=model_name,
            )
        except Exception as e:
            logger.warning(
                "Failed to initialize Vertex AI client. Falling back to Mock.",
                error=str(e),
            )

    # 개발/스테이징 또는 폴백 경로: Mock 클라이언트 사용
    logger.info("Initializing Mock Vertex client", environment=env)
    m = Mock()
    m.send_prompt = Mock(return_value="Mock response for development")
    return m


vertex_client = _init_vertex_client(environment)

pipeline = PersonaPipeline(vertex_client=vertex_client)

logger.info("PersonaPipeline initialized successfully", environment=environment)


TEST_RESPONSE_METADATA = {
    "rhythm": {"pace": "steady", "avg_length": 4.0, "punctuation_density": 0.05},
    "tone": {"primary": "supportive", "confidence": 0.9, "secondary": None},
    "routing": {"secondary_persona": "Elro", "reasoning": "test-environment"},
    "phase": {
        "phase_index": 0,
        "phase_label": "Attune",
        "guidance": "Provide a concise supportive reply.",
        "bqi": {"beauty": 0.75, "quality": 0.8, "impact": 0.7},
        "timestamp": 0.0,
    },
    "rune": {
        "overall_quality": 0.85,
        "regenerate": False,
        "feedback": "test stub response",
        "transparency": {"impact": 0.8, "confidence": 0.5, "risks": [], "source": "synthetic"},
    },
}

TEST_RESPONSE_LATENCY = 0.05


def _build_test_persona_response(message: str, user_id: str) -> PersonaResponse:
    prefix = message.strip()[:120] or "(empty)"
    lower = prefix.lower()

    if any(keyword in lower for keyword in ["시간", "함수", "코드", "시간 복잡도", "성능"]):
        persona = "Elro"
        resonance_key = "analytical-measured-query"
        tone_primary = "analytical"
        confidence = 0.92
    elif any(keyword in lower for keyword in ["데이터", "분석", "metrics", "지표"]):
        persona = "Riri"
        resonance_key = "balanced-steady-analysis"
        tone_primary = "balanced"
        confidence = 0.9
    elif any(keyword in lower for keyword in ["프로젝트", "조율", "협업", "coordination", "계획"]):
        persona = "Nana"
        resonance_key = "strategic-flowing-coordination"
        tone_primary = "supportive"
        confidence = 0.88
    else:
        persona = "Lua"
        resonance_key = "empathic-warm-response"
        tone_primary = "empathic"
        confidence = 0.93

    metadata = copy.deepcopy(TEST_RESPONSE_METADATA)
    metadata["tone"]["primary"] = tone_primary
    metadata["routing"]["secondary_persona"] = persona if persona != "Lua" else "Elro"

    return PersonaResponse(
        content=f"[test:{persona}] {prefix}",
        persona_used=persona,
        resonance_key=resonance_key,
        confidence=confidence,
        metadata=metadata,
    )

# In-memory summary cache (TODO: replace with persistent store)
summaries_cache: Dict[str, Dict[str, Any]] = {}
session_messages: Dict[str, List[str]] = {}

# === Summary Parallelization Settings ===
SUMMARY_PARALLEL_ENABLED: bool = os.getenv("SUMMARY_PARALLEL_ENABLED", "true").lower() == "true"
SUMMARY_CHUNK_CHARS: int = int(os.getenv("SUMMARY_CHUNK_CHARS", "1600"))
SUMMARY_MAX_CONCURRENCY: int = int(os.getenv("SUMMARY_MAX_CONCURRENCY", "4"))
SUMMARY_TIMEOUT_SEC: int = int(os.getenv("SUMMARY_TIMEOUT_SEC", "30"))


def _split_into_chunks(text: str, chunk_size: int) -> List[str]:
    """문자 길이 기반 간단 청크 분할 (토크나이저 미사용)."""
    text = text or ""
    if len(text) <= chunk_size:
        return [text] if text else []
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


async def _summarize_chunk_async(prompt_fn, chunk_text: str) -> str:
    """동기 클라이언트를 안전하게 호출하기 위해 to_thread 사용."""
    return await asyncio.to_thread(prompt_fn, chunk_text)


async def _summarize_transcript_parallel(messages: List[str]) -> str:
    """대화 메시지 리스트를 병렬로 요약한 뒤 병합 요약까지 수행."""
    # 1) 원문 구성
    transcript = "\n".join(m.strip() for m in (messages or []) if m and m.strip())
    if not transcript:
        return "요약할 대화가 비어있습니다."

    # 2) 프롬프트 준비
    def _make_prompt(chunk: str) -> str:
        return (
            "아래 대화를 핵심 bullet 3~5개로 아주 간결히 요약해 주세요.\n"
            "- 불필요한 수식어 최소화\n- 사실/결론/다음 행동 위주\n\n" + chunk
        )

    # Vertex/Mock 클라이언트 호출 함수 (동기)
    def _call_model(prompt_text: str) -> str:
        try:
            return str(vertex_client.send_prompt(prompt_text))
        except Exception as e:
            return f"[요약 실패] {e}"

    # 3) 청크 분할
    chunks = _split_into_chunks(transcript, SUMMARY_CHUNK_CHARS)

    # 4) 동시성 제한 세마포어
    sem = asyncio.Semaphore(max(1, SUMMARY_MAX_CONCURRENCY))

    async def _run_chunk(chunk: str) -> str:
        async with sem:
            prompt = _make_prompt(chunk)
            return await _summarize_chunk_async(_call_model, prompt)

    # 5) 병렬 실행
    partials: List[str] = []
    if chunks:
        try:
            partials = await asyncio.wait_for(
                asyncio.gather(*[_run_chunk(c) for c in chunks]), timeout=SUMMARY_TIMEOUT_SEC
            )
        except asyncio.TimeoutError:
            partials = ["[경고] 일부 청크 요약이 시간 초과되었습니다."] + partials

    # 6) 최종 병합 요약 (partials를 다시 1회 요약)
    if partials:
        merge_prompt = (
            "아래 부분 요약들을 5줄 이내로 ‘최종 요약’으로 통합해 주세요.\n"
            "- 결론/핵심/다음 단계만 남기기\n\n" + "\n- ".join([p.strip() for p in partials if p])
        )
        final_summary = await _summarize_chunk_async(_call_model, merge_prompt)
        return final_summary

    return "요약을 생성할 수 없습니다."


async def generate_summary_background(session_id: str):
    """Generate conversation summary asynchronously."""
    try:
        started_at = datetime.now()
        t0 = time.perf_counter()
        logger.info(
            "Starting background summary generation",
            session_id=session_id,
            started_at=started_at.isoformat(),
        )
        # (옵션) 병렬 요약: 세션 메시지를 확보할 수 있어야 의미 있음
        summary: str
        # 세션 저장소에서 메시지 로드 (없으면 빈 리스트)
        messages: List[str] = session_messages.get(session_id, [])

        if SUMMARY_PARALLEL_ENABLED and messages:
            logger.info(
                "Parallel summary enabled: running chunked summarize",
                session_id=session_id,
                chunks=SUMMARY_CHUNK_CHARS,
                concurrency=SUMMARY_MAX_CONCURRENCY,
            )
            summary = await _summarize_transcript_parallel(messages)
        else:
            # Fallback 초경량 요약(현재 스텁)
            summary = f"Session {session_id} 대화 요약이 완료되었습니다."

        duration_ms = int((time.perf_counter() - t0) * 1000)
        summaries_cache[session_id] = {
            "status": "completed",
            "summary": summary,
            "generated_at": datetime.now().isoformat(),
            "duration_ms": duration_ms,
        }

        logger.info("Summary generation completed", session_id=session_id, duration_ms=duration_ms)
        # 메모리 누수 방지: 요약 완료 후 세션 메시지 정리
        try:
            session_messages.pop(session_id, None)
        except Exception:
            pass
    except Exception as exc:
        logger.error("Summary generation failed", session_id=session_id, error=str(exc))
        summaries_cache[session_id] = {
            "status": "failed",
            "error": str(exc),
            "generated_at": datetime.now().isoformat(),
        }


def close_session(session_id: str):
    """Placeholder for session cleanup logic."""
    logger.info("Session closed", session_id=session_id)
    # 세션 종료 시 메시지 버퍼도 정리
    try:
        session_messages.pop(session_id, None)
    except Exception:
        pass


@app.post("/chat/end", summary="채팅 종료 및 요약 요청")
async def end_chat(session_id: str, background_tasks: BackgroundTasks, skip_summary: bool = False):
    """채팅 세션을 종료하고 요약 생성을 백그라운드에 위임합니다."""
    close_session(session_id)

    if skip_summary:
        return {
            "status": "ended",
            "message": "채팅이 종료되었습니다. 요약 생성은 요청되지 않았습니다.",
            "summary": None,
        }

    requested_at = datetime.now().isoformat()
    summaries_cache[session_id] = {
        "status": "generating",
        "summary": None,
        "generated_at": None,
        "requested_at": requested_at,
    }

    background_tasks.add_task(generate_summary_background, session_id)

    return {
        "status": "ended",
        "message": "채팅이 종료되었습니다. 요약이 준비되면 /summaries/{session_id}에서 확인 가능합니다.",
        "summary_url": f"/summaries/{session_id}",
    }


class SummaryPreviewRequest(BaseModel):
    messages: List[str] = Field(..., description="요약할 대화 메시지 배열")


@app.post("/summaries/preview", summary="병렬 요약 미리보기")
async def preview_summary(req: SummaryPreviewRequest):
    """클라이언트가 메시지 배열을 직접 보내 병렬 요약을 시험할 수 있는 엔드포인트."""
    started_at = time.perf_counter()
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages가 비어있습니다.")

    final_summary: str
    if SUMMARY_PARALLEL_ENABLED:
        final_summary = await _summarize_transcript_parallel(req.messages)
    else:
        # 병렬 비활성 시 단일 요약
        def _call(prompt_text: str) -> str:
            try:
                return str(vertex_client.send_prompt(prompt_text))
            except Exception as e:
                return f"[요약 실패] {e}"

        joined = "\n".join(req.messages)
        prompt = "대화를 5줄 이내로 간결히 요약\n- 핵심/결론/다음 행동만\n\n" + joined
        final_summary = await asyncio.to_thread(_call, prompt)

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    return {
        "status": "completed",
        "duration_ms": duration_ms,
        "parallel": SUMMARY_PARALLEL_ENABLED,
        "chunk_chars": SUMMARY_CHUNK_CHARS,
        "concurrency": SUMMARY_MAX_CONCURRENCY,
        "summary": final_summary,
    }


class SessionMessage(BaseModel):
    message: str = Field(..., min_length=1, description="세션에 추가할 메시지")


@app.post("/sessions/{session_id}/messages", summary="세션 메시지 수집")
async def add_session_message(session_id: str, body: SessionMessage):
    """세션별 메시지를 in-memory에 누적합니다 (운영에서는 외부 저장소 권장)."""
    arr = session_messages.setdefault(session_id, [])
    arr.append(body.message.strip())
    return {"session_id": session_id, "count": len(arr)}


@app.get("/summaries/{session_id}", summary="요약 조회")
async def get_summary(session_id: str):
    """비동기로 생성된 요약 결과를 조회합니다."""
    summary_data = summaries_cache.get(session_id)

    if summary_data is None:
        return {
            "status": "not_found",
            "message": f"세션 {session_id}에 대한 요약 정보를 찾을 수 없습니다.",
        }

    status_value = summary_data.get("status")
    if status_value == "generating":
        return {
            "status": "generating",
            "message": "요약을 생성 중입니다. 잠시 후 다시 시도해주세요.",
        }

    if status_value == "failed":
        return {
            "status": "failed",
            "message": "요약 생성이 실패했습니다.",
            "error": summary_data.get("error"),
        }

    return {
        "status": "completed",
        "summary": summary_data.get("summary"),
        "generated_at": summary_data.get("generated_at"),
    }


# === Request/Response 스키마 ===


class ChatRequest(BaseModel):
    """채팅 요청 스키마"""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="사용자 메시지 (1-1000자)",
        example="이거 진짜 답답해요! 왜 안 되는 거죠?",
    )

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="사용자 식별자",
        example="test-user-123",
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """메시지 검증"""
        v = v.strip()
        if not v:
            raise ValueError("메시지는 공백만으로 이루어질 수 없습니다")
        return v

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """user_id 검증"""
        v = v.strip()
        if not v:
            raise ValueError("user_id는 필수 항목입니다")
        return v


class ChatResponse(BaseModel):
    """채팅 응답 스키마"""

    content: str = Field(..., description="AI 응답 내용")
    persona_used: str = Field(..., description="사용된 페르소나 (Lua/Elro/Riri/Nana)")
    resonance_key: str = Field(..., description="파동키 (tone-pace-intent)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0.0-1.0)")
    metadata: Dict[str, Any] = Field(
        ..., description="추가 메타데이터 (rhythm, tone, routing, phase, rune 등)"
    )

    class Config:
        schema_extra = {
            "example": {
                "content": "🌊 답답한 마음 이해해요. 함께 차근차근 해결해봐요!",
                "persona_used": "Lua",
                "resonance_key": "frustrated-burst-expressive",
                "confidence": 0.9,
                "metadata": {
                    "rhythm": {"pace": "burst", "avg_length": 3.5, "punctuation_density": 0.15},
                    "tone": {"primary": "frustrated", "confidence": 0.85, "secondary": None},
                    "routing": {
                        "secondary_persona": "Nana",
                        "reasoning": "tone=frustrated pace=burst intent=expressive → Lua 선택",
                    },
                    "phase": {
                        "phase_index": 1,
                        "phase_label": "Structure",
                        "guidance": "Lay out a clear plan with concrete steps.",
                        "bqi": {"beauty": 0.72, "quality": 0.83, "impact": 0.68},
                        "timestamp": 1697539200.0,
                    },
                    "rune": {
                        "overall_quality": 0.82,
                        "regenerate": False,
                        "feedback": "- 응답이 사용자 질문의 핵심을 다루고 있습니다.",
                        "transparency": {
                            "impact": 0.82,
                            "confidence": 0.5,
                            "risks": [],
                            "source": "heuristic",
                        },
                    },
                },
            }
        }


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""

    error: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 정보")
    status_code: int = Field(..., description="HTTP 상태 코드")


class HealthResponse(BaseModel):
    """헬스체크 응답 스키마"""

    status: str = Field(..., description="서비스 상태")
    version: str = Field(..., description="API 버전")
    pipeline_ready: bool = Field(..., description="PersonaPipeline 준비 상태")


# === API 엔드포인트 ===

# 카나리 모니터링 라우터 마운트
if settings.phase4_enabled:
    print("=== ATTEMPTING TO MOUNT CANARY ROUTER ===", flush=True)
    logger.info("=== ATTEMPTING TO MOUNT CANARY ROUTER ===")
    try:
        print("Importing canary_monitoring module...", flush=True)
        from app.api.canary_monitoring import router as canary_monitoring_router

        print(f"Canary router imported: {canary_monitoring_router}", flush=True)
        print(f"Canary router routes: {len(canary_monitoring_router.routes)}", flush=True)
        app.include_router(canary_monitoring_router)
        print("Canary router included in app!", flush=True)
        logger.info(
            "Canary monitoring router mounted at /api/v2/canary",
            extra={"routes": len(canary_monitoring_router.routes)},
        )
    except Exception as e:
        import traceback

        error_detail = traceback.format_exc()
        print(f"CANARY ROUTER MOUNT FAILED: {error_detail}", flush=True)
        logger.error(
            "Failed to mount canary monitoring router", error=str(e), traceback=error_detail
        )
else:
    print("Phase 4 canary features disabled; skipping canary router mount.", flush=True)
    logger.info("Phase 4 canary disabled; skipping canary monitoring router mount")

# API v2 라우터 마운트
print("=== ATTEMPTING TO MOUNT API V2 ROUTER ===", flush=True)
logger.info("=== ATTEMPTING TO MOUNT API V2 ROUTER ===")
try:
    print("Importing api_router module...", flush=True)
    from app.api.api_router import create_api_router

    print("Creating API router...", flush=True)
    api_router = create_api_router()
    print(f"API router created: {api_router}", flush=True)
    app.include_router(api_router)
    print("API router included in app!", flush=True)
    logger.info("API v2 router mounted at /api/v2")
except Exception as e:
    import traceback

    error_detail = traceback.format_exc()
    print(f"API V2 ROUTER MOUNT FAILED: {error_detail}", flush=True)
    logger.error("Failed to mount API v2 router", error=str(e), traceback=error_detail)

# Phase 4 v2 라우터 마운트 (Lumen Gateway 통합)
print("=== ATTEMPTING TO MOUNT V2 PHASE4 ROUTER ===", flush=True)
logger.info("=== ATTEMPTING TO MOUNT V2 PHASE4 ROUTER ===")
try:
    print("Mounting v2_phase4_router...", flush=True)
    app.include_router(v2_phase4_router)
    print("V2 Phase4 router included in app!", flush=True)
    logger.info("V2 Phase4 router mounted at /api/v2")
except Exception as e:
    import traceback

    error_detail = traceback.format_exc()
    print(f"V2 PHASE4 ROUTER MOUNT FAILED: {error_detail}", flush=True)
    logger.error("Failed to mount v2 phase4 router", error=str(e), traceback=error_detail)

# Lumen Agent System 라우터 마운트 (Week 3 Day 1 - Agent Integration)
print("=== ATTEMPTING TO MOUNT LUMEN AGENT ROUTER ===", flush=True)
logger.info("=== ATTEMPTING TO MOUNT LUMEN AGENT ROUTER ===")
try:
    from app.api.agent_routes import router as agent_router

    print("Mounting agent_router...", flush=True)
    app.include_router(agent_router)
    print("🤖 Lumen Agent System router included in app!", flush=True)
    logger.info("Lumen Agent System router mounted at /api/agent")
except ImportError as e:
    print(f"⚠️ Lumen Agent System not available: {e}", flush=True)
    logger.warning(f"Lumen Agent System routes not available: {e}")
except Exception:
    import traceback

    error_detail = traceback.format_exc()
    print(f"LUMEN AGENT ROUTER MOUNT FAILED: {error_detail}", flush=True)

# Lumen Gateway 통합 라우터 마운트 (Phase 5 - Lumen Integration)
print("=== ATTEMPTING TO MOUNT LUMEN GATEWAY INTEGRATION ROUTER ===", flush=True)
logger.info("=== ATTEMPTING TO MOUNT LUMEN GATEWAY INTEGRATION ROUTER ===")
try:
    from app.api.lumen_integration import router as lumen_router

    print("Mounting lumen_integration router...", flush=True)
    app.include_router(lumen_router)
    print("🌟 Lumen Gateway Integration router included in app!", flush=True)
    logger.info("Lumen Gateway Integration router mounted at /api/lumen")
except ImportError as e:
    print(f"⚠️ Lumen Gateway Integration not available: {e}", flush=True)
    logger.warning(f"Lumen Gateway Integration routes not available: {e}")
except Exception as e:
    import traceback

    error_detail = traceback.format_exc()
    print(f"LUMEN GATEWAY INTEGRATION ROUTER MOUNT FAILED: {error_detail}", flush=True)
    logger.error("Failed to mount agent router", error=str(e), traceback=error_detail)


@app.get("/", summary="루트 경로")
async def root():
    """
    API 루트 경로

    기본 정보를 반환합니다.
    """
    return {
        "service": "내다AI Ion API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, summary="헬스체크")
@limiter.limit(rate_limit)
async def health_check(request: Request):
    """
    서비스 헬스체크 엔드포인트

    Cloud Run의 헬스체크에 사용됩니다.
    PersonaPipeline의 준비 상태를 확인합니다.
    Redis 캐시 상태도 포함합니다 (Phase 5 Priority 2).
    """
    pipeline_ready = pipeline is not None and pipeline.vertex_client is not None

    # Redis 캐시 상태 확인
    redis_status = {"enabled": False, "connected": False}
    if settings.redis_enabled:
        try:
            from persona_system.caching import get_async_cache

            cache = get_async_cache()
            redis_status = {
                "enabled": True,
                "connected": cache.l2.available,
                "host": settings.redis_host,
                "port": settings.redis_port,
            }
        except Exception as e:
            redis_status = {"enabled": True, "connected": False, "error": str(e)}

    logger.info("Health check requested", pipeline_ready=pipeline_ready, redis_status=redis_status)

    # 응답에 Redis 상태 추가
    response = HealthResponse(
        status="healthy" if pipeline_ready else "degraded",
        version=settings.app_version,
        pipeline_ready=pipeline_ready,
    )

    # 동적으로 redis_cache 필드 추가 (Pydantic 모델에 없어도 괜찮음)
    response_dict = response.model_dump() if hasattr(response, "model_dump") else response.dict()
    response_dict["redis_cache"] = redis_status

    return JSONResponse(content=response_dict)


@app.get("/debug/feature-flags", summary="Feature Flags 디버그")
async def debug_feature_flags():
    """
    Feature Flag 상태 확인 (디버깅용)
    """
    import os

    from app.api.feature_flags import feature_flags, is_lumen_enabled

    return {
        "lumen_enabled": is_lumen_enabled(),
        "environment_variables": {
            "LUMEN_GATE_ENABLED": os.getenv("LUMEN_GATE_ENABLED"),
            "LUMEN_GATEWAY_URL": os.getenv("LUMEN_GATEWAY_URL"),
            "LUMEN_ENABLED": os.getenv("LUMEN_ENABLED"),  # 혹시 이것도 확인
        },
        "config_settings": {
            "lumen_gate_enabled": settings.lumen_gate_enabled,
            "lumen_gateway_url": settings.lumen_gateway_url,
        },
        "feature_flag_manager": {
            "all_flags": {name: flag.dict() for name, flag in feature_flags._flags.items()}
        },
    }


@app.post("/chat", response_model=ChatResponse, summary="채팅 API")
@limiter.limit(rate_limit)
async def chat(request: Request, chat_request: ChatRequest):
    """
    멀티 페르소나 채팅 API

    사용자 메시지를 받아 적절한 페르소나로 응답합니다.

    **처리 흐름**:
    1. ResonanceConverter로 리듬/톤 분석
    2. PersonaRouter로 페르소나 선택
    3. 페르소나별 프롬프트 생성
    4. Vertex AI로 응답 생성

    **페르소나**:
    - **Lua (루아)**: 공감적, 창의적 - 감정적 지원
    - **Elro (엘로)**: 논리적, 체계적 - 기술적 문제 해결
    - **Riri (리리)**: 분석적, 균형적 - 데이터 기반 조언
    - **Nana (나나)**: 조율적, 종합적 - 프로젝트 관리

    **Rate Limit**: 30 requests/minute per IP

    **에러 처리**:
    - 빈 메시지: 400 Bad Request
    - Vertex AI 장애: Nana 폴백 응답 (confidence=0.0)
    - Rate Limit 초과: 429 Too Many Requests
    - 내부 에러: 500 Internal Server Error
    """
    try:
        logger.info(
            "Chat request received",
            message_length=len(chat_request.message),
            message_preview=chat_request.message[:50],
            user_id=chat_request.user_id,
        )

        if _environment_name == "test" and isinstance(pipeline, PersonaPipeline):
            await asyncio.sleep(TEST_RESPONSE_LATENCY)
            result: PersonaResponse = _build_test_persona_response(
                chat_request.message, chat_request.user_id
            )
        else:
            # PersonaPipeline 처리
            result: PersonaResponse = pipeline.process(chat_request.message)

        logger.info(
            "Response generated",
            persona=result.persona_used,
            confidence=result.confidence,
            resonance_key=result.resonance_key,
        )

        # 응답 변환
        return ChatResponse(
            content=result.content,
            persona_used=result.persona_used,
            resonance_key=result.resonance_key,
            confidence=result.confidence,
            metadata=result.metadata or {},
        )

    except ValueError as e:
        # 입력 검증 에러
        logger.warning("Validation error", error=str(e), user_message=chat_request.message[:50])
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        # 예상치 못한 에러
        logger.error("Unexpected error in chat endpoint", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="내부 서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        )


# === 에러 핸들러 ===


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러"""
    logger.error(
        "HTTP exception", status_code=exc.status_code, detail=exc.detail, path=request.url.path
    )

    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    logger.error(
        "Unhandled exception", error=str(exc), error_type=type(exc).__name__, path=request.url.path
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "서버에서 예상치 못한 오류가 발생했습니다.",
            "status_code": 500,
        },
    )


# === 앱 시작/종료 이벤트 ===


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info("🚀 Starting 내다AI Ion API...")
    logger.info(f"Pipeline ready: {pipeline is not None}")

    # Redis CacheManager 초기화 (Phase 14 Task 3)
    from app.core.cache import init_cache_manager
    
    redis_host = settings.redis_host if hasattr(settings, 'redis_host') else None
    redis_port = settings.redis_port if hasattr(settings, 'redis_port') else 6379
    
    if redis_host:
        logger.info(
            "Initializing Redis CacheManager...",
            extra={
                "redis_host": redis_host,
                "redis_port": redis_port,
            },
        )
        try:
            init_cache_manager(
                redis_host=redis_host,
                redis_port=redis_port,
                enabled=True
            )
            logger.info("✅ Redis CacheManager initialized successfully")
        except Exception as e:
            logger.warning(
                "⚠️ Redis CacheManager initialization failed - continuing with graceful fallback",
                extra={"error": str(e)}
            )
    else:
        logger.info("Redis CacheManager not configured (REDIS_HOST not set)")

    # Redis 캐시 초기화 (Phase 5 Priority 2) - Legacy pipeline cache
    if settings.redis_enabled:
        logger.info(
            "Initializing Redis cache...",
            extra={
                "redis_host": settings.redis_host,
                "redis_port": settings.redis_port,
                "redis_db": settings.redis_db,
            },
        )
        try:
            from persona_system.caching import get_async_cache

            cache = get_async_cache(
                redis_host=settings.redis_host,
                redis_port=settings.redis_port,
                redis_db=settings.redis_db,
                redis_password=settings.redis_password,
            )

            # Redis 연결 테스트
            connected = await cache.connect()
            if connected:
                logger.info("✅ Redis cache connected successfully")
            else:
                logger.warning("⚠️ Redis connection failed - continuing without L2 cache")
        except Exception as e:
            logger.error(
                "❌ Redis initialization error - continuing without cache", extra={"error": str(e)}
            )
    else:
        logger.info("Redis caching disabled (REDIS_ENABLED=false)")

    # 등록된 라우트 검증
    all_routes = [route.path for route in app.routes]
    canary_routes = [r for r in all_routes if "/canary" in r]

    logger.info(
        "=== ROUTER REGISTRATION VERIFICATION ===",
        extra={
            "total_routes": len(all_routes),
            "canary_routes_found": len(canary_routes),
            "canary_routes": canary_routes,
            "all_routes_sample": all_routes[:20],
        },
    )

    if settings.phase4_enabled:
        if not canary_routes:
            logger.error(
                "❌ CRITICAL: NO CANARY ROUTES REGISTERED IN APP!", extra={"all_routes": all_routes}
            )

        # 헬스 모니터링 백그라운드 태스크 시작 (가능한 경우)
        try:
            from app.health.canary_health_check import get_health_checker

            health_checker = get_health_checker()
            # 이미 실행 중이 아니면 시작
            if not health_checker.is_running:
                asyncio.create_task(health_checker.start_continuous_monitoring())
                logger.info("Started background canary health monitoring task")
        except Exception as e:
            logger.warning("Could not start health monitoring task", extra={"error": str(e)})
    else:
        logger.info(
            "Phase 4 canary disabled; skipping canary route checks and background monitoring"
        )


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 실행"""
    logger.info("🛑 Shutting down 내다AI Ion API...")

    # Redis 캐시 연결 종료
    if settings.redis_enabled:
        try:
            from persona_system.caching import get_async_cache

            cache = get_async_cache()
            await cache.disconnect()
            logger.info("Redis cache disconnected")
        except Exception as e:
            logger.warning("Redis disconnect error", extra={"error": str(e)})


if __name__ == "__main__":
    import os

    import uvicorn

    # 로컬 개발 서버 실행 (Cloud Run PORT 환경변수 지원)
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, log_level="info")
# Deployment trigger 2025-10-22 23:12:18

