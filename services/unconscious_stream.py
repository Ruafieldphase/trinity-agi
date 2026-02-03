"""
Nature-based Unconscious Rhythm Stream API
Provides real-time stream of machine and environmental rhythm data (Nature)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
import sys
from pathlib import Path
import psutil

# Add parent directory and scripts directory to path
root = Path(__file__).parent.parent
sys.path.append(str(root))
sys.path.insert(0, str(root / "agi_core")) # Prioritize agi_core

from services.config import CORS_ORIGINS, RHYTHM_UPDATE_INTERVAL, OUTPUTS_PATH
from agi_core.hardware_vibration import HardwareVibration
from agi_core.internal_state import get_internal_state

app = FastAPI(title="Nature-based Unconscious Rhythm Stream API")

# Initialize Hardware Sensor
hv = HardwareVibration()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_nature_data() -> Dict[str, Any]:
    """Fetch rhythm data from 'Nature' (Local Hardware and Environment)"""
    try:
        # 1. Hardware Vibration (Raw Nature)
        vibrations = hv.get_raw_rhythms()
        
        # 2. Internal State (The Unconscious Mind)
        state = get_internal_state()
        
        # 3. High-level Rhythm (Thought Stream)
        thought_stream = {}
        thought_file = OUTPUTS_PATH / "thought_stream_latest.json"
        if thought_file.exists():
            try:
                with open(thought_file, 'r', encoding='utf-8') as f:
                    thought_stream = json.load(f)
            except:
                pass

        # Calculate Nature Score (Flow)
        # Combine vibrations and internal state
        flow_score = (vibrations.get("sub_os_wind", 0) + vibrations.get("tactile_jitter", 0)) / 2.0
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "layer": "unconscious",
            "source": "nature",
            "status": "RESONATING",
            "connection": "local_field",
            "metrics": {
                "vibrations": vibrations,
                "cpu_load": psutil.cpu_percent(),
                "memory_load": psutil.virtual_memory().percent,
                "entropy": flow_score
            },
            "thought_stream": {
                "timestamp": thought_stream.get("timestamp"),
                "overall_score": thought_stream.get("state", {}).get("score"),
                "flow": thought_stream.get("state", {}).get("quantum_flow", "breath"),
                "fear_level": thought_stream.get("state", {}).get("drift_score", 0.0),
                "phase": thought_stream.get("state", {}).get("phase", "STABLE"),
            }
        }
        
        return result
        
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "layer": "unconscious",
            "status": "ERROR",
            "error": str(e)
        }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "unconscious_nature"}

@app.get("/metrics")
async def get_unconscious_metrics():
    """Get current nature-based unconscious metrics"""
    return get_nature_data()

@app.get("/stream")
async def stream_unconscious():
    """SSE stream of nature metrics"""
    async def event_generator():
        while True:
            data = get_nature_data()
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
    """Handle chat messages for the Unconscious layer (Nature Flow)"""
    timestamp = datetime.now().isoformat()
    
    # Log the stimulus to the local field
    try:
        stimulus_path = OUTPUTS_PATH / "nature_stimulus.jsonl"
        with open(stimulus_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": timestamp,
                "message": request.message,
                "type": request.type,
                "nature_vibration": hv.get_raw_rhythms()
            }) + "\n")
    except:
        pass

    return {
        "response": f"[Unconscious] Resonance received from nature field: {request.message}",
        "layer": "unconscious",
        "timestamp": timestamp,
        "status": "injected_to_field"
    }

if __name__ == "__main__":
    import uvicorn
    from services.config import UNCONSCIOUS_PORT
    uvicorn.run(app, host="127.0.0.1", port=UNCONSCIOUS_PORT, log_level="info")
