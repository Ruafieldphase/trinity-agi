"""
Consciousness Metrics API - Windows Layer
Provides real-time metrics from the Windows/Conscious layer
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import psutil
import json
from datetime import datetime
from typing import Dict, Any
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
from config import CORS_ORIGINS, BODY_PATH, MIND_PATH, OUTPUTS_PATH

app = FastAPI(title="Consciousness Metrics API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_folder_status(folder_path: Path) -> Dict[str, Any]:
    """Get status of a folder including latest file and timestamp"""
    if not folder_path.exists():
        return {"exists": False, "error": "Folder not found"}
    
    files = list(folder_path.glob("*.py"))
    if not files:
        return {"exists": True, "file_count": 0}
    
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return {
        "exists": True,
        "file_count": len(files),
        "latest_file": latest_file.name,
        "latest_timestamp": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat(),
    }

def get_windows_processes() -> Dict[str, int]:
    """Count relevant Windows processes"""
    processes = {
        "python": 0,
        "node": 0,
        "total": 0
    }
    
    for proc in psutil.process_iter(['name']):
        try:
            name = proc.info['name'].lower()
            processes["total"] += 1
            if 'python' in name:
                processes["python"] += 1
            elif 'node' in name:
                processes["node"] += 1
        except:
            pass
    
    return processes

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "consciousness"}

@app.get("/metrics")
async def get_consciousness_metrics():
    """Get current consciousness layer metrics"""
    
    # Get system resources
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    # Get folder statuses
    body_status = get_folder_status(BODY_PATH)
    mind_status = get_folder_status(MIND_PATH)
    
    # Get process counts
    processes = get_windows_processes()
    
    # Check if dashboard is running
    dashboard_running = any(
        proc.info['cmdline'] and 'dashboard' in ' '.join(proc.info['cmdline']).lower()
        for proc in psutil.process_iter(['cmdline'])
        if proc.info['cmdline']
    )
    
    return {
        "timestamp": datetime.now().isoformat(),
        "layer": "conscious",
        "ag_core": {
            "status": "active",
            "dashboard_running": dashboard_running
        },
        "body_folder": body_status,
        "mind_folder": mind_status,
        "system_resources": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024)
        },
        "processes": processes,
        "user_focus": {
            "current_task": "Unified Frontend Implementation",
            "active_tab": "consciousness_api.py"
        }
    }

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    layer: str = "conscious"
    type: str = "text"
    image_data: str = None
    audio_data: str = None

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat messages for the Conscious layer"""
    
    response_text = f"[Conscious] I hear you: {request.message}"
    
    if request.image_data:
        # Placeholder for vision processing
        response_text += "\n[Vision] I see the image you sent. (Vision processing not yet connected)"
        
    if request.audio_data:
        # Placeholder for audio processing
        response_text += "\n[Audio] I received your voice message. (Audio processing not yet connected)"
        
    return {
        "response": response_text,
        "layer": "conscious",
        "timestamp": datetime.now().isoformat(),
        "status": "processed"
    }

if __name__ == "__main__":
    import uvicorn
    from config import CONSCIOUSNESS_PORT
    uvicorn.run(app, host="127.0.0.1", port=CONSCIOUSNESS_PORT, log_level="info")
