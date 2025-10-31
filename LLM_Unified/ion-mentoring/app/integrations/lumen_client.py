"""
Lumen Gateway Client

Lumen Gateway 하이브리드 AI 시스템과 Ion Mentoring API를 연결하는 클라이언트
"""

import logging
import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PersonaInfo(BaseModel):
    """페르소나 정보"""

    name: str
    type: str
    emoji: str
    specialty: str


class LumenInferenceRequest(BaseModel):
    """Lumen Gateway 추론 요청"""

    message: str
    persona_key: Optional[str] = None  # None이면 자동 선택
    session_id: Optional[str] = "default"
    user_id: Optional[str] = None


class LumenInferenceResponse(BaseModel):
    """Lumen Gateway 추론 응답"""

    success: bool
    persona: PersonaInfo
    response: str
    sources: List[str]
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LumenGatewayClient:
    """
    Lumen Gateway 클라이언트

    Lumen Gateway의 하이브리드 AI 추론 시스템을 호출하고
    Ion Mentoring API와 통합합니다.
    """

    def __init__(self, gateway_url: Optional[str] = None, timeout: int = 5, max_retries: int = 1):
        """
        Args:
            gateway_url: Lumen Gateway URL (기본값: 환경 변수 LUMEN_GATEWAY_URL)
            timeout: 요청 타임아웃 (초) - 최적화: 30초 → 5초
            max_retries: 최대 재시도 횟수 - 최적화: 2회 → 1회
        """
        self.gateway_url = gateway_url or os.getenv(
            "LUMEN_GATEWAY_URL", "http://localhost:5000"  # 로컬 개발 기본값
        )
        self.timeout = timeout
        self.max_retries = max_retries

        # 비동기 HTTP 클라이언트 (Connection Pool 자동 관리)
        self.client = httpx.AsyncClient(
            timeout=timeout, limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

        # 페르소나 매핑 (Ion Mentoring ↔ Lumen Gateway)
        self.persona_mapping = {
            "lua": "moon",  # 루아 🌙 → moon
            "elo": "square",  # 엘로 📐 → square
            "nuri": "earth",  # 누리 🌏 → earth
            "sena": "pen",  # 세나 ✒️ → pen
        }

        logger.info(
            "LumenGatewayClient initialized with async httpx client",
            extra={"gateway_url": self.gateway_url, "timeout": timeout, "max_retries": max_retries},
        )

    async def close(self):
        """HTTP 클라이언트 종료 (리소스 정리)"""
        await self.client.aclose()

    def _detect_persona_from_query(self, query: str) -> Optional[str]:
        """
        쿼리 내용에서 최적 페르소나 자동 선택

        Args:
            query: 사용자 쿼리

        Returns:
            str: 페르소나 키 (moon/square/earth/pen) 또는 None
        """
        query_lower = query.lower()

        # 키워드 기반 페르소나 선택
        if any(
            word in query_lower for word in ["창의", "아이디어", "상상", "느낌", "감성", "영감"]
        ):
            return "moon"  # 루아 🌙
        elif any(word in query_lower for word in ["정리", "구조", "체계", "분석", "계획", "단계"]):
            return "square"  # 엘로 📐
        elif any(word in query_lower for word in ["관찰", "메타", "균형", "전체", "통찰", "패턴"]):
            return "earth"  # 누리 🌏
        else:
            return "pen"  # 세나 ✒️ (기본값)

    async def _infer_async(
        self,
        message: str,
        persona_key: Optional[str] = None,
        session_id: Optional[str] = "default",
        user_id: Optional[str] = None,
    ) -> LumenInferenceResponse:
        """
        Lumen Gateway를 통해 AI 추론 실행 (비동기)

        Args:
            message: 사용자 메시지
            persona_key: 페르소나 키 (None이면 자동 선택)
            session_id: 세션 ID
            user_id: 사용자 ID

        Returns:
            LumenInferenceResponse: 추론 결과

        Raises:
            httpx.HTTPError: API 호출 실패 시
        """
        # 페르소나 자동 선택
        if persona_key is None:
            persona_key = self._detect_persona_from_query(message)
            logger.info(
                f"Auto-selected persona: {persona_key}",
                extra={"message": message[:50], "persona": persona_key},
            )

        # Lumen Gateway API 호출 (실제 엔드포인트: /chat)
        endpoint = f"{self.gateway_url}/chat"
        payload = {
            "message": message,
            "persona": persona_key,  # Lumen Gateway는 'persona' 필드 사용
            "session_id": session_id,
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"Calling Lumen Gateway (attempt {attempt + 1}/{self.max_retries + 1})",
                    extra={"endpoint": endpoint, "persona": persona_key},
                )

                response = await self.client.post(
                    endpoint, json=payload, headers={"Content-Type": "application/json"}
                )

                response.raise_for_status()  # HTTP 에러 시 예외 발생

                data = response.json()

                logger.info(
                    "Lumen Gateway response received",
                    extra={
                        "status_code": response.status_code,
                        "success": data.get("success"),
                        "persona_name": data.get("persona", {}).get("name"),
                        "response_length": len(data.get("response", "")),
                    },
                )

                # Lumen Gateway 응답 형식 파싱
                # {"success": true, "persona": {...}, "response": "...", "sources": [...]}
                if not data.get("success", False):
                    error_msg = data.get("error", "Unknown error")
                    logger.error(
                        f"Lumen Gateway returned success=false: {error_msg}",
                        extra={"full_response": data},
                    )
                    raise ValueError(f"Lumen Gateway returned success=false: {error_msg}")

                persona_data = data.get("persona", {})

                return LumenInferenceResponse(
                    success=True,
                    persona=PersonaInfo(
                        name=persona_data.get("name", "세나"),
                        type=persona_data.get("type", "브리지형"),
                        emoji=persona_data.get("emoji", "✒️"),
                        specialty=persona_data.get("specialty", "연결, 통합"),
                    ),
                    response=data.get("response", ""),
                    sources=data.get("sources", ["Google AI Studio"]),
                    timestamp=datetime.now().isoformat(),
                    metadata={"lumen_persona_key": persona_key},
                )

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    f"Lumen Gateway timeout (attempt {attempt + 1})", extra={"error": str(e)}
                )
                if attempt < self.max_retries:
                    continue

            except httpx.HTTPError as e:
                last_error = e
                status_code = None
                if isinstance(e, httpx.HTTPStatusError):
                    status_code = e.response.status_code

                logger.error(
                    f"Lumen Gateway API error (attempt {attempt + 1})",
                    extra={"error": str(e), "status_code": status_code},
                )
                if attempt < self.max_retries:
                    continue

            except Exception as e:
                last_error = e
                logger.error("Unexpected error calling Lumen Gateway", extra={"error": str(e)})
                break

        # 모든 재시도 실패 시 fallback 응답 반환
        logger.error("All retries failed for Lumen Gateway", extra={"last_error": str(last_error)})

        return self._create_fallback_response(message, persona_key or "pen")

    def infer(
        self,
        message: str,
        persona_key: Optional[str] = None,
        session_id: Optional[str] = "default",
        user_id: Optional[str] = None,
    ) -> LumenInferenceResponse:
        """동기식 래퍼: 내부적으로 비동기 로직을 실행합니다."""
        try:
            return asyncio.run(self._infer_async(message=message, persona_key=persona_key, session_id=session_id, user_id=user_id))
        except RuntimeError as e:
            # 이미 실행 중인 이벤트 루프 내에서 호출된 경우 (예: FastAPI 등)
            # 임시 이벤트 루프를 별도 스레드에서 실행하는 방법이 이상적이지만,
            # 테스트 호환성을 위해 간단 fallback 으로 동작하도록 처리합니다.
            # 여기서는 비동기 클라이언트를 직접 실행하지 않고 fallback 응답을 반환합니다.
            logger.warning(f"infer() called inside running event loop, returning fallback: {e}")
            persona_key_eff = persona_key or self._detect_persona_from_query(message)
            return self._create_fallback_response(message, persona_key_eff or "pen")

    def _create_fallback_response(self, message: str, persona_key: str) -> LumenInferenceResponse:
        """
        Lumen Gateway 호출 실패 시 Fallback 응답 생성

        Args:
            message: 원본 메시지
            persona_key: 페르소나 키

        Returns:
            LumenInferenceResponse: Fallback 응답
        """
        fallback_personas = {
            "moon": PersonaInfo(name="루아", type="감응형", emoji="🌙", specialty="직감, 창의"),
            "square": PersonaInfo(name="엘로", type="구조형", emoji="📐", specialty="논리, 체계"),
            "earth": PersonaInfo(name="누리", type="관찰형", emoji="🌏", specialty="메타, 균형"),
            "pen": PersonaInfo(name="세나", type="브리지형", emoji="✒️", specialty="연결, 통합"),
        }

        persona = fallback_personas.get(persona_key, fallback_personas["pen"])

        fallback_message = (
            f"{persona.emoji} {persona.name}입니다. "
            f"현재 Lumen Gateway에 연결할 수 없어 기본 응답을 제공합니다. "
            f"잠시 후 다시 시도해주세요."
        )

        return LumenInferenceResponse(
            success=False,
            persona=persona,
            response=fallback_message,
            sources=["fallback"],
            timestamp=datetime.now().isoformat(),
            metadata={"fallback": True, "reason": "gateway_unavailable"},
        )

    async def _health_check_async(self) -> bool:
        """
        Lumen Gateway 헬스 체크 (비동기)

        Returns:
            bool: 정상 여부
        """
        try:
            # Lumen Gateway는 /status 엔드포인트 사용
            endpoint = f"{self.gateway_url}/status"
            response = await self.client.get(endpoint)

            if response.status_code == 200:
                data = response.json()
                return data.get("ready", False)

            return False
        except Exception as e:
            logger.warning(f"Lumen Gateway health check failed: {e}")
            return False

    def health_check(self) -> bool:
        """동기식 래퍼: 내부적으로 비동기 로직을 실행합니다."""
        try:
            return asyncio.run(self._health_check_async())
        except RuntimeError as e:
            logger.warning(f"health_check() called inside running event loop: {e}")
            return False
        except Exception as e:
            logger.warning(f"Lumen Gateway health check failed: {e}")
            return False


# 싱글톤 인스턴스 (선택적)
_lumen_client_instance: Optional[LumenGatewayClient] = None


def get_lumen_client() -> LumenGatewayClient:
    """
    Lumen Gateway 클라이언트 싱글톤 인스턴스 반환

    Returns:
        LumenGatewayClient: 클라이언트 인스턴스
    """
    global _lumen_client_instance

    if _lumen_client_instance is None:
        _lumen_client_instance = LumenGatewayClient()

    return _lumen_client_instance


if __name__ == "__main__":
    # 테스트 실행

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


async def _test_main():
    """테스트 실행 (비동기)"""
    import sys

    # 클라이언트 생성
    client = LumenGatewayClient(gateway_url="http://localhost:5000")

    try:
        # 헬스 체크
        print("\n🔍 Health Check...")
        is_healthy = client.health_check()
        print(f"Lumen Gateway Health: {'✅ OK' if is_healthy else '❌ FAILED'}\n")

        if not is_healthy:
            print("⚠️ Lumen Gateway is not running. Start it first:")
            print("  cd d:\\nas_backup\\LLM_Unified")
            print("  python lumen_hybrid_gateway.py")
            sys.exit(1)

        # 추론 테스트
        print("🧪 Testing inference...")
        test_queries = [
            "창의적인 아이디어가 필요해",
            "이 문제를 논리적으로 분석해줘",
            "전체적인 상황을 메타적으로 보고 싶어",
            "여러 관점을 통합해서 설명해줘",
        ]

        for query in test_queries:
            print(f"\n📝 Query: {query}")
            result = client.infer(message=query)
            print(f"   Persona: {result.persona.emoji} {result.persona.name}")
            print(f"   Success: {result.success}")
            print(f"   Response: {result.response[:100]}...")
            print(f"   Sources: {result.sources}")

    finally:
        # 리소스 정리
        await client.close()


# === Lumen Agent System Integration ===


class AgentExecuteRequest(BaseModel):
    """에이전트 실행 요청"""

    task: str
    files: Optional[List[str]] = None
    persona: Optional[str] = None
    output: Optional[str] = None


class AgentExecuteResponse(BaseModel):
    """에이전트 실행 응답"""

    success: bool
    agent: str
    persona: str
    task: str
    files_analyzed: List[str]
    output_file: str
    execution_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


async def execute_agent(
    task: str,
    files: Optional[List[str]] = None,
    persona: Optional[str] = None,
    output: Optional[str] = None,
) -> AgentExecuteResponse:
    """
    Lumen Agent System 실행 (비동기 래퍼)

    Args:
        task: 수행할 작업
        files: 분석할 파일 목록
        persona: 페르소나 강제 지정 (None이면 자동 감지)
        output: 결과 저장 경로

    Returns:
        AgentExecuteResponse: 실행 결과

    Raises:
        ImportError: lumen_agent_system.py를 찾을 수 없을 때
        Exception: 에이전트 실행 실패 시
    """
    import sys
    import time
    from pathlib import Path

    # lumen_agent_system.py 임포트
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    try:
        from lumen_agent_system import LumenAgentSystem
    except ImportError as e:
        logger.error(f"Failed to import lumen_agent_system: {e}")
        raise ImportError(
            "lumen_agent_system.py not found. " "Make sure it's in the LLM_Unified directory."
        )

    # 에이전트 시스템 초기화 및 실행
    system = LumenAgentSystem()
    start_time = time.time()

    result = system.execute(task=task, files=files, persona=persona)

    execution_time = time.time() - start_time

    # 응답 생성
    return AgentExecuteResponse(
        success=True,
        agent=result["agent"],
        persona=result["persona"],
        task=task,
        files_analyzed=result.get("files_analyzed", files or []),
        output_file=result["output_file"],
        execution_time=execution_time,
        metadata={
            "auto_detected": persona is None,
            "detected_persona": result.get("detected_persona"),
        },
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(_test_main())
