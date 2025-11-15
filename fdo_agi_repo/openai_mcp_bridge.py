#!/usr/bin/env python3
"""
OpenAI ChatGPT + MCP + Lua Bridge

OpenAI API를 MCP 서버로 노출하고, Lua 스크립트와 양방향 통신을 지원합니다.

Architecture:
    ChatGPT (OpenAI API)
        ↕
    MCP Server (this module)
        ↕
    Lua Scripts / AGI Core
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from openai import AsyncOpenAI
except ImportError:
    print("❌ openai package not installed. Run: pip install openai")
    exit(1)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("❌ MCP SDK not installed. Run: pip install mcp")
    exit(1)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from threading import Thread

# Paths
REPO_ROOT = Path(__file__).parent
OUTPUTS_DIR = REPO_ROOT.parent / "outputs"
LUA_REQUESTS_DIR = OUTPUTS_DIR / "lua_requests"
LUA_RESPONSES_DIR = OUTPUTS_DIR / "lua_responses"
CHATGPT_LOG = OUTPUTS_DIR / "chatgpt_bridge_log.jsonl"

# Ensure directories exist
LUA_REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
LUA_RESPONSES_DIR.mkdir(parents=True, exist_ok=True)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY not set. Using MCP-only mode.")
    client = None
else:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Initialize MCP server
app = Server("openai-lua-bridge")

# Initialize FastAPI
api = FastAPI(title="OpenAI ChatGPT Bridge API")


# ============================================================
# Data Models
# ============================================================

class ChatRequest(BaseModel):
    """ChatGPT 요청"""
    prompt: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000
    request_id: Optional[str] = None
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    """ChatGPT 응답"""
    response: str
    model: str
    tokens_used: Dict[str, int]
    request_id: str
    timestamp: str


@dataclass
class LuaRequest:
    """Lua 스크립트 요청"""
    prompt: str
    request_id: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LuaResponse:
    """Lua 스크립트 응답"""
    request_id: str
    response: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


# ============================================================
# OpenAI ChatGPT Wrapper
# ============================================================

async def call_chatgpt(
    prompt: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    OpenAI ChatGPT API 호출
    
    Returns:
        {
            "response": str,
            "model": str,
            "tokens": {"prompt": int, "completion": int, "total": int}
        }
    """
    if not client:
        raise RuntimeError("OpenAI API key not configured")
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return {
        "response": response.choices[0].message.content,
        "model": response.model,
        "tokens": {
            "prompt": response.usage.prompt_tokens,
            "completion": response.usage.completion_tokens,
            "total": response.usage.total_tokens
        }
    }


def log_chatgpt_call(request: Dict[str, Any], response: Dict[str, Any]):
    """ChatGPT 호출 로깅"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "request": request,
        "response": response
    }
    with open(CHATGPT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# ============================================================
# Lua Bridge Functions
# ============================================================

def scan_lua_requests() -> List[Path]:
    """Lua 요청 스캔"""
    return sorted(LUA_REQUESTS_DIR.glob("*.json"))


def read_lua_request(path: Path) -> Optional[LuaRequest]:
    """Lua 요청 읽기"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return LuaRequest(
            prompt=data["prompt"],
            request_id=data.get("request_id", path.stem),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata")
        )
    except Exception as e:
        print(f"❌ Failed to read Lua request {path}: {e}")
        return None


def write_lua_response(response: LuaResponse):
    """Lua 응답 쓰기"""
    response_path = LUA_RESPONSES_DIR / f"response_{response.request_id}.json"
    with open(response_path, "w", encoding="utf-8") as f:
        json.dump(asdict(response), f, ensure_ascii=False, indent=2)


async def process_lua_request(request: LuaRequest) -> LuaResponse:
    """Lua 요청 처리 (ChatGPT 호출)"""
    try:
        result = await call_chatgpt(
            prompt=request.prompt,
            system_prompt="You are Lumen, an AGI assistant integrated with Lua scripting."
        )
        
        response = LuaResponse(
            request_id=request.request_id,
            response=result["response"],
            timestamp=datetime.now().isoformat(),
            metadata={"tokens": result["tokens"], "model": result["model"]}
        )
        
        # Log
        log_chatgpt_call(
            request=asdict(request),
            response=asdict(response)
        )
        
        return response
    
    except Exception as e:
        print(f"❌ Error processing Lua request: {e}")
        return LuaResponse(
            request_id=request.request_id,
            response=f"Error: {str(e)}",
            timestamp=datetime.now().isoformat(),
            metadata={"error": str(e)}
        )


# ============================================================
# MCP Tools
# ============================================================

@app.list_tools()
async def list_tools() -> List[Tool]:
    """MCP 도구 목록"""
    return [
        Tool(
            name="chatgpt_query",
            description="Query OpenAI ChatGPT API",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "User prompt"},
                    "model": {"type": "string", "default": "gpt-4o-mini"},
                    "temperature": {"type": "number", "default": 0.7},
                    "max_tokens": {"type": "integer", "default": 1000}
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="process_lua_requests",
            description="Process pending Lua requests from lua_requests/ directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_requests": {"type": "integer", "default": 10}
                }
            }
        ),
        Tool(
            name="get_chatgpt_log",
            description="Get recent ChatGPT API calls log",
            inputSchema={
                "type": "object",
                "properties": {
                    "last_n": {"type": "integer", "default": 10}
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """MCP 도구 실행"""
    
    if name == "chatgpt_query":
        prompt = arguments["prompt"]
        model = arguments.get("model", "gpt-4o-mini")
        temperature = arguments.get("temperature", 0.7)
        max_tokens = arguments.get("max_tokens", 1000)
        
        result = await call_chatgpt(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    elif name == "process_lua_requests":
        max_requests = arguments.get("max_requests", 10)
        requests = scan_lua_requests()[:max_requests]
        
        processed = []
        for req_path in requests:
            req = read_lua_request(req_path)
            if req:
                resp = await process_lua_request(req)
                write_lua_response(resp)
                processed.append({
                    "request_id": req.request_id,
                    "status": "success"
                })
                req_path.unlink()  # Remove processed request
        
        return [TextContent(
            type="text",
            text=json.dumps({"processed": processed}, ensure_ascii=False, indent=2)
        )]
    
    elif name == "get_chatgpt_log":
        last_n = arguments.get("last_n", 10)
        
        if not CHATGPT_LOG.exists():
            return [TextContent(type="text", text="No log entries found")]
        
        with open(CHATGPT_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        recent = [json.loads(line) for line in lines[-last_n:]]
        
        return [TextContent(
            type="text",
            text=json.dumps(recent, ensure_ascii=False, indent=2)
        )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


# ============================================================
# FastAPI HTTP Endpoints
# ============================================================

@api.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """ChatGPT API 엔드포인트"""
    result = await call_chatgpt(
        prompt=request.prompt,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        system_prompt=request.system_prompt
    )
    
    return ChatResponse(
        response=result["response"],
        model=result["model"],
        tokens_used=result["tokens"],
        request_id=request.request_id or f"http_{datetime.now().timestamp()}",
        timestamp=datetime.now().isoformat()
    )


@api.get("/api/v1/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "ok",
        "openai_configured": client is not None,
        "pending_lua_requests": len(scan_lua_requests()),
        "timestamp": datetime.now().isoformat()
    }


def run_api_server():
    """FastAPI 서버 실행 (별도 스레드)"""
    uvicorn.run(api, host="127.0.0.1", port=8094, log_level="info")


# ============================================================
# Main Entry Point
# ============================================================

async def main():
    """MCP stdio server 실행"""
    # Start FastAPI in background
    api_thread = Thread(target=run_api_server, daemon=True)
    api_thread.start()
    print("[OpenAI Bridge] HTTP API started on port 8094")
    
    # Run MCP server
    async with stdio_server() as (read_stream, write_stream):
        print("[OpenAI Bridge] MCP server started (stdio)")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
