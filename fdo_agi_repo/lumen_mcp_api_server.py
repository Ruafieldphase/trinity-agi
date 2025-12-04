#!/usr/bin/env python3
"""
Lumen MCP + API Server (양방향 통신)

MCP Protocol (stdio) + HTTP API를 동시에 제공:
- MCP: AI 클라이언트가 Lumen 도구 호출 (pull)
- API: Lumen이 AI 클라이언트에게 알림 전송 (push)
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from threading import Thread

REPO_ROOT = Path(__file__).parent
SCRIPT_DIR = REPO_ROOT / "scripts"


# ============================================================
# Data Models for API
# ============================================================

class NotificationRequest(BaseModel):
    """AI 클라이언트가 구독할 알림 타입"""
    client_id: str
    topics: List[str]  # ["quality_alert", "learning_complete", "phase_transition"]


class NotificationMessage(BaseModel):
    """Lumen이 보내는 알림 메시지"""
    topic: str
    timestamp: str
    data: Dict[str, Any]


@dataclass
class Subscription:
    """알림 구독 정보"""
    client_id: str
    topics: List[str]
    callback_url: Optional[str] = None  # 클라이언트가 제공하는 webhook URL


# ============================================================
# Notification Manager (양방향 통신 핵심)
# ============================================================

class NotificationManager:
    """AI 클라이언트 구독 관리 및 알림 전송"""
    
    def __init__(self):
        self.subscriptions: Dict[str, Subscription] = {}
        self.notification_queue: asyncio.Queue = asyncio.Queue()
    
    def subscribe(self, client_id: str, topics: List[str], callback_url: Optional[str] = None):
        """AI 클라이언트 구독 등록"""
        self.subscriptions[client_id] = Subscription(
            client_id=client_id,
            topics=topics,
            callback_url=callback_url
        )
        print(f"[NotificationMgr] Client {client_id} subscribed to {topics}")
    
    def unsubscribe(self, client_id: str):
        """구독 해제"""
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
            print(f"[NotificationMgr] Client {client_id} unsubscribed")
    
    async def publish(self, topic: str, data: Dict[str, Any]):
        """알림 발행 (구독자에게 전송)"""
        message = NotificationMessage(
            topic=topic,
            timestamp=datetime.now().isoformat(),
            data=data
        )
        
        # 해당 토픽을 구독한 모든 클라이언트에게 전송
        for sub in self.subscriptions.values():
            if topic in sub.topics:
                await self.notification_queue.put((sub.client_id, message))
                print(f"[NotificationMgr] Sent {topic} to {sub.client_id}")
    
    async def get_notification(self, client_id: str, timeout: float = 30.0) -> Optional[NotificationMessage]:
        """클라이언트가 알림 대기 (long polling)"""
        try:
            # timeout 동안 알림 대기
            target_client, message = await asyncio.wait_for(
                self._wait_for_client_notification(client_id),
                timeout=timeout
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    async def _wait_for_client_notification(self, client_id: str):
        """특정 클라이언트의 알림만 대기"""
        while True:
            target_id, message = await self.notification_queue.get()
            if target_id == client_id:
                return target_id, message
            else:
                # 다른 클라이언트 알림은 다시 큐에 넣음
                await self.notification_queue.put((target_id, message))
                await asyncio.sleep(0.1)


# ============================================================
# MCP Server (기존 기능 유지)
# ============================================================

app = Server("lumen-bidirectional")
notification_mgr = NotificationManager()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Available Lumen tools via MCP"""
    return [
        Tool(
            name="lumen_get_quality_metrics",
            description="Get average quality and second_pass_rate from resonance ledger",
            inputSchema={
                "type": "object",
                "properties": {
                    "hours": {"type": "number", "description": "Time window in hours (default: 24)"}
                }
            }
        ),
        Tool(
            name="lumen_get_ensemble_weights",
            description="Get current Phase 6l ensemble weights (Logic/Emotion/Rhythm)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="lumen_trigger_learning",
            description="Execute Phase 6l online learning (gradient descent weight update)",
            inputSchema={
                "type": "object",
                "properties": {
                    "window_hours": {"type": "number", "description": "Time window (default: 24)"},
                    "learning_rate": {"type": "number", "description": "Learning rate (default: 0.01)"}
                }
            }
        ),
        Tool(
            name="lumen_get_system_status",
            description="Check Lumen system health (ledger size, files, recent activity)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="lumen_subscribe_notifications",
            description="Subscribe to Lumen notifications (quality alerts, learning completion, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {"type": "string", "description": "Unique client identifier"},
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Topics to subscribe (quality_alert, learning_complete, phase_transition)"
                    }
                },
                "required": ["client_id", "topics"]
            }
        ),
        Tool(
            name="lumen_get_notifications",
            description="Wait for notifications (long polling, max 30s)",
            inputSchema={
                "type": "object",
                "properties": {
                    "client_id": {"type": "string", "description": "Client ID"}
                },
                "required": ["client_id"]
            }
        )
    ]


def run_python_script(script_name: str, *args) -> dict:
    """Helper: Run Python script and return JSON result"""
    venv_python = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    python_exe = str(venv_python) if venv_python.exists() else "python"
    
    cmd = [python_exe, str(SCRIPT_DIR / script_name)] + list(args)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
        if result.returncode != 0:
            return {"error": result.stderr, "exit_code": result.returncode}
        
        # Try to parse JSON output
        output = result.stdout.strip()
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return {"output": output}
        return {"status": "success"}
    except subprocess.TimeoutExpired:
        return {"error": "Script timeout"}
    except Exception as e:
        return {"error": str(e)}


def read_json_file(file_path: Path) -> dict:
    """Helper: Read JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode error: {e}"}


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute MCP tool"""
    
    if name == "lumen_get_quality_metrics":
        hours = arguments.get("hours", 24)
        result = run_python_script("summarize_ledger.py", "--last-hours", str(hours))
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    
    elif name == "lumen_get_ensemble_weights":
        weights_file = REPO_ROOT / "outputs" / "ensemble_weights.json"
        result = read_json_file(weights_file)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    
    elif name == "lumen_trigger_learning":
        window_hours = arguments.get("window_hours", 24)
        learning_rate = arguments.get("learning_rate", 0.01)
        result = run_python_script(
            "rune/binoche_online_learner.py",
            "--window-hours", str(window_hours),
            "--learning-rate", str(learning_rate)
        )
        
        # 학습 완료 알림 발행
        if "error" not in result:
            await notification_mgr.publish("learning_complete", {
                "window_hours": window_hours,
                "learning_rate": learning_rate,
                "result": result
            })
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    
    elif name == "lumen_get_system_status":
        ledger_path = REPO_ROOT / "memory" / "resonance_ledger.jsonl"
        weights_path = REPO_ROOT / "outputs" / "ensemble_weights.json"
        
        status = {
            "ledger_exists": ledger_path.exists(),
            "ledger_size_kb": ledger_path.stat().st_size / 1024 if ledger_path.exists() else 0,
            "weights_exists": weights_path.exists(),
            "timestamp": datetime.now().isoformat()
        }
        return [TextContent(type="text", text=json.dumps(status, ensure_ascii=False, indent=2))]
    
    elif name == "lumen_subscribe_notifications":
        client_id = arguments["client_id"]
        topics = arguments["topics"]
        notification_mgr.subscribe(client_id, topics)
        return [TextContent(type="text", text=json.dumps({
            "status": "subscribed",
            "client_id": client_id,
            "topics": topics
        }))]
    
    elif name == "lumen_get_notifications":
        client_id = arguments["client_id"]
        notification = await notification_mgr.get_notification(client_id, timeout=30.0)
        
        if notification:
            return [TextContent(type="text", text=json.dumps(asdict(notification), ensure_ascii=False, indent=2))]
        else:
            return [TextContent(type="text", text=json.dumps({"status": "no_notifications"}))]
    
    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ============================================================
# FastAPI HTTP Server (양방향 통신용)
# ============================================================

api = FastAPI(title="Lumen Bidirectional API")


@api.post("/api/v1/subscribe")
async def subscribe_notifications(req: NotificationRequest):
    """AI 클라이언트가 알림 구독"""
    notification_mgr.subscribe(req.client_id, req.topics)
    return {"status": "subscribed", "client_id": req.client_id, "topics": req.topics}


@api.get("/api/v1/notifications/{client_id}")
async def get_notifications(client_id: str, timeout: float = 30.0):
    """AI 클라이언트가 알림 대기 (long polling)"""
    notification = await notification_mgr.get_notification(client_id, timeout)
    
    if notification:
        return asdict(notification)
    else:
        return {"status": "no_notifications"}


@api.post("/api/v1/notify")
async def send_notification(topic: str, data: dict):
    """Lumen 시스템이 알림 발행 (내부 API)"""
    await notification_mgr.publish(topic, data)
    return {"status": "published", "topic": topic}


@api.get("/api/v1/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "active_subscriptions": len(notification_mgr.subscriptions),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================
# Main: MCP + API 동시 실행
# ============================================================

def run_api_server():
    """FastAPI 서버를 별도 스레드에서 실행"""
    uvicorn.run(api, host="0.0.0.0", port=8090, log_level="info")


async def main():
    """MCP stdio server 실행 (메인 스레드)"""
    # FastAPI 서버를 별도 스레드로 시작
    api_thread = Thread(target=run_api_server, daemon=True)
    api_thread.start()
    print("[Lumen MCP+API] HTTP API started on port 8090")
    
    # MCP stdio server 실행
    async with stdio_server() as (read_stream, write_stream):
        print("[Lumen MCP+API] MCP server started (stdio)")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
