"""
RPA Bridge Module
Phase 2.5 Day 3: Task Queue Server와 RPA 명령 통신

담당:
- RPA 명령 전송 (클릭, 타이핑, 스크린샷, OCR 등)
- Task Queue Server 통신 (POST /api/tasks/enqueue, GET /api/tasks/result)
- 비동기 결과 대기 및 재시도 로직
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

import httpx


class RPAAction(str, Enum):
    """
    RPA 액션 타입
    
    지원되는 명령:
    - CLICK: 좌표 또는 이미지 기반 클릭
    - TYPE: 텍스트 입력
    - HOTKEY: 단축키 실행 (Ctrl+C, Alt+Tab 등)
    - SCREENSHOT: 화면 캡처
    - OCR: 텍스트 인식
    - FIND_ELEMENT: 이미지 템플릿 찾기
    - WAIT: 대기 (초 단위)
    - OPEN_BROWSER: 브라우저 실행 + URL 이동
    """
    CLICK = "click"
    TYPE = "type"
    HOTKEY = "hotkey"
    SCREENSHOT = "screenshot"
    OCR = "ocr"
    FIND_ELEMENT = "find_element"
    WAIT = "wait"
    OPEN_BROWSER = "open_browser"


@dataclass
class RPACommand:
    """
    RPA 명령 데이터 모델
    
    Attributes:
        action: 액션 타입 (RPAAction enum)
        params: 액션별 파라미터
        timeout: 최대 실행 시간 (초)
        retry_on_fail: 실패 시 재시도 여부
        max_retries: 최대 재시도 횟수
        
    Examples:
        # 클릭 명령
        RPACommand(
            action=RPAAction.CLICK,
            params={"x": 100, "y": 200}
        )
        
        # 텍스트 입력
        RPACommand(
            action=RPAAction.TYPE,
            params={"text": "Hello World", "interval": 0.1}
        )
        
        # 브라우저 열기
        RPACommand(
            action=RPAAction.OPEN_BROWSER,
            params={"url": "https://www.google.com"}
        )
        
        # 스크린샷 + OCR
        RPACommand(
            action=RPAAction.SCREENSHOT,
            params={"region": None, "save_path": "outputs/screen.png"}
        )
    """
    action: RPAAction
    params: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    retry_on_fail: bool = False
    max_retries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Task Queue Server 전송용 dict 변환"""
        return {
            'action': self.action.value,
            'params': self.params,
            'timeout': self.timeout,
            'retry_on_fail': self.retry_on_fail,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RPACommand':
        """dict → RPACommand 변환"""
        return cls(
            action=RPAAction(data.get('action', 'wait')),
            params=data.get('params', {}),
            timeout=data.get('timeout', 30.0),
            retry_on_fail=data.get('retry_on_fail', False),
            max_retries=data.get('max_retries', 0)
        )


@dataclass
class RPAResult:
    """
    RPA 명령 실행 결과
    
    Attributes:
        success: 성공 여부
        data: 반환 데이터 (스크린샷 경로, OCR 텍스트 등)
        error: 에러 메시지 (실패 시)
        execution_time: 실행 시간 (초)
        timestamp: 완료 시각
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RPAResult':
        """dict → RPAResult 변환"""
        return cls(
            success=data.get('success', False),
            data=data.get('data'),
            error=data.get('error'),
            execution_time=data.get('execution_time', 0.0),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now()
        )


class RPABridge:
    """
    RPA Bridge: Task Queue Server와 통신
    
    Phase 2.5 Day 3: RPA 명령을 Task Queue에 전송하고 결과 대기
    
    Usage:
        bridge = RPABridge(queue_url='http://localhost:8091')
        
        # 단일 명령 실행
        command = RPACommand(
            action=RPAAction.CLICK,
            params={'x': 100, 'y': 200}
        )
        result = await bridge.execute_command(command)
        
        if result.success:
            print(f"Success: {result.data}")
        else:
            print(f"Failed: {result.error}")
        
        # 명령 배치 실행
        commands = [
            RPACommand(RPAAction.OPEN_BROWSER, {'url': 'https://www.google.com'}),
            RPACommand(RPAAction.WAIT, {'seconds': 2}),
            RPACommand(RPAAction.SCREENSHOT, {'save_path': 'outputs/google.png'})
        ]
        results = await bridge.execute_batch(commands)
    """
    
    def __init__(
        self,
        queue_url: str = "http://localhost:8091",
        poll_interval: float = 0.5,
        max_poll_attempts: int = 120
    ):
        """
        Args:
            queue_url: Task Queue Server URL
            poll_interval: 결과 폴링 간격 (초)
            max_poll_attempts: 최대 폴링 시도 횟수 (기본 60초)
        """
        self.queue_url = queue_url
        self.poll_interval = poll_interval
        self.max_poll_attempts = max_poll_attempts
        
        self.logger = logging.getLogger("RPABridge")
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Context manager entry"""
        self.session = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, *args):
        """Context manager exit"""
        if self.session:
            await self.session.aclose()
    
    async def health_check(self) -> bool:
        """
        Task Queue Server 상태 확인
        
        Returns:
            True if server is healthy
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context.")
        
        try:
            response = await self.session.get(f"{self.queue_url}/api/health")
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok':
                self.logger.info(
                    f"[RPABridge] Task Queue Server: ONLINE "
                    f"(queue_size={data.get('queue_size', 0)})"
                )
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"[RPABridge] Health check failed: {e}")
            return False
    
    async def execute_command(
        self,
        command: RPACommand,
        wait_for_result: bool = True
    ) -> Optional[RPAResult]:
        """
        단일 RPA 명령 실행
        
        Args:
            command: 실행할 RPA 명령
            wait_for_result: 결과 대기 여부 (False면 task_id만 반환)
        
        Returns:
            RPAResult 또는 None (실패 시)
        
        Example:
            result = await bridge.execute_command(
                RPACommand(RPAAction.CLICK, {'x': 100, 'y': 200})
            )
            print(result.success, result.data)
        """
        try:
            start_time = time.time()
            
            self.logger.info(f"[RPABridge] Executing: {command.action.value}")
            
            # 1. Task 등록
            task_id = await self._enqueue_task(command)
            
            if not task_id:
                return RPAResult(
                    success=False,
                    error="Failed to enqueue task",
                    execution_time=time.time() - start_time
                )
            
            self.logger.info(f"[RPABridge] Task enqueued: {task_id}")
            
            if not wait_for_result:
                return RPAResult(
                    success=True,
                    data={'task_id': task_id},
                    execution_time=time.time() - start_time
                )
            
            # 2. 결과 대기 (폴링)
            result = await self._poll_result(task_id, command.timeout)
            
            if result:
                result.execution_time = time.time() - start_time
                self.logger.info(
                    f"[RPABridge] ✅ Completed in {result.execution_time:.2f}s"
                )
            else:
                self.logger.error(f"[RPABridge] ❌ Timeout after {command.timeout}s")
                result = RPAResult(
                    success=False,
                    error=f"Timeout after {command.timeout}s",
                    execution_time=time.time() - start_time
                )
            
            return result
        
        except Exception as e:
            self.logger.error(f"[RPABridge] ❌ Execution failed: {e}")
            return RPAResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _enqueue_task(self, command: RPACommand) -> Optional[str]:
        """
        Task Queue에 명령 등록
        
        Args:
            command: RPA 명령
        
        Returns:
            task_id 또는 None
        """
        try:
            payload = {
                'type': 'rpa_command',
                'data': command.to_dict(),
                'priority': 5,
                'timestamp': datetime.now().isoformat()
            }
            
            response = await self.session.post(
                 f"{self.queue_url}/api/tasks/create",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('task_id')
        
        except Exception as e:
            self.logger.error(f"[RPABridge] Enqueue failed: {e}")
            return None
    
    async def _poll_result(
        self,
        task_id: str,
        timeout: float
    ) -> Optional[RPAResult]:
        """
        Task 결과 폴링
        
        Args:
            task_id: Task ID
            timeout: 최대 대기 시간 (초)
        
        Returns:
            RPAResult 또는 None (타임아웃)
        """
        max_attempts = int(timeout / self.poll_interval)
        
        for attempt in range(max_attempts):
            try:
                response = await self.session.get(
                    f"{self.queue_url}/api/tasks/result/{task_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('status') == 'completed':
                        return RPAResult.from_dict(data.get('result', {}))
                    
                    elif data.get('status') == 'failed':
                        return RPAResult(
                            success=False,
                            error=data.get('error', 'Task failed')
                        )
                
                # 결과 없으면 대기
                await asyncio.sleep(self.poll_interval)
            
            except Exception as e:
                self.logger.warning(f"[RPABridge] Poll error (attempt {attempt}): {e}")
                await asyncio.sleep(self.poll_interval)
        
        # 타임아웃
        return None
    
    async def execute_batch(
        self,
        commands: List[RPACommand],
        stop_on_error: bool = True
    ) -> List[RPAResult]:
        """
        여러 RPA 명령 순차 실행
        
        Args:
            commands: 실행할 명령 리스트
            stop_on_error: 에러 발생 시 중단 여부
        
        Returns:
            RPAResult 리스트
        
        Example:
            commands = [
                RPACommand(RPAAction.OPEN_BROWSER, {'url': 'https://www.google.com'}),
                RPACommand(RPAAction.WAIT, {'seconds': 2}),
                RPACommand(RPAAction.SCREENSHOT, {'save_path': 'outputs/google.png'})
            ]
            results = await bridge.execute_batch(commands)
            
            for i, result in enumerate(results):
                print(f"Command {i}: {'✅' if result.success else '❌'}")
        """
        results = []
        
        self.logger.info(f"[RPABridge] Executing batch: {len(commands)} commands")
        
        for i, command in enumerate(commands):
            self.logger.info(f"[RPABridge] [{i+1}/{len(commands)}] {command.action.value}")
            
            result = await self.execute_command(command)
            results.append(result)
            
            if not result.success and stop_on_error:
                self.logger.error(
                    f"[RPABridge] ❌ Batch stopped at command {i+1}: {result.error}"
                )
                break
        
        success_count = sum(1 for r in results if r.success)
        self.logger.info(
            f"[RPABridge] Batch complete: {success_count}/{len(results)} succeeded"
        )
        
        return results
    
    async def get_queue_status(self) -> Optional[Dict[str, Any]]:
        """
        Task Queue 상태 조회
        
        Returns:
            {'queue_size': int, 'results_count': int} 또는 None
        """
        try:
            response = await self.session.get(f"{self.queue_url}/api/health")
            response.raise_for_status()
            
            data = response.json()
            return {
                'queue_size': data.get('queue_size', 0),
                'results_count': data.get('results_count', 0),
                'timestamp': data.get('timestamp')
            }
        
        except Exception as e:
            self.logger.error(f"[RPABridge] Failed to get queue status: {e}")
            return None


# Standalone Test
if __name__ == "__main__":
    async def main():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        
        print("\n" + "=" * 60)
        print("RPA BRIDGE TEST")
        print("=" * 60 + "\n")
        
        bridge = RPABridge(queue_url="http://localhost:8091")
        
        async with bridge:
            # Test 1: Health Check
            print("TEST 1: Task Queue Server Health Check")
            healthy = await bridge.health_check()
            print(f"{'✅' if healthy else '❌'} Server Status: {'ONLINE' if healthy else 'OFFLINE'}\n")
            
            if not healthy:
                print("⚠️  Task Queue Server가 실행 중이 아닙니다.")
                print("   실행 방법: 터미널에서 Task Queue Server 시작")
                return
            
            # Test 2: Queue Status
            print("TEST 2: Get Queue Status")
            status = await bridge.get_queue_status()
            if status:
                print(f"✅ Queue Size: {status['queue_size']}")
                print(f"   Results Count: {status['results_count']}\n")
            
            # Test 3: Simple Command (WAIT)
            print("TEST 3: Execute Simple Command (WAIT 1초)")
            command = RPACommand(
                action=RPAAction.WAIT,
                params={'seconds': 1},
                timeout=5.0
            )
            
            result = await bridge.execute_command(command)
            
            if result:
                print(f"{'✅' if result.success else '❌'} Result:")
                print(f"   Success: {result.success}")
                print(f"   Execution Time: {result.execution_time:.2f}s")
                if result.error:
                    print(f"   Error: {result.error}")
            else:
                print("❌ No result received")
            
            # Test 4: Batch Commands
            print(f"\nTEST 4: Execute Batch Commands")
            commands = [
                RPACommand(RPAAction.WAIT, {'seconds': 0.5}),
                RPACommand(RPAAction.WAIT, {'seconds': 0.5}),
                RPACommand(RPAAction.WAIT, {'seconds': 0.5})
            ]
            
            results = await bridge.execute_batch(commands)
            
            print(f"✅ Batch Results: {len(results)} commands")
            for i, r in enumerate(results):
                status = "✅" if r.success else "❌"
                print(f"   {status} Command {i+1}: {r.execution_time:.2f}s")
        
        print("\n" + "=" * 60)
    
    asyncio.run(main())
