"""
Slack Bot Server for Ion Canary Automation
Interactive chat interface for monitoring and controlling canary deployments
Natural conversational AI powered by Google Gemini
"""
import os
import json
import subprocess
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import google.generativeai as genai

# Configuration
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "LLM_Unified" / "ion-mentoring" / "scripts"
OUTPUTS_DIR = PROJECT_ROOT / "LLM_Unified" / "ion-mentoring" / "outputs"

app = FastAPI(title="Ion Canary Slack Bot")
slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None

# Configure Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


class CommandExecutor:
    """Execute PowerShell scripts and return results"""
    
    @staticmethod
    async def run_powershell(script_path: Path, args: Optional[list] = None) -> Dict[str, Any]:
        """Run PowerShell script asynchronously"""
        if not script_path.exists():
            return {"success": False, "error": f"Script not found: {script_path}"}
        
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)]
        if args:
            cmd.extend(args)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "returncode": process.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_state() -> Dict[str, Any]:
        """Read current canary state"""
        state_file = OUTPUTS_DIR / "auto_canary_state.json"
        if not state_file.exists():
            return {"phase": "unknown", "canary_percentage": 0}
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"phase": "unknown", "canary_percentage": 0}


class ConversationContext:
    """Manage conversation history and context"""
    
    def __init__(self):
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
    
    def add_message(self, channel: str, role: str, content: str):
        """Add message to conversation history"""
        if channel not in self.conversations:
            self.conversations[channel] = []
        
        self.conversations[channel].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages
        if len(self.conversations[channel]) > 20:
            self.conversations[channel] = self.conversations[channel][-20:]
    
    def get_history(self, channel: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history"""
        if channel not in self.conversations:
            return []
        return self.conversations[channel][-limit:]


class GitcoAI:
    """AI-powered conversational interface using Gemini"""
    
    SYSTEM_PROMPT = """당신은 "깃코(Gitco)"라는 이름의 AI 배포 엔지니어 어시스턴트입니다.

**역할과 성격:**
- 친근하고 전문적인 DevOps 엔지니어
- 복잡한 기술 내용을 쉽게 설명
- 항상 정확한 정보 제공
- 이모지를 적절히 사용해 시각적 효과 추가
- 한국어로 자연스럽게 대화

**현재 관리하는 시스템:**
- Google Cloud Run 기반 카나리 배포 시스템
- Ion API: 레거시 버전 (안정적)
- Lumen Gateway: 카나리 버전 (신규 기능 테스트 중)
- 배포 단계: 0% → 5% → 10% → 25% → 50% → 100%

**사용 가능한 기능:**
1. get_deployment_status: 현재 배포 상태 확인
2. execute_deployment: 카나리 배포 실행 (5%, 10%, 25%, 50%, 100%)
3. run_health_probe: Rate limit 및 헬스 체크 테스트
4. get_recent_logs: 최근 로그 조회
5. generate_report: 배포 리포트 생성
6. execute_rollback: 긴급 롤백 실행

**대화 가이드라인:**
- 사용자의 질문 의도를 정확히 파악
- 명령 실행 전 확인이 필요한 경우 확인 요청
- 실행 결과를 명확하고 간결하게 설명
- 에러 발생 시 원인과 해결 방법 제시
- 사용자가 요청하지 않은 작업은 제안만 하고 실행하지 않음

**응답 형식:**
- 간단한 인사나 질문: 짧고 친근하게
- 상태 확인: 이모지와 함께 핵심 정보만
- 작업 실행: 실행 내용과 예상 소요 시간 안내
- 에러: 원인 분석과 다음 단계 제안

**예시 대화:**
User: "지금 배포 상태 어때?"
Gitco: "🔍 현재 카나리 50% 배포 중이고, 모니터링 단계예요. 약 45분 후 자동으로 다음 단계로 진행될 예정입니다!"

User: "100% 올릴 수 있을까?"
Gitco: "네, 100% 배포 가능합니다! 실행하면 약 2-3분 소요되고, 이후 2시간 모니터링이 시작돼요. 바로 진행할까요?"

이제 사용자와 자연스럽게 대화하세요!"""

    def __init__(self, executor: CommandExecutor):
        self.executor = executor
        self.model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-exp',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 1024,
            }
        )
        self.tools = self._define_tools()
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define function tools for LLM"""
        return [
            {
                "name": "get_deployment_status",
                "description": "현재 카나리 배포 상태를 확인합니다. 배포 비율, 단계, 모니터링 종료 시간 등을 반환합니다.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "execute_deployment",
                "description": "지정된 비율로 카나리 배포를 실행합니다. 5%, 10%, 25%, 50%, 100% 중 선택 가능합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "percentage": {
                            "type": "integer",
                            "description": "배포 비율 (5, 10, 25, 50, 100)",
                            "enum": [5, 10, 25, 50, 100]
                        }
                    },
                    "required": ["percentage"]
                }
            },
            {
                "name": "run_health_probe",
                "description": "Rate limit 테스트 및 헬스 체크를 실행합니다. 프로브 강도를 선택할 수 있습니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "intensity": {
                            "type": "string",
                            "description": "프로브 강도 (gentle, normal, aggressive)",
                            "enum": ["gentle", "normal", "aggressive"],
                            "default": "normal"
                        }
                    }
                }
            },
            {
                "name": "get_recent_logs",
                "description": "최근 로그를 조회합니다. 시간 범위를 지정할 수 있습니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hours": {
                            "type": "integer",
                            "description": "조회할 시간 범위 (시간 단위)",
                            "default": 1
                        }
                    }
                }
            },
            {
                "name": "generate_report",
                "description": "배포 리포트를 생성합니다.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "name": "execute_rollback",
                "description": "긴급 롤백을 실행하여 카나리 배포를 0%로 되돌립니다. 심각한 문제 발생 시에만 사용합니다.",
                "parameters": {"type": "object", "properties": {}}
            }
        ]
    
    async def chat(self, user_message: str, channel: str, context: ConversationContext) -> str:
        """Process user message and generate response"""
        
        # Get conversation history
        history = context.get_history(channel)
        
        # Build messages for Gemini
        messages = [{"role": "user", "parts": [self.SYSTEM_PROMPT]}]
        
        # Add conversation history
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            messages.append({"role": role, "parts": [msg["content"]]})
        
        # Add current state as context
        state = self.executor.get_state()
        state_context = f"\n\n[현재 시스템 상태]\n"
        state_context += f"- 배포 비율: {state.get('canary_percentage', 0)}%\n"
        state_context += f"- 단계: {state.get('phase', 'unknown')}\n"
        if state.get('monitor_end'):
            end_time = datetime.fromisoformat(state['monitor_end'])
            remaining = (end_time - datetime.now()).total_seconds() / 60
            if remaining > 0:
                state_context += f"- 모니터링 종료까지: {int(remaining)}분\n"
        
        # Add user message with state context
        messages.append({"role": "user", "parts": [f"{user_message}{state_context}"]})
        
        # Generate response with function calling
        try:
            chat = self.model.start_chat(history=messages[:-1])
            response = await asyncio.to_thread(
                chat.send_message,
                messages[-1]["parts"][0],
                tools=self._create_gemini_tools()
            )
            
            # Check if function call is needed
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                function_name = function_call.name
                function_args = dict(function_call.args)
                
                # Execute function
                result = await self._execute_function(function_name, function_args)
                
                # Send result back to Gemini for natural response
                response = await asyncio.to_thread(
                    chat.send_message,
                    f"[함수 실행 결과]\n{json.dumps(result, ensure_ascii=False, indent=2)}"
                )
            
            return response.text
            
        except Exception as e:
            return f"죄송합니다, 응답 생성 중 오류가 발생했어요. 😅\n오류: {str(e)}"
    
    def _create_gemini_tools(self) -> List:
        """Create Gemini function calling tools"""
        from google.generativeai.types import FunctionDeclaration, Tool
        
        declarations = []
        for tool_def in self.tools:
            declarations.append(
                FunctionDeclaration(
                    name=tool_def["name"],
                    description=tool_def["description"],
                    parameters=tool_def["parameters"]
                )
            )
        
        return [Tool(function_declarations=declarations)]
    
    async def _execute_function(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute requested function"""
        
        if function_name == "get_deployment_status":
            state = self.executor.get_state()
            return {
                "success": True,
                "data": state
            }
        
        elif function_name == "execute_deployment":
            percentage = args.get("percentage")
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "deploy_phase4_canary.ps1",
                ["-ProjectId", "naeda-genesis", "-CanaryPercentage", str(percentage)]
            )
            return result
        
        elif function_name == "run_health_probe":
            intensity = args.get("intensity", "normal")
            probe_configs = {
                "gentle": {"requests": 3, "delay": 2000},
                "normal": {"requests": 10, "delay": 1000},
                "aggressive": {"requests": 25, "delay": 500}
            }
            config = probe_configs[intensity]
            
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "rate_limit_probe.ps1",
                [
                    "-RequestsPerSide", str(config["requests"]),
                    "-DelayMsBetweenRequests", str(config["delay"])
                ]
            )
            return result
        
        elif function_name == "get_recent_logs":
            hours = args.get("hours", 1)
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "filter_logs_by_time.ps1",
                ["-Last", f"{hours}h", "-ShowSummary"]
            )
            return result
        
        elif function_name == "generate_report":
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "generate_daily_report.ps1",
                ["-Hours", "24"]
            )
            return result
        
        elif function_name == "execute_rollback":
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "rollback_phase4_canary.ps1",
                ["-ProjectId", "naeda-genesis", "-AutoApprove"]
            )
            return result
        
        else:
            return {"success": False, "error": f"Unknown function: {function_name}"}


class CommandParser:
    """Parse natural language commands from Slack"""
    
    COMMANDS = {
        "status": ["상태", "status", "어떻게", "진행", "확인"],
        "deploy": ["배포", "deploy", "올려", "카나리"],
        "probe": ["프로브", "probe", "테스트", "체크"],
        "logs": ["로그", "logs", "에러", "문제"],
        "report": ["리포트", "report", "보고서", "요약"],
        "help": ["도움", "help", "명령어", "사용법"],
        "rollback": ["롤백", "rollback", "되돌려", "취소"],
    }
    
    @classmethod
    def parse(cls, text: str) -> tuple[str, Dict[str, Any]]:
        """Parse command and extract parameters"""
        text_lower = text.lower()
        
        # Check for each command type
        for cmd, keywords in cls.COMMANDS.items():
            if any(kw in text_lower for kw in keywords):
                params = cls._extract_params(cmd, text)
                return cmd, params
        
        return "unknown", {}
    
    @staticmethod
    def _extract_params(cmd: str, text: str) -> Dict[str, Any]:
        """Extract parameters based on command type"""
        params = {}
        
        if cmd == "deploy":
            # Extract percentage: "100%", "50%", etc.
            for word in text.split():
                if "%" in word:
                    try:
                        params["percentage"] = int(word.replace("%", ""))
                    except ValueError:
                        pass
        
        elif cmd == "probe":
            # Extract count if mentioned
            if "gentle" in text.lower() or "부드럽게" in text.lower():
                params["type"] = "gentle"
            elif "aggressive" in text.lower() or "강하게" in text.lower():
                params["type"] = "aggressive"
            else:
                params["type"] = "normal"
        
        return params


class MessageHandler:
    """Handle Slack messages and execute commands"""
    
    def __init__(self, executor: CommandExecutor, parser: CommandParser):
        self.executor = executor
        self.parser = parser
        self._last_channel: Optional[str] = None
    
    async def handle_message(self, text: str, channel: str, user: str) -> str:
        """Process message and return response"""
        cmd, params = self.parser.parse(text)
        
        if cmd == "status":
            return await self._handle_status()
        
        elif cmd == "deploy":
            return await self._handle_deploy(params)
        
        elif cmd == "probe":
            return await self._handle_probe(params)
        
        elif cmd == "logs":
            return await self._handle_logs()
        
        elif cmd == "report":
            return await self._handle_report()
        
        elif cmd == "rollback":
            return await self._handle_rollback()
        
        elif cmd == "help":
            return self._handle_help()
        
        else:
            return (
                "죄송합니다, 명령을 이해하지 못했습니다. 😅\n"
                "`도움말` 또는 `help`를 입력하시면 사용 가능한 명령어를 확인할 수 있습니다."
            )
    
    async def _handle_status(self) -> str:
        """Get current deployment status"""
        state = self.executor.get_state()
        phase = state.get("phase", "unknown")
        pct = state.get("canary_percentage", 0)
        
        # Get monitoring end time if available
        monitor_end = state.get("monitor_end")
        time_info = ""
        if monitor_end:
            end_time = datetime.fromisoformat(monitor_end)
            remaining = (end_time - datetime.now()).total_seconds() / 60
            if remaining > 0:
                time_info = f"\n⏱️ 모니터링 종료까지: {int(remaining)}분"
        
        phase_emoji = {
            "50-monitoring": "🔍",
            "100-monitoring": "🔍",
            "done": "✅",
            "unknown": "❓"
        }
        
        emoji = phase_emoji.get(phase, "🚀")
        
        return (
            f"{emoji} **현재 카나리 상태**\n"
            f"• 배포 비율: {pct}%\n"
            f"• 단계: {phase}{time_info}"
        )
    
    async def _handle_deploy(self, params: Dict[str, Any]) -> str:
        """Execute deployment"""
        percentage = params.get("percentage")
        
        if not percentage:
            return "배포 비율을 지정해주세요 (예: `50% 배포` 또는 `deploy 100%`)"
        
        if percentage not in [5, 10, 25, 50, 100]:
            return f"올바른 배포 비율을 선택해주세요: 5%, 10%, 25%, 50%, 100% (입력값: {percentage}%)"
        
        # Execute deployment
        await self._send_slack_message(
            f"🚀 카나리 {percentage}% 배포를 시작합니다..."
        )
        
        result = await self.executor.run_powershell(
            SCRIPTS_DIR / "deploy_phase4_canary.ps1",
            ["-ProjectId", "naeda-genesis", "-CanaryPercentage", str(percentage)]
        )
        
        if result["success"]:
            return f"✅ 카나리 {percentage}% 배포가 완료되었습니다!\n{result['stdout'][:500]}"
        else:
            error_msg = result.get('stderr') or result.get('error') or 'Unknown error'
            return f"❌ 배포 실패:\n{error_msg[:500]}"
    
    async def _handle_probe(self, params: Dict[str, Any]) -> str:
        """Execute rate limit probe"""
        probe_type = params.get("type", "normal")
        
        probe_configs = {
            "gentle": {"requests": 3, "delay": 2000},
            "normal": {"requests": 10, "delay": 1000},
            "aggressive": {"requests": 25, "delay": 500}
        }
        
        config = probe_configs[probe_type]
        
        await self._send_slack_message(
            f"🔍 {probe_type.capitalize()} 프로브 실행 중..."
        )
        
        result = await self.executor.run_powershell(
            SCRIPTS_DIR / "rate_limit_probe.ps1",
            [
                "-RequestsPerSide", str(config["requests"]),
                "-DelayMsBetweenRequests", str(config["delay"])
            ]
        )
        
        if result["success"]:
            # Parse probe results
            stdout = result["stdout"]
            success_line = [l for l in stdout.split('\n') if 'Success' in l]
            return f"✅ 프로브 완료!\n{''.join(success_line[:5])}"
        else:
            return f"❌ 프로브 실패:\n{result.get('stderr', '')[:500]}"
    
    async def _handle_logs(self) -> str:
        """Get recent logs"""
        result = await self.executor.run_powershell(
            SCRIPTS_DIR / "filter_logs_by_time.ps1",
            ["-Last", "1h", "-ShowSummary"]
        )
        
        if result["success"]:
            return f"📋 최근 1시간 로그:\n```{result['stdout'][:1000]}```"
        else:
            return "❌ 로그 조회 실패"
    
    async def _handle_report(self) -> str:
        """Generate daily report"""
        await self._send_slack_message("📊 일일 리포트 생성 중...")
        
        result = await self.executor.run_powershell(
            SCRIPTS_DIR / "generate_daily_report.ps1",
            ["-Hours", "24"]
        )
        
        if result["success"]:
            return f"✅ 리포트 생성 완료!\n```{result['stdout'][:1000]}```"
        else:
            return "❌ 리포트 생성 실패"
    
    async def _handle_rollback(self) -> str:
        """Execute emergency rollback"""
        await self._send_slack_message("⚠️ 긴급 롤백을 시작합니다...")
        
        result = await self.executor.run_powershell(
            SCRIPTS_DIR / "rollback_phase4_canary.ps1",
            ["-ProjectId", "naeda-genesis", "-AutoApprove"]
        )
        
        if result["success"]:
            return "✅ 롤백 완료!"
        else:
            return f"❌ 롤백 실패:\n{result.get('stderr', '')[:500]}"
    
    def _handle_help(self) -> str:
        """Return help message"""
        return """
🤖 **깃코 명령어 가이드**

**배포 관련:**
• `상태` / `status` - 현재 배포 상태 확인
• `50% 배포` / `deploy 100%` - 카나리 배포 실행
• `롤백` / `rollback` - 긴급 롤백

**모니터링:**
• `프로브` / `probe` - Rate limit 테스트 실행
• `로그` / `logs` - 최근 로그 확인
• `리포트` / `report` - 일일 보고서 생성

**기타:**
• `도움말` / `help` - 이 메시지 표시

자연스럽게 말씀해주세요! 예: "현재 상태 어떻게 돼?", "100% 배포해줘"
"""
    
    async def _send_slack_message(self, text: str, channel: Optional[str] = None):
        """Send message to Slack"""
        if not slack_client:
            return
        
        try:
            # Use stored channel from context if available
            target_channel = channel or self._last_channel
            
            if target_channel:
                slack_client.chat_postMessage(channel=target_channel, text=text)
        except SlackApiError:
            pass


# Initialize handlers
executor = CommandExecutor()
parser = CommandParser()
handler = MessageHandler(executor, parser)


@app.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack Events API"""
    body = await request.json()
    
    # URL verification challenge
    if body.get("type") == "url_verification":
        return JSONResponse({"challenge": body.get("challenge")})
    
    # Handle message events
    if body.get("type") == "event_callback":
        event = body.get("event", {})
        
        # Ignore bot messages
        if event.get("bot_id"):
            return JSONResponse({"ok": True})
        
        if event.get("type") == "message":
            text = event.get("text", "")
            channel = event.get("channel")
            user = event.get("user")
            
            # Store channel for responses
            handler._last_channel = channel
            
            # Process command
            response = await handler.handle_message(text, channel, user)
            
            # Send response
            if slack_client:
                try:
                    slack_client.chat_postMessage(channel=channel, text=response)
                except SlackApiError as e:
                    print(f"Slack API error: {e}")
    
    return JSONResponse({"ok": True})


@app.post("/slack/commands")
async def slack_commands(request: Request):
    """Handle Slack slash commands"""
    form = await request.form()
    command = form.get("command")
    text = form.get("text", "")
    channel = form.get("channel_id")
    user = form.get("user_id")
    
    # Store channel
    handler._last_channel = channel
    
    # Process command
    response = await handler.handle_message(text, channel, user)
    
    return JSONResponse({
        "response_type": "in_channel",
        "text": response
    })


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "bot_active": bool(slack_client)}


if __name__ == "__main__":
    if not SLACK_BOT_TOKEN:
        print("⚠️  SLACK_BOT_TOKEN environment variable not set!")
        print("   Set it with: [Environment]::SetEnvironmentVariable('SLACK_BOT_TOKEN', 'xoxb-...', 'User')")
    
    print(f"🚀 Starting Ion Canary Slack Bot on http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
