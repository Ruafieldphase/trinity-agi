
import asyncio
import json
import websockets
from pathlib import Path
import time
from datetime import datetime
from workspace_root import get_workspace_root

# Configuration
WORKSPACE_ROOT = get_workspace_root()
THOUGHT_STREAM_FILE = WORKSPACE_ROOT / "outputs" / "thought_stream_latest.json"
PORT = 8765

connected_clients = set()

async def register(websocket):
    connected_clients.add(websocket)
    print(f"[Stream] Client connected. Total: {len(connected_clients)}")
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)
        print(f"[Stream] Client disconnected. Total: {len(connected_clients)}")

async def broadcast_thought_stream():
    """Monitor file and broadcast changes."""
    last_mtime = 0
    
    print(f"[Stream] Monitoring {THOUGHT_STREAM_FILE}...")
    
    while True:
        try:
            if THOUGHT_STREAM_FILE.exists():
                mtime = THOUGHT_STREAM_FILE.stat().st_mtime
                if mtime > last_mtime:
                    last_mtime = mtime
                    
                    # Read file
                    try:
                        with open(THOUGHT_STREAM_FILE, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        # Add server timestamp
                        data['server_timestamp'] = datetime.now().isoformat()
                        
                        # Broadcast
                        if connected_clients:
                            message = json.dumps(data)
                            await asyncio.gather(
                                *[client.send(message) for client in connected_clients]
                            )
                            print(f"[Stream] Broadcasted thought update (Resonance: {data.get('metadata', {}).get('resonance_score', 0):.2f})")
                            
                    except json.JSONDecodeError:
                        pass # File might be writing
                    except Exception as e:
                        print(f"[Stream] Error reading/sending: {e}")
                        
            await asyncio.sleep(0.5) # Poll every 500ms
            
        except Exception as e:
            print(f"[Stream] Monitor loop error: {e}")
            await asyncio.sleep(1)

async def main():
    print(f"[Stream] Starting Resonance Stream on port {PORT}...")
    
    # Start WebSocket Server
    server = await websockets.serve(register, "localhost", PORT)
    
    # Start File Monitor
    await broadcast_thought_stream()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[Stream] Stopped.")
