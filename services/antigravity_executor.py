"""
Antigravity Executor - 실행 레이어
=====================================

Front-Engine의 신호를 받아 실제 윈도우 제어를 수행하는 실행 엔진.

코어 설계서 기준:
- 프론트엔진의 설계 해석
- 현재 가능한 기능 판단
- UI 자동 조작을 통해 모델 전환 및 작업 실행
"""

import asyncio
import subprocess
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from enum import Enum

# RPA Core import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "fdo_agi_repo"))

try:
    from rpa.core import RPACore, RPACoreConfig, ScreenRegion
    RPA_AVAILABLE = True
except ImportError:
    RPA_AVAILABLE = False
    print("⚠️ RPA Core not available")


class ExecutionType(Enum):
    """실행 타입"""
    MOUSE_CLICK = "mouse_click"
    KEYBOARD_TYPE = "keyboard_type"
    HOTKEY = "hotkey"
    SCREENSHOT = "screenshot"
    OPEN_APP = "open_app"
    SHELL_COMMAND = "shell_command"
    FILE_OPERATION = "file_operation"
    NAVIGATE = "navigate"


@dataclass
class ExecutionRequest:
    """실행 요청"""
    action_type: ExecutionType
    target: Optional[str] = None
    params: Dict[str, Any] = None
    require_approval: bool = True
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}


@dataclass
class ExecutionResult:
    """실행 결과"""
    success: bool
    action_type: ExecutionType
    message: str
    output: Optional[Any] = None
    screenshot_path: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class AntigravityExecutor:
    """
    Antigravity 실행 엔진
    
    Front-Engine → 실행 변환 → 윈도우 제어
    """
    
    def __init__(self, require_approval: bool = True):
        self.require_approval = require_approval
        self.logger = logging.getLogger("antigravity")
        self.logger.setLevel(logging.INFO)
        
        # RPA Core 초기화
        if RPA_AVAILABLE:
            self.rpa = RPACore(RPACoreConfig(
                pause=0.3,
                failsafe=True,
                enable_ocr=False
            ))
            self.logger.info("✓ Antigravity Executor initialized with RPA")
        else:
            self.rpa = None
            self.logger.warning("⚠ RPA Core not available - limited functionality")
        
        # 안전한 명령 목록
        self.safe_commands = {
            "notepad", "calc", "explorer", "mspaint", "code",
            "chrome", "firefox", "edge"
        }
        
        # 의미(meaning) → 실행 타입 매핑
        self.meaning_to_execution = {
            "CREATE": [ExecutionType.OPEN_APP, ExecutionType.FILE_OPERATION],
            "MODIFY": [ExecutionType.KEYBOARD_TYPE, ExecutionType.FILE_OPERATION],
            "QUERY": [ExecutionType.SCREENSHOT],
            "VERIFY": [ExecutionType.SCREENSHOT],
            "DELETE": [ExecutionType.FILE_OPERATION],
            "NAVIGATE": [ExecutionType.NAVIGATE, ExecutionType.MOUSE_CLICK],
        }
    
    def interpret_front_engine_output(self, fe_output: Dict[str, Any]) -> List[ExecutionRequest]:
        """Front-Engine 출력을 실행 요청으로 변환"""
        requests = []
        
        meaning = fe_output.get("meaning", "")
        raw_input = fe_output.get("input", "")
        rhythm = fe_output.get("rhythm", "normal")
        validated = fe_output.get("validated", True)
        warnings = fe_output.get("warnings", [])
        
        # 위험 경고가 있으면 승인 필수
        require_approval = len([w for w in warnings if "CRITICAL" in w]) > 0 or not validated
        
        # 입력 텍스트 분석
        lower_input = raw_input.lower()
        
        # 앱 실행 패턴
        app_patterns = {
            "메모장": "notepad",
            "notepad": "notepad",
            "계산기": "calc",
            "calculator": "calc",
            "calc": "calc",
            "탐색기": "explorer",
            "explorer": "explorer",
            "그림판": "mspaint",
            "paint": "mspaint",
            "vscode": "code",
            "vs code": "code",
            "코드": "code",
            "크롬": "chrome",
            "chrome": "chrome",
            "브라우저": "chrome",
        }
        
        for pattern, app in app_patterns.items():
            if pattern in lower_input:
                # 모든 앱 실행은 pending에 표시, safe 여부만 추가 정보로
                requests.append(ExecutionRequest(
                    action_type=ExecutionType.OPEN_APP,
                    target=app,
                    params={"is_safe": app in self.safe_commands},
                    require_approval=True  # 항상 pending에 표시
                ))
                break
        
        # 스크린샷 패턴
        if any(kw in lower_input for kw in ["스크린샷", "화면 캡처", "screenshot", "캡처"]):
            requests.append(ExecutionRequest(
                action_type=ExecutionType.SCREENSHOT,
                require_approval=False
            ))
        
        # 클릭 패턴
        if any(kw in lower_input for kw in ["클릭", "click", "눌러"]):
            # 좌표 추출 시도 (예: "100, 200 클릭")
            import re
            coord_match = re.search(r'(\d+)\s*,\s*(\d+)', raw_input)
            if coord_match:
                x, y = int(coord_match.group(1)), int(coord_match.group(2))
                requests.append(ExecutionRequest(
                    action_type=ExecutionType.MOUSE_CLICK,
                    params={"x": x, "y": y},
                    require_approval=True
                ))
            elif "중앙" in lower_input or "center" in lower_input:
                requests.append(ExecutionRequest(
                    action_type=ExecutionType.MOUSE_CLICK,
                    params={"x": 960, "y": 540},  # 1920x1080 중앙
                    require_approval=True
                ))
        
        # 타이핑 패턴
        if any(kw in lower_input for kw in ["입력", "타이핑", "type", "작성"]):
            # 따옴표 안의 텍스트 추출
            import re
            text_match = re.search(r'["\'](.+?)["\']', raw_input)
            if text_match:
                requests.append(ExecutionRequest(
                    action_type=ExecutionType.KEYBOARD_TYPE,
                    params={"text": text_match.group(1)},
                    require_approval=True
                ))
        
        # 단축키 패턴
        hotkey_patterns = {
            "복사": ["ctrl", "c"],
            "붙여넣기": ["ctrl", "v"],
            "저장": ["ctrl", "s"],
            "실행취소": ["ctrl", "z"],
            "전체선택": ["ctrl", "a"],
        }
        for pattern, keys in hotkey_patterns.items():
            if pattern in lower_input:
                requests.append(ExecutionRequest(
                    action_type=ExecutionType.HOTKEY,
                    params={"keys": keys},
                    require_approval=True
                ))
        
        return requests
    
    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """실행 요청 처리"""
        self.logger.info(f"Executing: {request.action_type.value} - {request.target or request.params}")
        
        try:
            if request.action_type == ExecutionType.OPEN_APP:
                return await self._execute_open_app(request)
            elif request.action_type == ExecutionType.SCREENSHOT:
                return await self._execute_screenshot(request)
            elif request.action_type == ExecutionType.MOUSE_CLICK:
                return await self._execute_mouse_click(request)
            elif request.action_type == ExecutionType.KEYBOARD_TYPE:
                return await self._execute_keyboard_type(request)
            elif request.action_type == ExecutionType.HOTKEY:
                return await self._execute_hotkey(request)
            elif request.action_type == ExecutionType.SHELL_COMMAND:
                return await self._execute_shell(request)
            else:
                return ExecutionResult(
                    success=False,
                    action_type=request.action_type,
                    message=f"Unsupported action type: {request.action_type}"
                )
        except Exception as e:
            self.logger.error(f"Execution error: {e}")
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message=f"Error: {str(e)}"
            )
    
    async def _execute_open_app(self, request: ExecutionRequest) -> ExecutionResult:
        """앱 실행"""
        app = request.target
        
        if app not in self.safe_commands:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message=f"'{app}'은(는) 안전하지 않은 명령입니다."
            )
        
        try:
            subprocess.Popen(app, shell=True)
            await asyncio.sleep(1)  # 앱 시작 대기
            
            return ExecutionResult(
                success=True,
                action_type=request.action_type,
                message=f"'{app}' 실행됨"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message=f"앱 실행 실패: {e}"
            )
    
    async def _execute_screenshot(self, request: ExecutionRequest) -> ExecutionResult:
        """스크린샷"""
        if not self.rpa:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message="RPA Core 사용 불가"
            )
        
        try:
            path = await self.rpa.save_screenshot()
            return ExecutionResult(
                success=True,
                action_type=request.action_type,
                message="스크린샷 저장됨",
                screenshot_path=str(path)
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message=f"스크린샷 실패: {e}"
            )
    
    async def _execute_mouse_click(self, request: ExecutionRequest) -> ExecutionResult:
        """마우스 클릭"""
        if not self.rpa:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message="RPA Core 사용 불가"
            )
        
        x = request.params.get("x", 0)
        y = request.params.get("y", 0)
        
        try:
            await self.rpa.click(x, y)
            return ExecutionResult(
                success=True,
                action_type=request.action_type,
                message=f"클릭: ({x}, {y})"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message=f"클릭 실패: {e}"
            )
    
    async def _execute_keyboard_type(self, request: ExecutionRequest) -> ExecutionResult:
        """키보드 입력"""
        if not self.rpa:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message="RPA Core 사용 불가"
            )
        
        text = request.params.get("text", "")
        
        try:
            await self.rpa.type_text(text)
            return ExecutionResult(
                success=True,
                action_type=request.action_type,
                message=f"입력: {text[:20]}..."
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message=f"입력 실패: {e}"
            )
    
    async def _execute_hotkey(self, request: ExecutionRequest) -> ExecutionResult:
        """단축키"""
        if not self.rpa:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message="RPA Core 사용 불가"
            )
        
        keys = request.params.get("keys", [])
        
        try:
            await self.rpa.hotkey(*keys)
            return ExecutionResult(
                success=True,
                action_type=request.action_type,
                message=f"단축키: {'+'.join(keys)}"
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message=f"단축키 실패: {e}"
            )
    
    async def _execute_shell(self, request: ExecutionRequest) -> ExecutionResult:
        """쉘 명령 실행"""
        command = request.target
        
        # 위험 명령 차단
        dangerous = ["rm", "del", "format", "shutdown", "reboot"]
        if any(d in command.lower() for d in dangerous):
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message=f"위험한 명령이 차단됨: {command}"
            )
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return ExecutionResult(
                success=result.returncode == 0,
                action_type=request.action_type,
                message="명령 실행됨",
                output=result.stdout or result.stderr
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                action_type=request.action_type,
                message="명령 타임아웃"
            )
    
    async def process_front_engine_output(
        self,
        fe_output: Dict[str, Any],
        auto_execute: bool = False
    ) -> Dict[str, Any]:
        """Front-Engine 출력을 받아 실행"""
        
        # 1. 실행 요청 변환
        requests = self.interpret_front_engine_output(fe_output)
        
        if not requests:
            return {
                "status": "no_action",
                "message": "실행할 액션이 없습니다.",
                "requests": []
            }
        
        # 2. 승인 필요 여부 확인
        pending_approval = [r for r in requests if r.require_approval]
        auto_executable = [r for r in requests if not r.require_approval]
        
        results = []
        
        # 3. 자동 실행 가능한 것 먼저 실행
        if auto_execute:
            for req in auto_executable:
                result = await self.execute(req)
                results.append(result.__dict__)
        
        return {
            "status": "processed",
            "auto_executed": len(results),
            "pending_approval": len(pending_approval),
            "pending_requests": [
                {"type": r.action_type.value, "target": r.target, "params": r.params}
                for r in pending_approval
            ],
            "results": results,
            "message": f"{len(results)}개 실행됨, {len(pending_approval)}개 승인 대기"
        }


# FastAPI 라우터 생성
def create_antigravity_routes(app):
    """FastAPI 앱에 Antigravity 라우트 추가"""
    from fastapi import APIRouter
    from pydantic import BaseModel
    from typing import Optional
    
    router = APIRouter(prefix="/antigravity", tags=["Antigravity Executor"])
    executor = AntigravityExecutor(require_approval=True)
    
    class ExecuteRequest(BaseModel):
        input: str
        auto_execute: bool = False
    
    class DirectExecuteRequest(BaseModel):
        action_type: str
        target: Optional[str] = None
        params: Optional[Dict[str, Any]] = None
    
    @router.post("/process")
    async def process_input(request: ExecuteRequest):
        """Front-Engine을 거쳐 실행"""
        # Front-Engine 호출
        from front_engine import UnifiedFrontEngine
        fe = UnifiedFrontEngine()
        fe_output = fe.process(request.input)
        
        # Antigravity 실행
        result = await executor.process_front_engine_output(
            fe_output,
            auto_execute=request.auto_execute
        )
        
        return {
            "front_engine": fe_output,
            "execution": result
        }
    
    @router.post("/execute")
    async def direct_execute(request: DirectExecuteRequest):
        """직접 실행 (승인된 요청)"""
        try:
            action_type = ExecutionType(request.action_type)
        except ValueError:
            return {"error": f"Unknown action type: {request.action_type}"}
        
        exec_request = ExecutionRequest(
            action_type=action_type,
            target=request.target,
            params=request.params or {},
            require_approval=False
        )
        
        result = await executor.execute(exec_request)
        return result.__dict__
    
    @router.get("/status")
    async def get_status():
        """Antigravity 상태"""
        return {
            "status": "active",
            "rpa_available": RPA_AVAILABLE,
            "safe_commands": list(executor.safe_commands),
            "supported_actions": [e.value for e in ExecutionType]
        }
    
    app.include_router(router)
    return router


# 테스트
if __name__ == "__main__":
    import asyncio
    
    async def test():
        executor = AntigravityExecutor()
        
        # 테스트 입력들
        test_inputs = [
            {"input": "메모장 열어줘", "meaning": "CREATE"},
            {"input": "스크린샷 찍어", "meaning": "QUERY"},
            {"input": "화면 중앙 클릭해줘", "meaning": "NAVIGATE"},
        ]
        
        print("=" * 60)
        print("Antigravity Executor 테스트")
        print("=" * 60)
        
        for inp in test_inputs:
            print(f"\n입력: {inp['input']}")
            requests = executor.interpret_front_engine_output(inp)
            print(f"  변환된 요청: {len(requests)}개")
            for req in requests:
                print(f"    - {req.action_type.value}: {req.target or req.params}")
                print(f"      승인필요: {req.require_approval}")
    
    asyncio.run(test())
