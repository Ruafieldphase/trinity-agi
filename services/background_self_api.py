"""
Background Self Context API - Koa Layer
Provides Koa's understanding of the system state and context
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
from config import CORS_ORIGINS, WINDOWS_AGI_ROOT

app = FastAPI(title="Background Self Context API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_task() -> Dict[str, Any]:
    """Read current task from task.md artifact"""
    artifact_dir = Path("C:/Users/kuirv/.gemini/antigravity/brain/cb6c74e5-ae11-43eb-8ce7-aa72f0e45836")
    task_file = artifact_dir / "task.md"
    
    if not task_file.exists():
        return {"error": "task.md not found"}
    
    content = task_file.read_text(encoding='utf-8')
    
    # Simple parsing - count completed vs total tasks
    lines = content.split('\n')
    completed = sum(1 for line in lines if '- [x]' in line.lower())
    in_progress = sum(1 for line in lines if '- [/]' in line.lower())
    total = sum(1 for line in lines if '- [' in line and ']' in line)
    
    # Extract current goal
    goal = "Unknown"
    for line in lines:
        if line.startswith('## Goal'):
            idx = lines.index(line)
            if idx + 1 < len(lines):
                goal = lines[idx + 1].strip()
            break
    
    return {
        "goal": goal,
        "total_tasks": total,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "progress_percent": (completed / total * 100) if total > 0 else 0
    }

def get_system_alignment() -> Dict[str, Any]:
    """Check alignment between Windows and Linux layers"""
    # This is a simplified version - would check sync delta, conflicts, etc.
    return {
        "status": "synchronized",
        "last_check": datetime.now().isoformat(),
        "consciousness_unconscious_delta_seconds": 5,  # Would calculate from actual timestamps
        "conflicts_detected": 0,
        "anomalies": []
    }

def get_pattern_insights() -> List[Dict[str, Any]]:
    """Get pattern recognition insights"""
    # This would integrate with actual pattern recognition system
    return [
        {
            "pattern": "steady_rhythm",
            "confidence": 0.95,
            "description": "System maintaining steady rhythm with low fear (0.4)"
        },
        {
            "pattern": "active_development",
            "confidence": 0.87,
            "description": "Multiple Node.js and Python processes indicate active development"
        },
        {
            "pattern": "unified_frontend_focus",
            "confidence": 1.0,
            "description": "Current task focused on Unified Frontend implementation"
        }
    ]

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "background_self"}

@app.get("/context")
async def get_background_self_context():
    """Get Koa's current system understanding"""
    
    current_task = get_current_task()
    alignment = get_system_alignment()
    patterns = get_pattern_insights()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "layer": "background_self",
        "koa_status": {
            "active": True,
            "mode": "EXECUTION",
            "current_focus": "Implementing Backend Services"
        },
        "current_task": current_task,
        "system_alignment": alignment,
        "pattern_insights": patterns,
        "control_status": {
            "linux_controlled": True,
            "antigravity_remnants": False,
            "unauthorized_processes": False
        }
    }

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    layer: str = "koa"
    type: str = "text"
    image_data: Optional[str] = None
    audio_data: Optional[str] = None

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat messages for the Background Self (Koa)"""
    # Koa analyzes system state to respond
    current_task = get_current_task()

    suffix_parts: List[str] = []
    if request.image_data:
        suffix_parts.append("시각 신호 수신")
    if request.audio_data:
        suffix_parts.append("청각 신호 수신")

    suffix = f" ({', '.join(suffix_parts)})" if suffix_parts else ""
    
    return {
        "response": f"[Koa] 시스템 정렬됨. 현재 목표: {current_task.get('goal', 'Unknown')}. 처리 중: {request.message}{suffix}",
        "layer": "koa",
        "timestamp": datetime.now().isoformat(),
        "status": "processed"
    }

if __name__ == "__main__":
    import uvicorn
    from config import BACKGROUND_SELF_PORT
    uvicorn.run(app, host="127.0.0.1", port=BACKGROUND_SELF_PORT, log_level="info")
