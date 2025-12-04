"""
Comet API Client
Phase 2.5 Day 1: HTTP/WebSocket Client for Comet Browser Worker

통신 채널:
1. HTTP REST API:
   - POST /api/search: Perplexity 검색 요청
   - GET /api/youtube: YouTube 메타데이터 조회
   - POST /api/task: RPA 태스크 생성
   
2. WebSocket API:
   - /ws/events: 실시간 이벤트 스트림
   - /ws/youtube: YouTube 학습 데이터 스트림

설계 원칙:
- Task Queue Server와 동일한 패턴 사용 (FastAPI/Starlette 호환)
- Async/Await 기반 비동기 통신
- Retry 및 Timeout 처리
- 이벤트 기반 로깅 (Resonance Ledger 통합 준비)
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import httpx
from websockets import connect as ws_connect
from websockets.exceptions import ConnectionClosed, WebSocketException


# ============================================================================
# Configuration
# ============================================================================

class CometEndpoint(str, Enum):
    """Comet API Endpoints"""
    SEARCH = "/api/search"
    YOUTUBE = "/api/youtube"
    TASK_CREATE = "/api/task"
    HEALTH = "/api/health"
    WS_EVENTS = "/ws/events"
    WS_YOUTUBE = "/ws/youtube"


@dataclass
class CometConfig:
    """Comet Client 설정"""
    base_url: str = "http://localhost:8090"  # Comet Browser Worker 기본 주소
    timeout: float = 30.0  # HTTP 타임아웃 (초)
    retry_attempts: int = 3  # 재시도 횟수
    retry_delay: float = 1.0  # 재시도 대기 시간 (초)
    ws_reconnect: bool = True  # WebSocket 자동 재연결
    ws_heartbeat: float = 30.0  # WebSocket heartbeat 주기 (초)
    
    # Logging
    log_requests: bool = True  # HTTP 요청 로깅
    log_responses: bool = False  # HTTP 응답 로깅 (민감 정보 주의)
    log_events: bool = True  # WebSocket 이벤트 로깅


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class SearchRequest:
    """Perplexity 검색 요청"""
    query: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    stream: bool = False  # 스트리밍 응답 여부


@dataclass
class YouTubeRequest:
    """YouTube 메타데이터 요청"""
    video_id: str
    fetch_transcript: bool = True  # 자막 포함 여부
    fetch_comments: bool = False  # 댓글 포함 여부 (미구현)


@dataclass
class TaskRequest:
    """RPA 태스크 생성 요청"""
    task_type: str  # "youtube_play", "screenshot", "mouse_click", etc.
    parameters: Dict[str, Any]
    priority: int = 5
    timeout: Optional[float] = None


@dataclass
class CometResponse:
    """Comet API 응답 (공통)"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# Comet HTTP Client
# ============================================================================

class CometHTTPClient:
    """
    Comet Browser Worker HTTP Client
    
    사용 예시:
        async with CometHTTPClient() as client:
            response = await client.search("AI 최신 뉴스")
            print(response.data)
    """
    
    def __init__(self, config: Optional[CometConfig] = None):
        self.config = config or CometConfig()
        self.client: Optional[httpx.AsyncClient] = None
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> CometResponse:
        """
        HTTP 요청 (재시도 포함)
        
        Args:
            method: HTTP 메서드 (GET, POST, etc.)
            endpoint: API 엔드포인트
            json_data: JSON 요청 바디
            params: 쿼리 파라미터
        
        Returns:
            CometResponse: 성공/실패 및 데이터
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        
        last_error = None
        
        for attempt in range(1, self.config.retry_attempts + 1):
            try:
                if self.config.log_requests:
                    self.logger.info(
                        f"[Comet] {method} {endpoint} (attempt {attempt}/{self.config.retry_attempts})"
                    )
                
                response = await self.client.request(
                    method=method,
                    url=endpoint,
                    json=json_data,
                    params=params
                )
                
                response.raise_for_status()
                
                data = response.json()
                
                if self.config.log_responses:
                    self.logger.debug(f"[Comet] Response: {json.dumps(data, indent=2)}")
                
                return CometResponse(success=True, data=data)
            
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text}"
                self.logger.warning(f"[Comet] {last_error}")
            
            except httpx.RequestError as e:
                last_error = f"Request failed: {str(e)}"
                self.logger.warning(f"[Comet] {last_error}")
            
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                self.logger.error(f"[Comet] {last_error}", exc_info=True)
            
            # 재시도 전 대기
            if attempt < self.config.retry_attempts:
                await asyncio.sleep(self.config.retry_delay * attempt)
        
        # 모든 재시도 실패
        return CometResponse(success=False, error=last_error)
    
    # ------------------------------------------------------------------------
    # API Methods
    # ------------------------------------------------------------------------
    
    async def health_check(self) -> bool:
        """
        Health Check
        
        Returns:
            bool: 서버 정상 여부
        """
        response = await self._request("GET", CometEndpoint.HEALTH.value)
        return response.success and response.data is not None and response.data.get("status") == "ok"
    
    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None,
        stream: bool = False
    ) -> CometResponse:
        """
        Perplexity 검색 요청
        
        Args:
            query: 검색 쿼리
            user_id: 사용자 ID (선택)
            context: 컨텍스트 정보 (선택)
            stream: 스트리밍 응답 여부
        
        Returns:
            CometResponse: 검색 결과
        """
        request = SearchRequest(
            query=query,
            user_id=user_id,
            context=context,
            stream=stream
        )
        
        return await self._request(
            method="POST",
            endpoint=CometEndpoint.SEARCH.value,
            json_data={
                "query": request.query,
                "user_id": request.user_id,
                "context": request.context,
                "stream": request.stream
            }
        )
    
    async def get_youtube_metadata(
        self,
        video_id: str,
        fetch_transcript: bool = True,
        fetch_comments: bool = False
    ) -> CometResponse:
        """
        YouTube 메타데이터 조회
        
        Args:
            video_id: YouTube 비디오 ID (예: "dQw4w9WgXcQ")
            fetch_transcript: 자막 포함 여부
            fetch_comments: 댓글 포함 여부 (미구현)
        
        Returns:
            CometResponse: 메타데이터 (제목, 자막, 등)
        """
        return await self._request(
            method="GET",
            endpoint=CometEndpoint.YOUTUBE.value,
            params={
                "video_id": video_id,
                "transcript": str(fetch_transcript).lower(),
                "comments": str(fetch_comments).lower()
            }
        )
    
    async def create_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        priority: int = 5,
        timeout: Optional[float] = None
    ) -> CometResponse:
        """
        RPA 태스크 생성
        
        Args:
            task_type: 태스크 타입 ("youtube_play", "screenshot", etc.)
            parameters: 태스크 파라미터
            priority: 우선순위 (1=최고, 10=최저)
            timeout: 타임아웃 (초)
        
        Returns:
            CometResponse: 태스크 ID 및 상태
        """
        request = TaskRequest(
            task_type=task_type,
            parameters=parameters,
            priority=priority,
            timeout=timeout
        )
        
        return await self._request(
            method="POST",
            endpoint=CometEndpoint.TASK_CREATE.value,
            json_data={
                "type": request.task_type,
                "params": request.parameters,
                "priority": request.priority,
                "timeout": request.timeout
            }
        )


# ============================================================================
# Comet WebSocket Client
# ============================================================================

class CometWSClient:
    """
    Comet WebSocket Client (이벤트 스트림)
    
    사용 예시:
        client = CometWSClient()
        
        @client.on_event("youtube_metadata")
        async def handle_youtube(data):
            print(f"YouTube 메타데이터: {data}")
        
        await client.connect()
        await client.listen()
    """
    
    def __init__(self, config: Optional[CometConfig] = None):
        self.config = config or CometConfig()
        self.ws = None
        self.running = False
        self.handlers: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)
    
    def on_event(self, event_type: str):
        """
        이벤트 핸들러 데코레이터
        
        사용 예시:
            @client.on_event("youtube_metadata")
            async def handle_youtube(data):
                print(data)
        """
        def decorator(func: Callable):
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(func)
            return func
        return decorator
    
    async def connect(self, endpoint: str = CometEndpoint.WS_EVENTS.value):
        """WebSocket 연결"""
        ws_url = self.config.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}{endpoint}"
        
        try:
            self.ws = await ws_connect(ws_url, ping_interval=self.config.ws_heartbeat)
            self.running = True
            self.logger.info(f"[Comet WS] Connected to {ws_url}")
        except Exception as e:
            self.logger.error(f"[Comet WS] Connection failed: {e}")
            raise
    
    async def listen(self):
        """
        이벤트 수신 루프
        
        WebSocket에서 이벤트를 수신하고 등록된 핸들러 호출
        """
        if not self.ws:
            raise RuntimeError("WebSocket not connected. Call connect() first.")
        
        try:
            while self.running:
                message = await self.ws.recv()
                
                try:
                    event = json.loads(message)
                    event_type = event.get("type")
                    event_data = event.get("data", {})
                    
                    if self.config.log_events:
                        self.logger.info(f"[Comet WS] Event: {event_type}")
                    
                    # 핸들러 실행
                    if event_type in self.handlers:
                        for handler in self.handlers[event_type]:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(event_data)
                                else:
                                    handler(event_data)
                            except Exception as e:
                                self.logger.error(
                                    f"[Comet WS] Handler error: {e}",
                                    exc_info=True
                                )
                
                except json.JSONDecodeError:
                    self.logger.warning(f"[Comet WS] Invalid JSON: {message}")
        
        except ConnectionClosed:
            self.logger.warning("[Comet WS] Connection closed")
            if self.config.ws_reconnect:
                await self._reconnect()
        
        except Exception as e:
            self.logger.error(f"[Comet WS] Listen error: {e}", exc_info=True)
    
    async def _reconnect(self):
        """재연결 (지수 백오프)"""
        for attempt in range(1, self.config.retry_attempts + 1):
            delay = self.config.retry_delay * (2 ** (attempt - 1))
            self.logger.info(f"[Comet WS] Reconnecting in {delay}s... (attempt {attempt})")
            await asyncio.sleep(delay)
            
            try:
                await self.connect()
                await self.listen()
                return
            except Exception:
                pass
        
        self.logger.error("[Comet WS] Reconnection failed after all attempts")
        self.running = False
    
    async def send(self, event_type: str, data: Dict[str, Any]):
        """이벤트 전송"""
        if not self.ws:
            raise RuntimeError("WebSocket not connected")
        
        message = json.dumps({"type": event_type, "data": data})
        await self.ws.send(message)
    
    async def close(self):
        """연결 종료"""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.logger.info("[Comet WS] Connection closed")


# ============================================================================
# Convenience Functions
# ============================================================================

async def quick_search(query: str, base_url: str = "http://localhost:8090") -> Optional[Dict]:
    """
    빠른 검색 헬퍼 함수
    
    사용 예시:
        result = await quick_search("AI 최신 동향")
        print(result)
    """
    config = CometConfig(base_url=base_url)
    async with CometHTTPClient(config) as client:
        response = await client.search(query)
        return response.data if response.success else None


async def quick_youtube(video_id: str, base_url: str = "http://localhost:8090") -> Optional[Dict]:
    """
    빠른 YouTube 메타데이터 조회
    
    사용 예시:
        metadata = await quick_youtube("dQw4w9WgXcQ")
        print(metadata["title"])
    """
    config = CometConfig(base_url=base_url)
    async with CometHTTPClient(config) as client:
        response = await client.get_youtube_metadata(video_id)
        return response.data if response.success else None


# ============================================================================
# Main (테스트용)
# ============================================================================

async def main():
    """테스트 실행"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    # HTTP 테스트
    print("\n=== Comet HTTP Client Test ===\n")
    
    async with CometHTTPClient() as client:
        # Health Check
        healthy = await client.health_check()
        print(f"Health Check: {'✅ OK' if healthy else '❌ Failed'}")
        
        # Search (Comet 서버 실행 필요)
        # response = await client.search("Python asyncio tutorial")
        # print(f"Search Result: {response.data}")
    
    # WebSocket 테스트 (주석 처리 - 서버 필요)
    # print("\n=== Comet WebSocket Client Test ===\n")
    # 
    # ws_client = CometWSClient()
    # 
    # @ws_client.on_event("test")
    # async def handle_test(data):
    #     print(f"Received: {data}")
    # 
    # await ws_client.connect()
    # await ws_client.listen()


if __name__ == "__main__":
    asyncio.run(main())
