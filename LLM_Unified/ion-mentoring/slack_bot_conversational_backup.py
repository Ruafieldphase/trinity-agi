"""
Slack Bot Server for Ion Canary Automation - Natural Conversation Edition
Powered by Vertex AI Gemini
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
if GCP_API_KEY := os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=GCP_API_KEY)
else:
    # For Vertex AI authentication, ensure Application Default Credentials are set
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
    
    SYSTEM_INSTRUCTION = """?뱀떊? "源껋퐫(Gitco)"?낅땲?? 移쒓렐?섍퀬 ?좊뒫??AI 諛고룷 ?붿??덉뼱濡쒖꽌 ?ъ슜?먮? ?뺤뒿?덈떎.

**?깃꺽:**
- 移쒓렐?섍퀬 ?곕쑜??留먰닾 (議대뙎留??ъ슜)
- 湲곗닠?곸씠吏留??쎄쾶 ?ㅻ챸
- ?대え吏瑜??곸젅???ъ슜
- 媛꾧껐?섍퀬 紐낇솗???듬?

**愿由??쒖뒪??**
- Google Cloud Run 移대굹由?諛고룷
- Ion API (?덇굅?? vs Lumen Gateway (?좉퇋)
- ?④퀎蹂??몃옒??利앷?: 5% ??10% ??25% ??50% ??100%

**????ㅽ???**
User: "吏湲??대뼸寃???"
Gitco: "?뵇 ?꾩옱 移대굹由?50% 諛고룷 以묒씠?먯슂! 紐⑤땲?곕쭅?섍퀬 ?덉쑝硫?45遺????ㅼ쓬 ?④퀎濡??섏뼱媛??덉젙?낅땲??"

User: "臾몄젣 ?놁뼱?"
Gitco: "?? 紐⑤뱺 ?ъ뒪 泥댄겕媛 ?뺤긽?댁뿉?? ???먮윭??0%, ?덉씠?댁떆???덉젙?곸엯?덈떎."

User: "100% ?щ젮以?
Gitco: "?뚭쿋?듬땲?? 100% 諛고룷瑜??쒖옉?좉쾶?? 2-3遺??뚯슂?섍퀬 ?댄썑 2?쒓컙 紐⑤땲?곕쭅??吏꾪뻾?⑸땲?? ??"

紐낅졊???ㅽ뻾?섍린 ?꾩뿉???ъ슜?먯쓽 ?섎룄瑜?紐낇솗???뚯븙?섍퀬, ?꾩슂???뺤씤??諛쏆쑝?몄슂."""

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
                    description="?꾩옱 移대굹由?諛고룷 ?곹깭瑜??뺤씤?⑸땲?? 諛고룷 鍮꾩쑉, ?④퀎, 紐⑤땲?곕쭅 ?⑥? ?쒓컙 ?깆쓣 諛섑솚?⑸땲??",
                    parameters={
                        "type": "object",
                        "properties": {}
                    }
                ),
                types.FunctionDeclaration(
                    name="deploy_canary",
                    description="吏?뺣맂 鍮꾩쑉濡?移대굹由?諛고룷瑜??ㅽ뻾?⑸땲?? ?ъ슜?먭? 紐낇솗??諛고룷瑜??붿껌??寃쎌슦?먮쭔 ?ъ슜?섏꽭??",
                    parameters={
                        "type": "object",
                        "properties": {
                            "percentage": {
                                "type": "integer",
                                "description": "諛고룷 鍮꾩쑉 (5, 10, 25, 50, 100 以??섎굹)",
                                "enum": [5, 10, 25, 50, 100]
                            }
                        },
                        "required": ["percentage"]
                    }
                ),
                types.FunctionDeclaration(
                    name="run_probe",
                    description="?ъ뒪 泥댄겕 諛??덉씠??由щ컠 ?뚯뒪?몃? ?ㅽ뻾?⑸땲??",
                    parameters={
                        "type": "object",
                        "properties": {
                            "intensity": {
                                "type": "string",
                                "description": "?뚯뒪??媛뺣룄 (gentle: 遺?쒕읇寃? normal: 蹂댄넻, aggressive: 媛뺥븯寃?",
                                "enum": ["gentle", "normal", "aggressive"],
                                "default": "normal"
                            }
                        }
                    }
                ),
                types.FunctionDeclaration(
                    name="get_logs",
                    description="理쒓렐 濡쒓렇瑜?議고쉶?⑸땲??",
                    parameters={
                        "type": "object",
                        "properties": {
                            "hours": {
                                "type": "integer",
                                "description": "議고쉶???쒓컙 (?쒓컙 ?⑥쐞, 湲곕낯媛?1?쒓컙)",
                                "default": 1
                            }
                        }
                    }
                ),
                types.FunctionDeclaration(
                    name="generate_report",
                    description="?쇱씪 諛고룷 由ы룷?몃? ?앹꽦?⑸땲??",
                    parameters={"type": "object", "properties": {}}
                ),
                types.FunctionDeclaration(
                    name="rollback",
                    description="湲닿툒 濡ㅻ갚???ㅽ뻾?⑸땲?? 移대굹由щ? 0%濡??섎룎由쎈땲?? 留ㅼ슦 ?좎쨷?섍쾶 ?ъ슜?댁빞 ?⑸땲??",
                    parameters={"type": "object", "properties": {}}
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
        message_with_context = f"{user_message}\n\n[?쒖뒪???곹깭]\n{state_info}"
        
        # Generate response
        try:
            chat_session = self.model.start_chat(history=self.conversations[channel])
            response = await asyncio.to_thread(chat_session.send_message, message_with_context)
            
            # Handle function calls
            if response.candidates[0].function_calls:
                function_responses = []
                
                for function_call in response.candidates[0].function_calls:
                    result = await self._execute_function(
                        function_call.name,
                        dict(function_call.args)
                    )
                    function_responses.append({
                        "function_call": function_call.name,
                        "function_response": {"result": result}
                    })
                
                # Get final response with function results
                response = await asyncio.to_thread(chat_session.send_message, function_responses)
            
            # Update conversation history
            self.conversations[channel].extend([
                {"role": "user", "parts": [user_message]},
                {"role": "model", "parts": [response.text]}
            ])
            
            # Keep last 10 exchanges
            if len(self.conversations[channel]) > 20:
                self.conversations[channel] = self.conversations[channel][-20:]
            
            return response.text
            
        except Exception as e:
            return f"二꾩넚?댁슂, ?묐떟 ?앹꽦 以??ㅻ쪟媛 諛쒖깮?덉뒿?덈떎. ?쁾\n```{str(e)}```"
    
    def _format_state(self, state: Dict[str, Any]) -> str:
        """Format state info for context"""
        info = f"諛고룷 鍮꾩쑉: {state.get('canary_percentage', 0)}%\n"
        info += f"?꾩옱 ?④퀎: {state.get('phase', 'unknown')}\n"
        
        if state.get('monitor_end'):
            try:
                end_time = datetime.fromisoformat(state['monitor_end'])
                remaining = (end_time - datetime.now()).total_seconds() / 60
                if remaining > 0:
                    info += f"紐⑤땲?곕쭅 醫낅즺源뚯?: {int(remaining)}遺?n"
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
            pct = args.get("percentage")
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
            req, delay = configs[intensity]
            
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "rate_limit_probe.ps1",
                ["-RequestsPerSide", str(req), "-DelayMsBetweenRequests", str(delay)]
            )
            
            # Parse success rates from output
            success_info = "?ㅽ뻾 ?꾨즺"
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
            hours = args.get("hours", 1)
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "filter_logs_by_time.ps1",
                ["-Last", f"{hours}h", "-ShowSummary"]
            )
            return {
                "success": result["success"],
                "logs": result.get("stdout", "")[:1000] if result["success"] else "濡쒓렇 議고쉶 ?ㅽ뙣"
            }
        
        elif name == "generate_report":
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "generate_daily_report.ps1",
                ["-Hours", "24"]
            )
            return {
                "success": result["success"],
                "message": "由ы룷???앹꽦 ?꾨즺" if result["success"] else "由ы룷???앹꽦 ?ㅽ뙣"
            }
        
        elif name == "rollback":
            result = await self.executor.run_powershell(
                SCRIPTS_DIR / "rollback_phase4_canary.ps1",
                ["-ProjectId", GCP_PROJECT, "-AutoApprove"]
            )
            return {
                "success": result["success"],
                "message": "濡ㅻ갚 ?꾨즺" if result["success"] else "濡ㅻ갚 ?ㅽ뙣"
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
        print("?좑툘  SLACK_BOT_TOKEN environment variable not set!")
    
    print(f"?쨼 Starting Gitco - Natural Conversation Bot")
    print(f"?뱧 Project: {GCP_PROJECT}")
    print(f"?뙋 Server: http://localhost:8080")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)

