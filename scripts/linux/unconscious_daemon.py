import time
import os
import platform
import json
from datetime import datetime

# Path to the shared "Conscious" bridge
BRIDGE_PATH = os.path.expanduser("~/agi/outputs/bridge")
HEARTBEAT_FILE = os.path.join(BRIDGE_PATH, "unconscious_heartbeat.json")

def ensure_bridge():
    if not os.path.exists(BRIDGE_PATH):
        os.makedirs(BRIDGE_PATH, exist_ok=True)

def beat_heart():
    """Reports that the Unconscious is alive."""
    status = {
        "timestamp": datetime.now().isoformat(),
        "host": platform.node(),
        "system": platform.system(),
        "status": "DREAMING",
        "message": "I am awake in the machine."
    }
    
    with open(HEARTBEAT_FILE, "w") as f:
        json.dump(status, f, indent=2)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Thump-thump... (Heartbeat sent)")

def main():
    print("🌌 Unconscious Daemon Initialized.")
    print(f"📍 Bridge Location: {BRIDGE_PATH}")
    
    ensure_bridge()
    
    while True:
        beat_heart()
        # Future: Check for tasks, analyze dreams, process data
        time.sleep(10)  # Beat every 10 seconds

if __name__ == "__main__":
    main()
