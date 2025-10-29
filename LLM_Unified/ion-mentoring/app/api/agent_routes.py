# -*- coding: utf-8 -*-
"""
Lumen Agent System API Routes

페르소나 AI 에이전트를 ION API를 통해 제공합니다.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

# lumen_agent_system.py import를 위한 경로 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from lumen_agent_system import LumenAgentSystem

    AGENT_SYSTEM_AVAILABLE = True
except ImportError:
    AGENT_SYSTEM_AVAILABLE = False
    logging.warning("lumen_agent_system.py not found - Agent routes will return 503")

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
    responses={503: {"description": "Agent system not available"}},
)


# === Request/Response Models ===


class AgentExecuteRequest(BaseModel):
    """에이전트 실행 요청"""

    task: str = Field(..., description="수행할 작업", min_length=1)
    files: Optional[List[str]] = Field(None, description="분석할 파일 경로 목록 (상대 경로)")
    persona: Optional[str] = Field(None, description="페르소나 강제 지정 (moon/square/earth/pen)")
    output: Optional[str] = Field(None, description="결과 저장 경로 (없으면 자동 생성)")

    class Config:
        json_schema_extra = {
            "example": {
                "task": "이 프로젝트를 창의적으로 분석해줘",
                "files": ["app/main.py", "persona_pipeline.py"],
                "persona": None,
                "output": None,
            }
        }


class AgentExecuteResponse(BaseModel):
    """에이전트 실행 응답"""

    success: bool
    agent: str = Field(..., description="실행된 에이전트 이름")
    persona: str = Field(..., description="페르소나 이모지")
    task: str = Field(..., description="수행한 작업")
    files_analyzed: List[str] = Field(..., description="분석한 파일 목록")
    output_file: Optional[str] = Field(None, description="결과 파일 경로 (있을 경우)")
    execution_time: float = Field(..., description="실행 시간 (초)")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentStatusResponse(BaseModel):
    """에이전트 시스템 상태"""

    available: bool
    agents: List[str] = Field(..., description="사용 가능한 에이전트 목록")
    version: str = "1.0.0"


# === Lumen Agent System 인스턴스 (싱글톤) ===

_agent_system: Optional[LumenAgentSystem] = None


def get_agent_system() -> LumenAgentSystem:
    """에이전트 시스템 인스턴스 반환 (싱글톤)"""
    global _agent_system

    if not AGENT_SYSTEM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Lumen Agent System not available - lumen_agent_system.py not found",
        )

    if _agent_system is None:
        _agent_system = LumenAgentSystem()
        logger.info("LumenAgentSystem initialized")

    return _agent_system


# === API Endpoints ===


@router.get("/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """
    에이전트 시스템 상태 확인

    Lumen Agent System이 정상 작동하는지 확인합니다.
    """
    if not AGENT_SYSTEM_AVAILABLE:
        return AgentStatusResponse(available=False, agents=[])

    return AgentStatusResponse(
        available=True, agents=["moon", "square", "earth", "pen"], version="1.0.0"
    )


@router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent(request: AgentExecuteRequest, background_tasks: BackgroundTasks):
    """
    에이전트 자동 실행 (페르소나 자동 감지)

    작업 내용에 따라 최적의 페르소나 에이전트를 자동으로 선택하여 실행합니다.

    **페르소나 자동 감지 규칙**:
    - 창의/혁신/아이디어 → 🌙 MoonAgent (루아)
    - 분석/체계/구조 → 📐 SquareAgent (엘로)
    - 최적화/모니터/전체 → 🌏 EarthAgent (누리)
    - 기본값 → ✒️ PenAgent (세나, 오케스트레이터)

    **Phase 4 개선**: asyncio.to_thread를 사용하여 비동기 실행
    """
    system = get_agent_system()

    try:
        import time

        start_time = time.time()

        # Phase 4: 비동기 처리 - FastAPI 이벤트 루프 블로킹 방지
        result = await asyncio.to_thread(
            system.execute, task=request.task, persona=request.persona, files=request.files
        )

        execution_time = time.time() - start_time

        # 출력 파일 추출 (results에서 file 키 찾기)
        output_file = None
        for step_result in result.get("results", []):
            if "file" in step_result:
                output_file = step_result["file"]
                break

        logger.info(
            "Agent executed successfully",
            extra={
                "agent": result["agent"],
                "persona": result["persona"],
                "execution_time": execution_time,
                "output_file": output_file,
            },
        )

        return AgentExecuteResponse(
            success=True,
            agent=result["agent"],
            persona=result["persona"],
            task=request.task,
            files_analyzed=request.files or [],
            output_file=output_file,
            execution_time=execution_time,
            metadata={
                "auto_detected": request.persona is None,
                "results": result.get("results", []),
            },
        )

    except FileNotFoundError as e:
        # Phase 4: 파일 없음 에러 (404)
        logger.warning(f"File not found during agent execution: {str(e)}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except ValueError as e:
        # Phase 4: 잘못된 요청 에러 (400)
        logger.warning(f"Invalid request for agent execution: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")
    except ImportError as e:
        # Phase 4: Agent 시스템 사용 불가 (503)
        logger.error(f"Agent system import error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Agent system unavailable: {str(e)}")
    except Exception as e:
        # Phase 4: 기타 내부 에러 (500)
        logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/moon", response_model=AgentExecuteResponse)
async def execute_moon_agent(request: AgentExecuteRequest, background_tasks: BackgroundTasks):
    """
    🌙 MoonAgent (루아) 강제 실행

    창의적이고 혁신적인 접근으로 문제를 해결합니다.

    **특화 도구**: brainstorm, prototype, experiment
    """
    request.persona = "moon"
    return await execute_agent(request, background_tasks)


@router.post("/square", response_model=AgentExecuteResponse)
async def execute_square_agent(request: AgentExecuteRequest, background_tasks: BackgroundTasks):
    """
    📐 SquareAgent (엘로) 강제 실행

    체계적이고 논리적인 분석으로 구조화합니다.

    **특화 도구**: analyze, structure, document
    """
    request.persona = "square"
    return await execute_agent(request, background_tasks)


@router.post("/earth", response_model=AgentExecuteResponse)
async def execute_earth_agent(request: AgentExecuteRequest, background_tasks: BackgroundTasks):
    """
    🌏 EarthAgent (누리) 강제 실행

    메타 관점에서 전체를 조망하고 최적화합니다.

    **특화 도구**: monitor, evaluate, optimize
    """
    request.persona = "earth"
    return await execute_agent(request, background_tasks)


@router.post("/pen", response_model=AgentExecuteResponse)
async def execute_pen_agent(request: AgentExecuteRequest, background_tasks: BackgroundTasks):
    """
    ✒️ PenAgent (세나) 강제 실행 - 멀티 에이전트 오케스트레이션

    복잡한 작업을 여러 전문가 에이전트에게 분산하고 결과를 통합합니다.

    **협업**: Moon, Square, Earth 에이전트를 조정하여 종합적인 해결책 제시
    """
    request.persona = "pen"
    return await execute_agent(request, background_tasks)


# === 추가 유틸리티 엔드포인트 ===


@router.get("/personas")
async def list_personas():
    """
    사용 가능한 페르소나 목록 조회

    각 페르소나의 특성과 특화 영역을 반환합니다.
    """
    return {
        "personas": [
            {
                "key": "moon",
                "name": "루아",
                "emoji": "🌙",
                "specialty": "창의적 문제 해결 및 혁신",
                "tools": ["brainstorm", "prototype", "experiment"],
                "description": "직감과 상상력으로 새로운 아이디어를 제안합니다.",
            },
            {
                "key": "square",
                "name": "엘로",
                "emoji": "📐",
                "specialty": "체계적 분석 및 구조화",
                "tools": ["analyze", "structure", "document"],
                "description": "논리와 체계로 정보를 정리하고 분석합니다.",
            },
            {
                "key": "earth",
                "name": "누리",
                "emoji": "🌏",
                "specialty": "메타 관점 모니터링 및 최적화",
                "tools": ["monitor", "evaluate", "optimize"],
                "description": "전체를 조망하며 균형과 최적화를 추구합니다.",
            },
            {
                "key": "pen",
                "name": "세나",
                "emoji": "✒️",
                "specialty": "멀티 에이전트 오케스트레이션",
                "tools": ["orchestrate", "delegate", "integrate"],
                "description": "여러 전문가를 조율하여 통합된 해결책을 제시합니다.",
            },
        ]
    }
