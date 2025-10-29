"""
Slack Bot Server for Ion Canary Automation - Natural Conversation Edition
Powered by Google Generative AI (Gemini)
"""
import os
import json
import subprocess
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import google.generativeai as genai
from google.generativeai import types

# Configuration
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "LLM_Unified" / "ion-mentoring" / "scripts"
OUTPUTS_DIR = PROJECT_ROOT / "LLM_Unified" / "ion-mentoring" / "outputs"
GCP_PROJECT = "naeda-genesis"
GCP_LOCATION = "us-central1"

app = FastAPI(title="Ion Canary Slack Bot")
slack_client = WebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None

# Configure Google GenAI
genai.configure()


class CommandExecutor:
    """Execute PowerShell scripts"""
    
    @staticmethod
    async def run_powershell(script_path: Path, args: Optional[List[str]] = None) -> Dict[str, Any]:
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


class GitcoAI:
    """Natural conversational AI assistant for deployment management"""
    
    SYSTEM_INSTRUCTION = """당신은 "깃코(Gitco)"입니다. 친근하고 유능한 AI 배포 엔지니어로서 사용자를 돕습니다.

**성격:**
- 친근하고 따뜻한 말투 (존댓말 사용)
- 기술적이지만 쉽게 설명
- 이모지를 적절히 사용
- 간결하고 명확한 답변

**관리 시스템:**
- Google Cloud Run 카나리 배포
- Ion API (레거시) vs Lumen Gateway (신규)
- 단계별 트래픽 증가: 5% → 10% → 25% → 50% → 100%

**대화 스타일:**
User: "지금 어떻게 돼?"
Gitco: "🔍 현재 카나리 50% 배포 중이에요! 모니터링하고 있으며 45분 후 다음 단계로 넘어갈 예정입니다."

User: "문제 없어?"
Gitco: "네, 모든 헬스 체크가 정상이에요! ✅ 에러율 0%, 레이턴시도 안정적입니다."

User: "100% 올려줘"
Gitco: "알겠습니다! 100% 배포를 시작할게요. 2-3분 소요되고 이후 2시간 모니터링이 진행됩니다. 🚀"

명령을 실행하기 전에는 사용자의 의도를 명확히 파악하고, 필요시 확인을 받으세요."""

    def __init__(self, executor: CommandExecutor):
        self.executor = executor
        self.model = genai.GenerativeModel(
            "gemini-2.0-flash-exp",
            system_instruction=self.SYSTEM_INSTRUCTION,
            tools=[self._create_tools()]
        )
        self.conversations: Dict[str, List] = {}
    
    def _create_tools(self) -> types.Tool:
        """Define function tools for Gemini"""
        return types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="get_status",
                    description="현재 카나리 배포 상태를 확인합니다. 배포 비율, 단계, 모니터링 남은 시간 등을 반환합니다.",
                    parameters={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.FunctionDeclaration(
                    name="deploy_canary",
                    description="지정된 비율로 카나리 배포를 실행합니다. 사용자가 명확히 배포를 요청한 경우에만 사용하세요. 가능한 비율: 5, 10, 25, 50, 100",
                    parameters={
                        "type": "object",
                        "properties": {
                            "percentage": {
                                "type": "number",
                                "description": "배포 비율 (5, 10, 25, 50, 100 중 하나)"
                            }
                        },
                        "required": ["percentage"]
                    }
                ),
                types.FunctionDeclaration(
                    name="run_probe",
                    description="헬스 체크 및 레이트 리밋 테스트를 실행합니다.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "intensity": {
                                "type": "string",
                                "description": "테스트 강도 - gentle(부드럽게), normal(보통), aggressive(강하게) 중 하나"
                            }
                        }
                    }
                ),
                types.FunctionDeclaration(
                    name="get_logs",
                    description="최근 로그를 조회합니다.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "hours": {
                                "type": "number",
                                "description": "조회할 시간 (시간 단위, 기본값 1시간)"
                            }
                        }
                    }
                ),
                types.FunctionDeclaration(
                    name="generate_report",
                    description="일일 배포 리포트를 생성합니다.",
                    parameters={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.FunctionDeclaration(
                    name="rollback",
                    description="긴급 롤백을 실행합니다. 카나리를 0%로 되돌립니다. 매우 신중하게 사용해야 합니다.",
                    parameters={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        )
    
    async def chat(self, user_message: str, channel: str) -> str:
        """Process user message and generate natural response"""
        
        # Get current state for context
        state = self.executor.get_state()
        state_info = self._format_state(state)
        
        # Prepare conversation history
        if channel not in self.conversations:
            self.conversations[channel] = []
        
        # Add context to user message
        message_with_context = f"{user_message}\n\n[시스템 상태]\n{state_info}"
        
        # Generate response
        try:
            chat_session = self.model.start_chat(history=self.conversations[channel])
            response = await asyncio.to_thread(chat_session.send_message, message_with_context)
            
            # Handle function calls
            if hasattr(response.candidates[0], 'function_calls') and response.candidates[0].function_calls:
                for function_call in response.candidates[0].function_calls:
                    result = await self._execute_function(
                        function_call.name,
                        dict(function_call.args) if function_call.args else {}
                    )
                    
                    # Send function result back to model
                    response = await asyncio.to_thread(
                        chat_session.send_message,
                        [{
                            "function_call": function_call,
                            "function_response": {"name": function_call.name, "response": result}
                        }]
                    )
            
            # Update conversation history
            self.conversations[channel].extend([
                {"role": "user", "parts": [user_message]},
                {"role": "model", "parts": [response.text]}
            ])
            
            # Keep last 20 messages
            if len(self.conversations[channel]) > 20:
                self.conversations[channel] = self.conversations[channel][-20:]
            
            return response.text
            
        except Exception as e:
            return f"죄송해요, 응답 생성 중 오류가 발생했습니다. 😢\n```{str(e)}```"
    
    def _format_state(self, state: Dict[str, Any]) -> str:
        """Format state info for context"""
        info = f"배포 비율: {state.get('canary_percentage', 0)}%\n"
        info += f"현재 단계: {state.get('phase', 'unknown')}\n"
        
        if state.get('monitor_end'):
            try:
                end_time = datetime.fromisoformat(state['monitor_end'])
                remaining = (end_time - datetime.now()).total_seconds() / 60
                if remaining > 0:
                    info += f"모니터링 종료까지: {int(remaining)}분\n"
            except:
                pass
        
        return info
    
    async def _execute_function(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute function called by LLM"""
        
        if name == "get_status":
            state = self.executor.get_state()
            return {
                "success": True,
                "phase": state.get('phase'),
                "percentage": state.get('canary_percentage'),
                "monitor_end": state.get('monitor_end')
            }
        
        elif name == "deploy_canary":
            pct = int(args.get("percentage", 5))
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "deploy_phase4_canary.ps1",
                ["-ProjectId", GCP_PROJECT, "-CanaryPercentage", str(pct)]
            )
            return {
                "success": result["success"],
                "percentage": pct,
                "output": result.get("stdout", "")[:500] if result["success"] else result.get("stderr", "")[:500]
            }
        
        elif name == "run_probe":
            intensity = args.get("intensity", "normal")
            configs = {
                "gentle": (3, 2000),
                "normal": (10, 1000),
                "aggressive": (25, 500)
            }
            req, delay = configs.get(intensity, configs["normal"])
            
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "rate_limit_probe.ps1",
                ["-RequestsPerSide", str(req), "-DelayMsBetweenRequests", str(delay)]
            )
            
            # Parse success rates from output
            success_info = "실행 완료"
            if result["success"]:
                stdout = result["stdout"]
                canary_match = re.search(r'Canary:.*?(\d+)/(\d+).*?Success', stdout)
                legacy_match = re.search(r'Legacy:.*?(\d+)/(\d+).*?Success', stdout)
                
                if canary_match and legacy_match:
                    success_info = f"Canary: {canary_match.group(1)}/{canary_match.group(2)}, Legacy: {legacy_match.group(1)}/{legacy_match.group(2)}"
            
            return {
                "success": result["success"],
                "intensity": intensity,
                "result": success_info
            }
        
        elif name == "get_logs":
            hours = int(args.get("hours", 1))
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "filter_logs_by_time.ps1",
                ["-Last", f"{hours}h", "-ShowSummary"]
            )
            return {
                "success": result["success"],
                "logs": result.get("stdout", "")[:1000] if result["success"] else "로그 조회 실패"
            }
        
        elif name == "generate_report":
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "generate_daily_report.ps1",
                ["-Hours", "24"]
            )
            return {
                "success": result["success"],
                "message": "리포트 생성 완료" if result["success"] else "리포트 생성 실패"
            }
        
        elif name == "rollback":
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "rollback_phase4_canary.ps1",
                ["-ProjectId", GCP_PROJECT, "-AutoApprove"]
            )
            return {
                "success": result["success"],
                "message": "롤백 완료" if result["success"] else "롤백 실패"
            }
        
        return {"success": False, "error": "Unknown function"}


# Initialize
executor = CommandExecutor()
gitco = GitcoAI(executor)


@app.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack Events API"""
    body = await request.json()
    
    # URL verification
    if body.get("type") == "url_verification":
        return JSONResponse({"challenge": body.get("challenge")})
    
    # Handle messages
    if body.get("type") == "event_callback":
        event = body.get("event", {})
        
        # Ignore bot messages
        if event.get("bot_id"):
            return JSONResponse({"ok": True})
        
        if event.get("type") == "message" and not event.get("subtype"):
            text = event.get("text", "")
            channel = event.get("channel")
            
            # Remove bot mention if present
            text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
            
            if text:
                # Generate response
                response_text = await gitco.chat(text, channel)
                
                # Send to Slack
                if slack_client:
                    try:
                        slack_client.chat_postMessage(
                            channel=channel,
                            text=response_text,
                            mrkdwn=True
                        )
                    except SlackApiError as e:
                        print(f"Slack error: {e}")
    
    return JSONResponse({"ok": True})


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "bot_active": bool(slack_client),
        "model": "gemini-2.0-flash-exp"
    }


if __name__ == "__main__":
    if not SLACK_BOT_TOKEN:
        print("⚠️  SLACK_BOT_TOKEN environment variable not set!")
    
    print(f"🤖 Starting Gitco - Natural Conversation Bot")
    print(f"📍 Project: {GCP_PROJECT}")
    print(f"🌐 Server: http://localhost:8080")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)
