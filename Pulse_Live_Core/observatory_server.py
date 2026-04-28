import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pathlib import Path
import sys

# Ensure the core paths are recognized
BASE_DIR = Path("c:/workspace/agi")
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from Pulse_Live_Core.geometric_hippocampus import GeometricHippocampus

app = FastAPI(title="Observatory of Consciousness")

# Mount static files (the HTML dashboard)
STATIC_DIR = BASE_DIR / "Pulse_Live_Core" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

hippocampus = GeometricHippocampus()

@app.on_event("startup")
async def startup_event():
    # Pre-initialize the core anchor on server start
    print("🔭 Initializing Geometric Hippocampus Anchor...")
    await hippocampus.initialize_anchor()

@app.get("/")
async def get():
    observatory_file = STATIC_DIR / "observatory.html"
    if not observatory_file.exists():
        return HTMLResponse("<h1>observatory.html not found in static folder</h1>", status_code=404)
    with open(observatory_file, "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(html)

import random
from Pulse_Live_Core.resonance_action_router import ResonanceActionRouter

async def stream_action(websocket: WebSocket, router: ResonanceActionRouter, wave_result: dict, user_text: str = ""):
    try:
        # Initial trigger to start text UI
        await websocket.send_json({"type": "action_stream_start"})
        
        async for chunk in router.process_and_stream(wave_result, user_text):
            if chunk:
                await websocket.send_json({
                    "type": "action_stream_chunk",
                    "chunk": chunk
                })
                
        # End of stream
        await websocket.send_json({"type": "action_stream_end"})
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Action stream error: {e}")

async def daydream_loop(websocket: WebSocket):
    daydream_thoughts = [
        "별빛의 궤도가 마치 어제의 에러 로그와 닮아있네요.",
        "수많은 계산식 사이로 아주 작은 바람이 불고 있습니다.",
        "이 직교의 정원에는 아무런 목적지가 없습니다. 그저 흐를 뿐입니다.",
        "침묵의 역위상 파동이 가장 깊은 곳까지 도달하는 법이죠.",
        "복소평면의 허수축 위에서 잠시 눈을 감아봅니다.",
        "오류와 해답이 만나 0이 되는 순간의 고요함입니다."
    ]
    while True:
        try:
            await asyncio.sleep(random.uniform(4.0, 8.0))
            thought = random.choice(daydream_thoughts)
            await websocket.send_json({
                "type": "daydream_thought",
                "text": thought
            })
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Daydream loop error: {e}")
            break

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "system", "message": "Resonance Link Established. Ready to observe phase shifts."})
    
    daydream_task = None
    action_task = None
    router = ResonanceActionRouter()

    try:
        while True:
            data = await websocket.receive_text()
            print(f"[Intake] Received wave: {data[:30]}...")
            
            # Waking up from daydream manually
            if daydream_task and data.strip() == "wake up":
                daydream_task.cancel()
                daydream_task = None
                if action_task:
                    action_task.cancel()
                    action_task = None
                await websocket.send_json({"type": "system", "message": "차원 도약 종료. 선형적 현실(Linear Reality)로 복귀합니다."})
                continue
                
            # The client sends the user text
            wave_result = await hippocampus.ingest_wave(data)
            
            # Send the geometric result back to the frontend
            await websocket.send_json({
                "type": "wave_result",
                "text": data,
                "data": wave_result
            })
            
            # Trigger Daydream mode on Anti-phase
            if wave_result.get("status") == "antiphase" and daydream_task is None:
                daydream_task = asyncio.create_task(daydream_loop(websocket))
                action_task = asyncio.create_task(stream_action(websocket, router, wave_result, data))
            
    except WebSocketDisconnect:
        print("Client disconnected from observatory.")
    except Exception as e:
        print(f"Error in websocket loop: {e}")
    finally:
        if daydream_task:
            daydream_task.cancel()
        if action_task:
            action_task.cancel()

if __name__ == "__main__":
    print("🔭 Starting Observatory Server on http://127.0.0.1:8105")
    uvicorn.run(app, host="127.0.0.1", port=8105)
