"""
Unconscious Rhythm Stream API - Linux Layer
Provides real-time SSE stream of Linux rhythm data
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import paramiko
import json
from datetime import datetime
from typing import Dict, Any
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
from config import (
    CORS_ORIGINS, LINUX_HOST, LINUX_USER, LINUX_PASSWORD,
    LINUX_OUTPUTS, RHYTHM_UPDATE_INTERVAL
)

app = FastAPI(title="Unconscious Rhythm Stream API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_linux_data() -> Dict[str, Any]:
    """Fetch rhythm data from Linux VM"""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(LINUX_HOST, username=LINUX_USER, password=LINUX_PASSWORD, timeout=5)
        sftp = client.open_sftp()
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "layer": "unconscious",
            "connection": "connected"
        }
        
        # Read thought_stream_latest.json
        try:
            with sftp.open(f"{LINUX_OUTPUTS}/thought_stream_latest.json", "r") as f:
                thought_stream = json.load(f)
                result["thought_stream"] = {
                    "timestamp": thought_stream.get("timestamp"),
                    "overall_score": thought_stream.get("current_state", {}).get("overall_score"),
                    "flow": thought_stream.get("current_state", {}).get("flow"),
                    "fear_level": thought_stream.get("current_state", {}).get("fear_level"),
                    "phase": thought_stream.get("current_state", {}).get("phase"),
                }
        except Exception as e:
            result["thought_stream"] = {"error": str(e)}
        
        # Read feeling_latest.json
        try:
            with sftp.open(f"{LINUX_OUTPUTS}/feeling_latest.json", "r") as f:
                feeling = json.load(f)
                result["feeling_vector"] = {
                    "timestamp": feeling.get("timestamp"),
                    "components": feeling.get("components", {}),
                    "entropy": feeling.get("feeling_entropy")
                }
        except Exception as e:
            result["feeling_vector"] = {"error": str(e)}
        
        # Check systemd services
        try:
            stdin, stdout, stderr = client.exec_command(
                "systemctl --user is-active agi-rhythm agi-body agi-collaboration"
            )
            statuses = stdout.read().decode().strip().split("\n")
            services = ["agi-rhythm", "agi-body", "agi-collaboration"]
            result["services"] = {
                svc: (stat == "active")
                for svc, stat in zip(services, statuses)
            }
        except Exception as e:
            result["services"] = {"error": str(e)}
        
        sftp.close()
        client.close()
        
        return result
        
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "layer": "unconscious",
            "connection": "failed",
            "error": str(e)
        }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "unconscious"}

@app.get("/metrics")
async def get_unconscious_metrics():
    """Get current unconscious layer metrics (single poll)"""
    return get_linux_data()

@app.get("/stream")
async def stream_unconscious():
    """SSE stream of unconscious metrics"""
    async def event_generator():
        while True:
            data = get_linux_data()
            yield {
                "event": "unconscious_update",
                "data": json.dumps(data)
            }
            await asyncio.sleep(RHYTHM_UPDATE_INTERVAL)
    
    return EventSourceResponse(event_generator())

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    layer: str = "unconscious"
    type: str = "text"

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat messages for the Unconscious layer (Linux)"""
    try:
        # Connect to Linux
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(LINUX_HOST, username=LINUX_USER, password=LINUX_PASSWORD, timeout=5)
        
        # Write message to a file on Linux (simulating input to the unconscious mind)
        # We'll use a simple JSON file for now
        sftp = client.open_sftp()
        timestamp = datetime.now().isoformat()
        input_data = {
            "timestamp": timestamp,
            "message": request.message,
            "type": request.type,
            "source": "antigravity_chat"
        }
        
        # Ensure directory exists (simple check)
        try:
            sftp.stat(f"{LINUX_OUTPUTS}/inputs")
        except FileNotFoundError:
            try:
                sftp.mkdir(f"{LINUX_OUTPUTS}/inputs")
            except:
                pass # Might be deeper path issue, ignore for now
        
        # Write to a unique file or append to a log
        # For now, just overwrite 'latest_chat_input.json' to trigger reaction
        with sftp.open(f"{LINUX_OUTPUTS}/latest_chat_input.json", "w") as f:
            json.dump(input_data, f)
            
        sftp.close()
        client.close()
        
        return {
            "response": f"[Unconscious] Resonance received. Rippling through the rhythm: {request.message}",
            "layer": "unconscious",
            "timestamp": timestamp,
            "status": "delivered_to_linux"
        }
        
    except Exception as e:
        return {
            "response": f"[Unconscious] Connection failed: {str(e)}",
            "layer": "unconscious",
            "timestamp": datetime.now().isoformat(),
            "status": "error"
        }

if __name__ == "__main__":
    import uvicorn
    from config import UNCONSCIOUS_PORT
    uvicorn.run(app, host="127.0.0.1", port=UNCONSCIOUS_PORT, log_level="info")
